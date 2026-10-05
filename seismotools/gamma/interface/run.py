#!/usr/bin/env python3
"""Associate a standardized pick table with local GaMMA."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "source"))
from gamma.utils import association, random_seed  # noqa: E402

DEFAULT_CONFIG = {
    "use_amplitude": False,
    "use_dbscan": False,
    "ncpu": 1,
    "dims": ["x(km)", "y(km)", "z(km)"],
    "vel": {"p": 6.0, "s": 3.46},
    "min_picks_per_eq": 6,
    "min_p_picks_per_eq": 3,
    "min_s_picks_per_eq": 2,
    "min_stations": 4,
    "oversample_factor": 2,
    "covariance_prior": [3.0],
    "max_sigma11": 1.5,
    "bfgs_bounds": [[-200, 200], [-200, 200], [-5, 35], [None, None]],
    "x(km)": [-200, 200],
    "y(km)": [-200, 200],
    "z(km)": [-5, 35],
}


def read_inputs(picks_path: Path, stations_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    picks = pd.read_csv(picks_path)
    stations = pd.read_csv(stations_path)
    required_picks = {"timestamp", "station_id", "phase"}
    required_stations = {"station_id", "x_km", "y_km", "z_km"}
    missing = required_picks - set(picks.columns)
    if missing:
        raise ValueError(f"picks CSV missing columns: {', '.join(sorted(missing))}")
    missing = required_stations - set(stations.columns)
    if missing:
        raise ValueError(f"stations CSV missing columns: {', '.join(sorted(missing))}")
    if picks.empty or stations.empty:
        raise ValueError("picks and stations must not be empty")
    picks = picks.copy()
    picks["timestamp"] = pd.to_datetime(picks["timestamp"], utc=True, errors="raise", format="mixed")
    picks["station_id"] = picks["station_id"].astype(str)
    picks["phase"] = picks["phase"].astype(str).str.upper()
    if not set(picks["phase"]).issubset({"P", "S"}):
        raise ValueError("phase values must be P or S")
    stations = stations.copy()
    stations["station_id"] = stations["station_id"].astype(str)
    if not set(picks["station_id"]).issubset(set(stations["station_id"])):
        missing = sorted(set(picks["station_id"]) - set(stations["station_id"]))
        raise ValueError(f"picks reference stations absent from station table: {missing}")
    internal_picks = pd.DataFrame({
        "timestamp": picks["timestamp"],
        "amp": picks.get("amplitude", pd.Series(1.0, index=picks.index)).astype(float),
        "id": picks["station_id"],
        "type": picks["phase"],
        "prob": picks.get("probability", pd.Series(1.0, index=picks.index)).astype(float),
    })
    internal_stations = pd.DataFrame({
        "id": stations["station_id"],
        "x(km)": pd.to_numeric(stations["x_km"], errors="raise"),
        "y(km)": pd.to_numeric(stations["y_km"], errors="raise"),
        "z(km)": pd.to_numeric(stations["z_km"], errors="raise"),
    })
    return internal_picks, internal_stations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--picks", type=Path, required=True, help="CSV with timestamp, station_id and phase")
    parser.add_argument("--stations", type=Path, required=True, help="CSV with station_id, x_km, y_km and z_km")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, help="Optional GaMMA JSON configuration")
    parser.add_argument("--method", choices=("BGMM", "GMM"), default="BGMM")
    args = parser.parse_args()
    picks, stations = read_inputs(args.picks.resolve(), args.stations.resolve())
    config = dict(DEFAULT_CONFIG)
    if args.config:
        supplied = json.loads(args.config.read_text())
        if not isinstance(supplied, dict):
            raise ValueError("GaMMA config must be a JSON object")
        config.update(supplied)
    args.output_dir.resolve().mkdir(parents=True, exist_ok=True)
    random_seed()
    events, assignments = association(picks, stations, config, method=args.method)
    events_df = pd.DataFrame(events)
    assignment_df = pd.DataFrame(assignments, columns=["pick_index", "event_index", "assignment_probability"])
    events_df.to_csv(args.output_dir / "events.csv", index=False)
    assignment_df.to_csv(args.output_dir / "assignments.csv", index=False)
    summary = {
        "status": "success",
        "method": args.method,
        "input_picks": len(picks),
        "input_stations": len(stations),
        "events": len(events_df),
        "assignments": len(assignment_df),
        "outputs": {"events": str(args.output_dir / "events.csv"), "assignments": str(args.output_dir / "assignments.csv")},
    }
    (args.output_dir / "run_result.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
