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
    path.parent.mkdir(parents=True, exist_ok=True)
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
    _write(run / "record" / "environment.json", record)
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
            "task": "control/task_spec.json",
            "input_manifest": "control/input_manifest.json",
            "agent_config": "control/agent_config.yaml" if (run / "control/agent_config.yaml").is_file() else None,
            "environment": "record/environment.json",
            "agent_command": "record/agent_command.json" if (run / "record/agent_command.json").is_file() else None,
            "execution": "record/execution.log",
            "artifacts": "record/artifact_manifest.json" if (run / "record/artifact_manifest.json").is_file() else None,
            "score": "evaluation/score.json" if (run / "evaluation/score.json").is_file() else None,
            "scientific_score": "evaluation/scientific_score.json" if (run / "evaluation/scientific_score.json").is_file() else None,
            "pick_scientific_score": "evaluation/pick_scientific_score.json" if (run / "evaluation/pick_scientific_score.json").is_file() else None,
            "task_summary": "evaluation/task_summary.json" if (run / "evaluation/task_summary.json").is_file() else None,
            "run_result": "record/run_result.json",
        },
    }
    _write(run / "evaluation" / "report.json", report)
    return report
