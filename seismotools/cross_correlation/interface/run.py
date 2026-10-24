#!/usr/bin/env python3
"""Measure waveform cross-correlation differential times (dt.cc) for event pairs."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "python"))

from ccdt import run  # noqa: E402

INTERFACE_VERSION = 1
KNOWN_OUTPUTS = ["dt.cc", "event_ids.csv", "measurements.csv", "run_result.json", "config.json"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True, help="event_id, origin_time_utc, latitude, longitude, depth_km")
    parser.add_argument("--arrivals", type=Path, required=True, help="event_id, station_id, phase, time_utc")
    parser.add_argument("--waveforms", type=Path, required=True, help="directory searched recursively for MiniSEED")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pairs", type=Path, default=None, help="optional event_id_1, event_id_2 list")
    parser.add_argument("--config", type=Path, default=None, help="JSON overriding runtime/python/ccdt DEFAULT_CONFIG")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--overwrite", action="store_true", help="remove known outputs first")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    out = args.output_dir.expanduser().resolve()
    if out.exists() and any((out / k).exists() for k in KNOWN_OUTPUTS):
        if not args.overwrite:
            parser.error(f"{out} holds outputs; pass --overwrite")
        for k in KNOWN_OUTPUTS:
            (out / k).unlink(missing_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    config = json.loads(args.config.read_text()) if args.config else None
    try:
        result = run(args.events, args.arrivals, args.waveforms, out, config=config, pairs_csv=args.pairs,
                     workers=args.workers, log=(lambda *a: None) if args.quiet else print)
        result["interface_version"] = INTERFACE_VERSION
        (out / "run_result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({k: result[k] for k in ("status", "events", "pairs_with_dt", "dt_lines")}))
        return 0
    except Exception as exc:
        (out / "run_result.json").write_text(json.dumps(
            {"status": "failed", "interface_version": INTERFACE_VERSION, "error": f"{type(exc).__name__}: {exc}",
             "traceback": traceback.format_exc()}, indent=2) + "\n")
        print(f"failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
