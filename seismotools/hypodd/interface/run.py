#!/usr/bin/env python3
"""Run a prepared hypoDD CT or CT+CC relocation directory."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DEFAULT_BIN = ROOT / "runtime" / "bin"


def copy_inputs(input_dir: Path, output_dir: Path, mode: str, run_ph2dt: bool) -> list[str]:
    required = ["hypoDD.inp", "station.dat"]
    if not run_ph2dt:
        required.extend(["event.dat", "dt.ct"])
    else:
        required.append("phase.dat")
    if mode == "ct_cc":
        required.append("dt.cc")
    if run_ph2dt:
        required.append("ph2dt.inp")
    missing = [name for name in required if not (input_dir / name).is_file()]
    if missing:
        raise ValueError(f"Missing hypoDD input files: {', '.join(missing)}")
    copied = []
    optional = ["hypoDD.inp", "event.dat", "station.dat", "phase.dat", "dt.ct", "dt.cc", "ph2dt.inp"]
    for name in optional:
        src = input_dir / name
        if src.is_file():
            shutil.copy2(src, output_dir / name)
            copied.append(name)
    if run_ph2dt:
        # ph2dt reads its station/phase paths from the control file.  The
        # packaged templates use input/station.dat and input/phase.dat; stage
        # those canonical paths without touching the declared input directory.
        ph2dt_input = output_dir / "input"
        ph2dt_input.mkdir(exist_ok=True)
        shutil.copy2(output_dir / "station.dat", ph2dt_input / "station.dat")
        shutil.copy2(output_dir / "phase.dat", ph2dt_input / "phase.dat")
        shutil.copy2(output_dir / "station.dat", output_dir / "hypoDD_station.dat")
        shutil.copy2(output_dir / "phase.dat", output_dir / "hypoDD_phase.dat")
    return copied


def run_command(binary: Path, control: str, cwd: Path, log) -> None:
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError(f"Missing or non-executable binary: {binary}")
    subprocess.run([str(binary), control], cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("ct", "ct_cc"), default="ct")
    parser.add_argument("--bin-dir", type=Path, default=None)
    parser.add_argument("--run-ph2dt", action="store_true", help="Run ph2dt.inp before hypoDD")
    parser.add_argument("--overwrite", action="store_true", help="Replace known output files in an existing directory")
    args = parser.parse_args()
    input_dir = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    bin_dir = (args.bin_dir.expanduser().resolve() if args.bin_dir else DEFAULT_BIN)
    log_path = output_dir / "hypodd.log"
    result_path = output_dir / "run_result.json"
    known_outputs = ["hypoDD.loc", "hypoDD.reloc", "hypoDD.res", "hypoDD.stares", "hypoDD.srcpar", "hypodd.log", "run_result.json"]
    if not args.overwrite:
        existing = [name for name in known_outputs if (output_dir / name).exists()]
        if existing:
            raise ValueError(f"output files already exist; choose a new directory or use --overwrite: {existing}")
    try:
        copied = copy_inputs(input_dir, output_dir, args.mode, args.run_ph2dt)
        with log_path.open("w", encoding="utf-8") as log:
            if args.run_ph2dt:
                run_command(bin_dir / "ph2dt", "ph2dt.inp", output_dir, log)
                if not (output_dir / "dt.ct").is_file():
                    raise RuntimeError("ph2dt completed without creating dt.ct")
            run_command(bin_dir / "hypoDD", "hypoDD.inp", output_dir, log)
        location = output_dir / "hypoDD.loc"
        if not location.is_file():
            raise RuntimeError("hypoDD completed without creating hypoDD.loc")
        generated = [str(output_dir / name) for name in known_outputs if (output_dir / name).is_file() and name != "run_result.json"]
        summary = {
            "status": "success",
            "interface_version": 2,
            "mode": args.mode,
            "inputs": {"input_dir": str(input_dir), "binary_dir": str(bin_dir)},
            "output_dir": str(output_dir),
            "inputs_copied": copied,
            "outputs": generated,
            "location_file": str(location),
        }
    except Exception as exc:
        summary = {"status": "failed", "interface_version": 2, "mode": args.mode, "output_dir": str(output_dir), "error": str(exc), "log": str(log_path)}
        result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2), file=sys.stderr)
        return 1
    result_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
