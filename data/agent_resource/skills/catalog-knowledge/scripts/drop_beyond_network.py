#!/usr/bin/env python3
"""Mark events outside the station coverage as rejected.

Outside the network an event is seen from one side only: its distance and depth trade off and the data cannot
constrain its location. Events more than --buffer-km outside the convex hull of the stations are set to
``status = rejected`` (they stay in the file and are not scored). The hull and the distances come from the
checker's ``interface/region.py``, so the rule is the same one the checker reports.

Usage:
    drop_beyond_network.py --checker $CHECKER_PATH --catalog catalog.csv --stations <StationXML file or folder>
        --output catalog_in_network.csv [--buffer-km 10]
Writes the output catalog and prints how many events were rejected; ``region/events_region.csv`` beside the
output lists every event with its distance outside the hull.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checker", type=Path, default=os.environ.get("CHECKER_PATH"), help="the checker directory (CHECKER_PATH)")
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--stations", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--buffer-km", type=float, default=10.0)
    a = ap.parse_args()
    if a.checker is None:
        ap.error("give --checker (the CHECKER_PATH of the task)")
    region_dir = a.output.parent / "region"
    subprocess.run([sys.executable, str(Path(a.checker) / "interface/region.py"), "--stations", str(a.stations),
                    "--catalog", str(a.catalog), "--output-dir", str(region_dir), "--buffer-km", str(a.buffer_km)], check=True)
    reg = pd.read_csv(region_dir / "events_region.csv", dtype={"event_id": str})
    beyond = set(reg.event_id[~reg.inside_station_coverage.astype(bool)])
    cat = pd.read_csv(a.catalog, dtype={"event_id": str})
    if "status" not in cat:
        cat["status"] = "accepted"
    hit = cat.event_id.isin(beyond) & (cat.status != "rejected")
    cat.loc[hit, "status"] = "rejected"
    cat.to_csv(a.output, index=False)
    print(f"{int(hit.sum())} of {len(cat)} events more than {a.buffer_km:g} km outside the station hull set to rejected -> {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
