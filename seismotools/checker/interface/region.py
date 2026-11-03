#!/usr/bin/env python3
"""The region of a catalog: the station coverage, and a region given by the user.

Usage:
    region.py --stations <StationXML file or folder, or CSV> --output-dir region/ \
        [--catalog catalog.csv] [--region LAT_MIN LAT_MAX LON_MIN LON_MAX] [--buffer-km 10]

Writes ``region.json``: the convex hull of the stations (latitude/longitude and km about the network
centre), the aperture, the buffer, and the given region if any. With ``--catalog`` also writes
``events_region.csv`` (event_id, km_outside_station_hull, inside_station_coverage[, inside_given_region])
and counts in ``region.json``.

The station coverage is the hull widened by the buffer. Outside it the network sees an event from one
side only; its distance and depth are poorly constrained, and on recorded runs such events almost never
belonged to the sequence that was studied. Inside it a catalog can still hold real earthquakes from
elsewhere in the network. A region given by the user (for example the task's study region) is kept as
given: events outside it are not wrong, but they are outside what was asked for. Whether to remove
events outside the coverage or the given region is a decision for the catalog; say which rule was used.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))

from catalog_checker.io import read_catalog, read_stations  # noqa: E402
from catalog_checker.region import REGION_DEFAULTS, classify, station_coverage  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stations", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--catalog", type=Path)
    ap.add_argument("--region", type=float, nargs=4, metavar=("LAT_MIN", "LAT_MAX", "LON_MIN", "LON_MAX"))
    ap.add_argument("--buffer-km", type=float, default=REGION_DEFAULTS["coverage_buffer_km"])
    a = ap.parse_args()
    cov = station_coverage(read_stations(a.stations), a.buffer_km)
    region = None
    if a.region:
        if a.region[0] >= a.region[1] or a.region[2] >= a.region[3]:
            ap.error("--region: LAT_MIN < LAT_MAX and LON_MIN < LON_MAX")
        region = {"latitude": a.region[:2], "longitude": a.region[2:]}
    out = {"station_coverage": cov, "given_region": region}
    a.output_dir.mkdir(parents=True, exist_ok=True)
    if a.catalog:
        events = read_catalog(a.catalog)
        table = classify(events, cov, region)
        table.to_csv(a.output_dir / "events_region.csv", index=False)
        located = table.km_outside_station_hull.notna()
        out["events"] = {"total": int(len(table)), "located": int(located.sum()),
                         "outside_station_coverage": int((table.inside_station_coverage == False).sum())}  # noqa: E712
        if region is not None:
            out["events"]["outside_given_region"] = int((table.inside_given_region == False).sum())  # noqa: E712
    (a.output_dir / "region.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "station_coverage"} | {
        "stations": cov["stations"], "aperture_km": cov["aperture_km"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
