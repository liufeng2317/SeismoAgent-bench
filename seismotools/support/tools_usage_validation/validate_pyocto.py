#!/usr/bin/env python3
"""Validate the PyOcto associator interface: travel-time table and synthetic known answers."""
from __future__ import annotations

import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "seismotools" / "pyocto"
PY = sys.executable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthetic_events import make_case, write_case  # noqa: E402

SYN_REGION = {"latitude": [35.3, 35.7], "longitude": [-97.25, -96.75], "depth_km": [0, 20]}


def run(tmp: Path, name: str, picks: Path, stations: Path, model: Path, cfg: dict, workers: int = 4) -> Path:
    (tmp / f"{name}.json").write_text(json.dumps(cfg))
    out = tmp / name
    subprocess.run([PY, "-I", str(TOOL / "interface/run.py"), "--picks", str(picks), "--stations", str(stations),
                    "--velocity-model", str(model), "--output-dir", str(out), "--config", str(tmp / f"{name}.json"),
                    "--workers", str(workers), "--quiet"], check=True, capture_output=True)
    assert json.loads((out / "run_result.json").read_text())["status"] == "success"
    return out


def match_events(truth: pd.DataFrame, found: pd.DataFrame, dt_s: float, dh_km: float) -> dict:
    """true event_id -> found event_index (nearest in time within the gates)."""
    tt, ft = pd.to_datetime(truth.origin_time_utc, utc=True), pd.to_datetime(found.time_utc, utc=True)
    out = {}
    for i, r in truth.reset_index(drop=True).iterrows():
        d = np.abs((ft - tt[i]).dt.total_seconds())
        h = np.hypot((found.latitude - r.latitude) * 111.195,
                     (found.longitude - r.longitude) * 111.195 * np.cos(np.radians(r.latitude)))
        ok = (d <= dt_s) & (h <= dh_km)
        if ok.any():
            out[r.event_id] = int(found.event_index[d.where(ok).idxmin()])
    return out


def check_table(out: Path, vp: float, vs: float) -> dict:
    """The table PyOcto built for the half-space against analytic straight-ray times."""
    raw = (out / "travel_time_table.bin").read_bytes()
    nx, nz, delta = struct.unpack("iid", raw[:16])
    p = np.frombuffer(raw[16:16 + 8 * nx * nz]).reshape(nx, nz)
    s = np.frombuffer(raw[16 + 8 * nx * nz:16 + 16 * nx * nz]).reshape(nx, nz)
    x, z = np.meshgrid(np.arange(nx) * delta, np.arange(nz) * delta, indexing="ij")
    r = np.hypot(x, z)
    far = r >= 2.0
    dp, ds = (p - r / vp)[far], (s - r / vs)[far]
    # First-order fast marching (pyrocko eikonal): never faster than the exact time, worst along the
    # grid diagonal and growing slowly with distance (~0.065 s P at 0.25 km spacing out to 65 km).
    res = {"nx": nx, "nz": nz, "delta_km": delta, "max_error_p_s": round(float(dp.max()), 4),
           "max_error_s_s": round(float(ds.max()), 4), "min_error_s": round(float(min(dp.min(), ds.min())), 4)}
    assert res["min_error_s"] > -1e-3 and res["max_error_p_s"] < 0.1 and res["max_error_s_s"] < 0.1 * vp / vs, res
    return res


def check_synthetic(tmp: Path) -> dict:
    case = make_case(seed=2, noise_s=0.05, false_per_station=3, drop_frac=0.1)
    d = write_case(case, tmp / "syn")
    truth, picks = case["events"], case["picks"]
    res = {}
    for label, extra, workers in (("default", {}, 4), ("default_1thread", {}, 1),
                                  ("tolerance_0.5", {"pick_match_tolerance": 0.5}, 4)):
        cfg = {"region": SYN_REGION, "time_before_s": 30, "associator": extra}
        out = run(tmp, f"syn_{label}", d / "picks.csv", d / "stations.csv", d / "velocity_model.txt", cfg, workers)
        found = pd.read_csv(out / "events.csv")
        m = match_events(truth, found, 1.0, 3.0)
        a = pd.read_csv(out / "assignments.csv", keep_default_na=False).merge(picks[["pick_id", "event_id"]],
                                                                               on="pick_id")
        a["event_id"] = a.event_id.fillna("").astype(str)
        inv = {v: k for k, v in m.items()}
        real = a[a.event_id != ""]
        correct = np.mean([s == "assigned" and inv.get(int(e)) == t
                           for s, e, t in zip(real.assignment_status, real.event_index.replace("", -1), real.event_id)])
        res[label] = {"true_events": len(truth), "found": len(found), "recovered_1s_3km": len(m),
                      "true_picks_correct": round(float(correct), 3),
                      "false_picks_assigned": round(float((a[a.event_id == ""].assignment_status == "assigned").mean()), 3)}
        if label == "default":
            res["table"] = check_table(out, case["vp"], case["vs"])
            events_4 = found
        if label == "default_1thread":
            res["threads_1_vs_4_same_events"] = bool(
                len(found) == len(events_4) and np.allclose(np.sort(pd.to_datetime(found.time_utc).astype("int64")),
                                                            np.sort(pd.to_datetime(events_4.time_utc).astype("int64"))))
    for label in ("default", "tolerance_0.5"):
        r = res[label]
        assert r["recovered_1s_3km"] >= 0.95 * r["true_events"] and r["found"] <= 1.05 * r["true_events"], r
        assert r["true_picks_correct"] >= 0.95, r
    assert res["tolerance_0.5"]["false_picks_assigned"] < 0.05, res
    assert res["threads_1_vs_4_same_events"], res
    return res


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="pyocto-validation-") as tmp:
        synthetic = check_synthetic(Path(tmp))
    print(json.dumps({"status": "pass", "tool": "PyOcto", "synthetic": synthetic}, indent=2))


if __name__ == "__main__":
    main()
