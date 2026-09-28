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
import subprocess
import sys
import time
from typing import Any, Sequence

from SeismoAgentBench.task.validation import ValidationError, load_json, validate_manifest, validate_task


class ExecutionError(RuntimeError):
    """Raised when a run cannot be prepared or completed."""


@dataclass(frozen=True)
class RunContext:
    run_id: str
    root: Path
    task_path: Path
    manifest_path: Path
    work: Path
    output: Path
    home: Path
    tmp: Path
    log: Path
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


def _context(root: Path, run_id: str, task: dict[str, Any], manifest: dict[str, Any]) -> RunContext:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ExecutionError("run_id must be a non-empty single path component")
    run = root / run_id
    if run.exists():
        raise ExecutionError(f"run already exists: {run}")
    run.mkdir(parents=True)
    task_path = run / "task_spec.json"
    manifest_path = run / "input_manifest.json"
    _write_json(task_path, task)
    _write_json(manifest_path, manifest)
    directories = {name: run / name for name in ("work", "output", "home", "tmp")}
    for directory in directories.values():
        directory.mkdir()
    return RunContext(run_id, run, task_path, manifest_path, **directories,
                      log=run / "execution.log", result=run / "run_result.json")


def _environment(context: RunContext) -> dict[str, str]:
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
    return env


def run_command(task_path: str | Path, manifest_path: str | Path, command: Sequence[str],
                run_root: str | Path, run_id: str, *, timeout: float = 600) -> dict[str, Any]:
    """Validate inputs and run one command in a fresh trusted-development context."""
    if not command or not all(isinstance(item, str) and item for item in command):
        raise ExecutionError("command must be a non-empty sequence of strings")
    if timeout <= 0:
        raise ExecutionError("timeout must be positive")
    task = load_json(task_path)
    manifest = load_json(manifest_path)
    try:
        validate_task(task)
        validate_manifest(manifest, task=task, check_paths=False)
    except ValidationError as exc:
        raise ExecutionError(f"input validation failed: {exc}") from exc
    context = _context(Path(run_root).resolve(), run_id, task, manifest)
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
        "started_at": _now(),
    }
    _write_json(context.result, result)
    with context.log.open("wb") as log:
        process: subprocess.Popen[bytes] | None = None
        try:
            result["state"] = "running"
            _write_json(context.result, result)
            process = subprocess.Popen(list(command), cwd=context.work, env=_environment(context),
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                result["exit_code"] = process.wait(timeout=timeout)
                result["state"] = "completed" if process.returncode == 0 else "execution_failed"
                if process.returncode != 0:
                    result["failure_reason"] = "nonzero_exit"
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
