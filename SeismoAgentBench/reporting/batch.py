"""Stable records for experiment units and serial experiment batches."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_unit_result(run_dir: str | Path, unit: Mapping[str, Any], result: Mapping[str, Any]) -> Path:
    """Write one normalized unit result under the runner-owned record directory."""
    run = result.get("run") if isinstance(result.get("run"), Mapping) else result
    payload = {
        "schema_version": 1,
        "unit": dict(unit),
        "run_id": run.get("run_id"),
        "state": run.get("state"),
        "execution_profile": run.get("execution_profile"),
        "formal_evaluation_eligible": run.get("formal_evaluation_eligible"),
        "exit_code": run.get("exit_code"),
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
    }
    target = Path(run_dir) / "record" / "unit_result.json"
    _json(target, payload)
    return target


def create_batch_id(experiment_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{experiment_id}-{timestamp}"


def write_batch_summary(
    batch_dir: str | Path,
    *,
    experiment_id: str,
    spec_path: str | Path,
    units: Sequence[Mapping[str, Any]],
    results: Sequence[Mapping[str, Any]],
) -> Path:
    """Write machine-readable and human-readable summaries for one batch."""
    records: list[dict[str, Any]] = []
    for unit, result in zip(units, results):
        run = result.get("run") if isinstance(result.get("run"), Mapping) else result
        records.append({
            "agent_id": unit.get("agent_id"),
            "harness": unit.get("harness"),
            "task_id": unit.get("task_id"),
            "variant": unit.get("variant"),
            "run_id": run.get("run_id"),
            "state": run.get("state"),
            "run_dir": str(Path(run.get("run_dir", ""))) if run.get("run_dir") else None,
        })
    counts: dict[str, int] = {}
    for record in records:
        state = str(record.get("state") or "unknown")
        counts[state] = counts.get(state, 0) + 1
    payload = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "spec": str(Path(spec_path).resolve()),
        "count": len(records),
        "state_counts": counts,
        "results": records,
    }
    root = Path(batch_dir)
    _json(root / "summary.json", payload)
    lines = [
        "# Experiment summary", "", f"- Experiment: `{experiment_id}`",
        f"- Units: {len(records)}", "",
        "| Agent | Harness | Task | Variant | Run | State |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| {record['agent_id']} | {record['harness']} | {record['task_id']} | "
            f"{record['variant']} | {record['run_id']} | {record['state']} |"
        )
    root.mkdir(parents=True, exist_ok=True)
    (root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root / "summary.json"
