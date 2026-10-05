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


def write_environment_record(run_dir: str | Path, result: Mapping[str, Any],
                             runtime_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Write runtime identity without copying the process environment."""
    run = Path(run_dir)
    runtime = dict(runtime_context or {})
    runtime.setdefault("python", {"executable": sys.executable, "version": platform.python_version()})
    runtime.setdefault("operating_system", platform.platform())
    runtime.setdefault("architecture", platform.machine())
    runtime.setdefault("network_policy", "allowed")
    record = {
        "schema_version": 1,
        "recorded_at": _now(),
        "run_id": result["run_id"],
        "execution_profile": result["execution_profile"],
        "formal_evaluation_eligible": result["formal_evaluation_eligible"],
        "runtime": runtime,
        "working_directory": str(run / "work"),
        "input_directory": str(run / "work" / "input"),
        "output_directory": str(run / "work"),
    }
    _write(run / "record" / "environment.json", record)
    return record


def write_evaluation_report(run_dir: str | Path, result: Mapping[str, Any],
                            agent: Mapping[str, Any] | None = None,
                            reference: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Write a compact index of run records and their status."""
    run = Path(run_dir)
    if agent is None:
        provenance_path = run / "record" / "provenance.json"
        if provenance_path.is_file():
            try:
                provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
                if isinstance(provenance.get("agent"), dict):
                    agent = provenance["agent"]
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
    records = {
        "task": "control/task_spec.json",
        "input_manifest": "control/input_manifest.json",
        "output_contract": "control/output_contract.json" if (run / "control/output_contract.json").is_file() else None,
        "task_prompt": "control/task_prompt.md" if (run / "control/task_prompt.md").is_file() else None,
        "agent_config": "control/agent_config.yaml" if (run / "control/agent_config.yaml").is_file() else None,
        "environment": "record/environment.json",
        "provenance": "record/provenance.json" if (run / "record/provenance.json").is_file() else None,
        "execution": "record/execution.log",
        "execution_jsonl": "record/execution.jsonl" if (run / "record/execution.jsonl").is_file() else None,
        "usage_summary": "record/usage_summary.json" if (run / "record/usage_summary.json").is_file() else None,
        "artifacts": "record/artifact_manifest.json" if (run / "record/artifact_manifest.json").is_file() else None,
        "score": "evaluation/score.json" if (run / "evaluation/score.json").is_file() else None,
        "scientific_score": "evaluation/scientific_score.json" if (run / "evaluation/scientific_score.json").is_file() else None,
        "pick_scientific_score": "evaluation/pick_scientific_score.json" if (run / "evaluation/pick_scientific_score.json").is_file() else None,
        "task_summary": "evaluation/task_summary.json" if (run / "evaluation/task_summary.json").is_file() else None,
        "run_result": "record/run_result.json",
    }
    # Keep legacy paths visible only for historical runs that still contain them.
    for name in ("agent_command", "codex_command"):
        legacy = run / "record" / f"{name}.json"
        if legacy.is_file():
            records[name] = f"record/{name}.json"
    report = {
        "schema_version": 1,
        "run_id": result["run_id"],
        "task": {"id": result["task_id"], "version": result["task_version"]},
        "state": result["state"],
        "execution_profile": result["execution_profile"],
        "formal_evaluation_eligible": result["formal_evaluation_eligible"],
        "agent": dict(agent) if agent is not None else None,
        "reference": dict(reference) if reference is not None else None,
        "records": records,
    }
    _write(run / "evaluation" / "report.json", report)
    return report
