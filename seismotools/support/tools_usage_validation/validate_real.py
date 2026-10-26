#!/usr/bin/env python3
"""Validate the REAL associator interface: travel-time table, synthetic known answers (incl. a
midnight crossing), Prague picks against the GaMMA association."""
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
PRAGUE = ROOT / "workflows/tasks/2011_prague_oklahoma/expert/export/r2"
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


def check_prague(tmp: Path) -> dict:
    """Six hours of Prague PhaseNet picks: REAL against the GaMMA r2 association."""
    t0, t1 = pd.Timestamp("2011-11-11T00:00Z"), pd.Timestamp("2011-11-11T06:00Z")
    p = pd.read_csv(PRAGUE / "02_pick_phasenet/full/picks.csv")
    pt = pd.to_datetime(p.time_utc, utc=True, format="ISO8601")
    p[(pt >= t0) & (pt < t1)][["pick_id", "station_id", "phase", "time_utc", "probability"]] \
        .to_csv(tmp / "prague_picks.csv", index=False)
    st = pd.read_csv(PRAGUE / "03_associate_gamma/full/stations.csv")
    st.assign(elevation_m=st.elevation_m - st.sensor_depth_m)[["station_id", "latitude", "longitude", "elevation_m"]] \
        .to_csv(tmp / "prague_stations.csv", index=False)
    inputs = json.loads((PRAGUE / "03_associate_gamma/full/inputs.json").read_text())
    s = inputs["settings"]
    (tmp / "prague_model.txt").write_text("".join(f"{r['top_of_layer_km']} {r['vp_km_s']} {r['vs_km_s']}\n"
                                                 for r in inputs["model_source"]["rows"]))
    cfg = {"reference_elevation_km": s["reference_elevation_km"], "velocity_layering": s["velocity_layering"],
           "region": {"latitude": s["latitude_bounds"], "longitude": s["longitude_bounds"],
                      "depth_km": s["depth_bounds_km"]},
           "thresholds": {"np0": s["min_p_picks_per_eq"], "ns0": s["min_s_picks_per_eq"],
                          "nps0": s["min_picks_per_eq"]}}
    out = run(tmp, "prague", tmp / "prague_picks.csv", tmp / "prague_stations.csv", tmp / "prague_model.txt", cfg, 16)
    e = pd.read_csv(out / "events.csv")
    e["t"] = pd.to_datetime(e.time_utc, utc=True)
    g = pd.read_csv(PRAGUE / "03_associate_gamma/full/events.csv")
    g["t"] = pd.to_datetime(g.origin_time, utc=True, format="ISO8601")
    g = g[(g.t >= t0) & (g.t < t1)]

    def frac(a, b):
        hit = [((np.abs((b.t - r.t).dt.total_seconds()) <= 2) &
                (np.hypot((b.latitude - r.latitude) * 111.195, (b.longitude - r.longitude) * 90.6) <= 10)).any()
               for r in a.itertuples()]
        return round(float(np.mean(hit)), 3) if hit else float("nan")
    res = {"window": [str(t0), str(t1)], "gamma_events": len(g), "real_events": len(e),
           "gamma_matched_by_real": frac(g, e), "gamma_10_stations_matched": frac(g[g.n_stations >= 10], e),
           "real_matched_by_gamma": frac(e, g)}
    assert 0.7 <= len(e) / len(g) <= 1.3 and res["gamma_10_stations_matched"] >= 0.9, res
    return res


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="real-validation-") as tmp:
        synthetic = check_synthetic(Path(tmp))
        prague = check_prague(Path(tmp))
    print(json.dumps({"status": "pass", "tool": "REAL", "synthetic": synthetic, "prague": prague}, indent=2))


if __name__ == "__main__":
    main()
