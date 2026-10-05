#!/usr/bin/env python3
"""Run the project-standard NonLinLoc workflow from a prepared input folder.

The input folder must contain ``velocity_model_1d.txt``, ``stations_native.txt``
and ``picks_simple.txt`` (or ``event.obs`` when ``--native-obs`` is used).
All generated files are written below the requested output directory.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PACKAGE_ROOT = HERE.parents[1] / "runtime" / "python" / "Nonlinlocpy"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from nonlinlocpy.standard_nonlinloc import StandardRunConfig, run_standard_workflow  # noqa: E402
from nonlinlocpy.utils import resolve_nlloc_bin_dir  # noqa: E402

REQUIRED = ("velocity_model_1d.txt", "stations_native.txt", "picks_simple.txt")


def validate_input(input_dir: Path, native_obs: bool) -> None:
    required = ("velocity_model_1d.txt", "stations_native.txt", "event.obs") if native_obs else REQUIRED
    missing = [name for name in required if not (input_dir / name).is_file()]
    if missing:
        raise ValueError(f"Missing required NonLinLoc input files in {input_dir}: {', '.join(missing)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="Prepared standard input folder")
    parser.add_argument("--output-dir", type=Path, required=True, help="Writable run/output folder")
    parser.add_argument("--bin-dir", type=Path, default=None, help="Directory containing NLLoc, Vel2Grid and Grid2Time")
    parser.add_argument("--date", default="201907040234", help="Pick-table reference date YYYYMMDDHHMM")
    parser.add_argument("--native-obs", action="store_true", help="Use event.obs instead of picks_simple.txt")
    parser.add_argument("--prepare-only", action="store_true", help="Write controls and grids inputs without locating")
    args = parser.parse_args()
    input_dir = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    validate_input(input_dir, args.native_obs)
    output_dir.mkdir(parents=True, exist_ok=True)
    bin_dir = str(args.bin_dir.expanduser().resolve()) if args.bin_dir else ""
    resolved = Path(resolve_nlloc_bin_dir(bin_dir))
    missing_bin = [name for name in ("NLLoc", "Vel2Grid", "Grid2Time") if not (resolved / name).is_file()]
    if missing_bin:
        raise ValueError(f"Missing NonLinLoc executables in {resolved}: {', '.join(missing_bin)}")
    config = StandardRunConfig(
        input_dir=str(input_dir),
        run_dir=str(output_dir),
        nlloc_bin=str(resolved),
        date=args.date,
        use_native_obs=args.native_obs,
        prepare_only=args.prepare_only,
    )
    result = run_standard_workflow(config)
    summary = {
        "status": "prepared" if args.prepare_only else "success",
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "binary_dir": str(resolved),
        "located_events": result.n_located_events,
        "located_csv": result.located_csv or None,
    }
    (output_dir / "run_result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
