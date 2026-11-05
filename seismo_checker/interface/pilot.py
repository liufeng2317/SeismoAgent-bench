#!/usr/bin/env python3
"""Choose a pilot batch: a small part of the data on which to test a workflow before the full run.

Usage:
    pilot.py events --catalog catalog.csv --picks picks.csv --output-dir pilot/ [--events 300]
    pilot.py windows --waveforms <waveform folder> --stations <StationXML or CSV> --output-dir pilot/ \
        [--picks picks.csv] [--n-windows 6] [--window-min 30] [--extract]

``events`` (a catalog exists, e.g. to test a velocity model, locator or magnitude code): writes
``catalog.csv`` and ``picks.csv`` with the pilot events only, in the input's columns, and ``pilot.json``
with the event ids of each part. ``windows`` (no catalog yet, e.g. to test picking and association
settings): writes ``pilot_windows.json`` with the UTC windows of each part; with ``--extract`` also the
records of each window as MiniSEED in the same file naming, one folder per window.

Every pilot has three parts. ``representative`` (60 %): spread evenly over time and over how well
events are recorded; only this part stands for the whole catalog. ``busiest`` (20 %): the hour with
the most events, for behaviour and run time at the highest event rate. ``largest`` (20 %): the largest
events, for clipping, long S trains and their magnitudes.

What a pilot shows, from replays of pilot batches against their full runs:
- errors of code and tool use (units, sign and datum conventions, wrong response, wrong columns): they
  affect every event alike and show on any part;
- how far a change moves depths and origin times (median over the representative part): close to the
  full catalog's move;
- every checker check of scope ``item`` (run the checker with ``--pilot``).
What it does not show: the distribution of the full catalog (pile-ups, depth layers, completeness), and
so not whether a change should be adopted. Decide that on the full run, with the checker and
``compare.py`` on the full products. The events recorded best are not a substitute for the
representative part: they can move in the opposite direction from the full catalog.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))

from catalog_checker.io import read_catalog, read_picks, read_stations  # noqa: E402
from catalog_checker.pilot import PILOT_DEFAULTS, select_events, select_windows  # noqa: E402


def _utc(t: float) -> str:
    return pd.Timestamp(t, unit="s", tz="UTC").strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def cmd_events(args) -> int:
    events, picks = read_catalog(args.catalog), read_picks(args.picks)
    parts = select_events(events, picks, {**PILOT_DEFAULTS, "events": args.events, "seed": args.seed})
    ids = set().union(*parts.values())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cat = pd.read_csv(args.catalog, dtype=str, keep_default_na=False)
    cat[cat.event_id.isin(ids)].to_csv(args.output_dir / "catalog.csv", index=False)
    pk = pd.read_csv(args.picks, dtype=str, keep_default_na=False)
    pk[pk.event_id.isin(ids)].to_csv(args.output_dir / "picks.csv", index=False)
    out = {"mode": "events", "catalog": str(args.catalog), "picks": str(args.picks), "events_total": int(len(events)),
           "parts": parts, "counts": {k: len(v) for k, v in parts.items()},
           "use": {"representative": "estimate the change to the whole catalog (median over these events only)",
                   "busiest": "behaviour and run time at the highest event rate",
                   "largest": "clipping, long S trains, magnitudes of large events"}}
    (args.output_dir / "pilot.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{args.output_dir}: {len(ids)} pilot events of {len(events)} (" + ", ".join(f"{k} {len(v)}" for k, v in parts.items()) + ")")
    return 0


def cmd_windows(args) -> int:
    from catalog_checker.waveforms import file_index
    index = file_index(args.waveforms)
    if index.empty:
        print(f"pilot: no MiniSEED files named NET.STA.LOC.CHA__start__end.mseed in {args.waveforms}", file=sys.stderr)
        return 2
    span = (float(index.file_start.min()), float(index.file_end.max()))
    picks = read_picks(args.picks) if args.picks else None
    windows, info = select_windows(index, read_stations(args.stations), span,
                                   {"n_windows": args.n_windows, "window_s": args.window_min * 60.0, "seed": args.seed}, picks=picks)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for i, w in enumerate(windows):
        w["start_utc"], w["end_utc"] = _utc(w["start"]), _utc(w["end"])
        w["folder"] = f"{w['part']}_{i:02d}"
    if args.extract:
        from obspy import UTCDateTime, read
        for w in windows:
            folder = args.output_dir / "waveforms" / w["folder"]
            folder.mkdir(parents=True, exist_ok=True)
            hit = index[(index.file_start < w["end"]) & (index.file_end > w["start"])]
            for seed, f in hit.groupby("seed_id"):
                st = None
                for path in f.file:
                    part = read(path, starttime=UTCDateTime(w["start"]), endtime=UTCDateTime(w["end"]))
                    st = part if st is None else st + part
                if st is None or not len(st):
                    continue
                st.merge(method=1)
                st = st.split()  # gaps become separate records
                name = f"{seed}__{UTCDateTime(w['start']).strftime('%Y%m%dT%H%M%SZ')}__{UTCDateTime(w['end']).strftime('%Y%m%dT%H%M%SZ')}.mseed"
                st.write(str(folder / name), format="MSEED")
    out = {"mode": "windows", "waveforms": str(args.waveforms), "span_utc": [_utc(span[0]), _utc(span[1])], "windows": windows,
           "scan": info}
    (args.output_dir / "pilot_windows.json").write_text(json.dumps(out, indent=1) + "\n")
    for w in windows:
        print(f"  {w['part']:14s} {w['start_utc']} – {w['end_utc']}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)
    e = sub.add_parser("events", help="pilot events from a catalog and its picks")
    e.add_argument("--catalog", type=Path, required=True)
    e.add_argument("--picks", type=Path, required=True)
    e.add_argument("--events", type=int, default=PILOT_DEFAULTS["events"])
    e.add_argument("--output-dir", type=Path, required=True)
    e.add_argument("--seed", type=int, default=0)
    e.set_defaults(func=cmd_events)
    w = sub.add_parser("windows", help="pilot time windows from the waveforms, before any catalog exists")
    w.add_argument("--waveforms", type=Path, required=True)
    w.add_argument("--stations", type=Path, required=True)
    w.add_argument("--output-dir", type=Path, required=True)
    w.add_argument("--n-windows", type=int, default=6, help="representative windows, one per equal-duration stratum")
    w.add_argument("--window-min", type=float, default=30.0)
    w.add_argument("--extract", action="store_true", help="also write the records of each window as MiniSEED")
    w.add_argument("--picks", type=Path, help="picks of a first picking pass (associated or not): the busiest window is the one with the most picks")
    w.add_argument("--seed", type=int, default=0)
    w.set_defaults(func=cmd_windows)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
