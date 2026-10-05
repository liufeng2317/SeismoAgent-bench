"""Minimal trusted-development execution runner.

This module records a command execution; it is not a security sandbox and does
not provide formal evaluation isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import selectors
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence

from SeismoAgentBench.reporting.transcript import append_execution_line, summarize_usage
from SeismoAgentBench.execution.auth import prepare_codex_runtime_home
from SeismoAgentBench.task.validation import ValidationError, load_json, load_task, validate_manifest


class ExecutionError(RuntimeError):
    """Raised when a run cannot be prepared or completed."""


@dataclass(frozen=True)
class RunContext:
    run_id: str
    root: Path
    control: Path
    task_path: Path
    manifest_path: Path | None
    output_contract_path: Path | None
    work: Path
    log: Path
    record: Path
    result: Path

    @property
    def environment(self) -> dict[str, str]:
        values = {
            "BENCH_TASK_SPEC": str(self.task_path),
            "BENCH_WORK": str(self.work),
            "BENCH_INPUT": str(self.work / "input"),
            # Output paths are relative to the single Agent-controlled work
            # directory. The Agent may choose any internal layout.
            "BENCH_OUTPUT": str(self.work),
        }
        if self.manifest_path is not None:
            values["BENCH_INPUT_MANIFEST"] = str(self.manifest_path)
        if self.output_contract_path is not None:
            values["BENCH_OUTPUT_CONTRACT"] = str(self.output_contract_path)
        return values


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _prepare_input_view(work: Path, manifest: Mapping[str, Any] | None) -> None:
    """Create a stable, read-only view of declared inputs below ``work``.

    Each entry is linked directly as ``work/input/<source-basename>``. The
    entry ID remains metadata; it is not used to rename the source. This
    avoids copying large data while keeping the agent's input path short and
    run-local.
    """
    view = work / "input"
    if view.exists() or view.is_symlink():
        raise ExecutionError(f"input view already exists: {view}")
    view.mkdir(mode=0o755)
    if manifest is None:
        return
    for entry in (manifest or {}).get("entries", []):
        if not isinstance(entry, Mapping):
            continue
        raw_path = entry.get("path")
        entry_id = entry.get("id")
        entry_type = entry.get("type")
        if not isinstance(raw_path, str) or not isinstance(entry_id, str):
            continue
        source = Path(raw_path)
        if not source.exists():
            continue
        source = source.resolve(strict=True)
        target = view / source.name
        if target.exists() or target.is_symlink():
            raise ExecutionError(
                f"duplicate input source basename {source.name!r} "
                f"for entry {entry_id!r}: {target}"
            )
        target.symlink_to(source, target_is_directory=entry_type == "folder")
    view.chmod(0o555)


def _failure_class(log: Path) -> tuple[str, bool]:
    """Classify known provider failures without treating output as success."""
    try:
        text = log.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return "nonzero_exit", False
    if "selected model is at capacity" in text or "model is at capacity" in text:
        return "capacity", True
    if "usage limit" in text or "hit your usage limit" in text:
        return "usage_limit", False
    return "nonzero_exit", False


def _stream_process(process: subprocess.Popen[bytes], event_stream: Any,
                    human_stream: Any, timeout: float) -> None:
    """Stream process output while retaining a timeout that can interrupt reads."""
    if process.stdout is None:
        process.wait(timeout=timeout)
        return
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, timeout)
            ready = selector.select(remaining)
            if not ready:
                raise subprocess.TimeoutExpired(process.args, timeout)
            for key, _ in ready:
                line = key.fileobj.readline()
                if line:
                    append_execution_line(line, event_stream, human_stream)
                else:
                    selector.unregister(key.fileobj)
            if process.poll() is not None and not selector.get_map():
                break
    finally:
        selector.close()


def _archive_retry(run: Path) -> int:
    attempts = run / "attempts"
    attempts.mkdir(exist_ok=True)
    existing = sorted(item for item in attempts.iterdir() if item.is_dir() and item.name.startswith("attempt-"))
    number = len(existing) + 1
    archive = attempts / f"attempt-{number:03d}"
    archive.mkdir()
    preserved = {"control", "attempts"}
    for item in list(run.iterdir()):
        if item.name in preserved:
            continue
        shutil.move(str(item), str(archive / item.name))
    return number


def _context(root: Path, run_id: str, task: dict[str, Any], manifest: dict[str, Any] | None,
    task_source: Path,
             *, resume: bool = False, agent_prompt: str | None = None) -> tuple[RunContext, int]:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ExecutionError("run_id must be a non-empty single path component")
    run = root / run_id
    attempt = 1
    if run.exists():
        if not resume:
            raise ExecutionError(f"run already exists: {run}")
        previous_path = run / "record" / "run_result.json"
        if not previous_path.is_file():
            raise ExecutionError("cannot resume a run without run_result.json")
        previous = load_json(previous_path)
        if previous.get("state") != "execution_retryable":
            raise ExecutionError("only execution_retryable runs can be resumed")
        attempt = _archive_retry(run) + 1
    else:
        run.mkdir(parents=True)
    control = run / "control"
    record = run / "record"
    control.mkdir(exist_ok=True)
    work = run / "work"
    work.mkdir(exist_ok=True)
    record.mkdir(exist_ok=True)
    _prepare_input_view(work, manifest)
    task_path = control / "task_spec.json"
    manifest_path = control / "input_manifest.json"
    output_contract_path = control / "output_contract.json"
    task_prompt_path = control / "task_prompt.md"
    # Keep task semantics and output requirements as separate immutable
    # control snapshots. ``load_task`` resolves the contract for evaluation,
    # so remove that derived expansion from the task snapshot.
    task_snapshot = dict(task)
    artifacts = task_snapshot.pop("output_artifacts", None)
    prompt = task_snapshot.pop("task_prompt", "")
    task_snapshot["task_prompt_file"] = "task_prompt.md"
    contract = None
    contract_ref = task_snapshot.get("output_contract")
    if isinstance(contract_ref, str):
        source_contract = task_source.parent / contract_ref
        if source_contract.is_file():
            contract = load_json(source_contract)
    if contract is None and (contract_ref is not None or artifacts is not None):
        contract = {"schema_version": 1, "artifacts": artifacts or []}
    _write_json(task_path, task_snapshot)
    if manifest is not None:
        _write_json(manifest_path, manifest)
    if contract is not None:
        _write_json(output_contract_path, contract)
    task_prompt_path.write_text(str(prompt).strip() + "\n", encoding="utf-8")
    if agent_prompt is not None:
        (control / "agent_prompt.md").write_text(agent_prompt, encoding="utf-8")
    return (RunContext(run_id, run, control, task_path,
                       manifest_path if manifest is not None else None,
                       output_contract_path if contract is not None else None, work,
                       log=record / "execution.log", record=record,
                       result=record / "run_result.json"), attempt)


def _environment(context: RunContext, extra_env: Mapping[str, str] | None = None,
                 auth_source_home: str | Path | None = None) -> tuple[dict[str, str], Path]:
    runtime_root = Path(tempfile.mkdtemp(prefix=f"seismoagentbench-{context.run_id}-"))
    home = runtime_root / "home"
    tmp = runtime_root / "tmp"
    home.mkdir()
    tmp.mkdir()
    env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "HOME": str(home),
        "TMPDIR": str(tmp),
        "XDG_CACHE_HOME": str(home / "cache"),
        "PYTHONNOUSERSITE": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    env.update(context.environment)
    if auth_source_home is not None:
        try:
            env["CODEX_HOME"] = str(prepare_codex_runtime_home(runtime_root, auth_source_home))
        except BaseException:
            shutil.rmtree(runtime_root, ignore_errors=True)
            raise
    if extra_env:
        if not all(isinstance(key, str) and key and isinstance(value, str)
                   for key, value in extra_env.items()):
            raise ExecutionError("extra_env must map non-empty names to strings")
        env.update(extra_env)
    return env, runtime_root


def run_command(task_path: str | Path, manifest_path: str | Path | None, command: Sequence[str],
                run_root: str | Path, run_id: str, *, timeout: float = 600,
                extra_env: Mapping[str, str] | None = None,
                resume: bool = False, agent_prompt: str | None = None,
                auth_source_home: str | Path | None = None) -> dict[str, Any]:
    """Validate inputs and run one command in a fresh trusted-development context."""
    if not command or not all(isinstance(item, str) and item for item in command):
        raise ExecutionError("command must be a non-empty sequence of strings")
    if timeout <= 0:
        raise ExecutionError("timeout must be positive")
    try:
        task = load_task(task_path)
        manifest = None
        if manifest_path is not None:
            manifest = load_json(manifest_path)
            validate_manifest(manifest, task=task, check_paths=False)
    except ValidationError as exc:
        raise ExecutionError(f"input validation failed: {exc}") from exc
    context, attempt = _context(Path(run_root).resolve(), run_id, task, manifest,
                                 Path(task_path).resolve(),
                                 resume=resume, agent_prompt=agent_prompt)
    result: dict[str, Any] = {
        "run_id": run_id,
        "state": "preparing",
        "execution_profile": "trusted-development",
        "formal_evaluation_eligible": False,
        "task_id": task["task_id"],
        "task_version": task["version"],
        "manifest_schema_version": manifest.get("schema_version") if manifest else None,
        "command": list(command),
        "timeout_s": timeout,
        "injected_environment_keys": sorted(extra_env) if extra_env else [],
        "attempt": attempt,
        "started_at": _now(),
    }
    _write_json(context.result, result)
    runtime_root: Path | None = None
    event_log = context.log.with_name("execution.jsonl")
    with event_log.open("w", encoding="utf-8") as event_stream, context.log.open("w", encoding="utf-8") as human_stream:
        process: subprocess.Popen[bytes] | None = None
        try:
            result["state"] = "running"
            _write_json(context.result, result)
            env, runtime_root = _environment(context, extra_env, auth_source_home)
            process = subprocess.Popen(list(command), cwd=context.work, env=env,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                _stream_process(process, event_stream, human_stream, timeout)
                result["exit_code"] = process.wait()
                result["state"] = "completed" if process.returncode == 0 else "execution_failed"
                if process.returncode != 0:
                    reason, retryable = _failure_class(event_log)
                    result["failure_reason"] = reason
                    result["retryable"] = retryable
                    if retryable:
                        result["state"] = "execution_retryable"
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                if process.stdout is not None:
                    for line in process.stdout:
                        append_execution_line(line, event_stream, human_stream)
                result["state"] = "execution_timeout"
                result["failure_reason"] = "timeout"
        except OSError as exc:
            result["state"] = "execution_failed"
            result["failure_reason"] = "launcher_error"
            result["error"] = str(exc)
        finally:
            if event_log.stat().st_size == 0:
                append_execution_line(f"launcher produced no output\n", event_stream, human_stream)
            if process is not None and process.stdout is not None:
                process.stdout.close()
            if runtime_root is not None:
                shutil.rmtree(runtime_root, ignore_errors=True)
            usage_path = context.record / "usage_summary.json"
            _write_json(usage_path, summarize_usage(event_log))
            result["usage_summary"] = "record/usage_summary.json"
            result["finished_at"] = _now()
            _write_json(context.result, result)
    return result
