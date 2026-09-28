"""Backward-compatible task execution wrapper.

New command-line workflows execute first and evaluate later.  ``run_task`` is
kept for older Python callers that still expect the historical combined call.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from SeismoAgentBench.execution import run_command
from SeismoAgentBench.reporting import write_environment_record
from .evaluate_run import evaluate_run


def run_task(task_path: str | Path, manifest_path: str | Path, command: Sequence[str],
             run_root: str | Path, run_id: str, *, timeout: float = 600,
             reference_manifest: str | Path | None = None,
             extra_env: Mapping[str, str] | None = None,
             resume: bool = False) -> dict[str, Any]:
    """Compatibility wrapper that executes and then evaluates a task."""
    result = run_command(task_path, manifest_path, command, run_root, run_id,
                         timeout=timeout, extra_env=extra_env, resume=resume)
    run = Path(run_root).resolve() / run_id
    write_environment_record(run, result)
    return evaluate_run(run, reference_manifest=reference_manifest)


__all__ = ["evaluate_run", "run_task"]
