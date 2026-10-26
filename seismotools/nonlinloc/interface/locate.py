#!/usr/bin/env python3
"""Locate a catalog of arrival groups with NonLinLoc (interface version 3).

One NLLoc run per event_id; travel-time grids are computed once per station.
See interface/README.md ("locate.py") for the input/output contract.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "runtime" / "python" / "Nonlinlocpy"))

import pandas as pd  # noqa: E402

from nonlinlocpy.catalog import locate_catalog, merge_config  # noqa: E402
from nonlinlocpy.utils import resolve_nlloc_bin_dir  # noqa: E402

INTERFACE_VERSION = 3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arrivals", type=Path, required=True,
                    help="CSV event_id, pick_id, station_id, phase, time_utc[, uncertainty_s]")
    ap.add_argument("--stations", type=Path, required=True, help="CSV station_id, latitude, longitude, elevation_m")
    ap.add_argument("--velocity-model", type=Path, required=True, help="text: depth_km vp_km_s vs_km_s")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--station-delays", type=Path, default=None, help="CSV station_id, phase, delay_s[, n_picks]")
    ap.add_argument("--config", type=Path, default=None, help="JSON, deep-merged over the defaults")
    ap.add_argument("--bin-dir", type=Path, default=None, help="directory with NLLoc, Vel2Grid, Grid2Time")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    out = a.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()) and not a.overwrite:
        print(f"output directory not empty (use --overwrite): {out}", file=sys.stderr)
        return 2
    result = {"status": "failed", "interface_version": INTERFACE_VERSION, "tool": "nonlinloc-locate"}
    try:
        user = json.loads(a.config.read_text()) if a.config else {}
        cfg = merge_config(user)
        (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
        bin_dir = Path(resolve_nlloc_bin_dir(str(a.bin_dir) if a.bin_dir else ""))
        delays = pd.read_csv(a.station_delays) if a.station_delays else None
        summary = locate_catalog(pd.read_csv(a.arrivals), pd.read_csv(a.stations), a.velocity_model, out, bin_dir,
                                 user, delays, a.workers, log=(lambda *_: None) if a.quiet else print)
        summary.pop("config")
        result.update(status="success" if summary["failed"] == 0 else "partial", **summary,
                      inputs={"arrivals": str(a.arrivals), "stations": str(a.stations),
                              "velocity_model": str(a.velocity_model),
                              "station_delays": str(a.station_delays) if a.station_delays else None},
                      binary_dir=str(bin_dir), outputs=["events.csv", "arrivals.csv", "failures.csv", "config.json"])
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    (out / "run_result.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    if not a.quiet or result["status"] == "failed":
        print(json.dumps({k: v for k, v in result.items() if k != "traceback"}, indent=2, default=str))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
