#!/usr/bin/env python3
"""Validate the catalog checker (seismotools/checker) on human-in-loop catalogs and scored Agent runs.

For each case it runs the checker on
- the human-in-loop located catalog of the picks round used for the component
  swap (stage 04 events with their stage 03 picks): a catalog the checker should
  find clean, so its flags measure false alarms;
- every completed formal Agent run (work/catalog.csv, work/picks.csv), whose
  errors against the final are known from the score table: its flags measure
  whether the checker sees those errors without any reference.

Writes outputs/checker/<case>/<catalog>/checker_report.json and
outputs/checker/summary.{csv,md} (every check, measured value, flag), plus the
known errors of each run from its exported scores for comparison.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "seismotools/checker/interface/run.py"
OUT = Path(__file__).resolve().parent / "outputs/checker"
CASES = ["2011_prague_oklahoma", "2020_magna_utah", "2017_maple_creek_yellowstone", "2018_kilauea_hawaii",
         "2019_ridgecrest_california", "2016_kaikoura_new_zealand"]
KNOWN = ["time_bias_final_s", "dz_final_km", "shift_final_km", "scatter_final_km", "out_of_mask_fraction",
         "off_structure_fraction", "depth_mode_share", "dmag_median", "dmag_slope_per_unit", "recall_final"]


def expert_inputs(task: Path, tmp: Path) -> tuple[Path, Path, Path]:
    """The human-in-loop located catalog and its picks in the output-contract columns."""
    round_ = yaml.safe_load((task / "evaluation/human_in_loop/expert_ladder.yaml").read_text())["swap"]["picks_round"]
    base = task / "expert/export" / round_
    ev = pd.read_csv(base / "04_locate_nonlinloc/full/events.csv")
    ev = ev[ev.status.astype(str).str.upper() == "LOCATED"]
    tmp.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"event_id": ev.event_id, "origin_time_utc": ev.origin_time, "latitude": ev.latitude,
                  "longitude": ev.longitude, "depth_km": ev.depth_below_sea_level_km, "magnitude": "",
                  "status": "accepted"}).to_csv(tmp / "catalog.csv", index=False)
    pk = pd.read_csv(base / "03_associate_gamma/full/picks.csv", dtype=str, keep_default_na=False)
    pd.DataFrame({"pick_id": pk.pick_id, "event_id": pk.event_id, "station_id": pk.station_id, "phase": pk.phase,
                  "time_utc": pk.time_utc, "status": "accepted"}).to_csv(tmp / "picks.csv", index=False)
    return tmp / "catalog.csv", tmp / "picks.csv", base / "03_associate_gamma/full/stations.csv"


def agent_runs(task: Path):
    for scores in sorted((task / "evaluation/agents").glob("*__*__*__*/scores.json")):
        s = json.loads(scores.read_text())
        run = task / s["run"]["path"]
        work = run / "work"
        if not (s.get("completion") or {}).get("completed") or not (work / "catalog.csv").is_file():
            continue
        stations = (work / "input/waveforms/stations").resolve()
        yield f"{s['run']['variant']}__{s['run']['run_id']}", work / "catalog.csv", work / "picks.csv", stations, s


def run_checker(catalog: Path, picks: Path, stations: Path, out: Path, python: str) -> dict:
    subprocess.run([python, "-W", "ignore", str(CHECKER), "--catalog", str(catalog), "--picks", str(picks),
                    "--stations", str(stations), "--output-dir", str(out)], check=True, capture_output=True, text=True)
    return json.loads((out / "checker_report.json").read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--cases", nargs="*", default=CASES)
    args = parser.parse_args()
    rows = []
    for case in args.cases:
        task = ROOT / "workflows/tasks" / case
        targets = [("human_in_loop", *expert_inputs(task, OUT / case / "human_in_loop" / "inputs"), None)]
        targets += [(name, cat, pk, st, s) for name, cat, pk, st, s in agent_runs(task)]
        for name, cat, pk, st, scores in targets:
            report = run_checker(cat, pk, st, OUT / case / name, args.python)
            known = {k: (scores or {}).get("headline", {}).get(k) for k in KNOWN} if scores else {}
            for c in report["checks"]:
                rows.append({"case": case, "catalog": name, "check": c["id"], "dimension": c["dimension"],
                             "measured": c["measured"], "n": c["n"], "flag": c["flag"],
                             "not_evaluated": (c.get("details") or {}).get("not_evaluated"),
                             **{f"known_{k}": v for k, v in known.items()}})
            print(f"{case} {name}: {len(report['flags'])} flags")
    table = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "summary.csv", index=False)
    wide = table.pivot_table(index="check", columns=["case", "catalog"], values="measured", aggfunc="first")
    flags = table.pivot_table(index="check", columns=["case", "catalog"], values="flag", aggfunc="first")
    cells = wide.round(3).astype(str).where(~flags.fillna(False).astype(bool), wide.round(3).astype(str) + " ⚑")
    (OUT / "summary.md").write_text(cells.to_markdown() + "\n", encoding="utf-8")
    print(OUT / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
