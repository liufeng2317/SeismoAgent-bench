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

ROOT = Path(__file__).resolve().parents[3]
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


def run_checker(catalog: Path, picks: Path, stations: Path, out: Path, python: str, *, checker: Path = CHECKER,
                stage: str | None = None, waveforms: Path | None = None, ensemble: bool = True) -> dict:
    cmd = [python, "-W", "ignore", str(checker), "--stations", str(stations), "--output-dir", str(out), "--no-figures"]
    if stage != "data":
        cmd += ["--catalog", str(catalog), "--picks", str(picks)]
    if stage:
        cmd += ["--stage", stage]
    if waveforms:
        cmd += ["--waveforms", str(waveforms)]
    if ensemble:
        cmd.append("--model-ensemble")
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads((out / "checker_report.json").read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--cases", nargs="*", default=CASES)
    parser.add_argument("--checker", type=Path, default=CHECKER, help="checker entry point (a development copy, for example)")
    parser.add_argument("--stages", nargs="*", help="run these stages (data, picks, association, location, magnitude, all); default: the checker's default only")
    parser.add_argument("--no-model-ensemble", action="store_true")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    out_root = args.output
    rows = []
    for case in args.cases:
        task = ROOT / "workflows/tasks" / case
        hil_waveforms = (ROOT / "data" / case / "data/waveforms/data").resolve()
        hil_cat, hil_picks, hil_stations = expert_inputs(task, out_root / case / "human_in_loop" / "inputs")
        if args.stages:  # stage runs read channels and orientations from the StationXML the Agent receives
            hil_stations = (ROOT / "data" / case / "data/waveforms/stations").resolve()
        targets = [("human_in_loop", hil_cat, hil_picks, hil_stations, None, hil_waveforms)]
        targets += [(name, cat, pk, st, s, (cat.parent / "input/waveforms/data").resolve()) for name, cat, pk, st, s in agent_runs(task)]
        for name, cat, pk, st, scores, wf in targets:
          for stage in (args.stages or [None]):
            if stage == "data" and name != "human_in_loop":
                continue  # every run of a case receives the same waveforms
            label = name if stage is None else f"{name}@{stage}"
            report = run_checker(cat, pk, st, out_root / case / label, args.python, checker=args.checker, stage=stage,
                                 waveforms=wf if stage else None, ensemble=not args.no_model_ensemble)
            known = {k: (scores or {}).get("headline", {}).get(k) for k in KNOWN} if scores else {}
            for c in report["checks"]:
                rows.append({"case": case, "catalog": label, "check": c["id"], "dimension": c["dimension"],
                             "measured": c["measured"], "n": c["n"], "flag": c["flag"],
                             "not_evaluated": (c.get("details") or {}).get("not_evaluated"),
                             **{f"known_{k}": v for k, v in known.items()}})
            print(f"{case} {label}: {len(report['flags'])} flags", flush=True)
    table = pd.DataFrame(rows)
    out_root.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_root / "summary.csv", index=False)
    wide = table.pivot_table(index="check", columns=["case", "catalog"], values="measured", aggfunc="first")
    flags = table.pivot_table(index="check", columns=["case", "catalog"], values="flag", aggfunc="first")
    cells = wide.round(3).astype(str).where(~flags.fillna(False).astype(bool), wide.round(3).astype(str) + " ⚑")
    (out_root / "summary.md").write_text(cells.to_markdown() + "\n", encoding="utf-8")
    print(out_root / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
