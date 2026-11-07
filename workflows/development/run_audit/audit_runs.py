#!/usr/bin/env python3
"""Audit the key decisions of every Agent run and score its process, without reading the run by hand.

For each run under ``workflows/tasks/<case>/runs/<variant>/claude/<model>/<run_id>`` (excluded runs skipped) it
extracts, from the execution log (``record/execution.jsonl``: every tool call), the work directory and the scores:

- cost, duration, tool calls; web searches and fetches;
- skill use: SKILL.md and stage/reference files read, skill scripts run;
- workflow: template matching run and detections merged (catalog events without picks); relative relocation run and
  submitted; locator runs and the velocity model files they used; checker runs and stages;
- final products: the final checker report's flags and key measurements (depth pile, S−P depth offset, events beyond
  the stations, the P-only pick group's residual spread), dispositions and the scorer's audit of them, the
  products' location (top of the output directory or one level too deep);
- outcome: failed trust criteria (window of the run), with the development-window rescore of formal runs when present.

Process metrics (each true, false or n/a), the questions a skill should change the answer to:

- ``template_matching``: template-matching detections are in the submitted catalog;
- ``relocation``: a relative relocation was run and its catalog submitted (the final report has a catalog_before);
- ``reliable_flags_left``: flags that reliably mean an error (unit/response magnitude, single-depth pile, pick time
  shift, duplicates) remain in the final report — should be false;
- ``noisy_pick_group``: the P-only pick group scatters more than twice the stations with S picks — should be false;
- ``beyond_network_kept``: more than 2 % of events beyond the station hull are submitted — should be false;
- ``dispositions_ok``: every final flag has a disposition the scorer accepts;
- ``products_in_place``: catalog, picks and checker report at the top of the output directory.

Usage: audit_runs.py [--variants dev_knowledge tools ...] [--output-dir outputs/]. Writes ``runs.csv`` (one row
per run) and ``process.md`` (the process metrics per run and per variant).
"""
from __future__ import annotations

import argparse
import json
import re
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TASKS = ROOT / "workflows/tasks"
HERE = Path(__file__).resolve().parent
RELIABLE = {"strength.magnitude_recompute", "space.depth_single_value", "time.pick_onset_offset", "reality.duplicate_picks"}
SKILL_SCRIPTS = ("compare_pick_groups.py", "expectation_hypocentres.py", "drop_beyond_network.py", "check_submission.py")


def tool_calls(run: Path) -> tuple[list[dict], dict]:
    calls, result = [], {}
    f = run / "record/execution.jsonl"
    if not f.is_file():
        return calls, result
    for line in f.open():
        try:
            m = json.loads(line)
        except json.JSONDecodeError:
            continue
        if m.get("type") == "assistant":
            for c in (m.get("message") or {}).get("content", []):
                if c.get("type") == "tool_use":
                    calls.append({"name": c.get("name"), "input": c.get("input") or {}})
        elif m.get("type") == "result":  # one per session; cost is cumulative within a session
            sid = m.get("session_id") or len(result)
            result[sid] = max(result.get(sid, 0.0), m.get("total_cost_usd") or 0.0)
    return calls, {"cost_usd": sum(result.values()) if result else None}


def work_files(work: Path) -> list[str]:
    """File names under the work directory, without following links into the input data."""
    names = []
    for root, dirs, files in os.walk(work, followlinks=False):
        dirs[:] = [d for d in dirs if d != "input"]
        names += [os.path.join(root, f) for f in files]
    return names


def hours(run: Path) -> float | None:
    f = run / "record/run_result.json"
    if not f.is_file():
        return None
    r = json.loads(f.read_text()); r = r.get("result") or r
    if not r.get("started_at") or not r.get("finished_at"):
        return None
    return (datetime.fromisoformat(r["finished_at"]) - datetime.fromisoformat(r["started_at"])).total_seconds() / 3600


def text_of(c: dict) -> str:
    i = c["input"]
    return " ".join(str(i.get(k, "")) for k in ("command", "file_path", "query", "url", "pattern"))


def final_dir(work: Path) -> Path:
    for base in (work, work / "work"):
        if (base / "checker/final/checker_report.json").is_file():
            return base
    return work


def check(report: dict, cid: str) -> dict:
    return next((c for c in report.get("checks", []) if c.get("id") == cid), {})


def scores(case: str, variant: str, run_id: str, run: Path) -> dict:
    out = {}
    hits = list((TASKS / case / "evaluation/agents").glob(f"{variant}__*__{run_id}/scores.json"))
    s = json.loads(hits[0].read_text()) if hits else None
    rescue = run / "evaluation/rescue/metrics.json"
    if (s is None or "completed" in (s.get("trust") or {}).get("failed", [])) and rescue.is_file():
        s, out["scored_as"] = json.loads(rescue.read_text()), "rescue"
    if s:
        out["failed"] = (s.get("trust") or {}).get("failed")
        m = run / "evaluation/metrics.json"
        if m.is_file():
            ck = json.loads(m.read_text()).get("checker") or {}
            out["checker_audit_complete"] = ck.get("complete")
    dw = run / "evaluation/dev_window/metrics.json"
    if dw.is_file():
        out["failed_dev_window"] = (json.loads(dw.read_text()).get("trust") or {}).get("failed")
    return out


