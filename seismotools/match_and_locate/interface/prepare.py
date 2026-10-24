#!/usr/bin/env python3
"""Prepare a Match&Locate dataset from MiniSEED waveforms and case tables.

Step 1 of 2: prepare.py (common inputs -> dataset), then run.py (dataset ->
detections). See prepare_schema.json for the inputs and settings.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "python" / "MatchLocatepy"))

INTERFACE_VERSION = 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--waveforms", type=Path, required=True, help="folder searched recursively for MiniSEED")
    parser.add_argument("--stations", type=Path, required=True, help="CSV: station_id (NET.STA), latitude, longitude[, elevation_m]")
    parser.add_argument("--templates", type=Path, required=True,
                        help="CSV: event_id, origin_time_utc, latitude, longitude, depth_km[, magnitude]")
    parser.add_argument("--picks", type=Path, default=None, help="optional CSV: event_id, station_id, phase, time_utc")
    parser.add_argument("--velocity-model", type=Path, required=True,
                        help="CSV or JSON rows with top_of_layer_km, vp_km_s, vs_km_s (or a JSON registry with --model-key)")
    parser.add_argument("--model-key", default=None, help="model name inside a JSON registry")
    parser.add_argument("--config", type=Path, required=True, help="JSON settings (prepare_schema.json)")
    parser.add_argument("--output-dir", type=Path, required=True, help="dataset folder to create (new or empty)")
    parser.add_argument("--workers", type=int, default=1, help="parallel (channel, day) tasks")
    parser.add_argument("--overwrite", action="store_true", help="remove an existing output folder first")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    out = args.output_dir.expanduser().resolve()
    result_path = out / "prepare_result.json"
    summary = {"status": "failed", "interface_version": INTERFACE_VERSION, "dataset_dir": str(out)}
    try:
        if out.exists() and any(out.iterdir()):
            if not args.overwrite:
                raise ValueError(f"{out} is not empty; use a new folder or --overwrite")
            shutil.rmtree(out)
        from matchlocate_runner.build import build_dataset
        config = json.loads(args.config.read_text())

        def progress(res, n, total):
            if not args.quiet:
                print(f"[{n}/{total}] {res['channel']} {'ERROR ' + res['error'] if res.get('error') else 'ok'}",
                      file=sys.stderr, flush=True)

        report = build_dataset(waveforms=args.waveforms.resolve(), stations_csv=args.stations.resolve(),
                               templates_csv=args.templates.resolve(), velocity_model=args.velocity_model.resolve(),
                               output_dir=out, config=config, picks_csv=args.picks.resolve() if args.picks else None,
                               model_key=args.model_key, workers=args.workers, progress=progress)
        status = "success" if report["templates_kept"] > 0 else "failed"
        summary.update({"status": status, "templates_in": report["templates_in"],
                        "templates_kept": report["templates_kept"], "rows_kept": report["rows_kept"],
                        "segments": report["segments"], "stations_used": report["stations_used"],
                        "task_errors": len(report["task_errors"]),
                        "outputs": [str(out / n) for n in ("templates.csv", "channels.csv", "config.json",
                                                           "dataset.json", "prepare_report.json")]})
        if status != "success":
            summary["error"] = "no template kept; see prepare_report.json for the per-row reasons"
    except Exception as exc:
        summary.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
    out.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), file=sys.stdout if summary["status"] == "success" else sys.stderr)
    return 0 if summary["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
