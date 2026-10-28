#!/usr/bin/env python3
"""Validate the REAL associator interface: travel-time table, synthetic known answers (incl. a
midnight crossing)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "seismotools" / "real"
PY = sys.executable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthetic_events import make_case, write_case  # noqa: E402
from validate_pyocto import match_events  # noqa: E402  (shared scoring helper)

# the synthetic network spans ~40 km, so the search distance is reduced and the
# nearest-station cut nxd * max_distance (upstream demo nxd 0.2) loosened accordingly
SYN_CFG = {"search": {"max_distance_deg": 0.5}, "table": {"max_distance_deg": 0.6, "max_depth_km": 25},
           "thresholds": {"nxd": 0.5}}


def run(tmp: Path, name: str, picks: Path, stations: Path, model: Path, cfg: dict, workers: int = 8) -> Path:
    (tmp / f"{name}.json").write_text(json.dumps(cfg))
    out = tmp / f"out_{name}"
    subprocess.run([PY, "-I", str(TOOL / "interface/run.py"), "--picks", str(picks), "--stations", str(stations),
                    "--velocity-model", str(model), "--output-dir", str(out), "--config", str(tmp / f"{name}.json"),
                    "--workers", str(workers), "--quiet"], check=True, capture_output=True)
    assert json.loads((out / "run_result.json").read_text())["status"] == "success"
    return out


def check_table(out: Path, vp: float, vs: float) -> dict:
    t = pd.read_csv(out / "ttdb.txt", sep=r"\s+", header=None,
                    names=["gd", "dep", "tp", "ts", "rp", "rs", "hp", "hs", "pp", "sp"])
    x, z = t.gd * 111.19, t.dep
    r = np.hypot(x, z)
    far = r >= 2.0
    ok = far & (x > 1.0) & (z > 1.0)
    res = {"rows": len(t),
           "max_error_p_s": round(float((t.tp - r / vp)[far].max()), 4),
           "min_error_s": round(float(min((t.tp - r / vp)[far].min(), (t.ts - r / vs)[far].min())), 4),
           "max_error_s_s": round(float((t.ts - r / vs)[far].max()), 4),
           "max_rel_error_dtdx": round(float((np.abs(t.rp / 111.19 - x / r / vp) / (1 / vp))[ok].max()), 4),
           "max_rel_error_dtdz": round(float((np.abs(t.hp - z / r / vp) / (1 / vp))[ok].max()), 4)}
    assert res["min_error_s"] > -1e-3 and res["max_error_p_s"] < 0.05 and res["max_error_s_s"] < 0.05 * vp / vs, res
    assert res["max_rel_error_dtdx"] < 0.1 and res["max_rel_error_dtdz"] < 0.1, res
    return res


def score(case: dict, out: Path) -> dict:
    truth, picks = case["events"], case["picks"]
    found = pd.read_csv(out / "events.csv")
    m = match_events(truth, found, 1.0, 3.0)
    a = pd.read_csv(out / "assignments.csv", keep_default_na=False).merge(picks[["pick_id", "event_id"]],
                                                                           on="pick_id")
    a["event_id"] = a.event_id.fillna("").astype(str)
    inv = {v: k for k, v in m.items()}
    real = a[a.event_id != ""]
    correct = np.mean([s == "assigned" and inv.get(int(e)) == t
                       for s, e, t in zip(real.assignment_status, real.event_index.replace("", -1), real.event_id)])
    dt = np.diff(np.sort(pd.to_datetime(found.time_utc).astype("int64") / 1e9))
    return {"true_events": len(truth), "found": len(found), "recovered_1s_3km": len(m),
            "true_picks_correct": round(float(correct), 3),
            "false_picks_assigned": round(float((a[a.event_id == ""].assignment_status == "assigned").mean()), 3),
            "duplicate_events_within_2s": int((dt < 2).sum())}


def check_synthetic(tmp: Path) -> dict:
    res = {}
    for label, t0 in (("same_day", "2020-01-01T00:00:00Z"), ("across_midnight", "2020-01-01T23:50:00Z")):
        case = make_case(seed=3, noise_s=0.05, false_per_station=3, drop_frac=0.1, t0=t0)
        d = write_case(case, tmp / f"syn_{label}")
        out = run(tmp, f"syn_{label}", d / "picks.csv", d / "stations.csv", d / "velocity_model.txt", SYN_CFG)
        res[label] = score(case, out)
        if label == "same_day":
            res["table"] = check_table(out, case["vp"], case["vs"])
        else:
            res[label]["chunks"] = json.loads((out / "run_result.json").read_text())["chunks"]
    for label in ("same_day", "across_midnight"):
        r = res[label]
        assert r["recovered_1s_3km"] >= 0.95 * r["true_events"] and r["found"] <= 1.05 * r["true_events"], r
        assert r["true_picks_correct"] >= 0.95 and r["false_picks_assigned"] < 0.05, r
        assert r["duplicate_events_within_2s"] == 0, r
    assert res["across_midnight"]["chunks"] == 2, res
    return res


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="real-validation-") as tmp:
        synthetic = check_synthetic(Path(tmp))
    print(json.dumps({"status": "pass", "tool": "REAL", "synthetic": synthetic}, indent=2))


if __name__ == "__main__":
    main()
