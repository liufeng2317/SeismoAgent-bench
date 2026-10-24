#!/usr/bin/env python3
"""Run Match&Locate (MatchLocate2) over a prepared template/continuous dataset."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DEFAULT_BIN = ROOT / "runtime" / "bin"
sys.path.insert(0, str(ROOT / "runtime" / "python" / "MatchLocatepy"))

from matchlocate_runner import DEFAULT_CONFIG, merge_config, run_dataset  # noqa: E402

INTERFACE_VERSION = 1
KNOWN_OUTPUTS = ["run_result.json", "config.json", "jobs.csv", "template_detections.csv",
                 "detections.csv", "progress.jsonl", "jobs", "merge"]


def _csv_list(value):
    return [v for v in (value or "").split(",") if v] or None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="prepared dataset (see input_schema.json)")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=None,
                        help="JSON parameters; default <input-dir>/config.json when present")
    parser.add_argument("--segments", default=None, help="comma-separated subset of continuous/<segment> folders")
    parser.add_argument("--templates", default=None, help="comma-separated template_id subset")
    parser.add_argument("--jobs", type=int, default=1, help="native jobs run concurrently")
    parser.add_argument("--threads", type=int, default=1, help="OpenMP threads per native job")
    parser.add_argument("--bin-dir", type=Path, default=None)
    parser.add_argument("--resume", action="store_true", help="reuse jobs whose job.json reports success")
    parser.add_argument("--overwrite", action="store_true", help="remove known outputs before running")
    parser.add_argument("--quiet", action="store_true", help="no per-job progress lines")
    args = parser.parse_args()

    input_dir = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    bin_dir = args.bin_dir.expanduser().resolve() if args.bin_dir else DEFAULT_BIN
    config_path = args.config or (input_dir / "config.json")
    result_path = output_dir / "run_result.json"
    summary = {"status": "failed", "interface_version": INTERFACE_VERSION, "output_dir": str(output_dir)}
    try:
        if args.resume and args.overwrite:
            raise ValueError("--resume and --overwrite are mutually exclusive")
        output_dir.mkdir(parents=True, exist_ok=True)
        existing = [n for n in KNOWN_OUTPUTS if (output_dir / n).exists()]
        if existing and args.overwrite:
            for name in existing:
                path = output_dir / name
                shutil.rmtree(path) if path.is_dir() else path.unlink()
        elif existing and not args.resume:
            raise ValueError(f"outputs already exist; use a new directory, --resume or --overwrite: {existing}")
        user_config = json.loads(config_path.read_text()) if config_path.is_file() else {}
        config = merge_config(DEFAULT_CONFIG, user_config)

        def progress(record, n, total):
            if not args.quiet:
                print(f"[{n}/{total}] {record['segment']} {record['template_id']} {record['status']} "
                      f"det={record.get('n_detections', 0)} {record.get('runtime_s', 0)} s",
                      file=sys.stderr, flush=True)

        result = run_dataset(input_dir, output_dir, config, bin_dir, jobs=args.jobs, threads=args.threads,
                             segments=_csv_list(args.segments), template_ids=_csv_list(args.templates),
                             resume=args.resume, progress=progress)
        failed = result["jobs"].get("failed", 0)
        summary.update({
            "status": "success" if failed == 0 else "failed",
            "inputs": {"input_dir": str(input_dir), "config": str(config_path) if config_path.is_file() else None,
                       "binary_dir": str(bin_dir)},
            "parallelism": {"jobs": args.jobs, "threads_per_job": args.threads},
            "outputs": [str(output_dir / n) for n in ("config.json", "jobs.csv", "template_detections.csv",
                                                       "detections.csv")],
            "detections_file": str(output_dir / "detections.csv"),
            **{k: result[k] for k in ("segments", "templates", "jobs", "template_detections", "detections",
                                       "failed_jobs")},
        })
        if failed:
            summary["error"] = f"{failed} native job(s) failed; see jobs.csv and jobs/<segment>/<template>/native.log"
    except Exception as exc:  # recorded as a failed run, never as partial success
        summary.update({"status": "failed", "error": str(exc)})
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "failed_jobs"}, indent=2),
          file=sys.stdout if summary["status"] == "success" else sys.stderr)
    return 0 if summary["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
