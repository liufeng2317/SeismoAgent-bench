#!/usr/bin/env python
"""Run a small synthetic NonLinLoc velocity/grid/location workflow."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="/tmp/nonlinloc-workflow")
    args = parser.parse_args()
    out = Path(args.output).expanduser().resolve()
    if out.exists():
        raise SystemExit(f"output exists: {out}; choose a new output path")
    input_dir = out / "input"
    result_dir = out / "result"
    input_dir.mkdir(parents=True)
    result_dir.mkdir()
    (input_dir / "velocity_model_1d.txt").write_text("0 5.0 2.9\n5 6.0 3.5\n20 7.0 4.0\n")
    (input_dir / "stations_native.txt").write_text(
        "S001 -117.0000 35.0000 0\nS002 -116.9900 35.0000 0\n"
        "S003 -117.0000 35.0100 0\nS004 -116.9900 35.0100 0\n"
    )
    (input_dir / "picks_simple.txt").write_text(
        "S001 P 10.0 ?\nS001 S 12.0 ?\nS002 P 10.8 ?\nS002 S 13.4 ?\n"
        "S003 P 10.7 ?\nS003 S 13.2 ?\nS004 P 11.4 ?\nS004 S 14.0 ?\n"
    )
    root = Path(__file__).resolve().parents[4]
    subprocess.run([
        "python", str(root / "seismotools/nonlinloc/interface/run.py"),
        "--input-dir", str(input_dir), "--output-dir", str(result_dir),
        "--bin-dir", str(root / "seismotools/nonlinloc/runtime/bin"),
        "--date", "201901010000",
    ], check=True)
    summary = json.loads((result_dir / "run_result.json").read_text())
    if summary.get("status") != "success":
        raise SystemExit("NonLinLoc adapter did not succeed")
    if not (result_dir / "located_events.csv").is_file():
        raise SystemExit("missing located_events.csv")
    print(json.dumps({"status": "pass", "located_events": summary.get("located_events")}, indent=2))


if __name__ == "__main__":
    main()
