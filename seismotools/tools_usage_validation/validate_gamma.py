#!/usr/bin/env python3
"""Associate a small deterministic synthetic pick set with local GaMMA."""
from __future__ import annotations

import json
import sys
import contextlib
import io
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
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
    print(json.dumps({"status": "pass", "tool": "GaMMA", "input_picks": len(picks),
                      "events": len(events), "assignments": len(assignments)}))


if __name__ == "__main__":
    main()
