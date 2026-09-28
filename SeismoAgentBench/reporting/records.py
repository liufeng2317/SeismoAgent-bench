"""Write small, non-sensitive records for a benchmark run."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sys
from typing import Any, Mapping


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_environment_record(run_dir: str | Path, result: Mapping[str, Any]) -> dict[str, Any]:
    """Write runtime identity without copying the process environment."""
    run = Path(run_dir)
    record = {
        "schema_version": 1,
        "recorded_at": _now(),
        "run_id": result["run_id"],
        "execution_profile": result["execution_profile"],
        "formal_evaluation_eligible": result["formal_evaluation_eligible"],
        "python": {"executable": sys.executable, "version": platform.python_version()},
        "platform": platform.platform(),
        "working_directory": str(run / "work"),
        "network_policy": "unspecified",
    }
    _write(run / "environment.json", record)
    return record


def write_evaluation_report(run_dir: str | Path, result: Mapping[str, Any],
                            agent: Mapping[str, Any] | None = None,
                            reference: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Write a compact index of run records and their status."""
    run = Path(run_dir)
    report = {
        "schema_version": 1,
        "run_id": result["run_id"],
        "task": {"id": result["task_id"], "version": result["task_version"]},
        "state": result["state"],
        "execution_profile": result["execution_profile"],
        "formal_evaluation_eligible": result["formal_evaluation_eligible"],
        "agent": dict(agent) if agent is not None else None,
        "reference": dict(reference) if reference is not None else None,
        "records": {
            "task": "task_spec.json",
            "input_manifest": "input_manifest.json",
            "environment": "environment.json",
            "agent_command": "agent_command.json" if (run / "agent_command.json").is_file() else None,
            "execution": "execution.log",
            "artifacts": "artifacts.json" if (run / "artifacts.json").is_file() else None,
            "score": "score/score.json" if (run / "score/score.json").is_file() else None,
            "scientific_score": "score/scientific_score.json" if (run / "score/scientific_score.json").is_file() else None,
            "task_summary": "score/task_summary.json" if (run / "score/task_summary.json").is_file() else None,
            "run_result": "run_result.json",
        },
    }
    _write(run / "evaluation_report.json", report)
    return report
