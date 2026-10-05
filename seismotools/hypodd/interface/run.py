#!/usr/bin/env python3
"""Run a prepared hypoDD CT or CT+CC relocation directory."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
DEFAULT_BIN = ROOT / "runtime" / "bin"


def copy_inputs(input_dir: Path, output_dir: Path, mode: str, run_ph2dt: bool) -> list[str]:
    required = ["hypoDD.inp", "event.dat", "station.dat", "dt.ct"]
    if mode == "ct_cc":
        required.append("dt.cc")
    if run_ph2dt:
        required.append("ph2dt.inp")
    missing = [name for name in required if not (input_dir / name).is_file()]
    if missing:
        raise ValueError(f"Missing hypoDD input files: {', '.join(missing)}")
    copied = []
    optional = ["hypoDD.inp", "event.dat", "station.dat", "dt.ct", "dt.cc", "ph2dt.inp"]
    for name in optional:
        src = input_dir / name
        if src.is_file():
            shutil.copy2(src, output_dir / name)
            copied.append(name)
    return copied


def run_command(binary: Path, control: str, cwd: Path, log) -> None:
    if not binary.is_file():
        raise ValueError(f"Missing executable: {binary}")
    subprocess.run([str(binary), control], cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("ct", "ct_cc"), default="ct")
    parser.add_argument("--bin-dir", type=Path, default=None)
    parser.add_argument("--run-ph2dt", action="store_true", help="Run ph2dt.inp before hypoDD")
    args = parser.parse_args()
    input_dir = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    bin_dir = (args.bin_dir.expanduser().resolve() if args.bin_dir else DEFAULT_BIN)
    copied = copy_inputs(input_dir, output_dir, args.mode, args.run_ph2dt)
    log_path = output_dir / "hypodd.log"
    try:
        with log_path.open("w", encoding="utf-8") as log:
            if args.run_ph2dt:
                run_command(bin_dir / "ph2dt", "ph2dt.inp", output_dir, log)
            run_command(bin_dir / "hypoDD", "hypoDD.inp", output_dir, log)
        location = output_dir / "hypoDD.loc"
        if not location.is_file():
            raise RuntimeError("hypoDD completed without creating hypoDD.loc")
        summary = {
            "status": "success",
            "mode": args.mode,
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "binary_dir": str(bin_dir),
            "inputs_copied": copied,
            "location_file": str(location),
            "log": str(log_path),
        }
    except Exception as exc:
        summary = {"status": "failed", "mode": args.mode, "output_dir": str(output_dir), "error": str(exc), "log": str(log_path)}
        (output_dir / "run_result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2), file=sys.stderr)
        return 1
    (output_dir / "run_result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
