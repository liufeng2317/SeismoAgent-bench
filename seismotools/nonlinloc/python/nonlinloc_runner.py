#!/usr/bin/env python3
"""Small, explicit runner for the native NonLinLoc tool chain.

The runner does not generate scientific control files. It executes already
prepared controls in the required order and returns a machine-readable stage
summary, keeping all run-specific files outside the shared tool directory.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Iterable


def run_stage(binary: Path, control: Path, work_dir: Path) -> dict[str, object]:
    """Run one native NonLinLoc program and capture its result."""
    binary = binary.resolve()
    control = control.resolve()
    work_dir = work_dir.resolve()
    if not binary.is_file():
        raise FileNotFoundError(f"NonLinLoc binary not found: {binary}")
    if not control.is_file():
        raise FileNotFoundError(f"Control file not found: {control}")
    work_dir.mkdir(parents=True, exist_ok=True)
    argument = os.path.relpath(control, work_dir)
    completed = subprocess.run(
        [str(binary), argument],
        cwd=work_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    result = {
        "program": binary.name,
        "control": str(control),
        "returncode": completed.returncode,
        "output": completed.stdout,
    }
    if completed.returncode:
        raise RuntimeError(json.dumps(result, indent=2))
    return result


def run_chain(
    work_dir: Path,
    velocity_control: Path,
    travel_time_controls: Iterable[Path],
    location_control: Path,
    bin_dir: Path,
) -> list[dict[str, object]]:
    """Run Vel2Grid, each Grid2Time control, then NLLoc."""
    stages = [run_stage(bin_dir / "Vel2Grid", velocity_control, work_dir)]
    stages.extend(
        run_stage(bin_dir / "Grid2Time", control, work_dir)
        for control in travel_time_controls
    )
    stages.append(run_stage(bin_dir / "NLLoc", location_control, work_dir))
    return stages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--velocity-control", type=Path, required=True)
    parser.add_argument("--travel-time-control", type=Path, action="append", required=True)
    parser.add_argument("--location-control", type=Path, required=True)
    parser.add_argument(
        "--bin-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "bin",
    )
    args = parser.parse_args()
    stages = run_chain(
        args.work_dir,
        args.velocity_control,
        args.travel_time_control,
        args.location_control,
        args.bin_dir,
    )
    print(json.dumps({"status": "success", "stages": stages}, indent=2))


if __name__ == "__main__":
    main()
