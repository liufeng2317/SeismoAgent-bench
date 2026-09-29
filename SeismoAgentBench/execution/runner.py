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
import shutil
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from SeismoAgentBench.task.validation import ValidationError, load_json, load_task, validate_manifest


class ExecutionError(RuntimeError):
    """Raised when a run cannot be prepared or completed."""


@dataclass(frozen=True)
class RunContext:
    run_id: str
    root: Path
    control: Path
    task_path: Path
    manifest_path: Path
    agent: Path
    work: Path
    output: Path
    home: Path
    tmp: Path
    log: Path
    record: Path
    result: Path

    @property
    def environment(self) -> dict[str, str]:
        return {
            "BENCH_TASK_SPEC": str(self.task_path),
            "BENCH_INPUT_MANIFEST": str(self.manifest_path),
            "BENCH_WORK": str(self.work),
            "BENCH_OUTPUT": str(self.output),
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def _context(root: Path, run_id: str, task: dict[str, Any], manifest: dict[str, Any],
             *, resume: bool = False) -> tuple[RunContext, int]:
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
    agent = run / "agent"
    record = run / "record"
    control.mkdir(exist_ok=True)
    agent.mkdir(exist_ok=True)
    record.mkdir(exist_ok=True)
    task_path = control / "task_spec.json"
    manifest_path = control / "input_manifest.json"
    _write_json(task_path, task)
    _write_json(manifest_path, manifest)
    directories = {name: agent / name for name in ("work", "output", "home", "tmp")}
    for directory in directories.values():
        directory.mkdir()
    return (RunContext(run_id, run, control, task_path, manifest_path, agent, **directories,
                       log=agent / "execution.log", record=record,
                       result=record / "run_result.json"), attempt)


def _environment(context: RunContext, extra_env: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "HOME": str(context.home),
        "TMPDIR": str(context.tmp),
        "XDG_CACHE_HOME": str(context.home / "cache"),
        "PYTHONNOUSERSITE": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    env.update(context.environment)
    if extra_env:
        if not all(isinstance(key, str) and key and isinstance(value, str)
                   for key, value in extra_env.items()):
            raise ExecutionError("extra_env must map non-empty names to strings")
        env.update(extra_env)
    return env


def run_command(task_path: str | Path, manifest_path: str | Path, command: Sequence[str],
                 run_root: str | Path, run_id: str, *, timeout: float = 600,
                 extra_env: Mapping[str, str] | None = None,
                 resume: bool = False) -> dict[str, Any]:
    """Validate inputs and run one command in a fresh trusted-development context."""
    if not command or not all(isinstance(item, str) and item for item in command):
        raise ExecutionError("command must be a non-empty sequence of strings")
    if timeout <= 0:
        raise ExecutionError("timeout must be positive")
    try:
        task = load_task(task_path)
        manifest = load_json(manifest_path)
        validate_manifest(manifest, task=task, check_paths=False)
    except ValidationError as exc:
        raise ExecutionError(f"input validation failed: {exc}") from exc
    context, attempt = _context(Path(run_root).resolve(), run_id, task, manifest, resume=resume)
    result: dict[str, Any] = {
        "run_id": run_id,
        "state": "preparing",
        "execution_profile": "trusted-development",
        "formal_evaluation_eligible": False,
        "task_id": task["task_id"],
        "task_version": task["version"],
        "manifest_schema_version": manifest["schema_version"],
        "command": list(command),
        "timeout_s": timeout,
        "injected_environment_keys": sorted(extra_env) if extra_env else [],
        "attempt": attempt,
        "started_at": _now(),
    }
    _write_json(context.result, result)
    with context.log.open("wb") as log:
        process: subprocess.Popen[bytes] | None = None
        try:
            result["state"] = "running"
            _write_json(context.result, result)
            process = subprocess.Popen(list(command), cwd=context.work, env=_environment(context, extra_env),
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                result["exit_code"] = process.wait(timeout=timeout)
                result["state"] = "completed" if process.returncode == 0 else "execution_failed"
                if process.returncode != 0:
                    reason, retryable = _failure_class(context.log)
                    result["failure_reason"] = reason
                    result["retryable"] = retryable
                    if retryable:
                        result["state"] = "execution_retryable"
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                result["state"] = "execution_timeout"
                result["failure_reason"] = "timeout"
        except OSError as exc:
            result["state"] = "execution_failed"
            result["failure_reason"] = "launcher_error"
            result["error"] = str(exc)
        finally:
            result["finished_at"] = _now()
            _write_json(context.result, result)
    return result
