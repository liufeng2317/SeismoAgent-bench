#!/usr/bin/env python3
"""Validate GrowClust: the upstream example reproduced by the local build, the interface on a
synthetic cluster with exact differential times."""
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
from pyproj import Proj

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "seismotools" / "growclust"
BIN = TOOL / "runtime" / "bin" / "growclust"
CCDT = ROOT / "seismotools" / "cross_correlation" / "interface" / "run.py"
PY = sys.executable
EXAMPLE = Path(os.environ.get("GROWCLUST_EXAMPLE", "/liufeng1afs/software/Download/growclust/extract/"
                              "GrowClust-53226cf7662ab5bab5db87138d1ae63227d4ba63/EXAMPLE"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthetic_events import make_case, write_case  # noqa: E402


def run(tmp: Path, name: str, events: Path, stations: Path, dtcc: Path, model: Path, cfg: dict | None = None) -> Path:
    out = tmp / f"out_{name}"
    cmd = [PY, "-I", str(TOOL / "interface/run.py"), "--events", str(events), "--stations", str(stations),
           "--dtcc", str(dtcc), "--velocity-model", str(model), "--output-dir", str(out), "--quiet"]
    if cfg:
        (tmp / f"{name}.json").write_text(json.dumps(cfg))
        cmd += ["--config", str(tmp / f"{name}.json")]
    subprocess.run(cmd, check=True, capture_output=True)
    assert json.loads((out / "run_result.json").read_text())["status"] == "success"
    return out


def check_upstream_example(tmp: Path) -> dict:
    """Native binary on the upstream Spanish Springs example: identical to the shipped catalog."""
    if not (EXAMPLE / "ssprings.inp").is_file():
        return {"status": "skipped", "reason": f"example not found: {EXAMPLE} (set GROWCLUST_EXAMPLE)"}
    work = tmp / "example"
    shutil.copytree(EXAMPLE / "IN", work / "IN")
    shutil.copy2(EXAMPLE / "ssprings.inp", work)
    (work / "TT").mkdir()
    (work / "OUT").mkdir()
    subprocess.run([str(BIN), "ssprings.inp"], cwd=work, check=True, capture_output=True)
    a = np.loadtxt(work / "OUT/out.growclust_cat")
    b = np.loadtxt(EXAMPLE / "OUT/out.growclust_cat")
    res = {"events": len(a), "max_abs_diff": float(np.abs(a - b).max()) if a.shape == b.shape else None}
    assert a.shape == b.shape and res["max_abs_diff"] < 1e-6, res
    return res


def check_synthetic(tmp: Path) -> dict:
    """60 events in a 6-km cluster, catalog perturbed by 0.5 km, exact dt.cc (ccdt format)."""
    case = make_case(seed=4, n_events=60, event_half_km=3.0, depth_km=(4.0, 8.0))
    d = write_case(case, tmp / "syn")
    ev, st = case["events"], case["stations"]
    proj = Proj(proj="aeqd", lon_0=case["projection_center"][0], lat_0=case["projection_center"][1],
                datum="WGS84", units="km")
    sx, sy = proj(st.longitude.to_numpy(), st.latitude.to_numpy())
    rng = np.random.default_rng(5)
    dx, dy, dz = rng.normal(0, 0.5, (3, len(ev)))
    pert = ev.copy()
    pert["longitude"], pert["latitude"] = proj(ev.x_km.to_numpy() + dx, ev.y_km.to_numpy() + dy, inverse=True)
    pert["depth_km"] = ev.depth_km + dz
    pert[["event_id", "origin_time_utc", "latitude", "longitude", "depth_km"]].to_csv(d / "perturbed.csv", index=False)
    cc = d / "dtcc"
    cc.mkdir()
    pd.DataFrame({"cusp_id": np.arange(1, len(ev) + 1), "event_id": ev.event_id}).to_csv(cc / "event_ids.csv",
                                                                                        index=False)
    code = st.station_id.str.split(".").str[-1]
    x, y, z = ev.x_km.to_numpy(), ev.y_km.to_numpy(), ev.depth_km.to_numpy()
    with (cc / "dt.cc").open("w") as f:
        for i in range(len(ev)):
            for j in range(i + 1, len(ev)):
                if np.hypot(x[i] - x[j], y[i] - y[j]) > 6:
                    continue
                f.write(f"# {i + 1:9d} {j + 1:9d} 0.0\n")
                for k in range(len(st)):
                    for ph, v in (("P", case["vp"]), ("S", case["vs"])):
                        t1 = np.sqrt((sx[k] - x[i]) ** 2 + (sy[k] - y[i]) ** 2 + z[i] ** 2) / v
                        t2 = np.sqrt((sx[k] - x[j]) ** 2 + (sy[k] - y[j]) ** 2 + z[j] ** 2) / v
                        f.write(f"{code[k]:<7s} {t1 - t2:10.5f} 0.9500 {ph}\n")
    out = run(tmp, "syn", d / "perturbed.csv", d / "stations.csv", cc, d / "velocity_model.txt")
    r = pd.read_csv(out / "relocated.csv").set_index("event_id")
    ids = r.index[r.cluster_id == r.cluster_id.value_counts().idxmax()]
    truth = ev.set_index("event_id").loc[ids]
    T = np.c_[truth.x_km, truth.y_km, truth.depth_km]
    T = T - T.mean(0)

    def rel(df):
        px, py = proj(df.loc[ids, "longitude"].to_numpy(), df.loc[ids, "latitude"].to_numpy())
        X = np.c_[px, py, df.loc[ids, "depth_km"]]
        return X - X.mean(0)
    e_pert = np.linalg.norm(rel(pert.set_index("event_id")) - T, axis=1)
    diff = rel(r) - T
    res = {"cluster_events": len(ids), "relocated": int(r.relocated.sum()),
           "median_rel_error_perturbed_km": round(float(np.median(e_pert)), 3),
           "median_rel_error_km": round(float(np.median(np.linalg.norm(diff, axis=1))), 3),
           "median_rel_error_horizontal_km": round(float(np.median(np.linalg.norm(diff[:, :2], axis=1))), 3),
           "max_rel_error_km": round(float(np.linalg.norm(diff, axis=1).max()), 3)}
    assert res["cluster_events"] == 60 and res["median_rel_error_horizontal_km"] < 0.05, res
    assert res["median_rel_error_km"] < 0.1 and res["median_rel_error_km"] * 5 < res["median_rel_error_perturbed_km"], res
    return res


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="growclust-validation-") as tmp:
        tmp = Path(tmp)
        example = check_upstream_example(tmp)
        synthetic = check_synthetic(tmp)
    print(json.dumps({"status": "pass", "tool": "GrowClust", "upstream_example": example, "synthetic": synthetic}, indent=2))


if __name__ == "__main__":
    main()
