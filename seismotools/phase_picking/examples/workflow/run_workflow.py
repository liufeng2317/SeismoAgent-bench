#!/usr/bin/env python
"""Run a deterministic CPU PhaseNet inference workflow."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="/tmp/phase-picking-workflow")
    args = parser.parse_args()
    out = Path(args.output).expanduser().resolve()
    if out.exists():
        raise SystemExit(f"output exists: {out}; choose a new output path")
    input_dir = out / "input"
    result_dir = out / "result"
    input_dir.mkdir(parents=True)
    result_dir.mkdir()

    rng = np.random.default_rng(42)
    data = (0.02 * rng.normal(size=(3, 3001))).astype("float32")
    data[:, 1500:1510] += np.array([[2.0], [1.0], [0.5]], dtype="float32")
    np.savez(input_dir / "waveform.npz", data=data)

    root = Path(__file__).resolve().parents[4]
    subprocess.run([
        os.environ.get("PYTHON", "python"), str(root / "seismotools/phase_picking/interface/run.py"),
        "--input-npz", str(input_dir / "waveform.npz"),
        "--output-dir", str(result_dir), "--model", "phasenet", "--sample-rate", "100",
    ], check=True)
    summary = json.loads((result_dir / "run_result.json").read_text())
    probabilities = np.load(result_dir / "probabilities.npz")
    if summary.get("status") != "success":
        raise SystemExit("PhaseNet adapter did not succeed")
    if probabilities["probabilities"].shape[0] != 1:
        raise SystemExit("unexpected probability batch shape")
    print(json.dumps({"status": "pass", "model": summary.get("model"),
                      "output_shape": list(probabilities["probabilities"].shape)}, indent=2))


if __name__ == "__main__":
    main()
