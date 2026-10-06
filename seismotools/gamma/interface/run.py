#!/usr/bin/env python3
"""Associate a standardized pick table with local GaMMA."""
from __future__ import annotations

import argparse
import copy
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
EVENT_COLUMNS = [
    "time", "event_index", "x(km)", "y(km)", "z(km)", "num_picks",
    "num_p_picks", "num_s_picks", "magnitude", "sigma_time", "sigma_amp",
    "cov_time_amp", "gamma_score",
]


def merge_config(base: dict, override: dict) -> dict:
    """Merge nested configuration objects without dropping default subkeys."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result


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
    if "pick_id" in picks.columns:
        picks["pick_id"] = picks["pick_id"].astype(str)
        if picks["pick_id"].eq("").any() or picks["pick_id"].duplicated().any():
            raise ValueError("pick_id values must be non-empty and unique")
    else:
        picks["pick_id"] = [f"pick-{i:06d}" for i in range(len(picks))]
    picks = picks.reset_index(drop=True)
    picks["timestamp"] = pd.to_datetime(picks["timestamp"], utc=True, errors="raise", format="mixed")
    picks["station_id"] = picks["station_id"].astype(str)
    picks["phase"] = picks["phase"].astype(str).str.upper()
    if not set(picks["phase"]).issubset({"P", "S"}):
        raise ValueError("phase values must be P or S")
    stations = stations.copy()
    stations["station_id"] = stations["station_id"].astype(str)
    if stations["station_id"].eq("").any() or stations["station_id"].duplicated().any():
        raise ValueError("station_id values must be non-empty and unique")
    if not set(picks["station_id"]).issubset(set(stations["station_id"])):
        missing = sorted(set(picks["station_id"]) - set(stations["station_id"]))
        raise ValueError(f"picks reference stations absent from station table: {missing}")
    internal_picks = pd.DataFrame({
        "timestamp": picks["timestamp"],
        "amp": picks.get("amplitude", pd.Series(1.0, index=picks.index)).astype(float),
        "id": picks["station_id"],
        "type": picks["phase"],
        "prob": picks.get("probability", pd.Series(1.0, index=picks.index)).astype(float),
        "pick_id": picks["pick_id"],
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
    parser.add_argument("--overwrite", action="store_true", help="Replace existing interface output files")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "run_result.json"
    output_files = [output_dir / "events.csv", output_dir / "assignments.csv", result_path]
    if not args.overwrite:
        existing = [str(path) for path in output_files if path.exists()]
        if existing:
            raise ValueError(f"output files already exist; choose a new directory or use --overwrite: {existing}")
    try:
        picks, stations = read_inputs(args.picks.resolve(), args.stations.resolve())
        config = copy.deepcopy(DEFAULT_CONFIG)
        if args.config:
            supplied = json.loads(args.config.read_text())
            if not isinstance(supplied, dict):
                raise ValueError("GaMMA config must be a JSON object")
            config = merge_config(config, supplied)
        random_seed()
        events, assignments = association(picks, stations, config, method=args.method)
        events_df = pd.DataFrame(events)
        # Keep a stable header even when no candidate event survives thresholds.
        for column in EVENT_COLUMNS:
            if column not in events_df:
                events_df[column] = pd.NA
        events_df = events_df[[column for column in EVENT_COLUMNS if column in events_df.columns] +
                              [column for column in events_df.columns if column not in EVENT_COLUMNS]]
        # The native adapter returns only associated rows. Expand the table so
        # every input pick remains traceable, including unassociated picks.
        assignment_map = {
            int(row[0]): (int(row[1]), float(row[2])) for row in assignments
        }
        assignment_df = pd.DataFrame({
            "pick_index": range(len(picks)),
            "pick_id": picks["pick_id"].tolist(),
            "event_index": [assignment_map.get(i, (None, None))[0] for i in range(len(picks))],
            "assignment_probability": [assignment_map.get(i, (None, 0.0))[1] for i in range(len(picks))],
            "assignment_status": ["assigned" if i in assignment_map else "unassigned" for i in range(len(picks))],
        })
        events_df.to_csv(output_files[0], index=False)
        assignment_df.to_csv(output_files[1], index=False)
        summary = {
            "status": "success",
            "interface_version": 2,
            "method": args.method,
            "inputs": {"picks": str(args.picks.resolve()), "stations": str(args.stations.resolve())},
            "input_picks": len(picks),
            "input_stations": len(stations),
            "events": len(events_df),
            "assignments": len(assignment_df),
            "assigned_picks": int((assignment_df["assignment_status"] == "assigned").sum()),
            "unassigned_picks": int((assignment_df["assignment_status"] == "unassigned").sum()),
            "config": config,
            "outputs": {"events": str(output_files[0]), "assignments": str(output_files[1])},
        }
        result_path.write_text(json.dumps(summary, indent=2, default=str) + "\n")
        print(json.dumps(summary, indent=2, default=str))
        return 0
    except Exception as exc:
        failure = {"status": "failed", "interface_version": 2, "error": str(exc)}
        result_path.write_text(json.dumps(failure, indent=2) + "\n")
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
