#!/usr/bin/env python3
"""Validate the local cross-correlation tool (ccdt): kernels and synthetic known answers."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "seismotools" / "cross_correlation"
PY = sys.executable
sys.path.insert(0, str(TOOL / "runtime" / "python"))

from ccdt import cc_curves, pick_peak  # noqa: E402



def check_kernels() -> dict:
    """cc_curves against a brute-force Pearson loop; parabolic peak on a cosine."""
    rng = np.random.default_rng(0)
    t, s = rng.normal(size=(5, 40)), rng.normal(size=(5, 40 + 2 * 7))
    fast = cc_curves(t, s)
    brute = np.array([[np.corrcoef(t[i], s[i, k:k + 40])[0, 1] for k in range(15)] for i in range(5)])
    true_frac = 0.3
    lags = np.arange(-10, 11)
    cc = np.cos(2 * np.pi * (lags - true_frac) / 40.0)[None, :]
    k, peak, frac, ok = pick_peak(cc)
    return {"max_abs_diff_vs_bruteforce": float(np.abs(fast - brute).max()),
            "parabola_frac": float(frac[0]), "parabola_true": true_frac,
            "status": "pass" if np.abs(fast - brute).max() < 1e-10 and abs(frac[0] - true_frac) < 0.01 and ok[0]
            else "fail"}


def check_synthetic(tmp: Path) -> dict:
    data, run1, run4 = tmp / "syn", tmp / "syn_run1", tmp / "syn_run4"
    subprocess.run([PY, "-I", str(TOOL / "examples/smoke/make_synthetic.py"), "--out", str(data)], check=True,
                   capture_output=True)
    for out, w in ((run1, 1), (run4, 4)):
        subprocess.run([PY, "-I", str(TOOL / "interface/run.py"), "--events", str(data / "events.csv"),
                        "--arrivals", str(data / "arrivals.csv"), "--waveforms", str(data / "waveforms"),
                        "--output-dir", str(out), "--workers", str(w), "--quiet"], check=True, capture_output=True)
    chk = subprocess.run([PY, "-I", str(TOOL / "examples/smoke/check_synthetic.py"), "--data", str(data),
                          "--run", str(run4)], capture_output=True, text=True)
    summary = json.loads(chk.stdout)
    summary["workers_1_vs_4_identical"] = (run1 / "dt.cc").read_bytes() == (run4 / "dt.cc").read_bytes()
    if not summary["workers_1_vs_4_identical"]:
        summary["status"] = "fail"
    return summary


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ccdt_validate_") as d:
        tmp = Path(d)
        report = {"tool": "cross_correlation", "kernels": check_kernels(), "synthetic": check_synthetic(tmp)}
    report["status"] = "pass" if all(report[k]["status"] in ("pass", "skipped")
                                     for k in ("kernels", "synthetic")) else "fail"
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