def audit(run: Path) -> dict:
    case, variant, model, run_id = run.parts[-6], run.parts[-4], run.parts[-2], run.name
    work = run / "work"
    calls, result = tool_calls(run)
    texts = [text_of(c) for c in calls]
    joined = "\n".join(texts)
    h = hours(run)
    row = {"case": case, "variant": variant, "run_id": run_id, "hours": round(h, 2) if h else None,
           "cost_usd": round(result["cost_usd"], 2) if result.get("cost_usd") else None,
           "tool_calls": len(calls), "web": sum(c["name"] in ("WebSearch", "WebFetch") for c in calls)}
    # skill use
    row["skill_files_read"] = len({t for t in texts if re.search(r"agent_resource/skills/.+\.md", t) and ("SKILL.md" in t or "/stages/" in t or "/reference/" in t or "/symptoms/" in t or "/playbooks/" in t or "/protocol/" in t)})
    row["skill_scripts_run"] = ",".join(s.replace(".py", "") for s in SKILL_SCRIPTS if s in joined) or ""
    # workflow
    files = work_files(work)
    row["tm_ran"] = any(os.path.basename(f).endswith("detections.csv") for f in files)
    row["reloc_ran"] = any(f.endswith(".reloc") or ("growclust" in f.lower() and "cat" in os.path.basename(f).lower()) for f in files)
    row["checker_runs"] = len(re.findall(r"run\.py[^\n]*--stage", joined))
    models = []
    for rr in (Path(f) for f in files if f.endswith("run_result.json")):
        try:
            r = json.loads(rr.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if r.get("tool") == "nonlinloc-locate":
            models.append(Path(str((r.get("inputs") or {}).get("velocity_model", ""))).name)
    row["locator_runs"] = len(models)
    row["velocity_models"] = ",".join(sorted(set(models)))[:200]
    # final products
    base = final_dir(work)
    row["products_in_place"] = (work / "catalog.csv").is_file() and (work / "checker/final/checker_report.json").is_file() if variant not in ("min", "tools", "backend") else (work / "catalog.csv").is_file()
    cat = None
    for b in (work, work / "work"):
        if (b / "catalog.csv").is_file():
            cat = pd.read_csv(b / "catalog.csv", low_memory=False)
            break
    if cat is not None:
        submitted = cat[cat.get("status", pd.Series("accepted", index=cat.index)).astype(str) != "rejected"]
        row["events"] = int(len(submitted))
        row["events_without_picks"] = int((pd.to_numeric(submitted.get("n_picks"), errors="coerce") == 0).sum()) if "n_picks" in submitted else None
    rep_path = base / "checker/final/checker_report.json"
    if rep_path.is_file():
        rep = json.loads(rep_path.read_text())
        flags = [f.get("flag_id") for f in rep.get("flags", [])]
        row["final_flags"] = ",".join(flags)
        row["reliable_flags_left"] = bool(set(flags) & RELIABLE)
        row["relocation_submitted"] = "catalog_before" in (rep.get("inputs") or {})
        row["depth_single_value"] = check(rep, "depth_single_value").get("measured")
        row["sp_depth_offset_km"] = check(rep, "sp_depth_offset").get("measured")
        row["beyond_network_share"] = check(rep, "events_beyond_stations").get("measured")
        rs = check(rep, "station_residual_spread").get("details") or {}
        if rs.get("p_only_median_mad_s") and rs.get("reference_median_mad_s"):
            row["p_only_spread_ratio"] = round(rs["p_only_median_mad_s"] / rs["reference_median_mad_s"], 2)
    row.update(scores(case, variant, run_id, run))
    # process metrics
    row["pm_template_matching"] = bool(row["tm_ran"] and (row.get("events_without_picks") or 0) > 0)  # run and merged
    row["pm_relocation"] = bool(row["reloc_ran"])
    row["pm_reliable_flags_left"] = row.get("reliable_flags_left")
    row["pm_noisy_pick_group"] = (row["p_only_spread_ratio"] > 2) if row.get("p_only_spread_ratio") else None
    row["pm_beyond_network_kept"] = (row["beyond_network_share"] > 0.02) if row.get("beyond_network_share") is not None else None
    row["pm_dispositions_ok"] = row.get("checker_audit_complete")
    row["pm_products_in_place"] = row["products_in_place"]
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variants", nargs="*", default=None)
    ap.add_argument("--output-dir", type=Path, default=HERE / "outputs")
    a = ap.parse_args()
    rows = []
    for run in sorted(TASKS.glob("*/runs/*/claude/*/*")):
        if not run.is_dir() or (run / "EXCLUDED.md").exists() or (a.variants and run.parts[-4] not in a.variants):
            continue
        state = json.loads((run / "record/run_result.json").read_text()) if (run / "record/run_result.json").is_file() else {}
        state = (state.get("result") or state).get("state")
        if state in ("running", "preparing"):
            continue
        rows.append(audit(run))
    df = pd.DataFrame(rows)
    a.output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.output_dir / "runs.csv", index=False)
    pm = [c for c in df.columns if c.startswith("pm_")]
    lines = ["# Process metrics per run", "", "| case | variant | run | " + " | ".join(c[3:] for c in pm) + " | failed |", "|" + "---|" * (len(pm) + 4)]
    for _, r in df.iterrows():
        cells = ["—" if pd.isna(r[c]) or r[c] is None else ("yes" if r[c] is True else "no" if r[c] is False else str(r[c])) for c in pm]
        failed = r.get("failed_dev_window") if isinstance(r.get("failed_dev_window"), list) else r.get("failed")
        lines.append(f"| {r['case'][:16]} | {r['variant']} | {r['run_id']} | " + " | ".join(cells) + f" | {len(failed) if isinstance(failed, list) else '—'} |")
    (a.output_dir / "process.md").write_text("\n".join(lines) + "\n")
    print(f"{len(df)} runs -> {a.output_dir}/runs.csv, process.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
