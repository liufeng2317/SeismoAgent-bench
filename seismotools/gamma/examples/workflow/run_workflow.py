#!/usr/bin/env python
"""Run a small, deterministic GaMMA association workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="/tmp/gamma-workflow")
    args = parser.parse_args()
    out = Path(args.output).expanduser().resolve()
    if out.exists():
        raise SystemExit(f"output exists: {out}; choose a new output path")
    input_dir = out / "input"
    result_dir = out / "result"
    input_dir.mkdir(parents=True)
    result_dir.mkdir()

    origin = pd.Timestamp("2019-01-01T00:00:00Z")
    stations = pd.DataFrame({
        "station_id": [f"S{i:02d}" for i in range(8)],
        "x_km": [i * 2.0 for i in range(8)],
        "y_km": [0.0] * 8,
        "z_km": [0.0] * 8,
    })
    picks = []
    for i in range(8):
        for phase, delay in (("P", 1.0 + i * 0.01), ("S", 2.0 + i * 0.01)):
            picks.append({
                "timestamp": (origin + pd.Timedelta(seconds=delay)).isoformat(),
                "station_id": f"S{i:02d}", "phase": phase, "probability": 0.99,
            })
    stations.to_csv(input_dir / "stations.csv", index=False)
    pd.DataFrame(picks).to_csv(input_dir / "picks.csv", index=False)

    root = Path(__file__).resolve().parents[4]
    import subprocess
    subprocess.run([
        "python", str(root / "seismotools/gamma/interface/run.py"),
        "--picks", str(input_dir / "picks.csv"),
        "--stations", str(input_dir / "stations.csv"),
        "--output-dir", str(result_dir),
    ], check=True)
    summary = json.loads((result_dir / "run_result.json").read_text())
    if summary.get("status") != "success":
        raise SystemExit("GaMMA adapter did not succeed")
    for name in ("events.csv", "assignments.csv"):
        if not (result_dir / name).is_file():
            raise SystemExit(f"missing {name}")
    print(json.dumps({"status": "pass", "events": summary.get("events"),
                      "assignments": summary.get("assignments")}, indent=2))


if __name__ == "__main__":
    main()
