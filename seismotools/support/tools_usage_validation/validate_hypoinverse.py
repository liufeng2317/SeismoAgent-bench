#!/usr/bin/env python3
"""Validate HypoInverse: the upstream testone example reproduced by the local build, the interface on
synthetic known hypocentres (both hemispheres), and on stations 0-2 km above the model datum (CRE models
must recover the hypocentres; CRH, which ignores elevations, must not)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "seismotools" / "hypoinverse"
BIN = TOOL / "runtime" / "bin" / "hyp1.40"
PY = sys.executable
TESTONE = Path(os.environ.get("HYPOINVERSE_TESTONE", "/liufeng1afs/software/Download/hypoinverse/extract/testone"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthetic_events import make_case, write_case  # noqa: E402


def run(tmp: Path, name: str, arrivals: Path, stations: Path, model: Path, cfg: dict | None = None) -> Path:
    out = tmp / f"out_{name}"
    cmd = [PY, "-I", str(TOOL / "interface/run.py"), "--arrivals", str(arrivals), "--stations", str(stations),
           "--velocity-model", str(model), "--output-dir", str(out), "--quiet"]
    if cfg:
        (tmp / f"{name}.json").write_text(json.dumps(cfg))
        cmd += ["--config", str(tmp / f"{name}.json")]
    subprocess.run(cmd, check=True, capture_output=True)
    assert json.loads((out / "run_result.json").read_text())["status"] == "success"
    return out


def check_testone(tmp: Path) -> dict:
    """Native hyp1.40 on the upstream testone example: summary and archive identical to the shipped ones."""
    if not (TESTONE / "testone.hyp").is_file():
        return {"status": "skipped", "reason": f"example not found: {TESTONE} (set HYPOINVERSE_TESTONE)"}
    work = tmp / "testone"
    work.mkdir()
    for f in TESTONE.iterdir():
        if f.suffix not in (".sum", ".arc", ".prt"):
            shutil.copy2(f, work / f.name)
    subprocess.run([str(BIN)], input="@testone.hyp\n\n\n\n\nLOC\nSTO\n", text=True, cwd=work, check=True,
                   capture_output=True, timeout=120)
    same = {k: (work / f"testone.{k}").read_text() == (TESTONE / f"testone.{k}").read_text() for k in ("sum", "arc")}
    assert all(same.values()), same
    return {"summary_identical": same["sum"], "archive_identical": same["arc"]}


def check_synthetic(tmp: Path) -> dict:
    res = {}
    for label, lat0, lon0 in (("north_west", 35.5, -97.0), ("south_east", -42.3, 173.7)):
        case = make_case(seed=6, lat0=lat0, lon0=lon0)
        d = write_case(case, tmp / f"syn_{label}")
        arr = case["picks"][case["picks"].event_id.astype(str) != ""]
        arr.to_csv(d / "arrivals.csv", index=False)
        out = run(tmp, label, d / "arrivals.csv", d / "stations.csv", d / "velocity_model.txt")
        truth = case["events"].set_index("event_id")
        e = pd.read_csv(out / "events.csv").set_index("event_id").loc[truth.index]
        dh = np.hypot((e.latitude - truth.latitude) * 111.195,
                      (e.longitude - truth.longitude) * 111.195 * np.cos(np.radians(lat0)))
        dt = (pd.to_datetime(e.origin_time_utc) - pd.to_datetime(truth.origin_time_utc)).dt.total_seconds()
        links = pd.read_csv(out / "arrivals.csv")
        res[label] = {"located": int((e.status == "LOCATED").sum()), "max_epi_km": round(float(dh.max()), 3),
                      "max_abs_depth_km": round(float((e.depth_km - truth.depth_km).abs().max()), 3),
                      "max_abs_origin_s": round(float(dt.abs().max()), 3),
                      "arrivals_parsed": len(links), "arrivals_in": len(arr),
                      "max_abs_residual_s": round(float(links.residual_s.abs().max()), 3)}
        r = res[label]
        assert r["located"] == 40 and r["max_epi_km"] < 0.1 and r["max_abs_depth_km"] < 0.2, r
        assert r["max_abs_origin_s"] < 0.03 and r["arrivals_parsed"] == r["arrivals_in"], r
    return res


def check_elevated(tmp: Path) -> dict:
    """Uniform half-space, stations at 0-2 km elevation, events 2-10 km below sea level; exact arrivals."""
    rng = np.random.default_rng(1)
    lat0, lon0, vp, vs = 40.0, -112.0, 6.0, 3.46
    kx = 111.195 * np.cos(np.radians(lat0))
    st = pd.DataFrame({"station_id": [f"XX.E{i:02d}" for i in range(15)], "x": rng.uniform(-20, 20, 15),
                       "y": rng.uniform(-20, 20, 15), "elevation_m": rng.uniform(0, 2000, 15).round()})
    st["latitude"], st["longitude"] = lat0 + st.y / 111.195, lon0 + st.x / kx
    ev = pd.DataFrame({"event_id": [f"e{i:03d}" for i in range(40)], "x": rng.uniform(-8, 8, 40),
                       "y": rng.uniform(-8, 8, 40), "z": rng.uniform(2, 10, 40)})
    ev["t"] = pd.Timestamp("2020-01-01T00:00:00Z") + pd.to_timedelta(np.arange(40) * 60, unit="s")
    rows = []
    for e in ev.itertuples():
        for s in st.itertuples():
            r = np.sqrt((e.x - s.x) ** 2 + (e.y - s.y) ** 2 + (e.z + s.elevation_m / 1000) ** 2)
            for ph, v in (("P", vp), ("S", vs)):
                rows.append({"event_id": e.event_id, "pick_id": f"{e.event_id}{s.station_id}{ph}", "station_id": s.station_id,
                             "phase": ph, "time_utc": (e.t + pd.Timedelta(seconds=r / v)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")})
    d = tmp / "elevated"
    d.mkdir()
    pd.DataFrame(rows).to_csv(d / "arrivals.csv", index=False)
    st[["station_id", "latitude", "longitude", "elevation_m"]].to_csv(d / "stations.csv", index=False)
    (d / "model.txt").write_text(f"0.0 {vp} {vs}\n")
    res = {}
    for model_type in ("CRE", "CRH"):
        out = run(tmp, f"elevated_{model_type}", d / "arrivals.csv", d / "stations.csv", d / "model.txt",
                  {"model_type": model_type})
        e = pd.read_csv(out / "events.csv").set_index("event_id").loc[ev.event_id]
        dz = e.depth_km.to_numpy() - ev.z.to_numpy()
        dt = (pd.to_datetime(e.origin_time_utc).reset_index(drop=True) - ev.t).dt.total_seconds().to_numpy()
        res[model_type] = {"max_abs_depth_km": round(float(np.abs(dz).max()), 3), "median_depth_error_km": round(float(np.median(dz)), 3),
                           "max_abs_origin_s": round(float(np.abs(dt).max()), 3)}
    assert res["CRE"]["max_abs_depth_km"] < 0.2 and res["CRE"]["max_abs_origin_s"] < 0.03, res
    assert res["CRH"]["median_depth_error_km"] > 0.5, res  # the known CRH limitation is still visible
    return res


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="hypoinverse-validation-") as tmp:
        tmp = Path(tmp)
        testone = check_testone(tmp)
        synthetic = check_synthetic(tmp)
        elevated = check_elevated(tmp)
    print(json.dumps({"status": "pass", "tool": "HypoInverse", "testone": testone, "synthetic": synthetic,
                      "elevated_stations": elevated}, indent=2))


if __name__ == "__main__":
    main()
