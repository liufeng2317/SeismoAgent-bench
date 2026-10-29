"""Per-configuration summary over repeated runs (docs/framework/03_EVALUATION_METRICS.md §6-§7)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from .agents import export_runs
from .case import AGENTS_DIR, RUN_SCORE_FILE, _scorer_record, score_run

SUMMARY_FILE = "metrics_summary.json"
# Detection metrics (recall*, f1_*) count a failed run as zero; the others average completed runs only.
DETECTION_PREFIXES = ("recall", "f1_")  # recall_final and recall_tight too
PROCESS = ("cost_usd", "elapsed_s", "turns")


def _stats(values: list) -> dict | None:
    values = [v for v in values if v is not None]
    if not values:
        return None
    return {"mean": round(float(np.mean(values)), 4), "min": round(float(min(values)), 4),
            "max": round(float(max(values)), 4), "n": len(values)}


def summarize(task_dir: Path, *, rescore: bool = False, write: bool = True) -> dict:
    task_dir = task_dir.resolve()
    groups = defaultdict(list)
    for run_dir in sorted((task_dir / "runs").glob("*/*/*/*")):
        if not (run_dir / "control").is_dir():
            continue  # runner logs and other non-run entries
        path = run_dir / "evaluation" / RUN_SCORE_FILE
        report = score_run(task_dir, run_dir) if rescore or not path.is_file() else json.loads(path.read_text())
        run = report["run"]
        groups[(run["variant"], run["harness"], run["model"])].append(report)
    configurations = []
    for (variant, harness, model), reports in sorted(groups.items()):
        clean = [r for r in reports if not r["process"]["leakage"].get("flag")]
        completed = [r for r in clean if r["completion"]["completed"]]
        keys = sorted({k for r in reports for k, v in r["headline"].items()
                       if isinstance(v, (int, float)) and not isinstance(v, bool) and k != "ceiling"})
        entry = {"variant": variant, "harness": harness, "model": model, "launched": len(reports),
                 "leakage_flagged": [r["run"]["run_id"] for r in reports if r["process"]["leakage"].get("flag")],
                 "completion_rate": round(len(completed) / len(clean), 4) if clean else None,
                 "runs": [{"run_id": r["run"]["run_id"], "completed": r["completion"]["completed"],
                           "trusted": (r.get("trust") or {}).get("trusted"),
                           "trust_failed": (r.get("trust") or {}).get("failed"),
                           **{k: r["headline"].get(k) for k in keys}} for r in reports], "metrics": {}}
        entry["trusted_runs"] = sum(1 for r in clean if (r.get("trust") or {}).get("trusted") is True)
        for key in keys:
            if key.startswith(DETECTION_PREFIXES):
                values = [r["headline"].get(key) if r["completion"]["completed"] else 0.0 for r in clean]
            else:
                values = [r["headline"].get(key) for r in completed]
            entry["metrics"][key] = _stats(values)
        for key in PROCESS:
            entry[key] = _stats([r["process"].get(key) for r in clean])
        configurations.append(entry)
    report = {**_scorer_record(), "task": task_dir.name, "configurations": configurations}
    if write:
        (task_dir / AGENTS_DIR).mkdir(parents=True, exist_ok=True)
        (task_dir / AGENTS_DIR / SUMMARY_FILE).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        report["exported"] = export_runs(task_dir)  # evaluation/agents/<run>/
    return report
