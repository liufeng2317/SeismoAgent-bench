#!/usr/bin/env python3
"""Validate the PyOcto associator interface: travel-time table, synthetic known answers, Prague picks."""
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
PRAGUE = ROOT / "workflows/tasks/2011_prague_oklahoma/expert/export/r2"
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


def check_prague(tmp: Path) -> dict:
    """Six hours of Prague PhaseNet picks: PyOcto against the GaMMA r2 association."""
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
    cfg = {"region": {"latitude": s["latitude_bounds"], "longitude": s["longitude_bounds"],
                      "depth_km": s["depth_bounds_km"]},
           "reference_elevation_km": s["reference_elevation_km"], "velocity_layering": s["velocity_layering"],
           "associator": {"n_picks": s["min_picks_per_eq"], "n_p_picks": s["min_p_picks_per_eq"],
                          "n_s_picks": s["min_s_picks_per_eq"]}}
    out = run(tmp, "prague", tmp / "prague_picks.csv", tmp / "prague_stations.csv", tmp / "prague_model.txt", cfg, 8)
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
    res = {"window": [str(t0), str(t1)], "gamma_events": len(g), "pyocto_events": len(e),
           "gamma_matched_by_pyocto": frac(g, e), "gamma_10_stations_matched": frac(g[g.n_stations >= 10], e),
           "pyocto_matched_by_gamma": frac(e, g)}
    assert 0.7 <= len(e) / len(g) <= 1.3 and res["gamma_10_stations_matched"] >= 0.9, res
    return res


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="pyocto-validation-") as tmp:
        synthetic = check_synthetic(Path(tmp))
        prague = check_prague(Path(tmp))
    print(json.dumps({"status": "pass", "tool": "PyOcto", "synthetic": synthetic, "prague": prague}, indent=2))


if __name__ == "__main__":
    main()
