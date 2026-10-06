#!/usr/bin/env python3
"""Associate a small deterministic synthetic pick set with local GaMMA."""
from __future__ import annotations

import json
import os
import sys
import contextlib
import io
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
EXPORT = Path(os.environ.get("RIDGECREST_EXPORT_ROOT", str(ROOT / "workflows/tasks/2019_ridgecrest_california/expert/export/01_baseline")))
sys.path.insert(0, str(ROOT / "seismotools" / "gamma" / "source"))
from gamma.utils import association


def main() -> None:
    origin = pd.Timestamp("2019-01-01T00:00:00Z")
    stations = pd.DataFrame({"id": [f"S{i}" for i in range(8)],
                             "x(km)": np.arange(8, dtype=float) * 2,
                             "y(km)": np.zeros(8), "z(km)": np.zeros(8)})
    rows = []
    for i in range(8):
        for phase, delay in (("P", 1.0 + i * 0.01), ("S", 2.0 + i * 0.01)):
            rows.append({"timestamp": origin + pd.Timedelta(seconds=delay),
                         "amp": 1.0, "id": f"S{i}", "type": phase, "prob": 0.99})
    picks = pd.DataFrame(rows)
    config = {"use_amplitude": False, "use_dbscan": False, "ncpu": 1,
              "dims": ["x(km)", "y(km)", "z(km)"], "vel": {"p": 6.0, "s": 3.46},
              "min_picks_per_eq": 10, "min_p_picks_per_eq": 4,
              "min_s_picks_per_eq": 3, "min_stations": 6, "oversample_factor": 2,
              "covariance_prior": [3.0], "max_sigma11": 1.5,
              "bfgs_bounds": [(-10, 20), (-10, 10), (0, 10), (None, None)],
              "x(km)": [-10, 20], "y(km)": [-10, 10], "z(km)": [0, 10]}
    # GaMMA prints progress to stdout; keep the validation result itself JSON.
    with contextlib.redirect_stdout(io.StringIO()):
        events, assignments = association(picks, stations, config, method="BGMM")
    assert len(events) >= 1 and len(assignments) >= 10
    folder = EXPORT / "03_associate_gamma/full"
    real_picks = pd.read_csv(folder / "picks.csv", keep_default_na=False)
    real_stations = pd.read_csv(folder / "stations.csv")
    counts = real_picks[real_picks.event_id != ""].groupby("event_id").agg(
        n=("pick_id", "size"), ns=("station_id", "nunique"))
    selected = counts[(counts.n >= 10) & (counts.ns >= 6)].sort_values("n", ascending=False).index[0]
    selected_picks = real_picks[real_picks.event_id == selected]
    converted = pd.DataFrame({"timestamp": pd.to_datetime(selected_picks.time_utc, utc=True),
                              "amp": 1.0, "id": selected_picks.instrument_id,
                              "type": selected_picks.phase, "prob": selected_picks.probability})
    station_table = real_stations[["id", "x(km)", "y(km)", "z(km)"]]
    real_config = {"use_amplitude": False, "use_dbscan": False, "ncpu": 1,
                   "dims": ["x(km)", "y(km)", "z(km)"], "vel": {"p": 6.0, "s": 3.46},
                   "min_picks_per_eq": 10, "min_p_picks_per_eq": 4,
                   "min_s_picks_per_eq": 3, "min_stations": 6, "oversample_factor": 2,
                   "covariance_prior": [3.0], "max_sigma11": 1.5,
                   "bfgs_bounds": [(-200, 200), (-200, 200), (-5, 35), (None, None)],
                   "x(km)": [-200, 200], "y(km)": [-200, 200], "z(km)": [-5, 35]}
    with contextlib.redirect_stdout(io.StringIO()):
        real_events, real_assignments = association(converted, station_table, real_config, method="BGMM")
    assert real_events and real_assignments
    print(json.dumps({"status": "pass", "tool": "GaMMA",
                      "smoke": {"input_picks": len(picks), "events": len(events), "assignments": len(assignments)},
                      "ridgecrest": {"source_event": str(selected), "input_picks": len(converted),
                                     "events": len(real_events), "assignments": len(real_assignments)}}, indent=2))


if __name__ == "__main__":
    main()
