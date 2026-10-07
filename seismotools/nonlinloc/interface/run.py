#!/usr/bin/env python3
"""Run the project-standard NonLinLoc workflow from a prepared input folder.

The input folder must contain ``velocity_model_1d.txt``, ``stations_native.txt``
and ``picks_simple.txt`` (or ``event.obs`` when ``--native-obs`` is used).
All generated files are written below the requested output directory.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PACKAGE_ROOT = HERE.parents[1] / "runtime" / "python" / "Nonlinlocpy"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from nonlinlocpy.standard_nonlinloc import StandardRunConfig, config_from_dict, run_standard_workflow  # noqa: E402
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
    parser.add_argument("--date", default=None, help="Pick-table reference date YYYYMMDDHHMM")
    parser.add_argument("--native-obs", action="store_true", default=None, help="Use event.obs instead of picks_simple.txt")
    parser.add_argument("--prepare-only", action="store_true", default=None, help="Write controls and grids inputs without locating")
    parser.add_argument("--config", type=Path, default=None, help="Optional JSON standard workflow settings")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing non-empty output directory")
    args = parser.parse_args()
    input_dir = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.overwrite and any(output_dir.iterdir()):
        raise ValueError(f"output directory is not empty; choose a new directory or use --overwrite: {output_dir}")
    settings = {}
    if args.config:
        settings = json.loads(args.config.read_text(encoding="utf-8"))
        if not isinstance(settings, dict):
            raise ValueError("NonLinLoc config must be a JSON object")
    try:
        bin_dir = str(args.bin_dir.expanduser().resolve()) if args.bin_dir else ""
        resolved = Path(resolve_nlloc_bin_dir(bin_dir))
        missing_bin = [name for name in ("NLLoc", "Vel2Grid", "Grid2Time")
                       if not (resolved / name).is_file() or not os.access(resolved / name, os.X_OK)]
        if missing_bin:
            raise ValueError(f"Missing NonLinLoc executables in {resolved}: {', '.join(missing_bin)}")
        config = config_from_dict(settings)
        config.input_dir = str(input_dir)
        config.run_dir = str(output_dir)
        config.nlloc_bin = str(resolved)
        if args.date is not None:
            config.date = args.date
        if args.native_obs is not None:
            config.use_native_obs = args.native_obs
        if args.prepare_only is not None:
            config.prepare_only = args.prepare_only
        validate_input(input_dir, config.use_native_obs)
        result = run_standard_workflow(config)
        outputs = [str(output_dir / name) for name in ("model", "time", "obs", "loc") if (output_dir / name).exists()]
        if result.located_csv:
            outputs.append(result.located_csv)
        summary = {
            "status": "prepared" if config.prepare_only else "success",
            "interface_version": 2,
            "inputs": {"input_dir": str(input_dir), "native_obs": config.use_native_obs},
            "config": dataclasses.asdict(config),
            "output_dir": str(output_dir),
            "binary_dir": str(resolved),
            "located_events": result.n_located_events,
            "located_csv": result.located_csv or None,
            "outputs": outputs,
        }
    except Exception as exc:
        summary = {
            "status": "failed",
            "interface_version": 2,
            "inputs": {"input_dir": str(input_dir), "native_obs": bool(args.native_obs)},
            "output_dir": str(output_dir),
            "error": str(exc),
        }
        result_path = output_dir / "run_result.json"
        if args.overwrite or not result_path.exists():
            result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2), file=sys.stderr)
        return 1
    (output_dir / "run_result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1)
