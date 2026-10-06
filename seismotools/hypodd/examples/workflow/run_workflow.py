#!/usr/bin/env python
"""Run a small synthetic hypoDD catalog-only relocation workflow."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="/tmp/hypodd-workflow")
    args = parser.parse_args()
    out = Path(args.output).expanduser().resolve()
    if out.exists():
        raise SystemExit(f"output exists: {out}; choose a new output path")
    input_dir = out / "input"
    result_dir = out / "result"
    input_dir.mkdir(parents=True)
    result_dir.mkdir()
    (input_dir / "event.dat").write_text(
        "20190101 000001 35.0 -117.0 5.0 1.0 0.1 0.1 0.0 1001\n"
        "20190101 000002 35.01 -117.01 5.0 1.0 0.1 0.1 0.0 1002\n"
    )
    (input_dir / "station.dat").write_text("STA01 35.0 -117.0\n")
    (input_dir / "dt.ct").write_text("# 1001 1002\nSTA01 0.0 1.0 1.0 P\n")
    (input_dir / "hypoDD.inp").write_text(
        "missing.cc\ndt.ct\nevent.dat\nstation.dat\nhypoDD.loc\n"
        "hypoDD.reloc\nhypoDD.res\nhypoDD.stares\nhypoDD.srcpar\n"
        "2 3 1000\n0 1\n1 2 1\n1 0.0 1.0 1.0 100.0 1.0 1.0 1.0 100.0 10.0\n"
        "1 1.73\n0.0\n6.0\n0\n"
    )
    root = Path(__file__).resolve().parents[4]
    subprocess.run([
        "python", str(root / "seismotools/hypodd/interface/run.py"),
        "--input-dir", str(input_dir), "--output-dir", str(result_dir), "--mode", "ct",
        "--bin-dir", str(root / "seismotools/hypodd/runtime/bin"),
    ], check=True)
    summary = json.loads((result_dir / "run_result.json").read_text())
    if summary.get("status") != "success":
        raise SystemExit("hypoDD adapter did not succeed")
    if not (result_dir / "hypoDD.loc").is_file():
        raise SystemExit("missing hypoDD.loc")
    print(json.dumps({"status": "pass", "mode": summary.get("mode")}, indent=2))


if __name__ == "__main__":
    main()
