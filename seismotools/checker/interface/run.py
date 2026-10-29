#!/usr/bin/env python3
"""Check a catalog against its own picks and the station geometry; report symptoms only.

Usage:
    python seismotools/checker/interface/run.py --catalog catalog.csv --picks picks.csv \
        --stations <StationXML file or directory | stations.csv> --output-dir checker/

Writes ``checker_report.json`` (every check with its measured value, expected
range and, when out of range, the symptom) and ``checker_diagnostics.png``.
Exit code 0 whether or not flags are raised; 2 on unreadable inputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))

from catalog_checker.checks import Data, run_checks  # noqa: E402
from catalog_checker.io import read_catalog, read_picks, read_stations  # noqa: E402
from catalog_checker.report import build_report, write_figures, write_report  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--picks", type=Path, required=True)
    parser.add_argument("--stations", type=Path, required=True,
                        help="StationXML file, directory of StationXML files, or CSV station_id,latitude,longitude,elevation_m")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, help="JSON overriding default ranges (see README); records itself in the report")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)
    try:
        events, picks, stations = read_catalog(args.catalog), read_picks(args.picks), read_stations(args.stations)
    except (OSError, KeyError, ValueError) as exc:
        print(f"checker: cannot read inputs: {exc}", file=sys.stderr)
        return 2
    if stations.empty:
        print(f"checker: no stations found in {args.stations}", file=sys.stderr)
        return 2
    config = json.loads(args.config.read_text()) if args.config else None
    data = Data(events, picks, stations)
    checks, extras = run_checks(data, config)
    report = build_report(checks, data, {"catalog": args.catalog, "picks": args.picks, "stations": args.stations},
                          extras["config"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    figures = [] if args.no_figures else write_figures(data, extras, args.output_dir)
    report["figures"] = figures
    path = write_report(report, args.output_dir)
    flags = report["flags"]
    print(f"{path}: {len(flags)} flag(s) from {len(checks)} checks")
    for f in flags:
        print(f"  [{f['dimension']}] {f['symptom']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
