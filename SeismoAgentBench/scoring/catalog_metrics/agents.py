"""Per-run export into the task's tracked ``evaluation/agents/`` folder.

Runs live under the ignored ``runs/``; this writes, for every run,
``evaluation/agents/<variant>__<harness>__<model>__<run_id>/scores.json`` (formal
state, completion, headline, process, audit, component swap and — for runs
whose outputs were recovered outside ``work/`` — the reference-only rescue
score) and copies its ``location_diagnostics`` figure. Case figure scripts add
their own panels to the same ``figures/`` folder.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .case import AGENTS_DIR, RUN_SCORE_FILE, run_layout

PROCESS_KEYS = ("cost_usd", "elapsed_s", "turns")


def run_name(layout: dict) -> str:
    return "__".join(layout[k] for k in ("variant", "harness", "model", "run_id"))


def _json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _score_part(score: dict | None, swap: dict | None) -> dict:
    part = {}
    if score:
        part["completion"] = score["completion"]
        part["metrics_version"] = score.get("metrics_version")
        part["headline"] = score["headline"]
        part["usability"] = score.get("usability")
        part["process"] = {k: score["process"].get(k) for k in PROCESS_KEYS}
        part["leakage_flag"] = (score["process"].get("leakage") or {}).get("flag")
        if score.get("audit"):
            part["audit"] = {k: score["audit"].get(k) for k in ("sampled", "unsupported", "labels")}
    if swap:
        part["swap"] = {k: swap.get(k) for k in ("picks_round", "location_method", "relocated", "rows")}
    return part


def export_run(task_dir: Path, run_dir: Path) -> Path:
    layout = run_layout(task_dir, run_dir)
    evaluation = run_dir / "evaluation"
    out = task_dir / AGENTS_DIR / run_name(layout)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    report = _json(evaluation / "report.json") or {}
    result = _json(run_dir / "record" / "run_result.json") or {}
    record = {"run": layout, "formal_state": report.get("state"), "run_state": result.get("state"),
              **_score_part(_json(evaluation / RUN_SCORE_FILE), _json(evaluation / "swap" / "swap.json"))}
    rescue = evaluation / "rescue"
    if (rescue / RUN_SCORE_FILE).is_file():
        record["rescue_reference_only"] = {
            "note": "outputs recovered outside work/ after the session ended; not a formal result (see rescue/README.md)",
            **_score_part(_json(rescue / RUN_SCORE_FILE), _json(rescue / "swap" / "swap.json"))}
    (out / "scores.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    for source, name in ((evaluation, "location_diagnostics.png"), (rescue, "location_diagnostics_rescue.png")):
        if (source / "location_diagnostics.png").is_file():
            shutil.copy2(source / "location_diagnostics.png", out / "figures" / name)
    return out


def export_runs(task_dir: Path) -> list[str]:
    task_dir = task_dir.resolve()
    written = []
    for run_dir in sorted((task_dir / "runs").glob("*/*/*/*")):
        if (run_dir / "control").is_dir():
            written.append(export_run(task_dir, run_dir).name)
    return written
