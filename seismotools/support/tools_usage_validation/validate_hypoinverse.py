#!/usr/bin/env python3
"""Validate HypoInverse: the upstream testone example reproduced by the local build, the interface on
synthetic known hypocentres (both hemispheres), and 50 Prague events against NonLinLoc."""
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
PRAGUE = ROOT / "workflows/tasks/2011_prague_oklahoma/expert/export/r2"
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


def check_prague(tmp: Path, n_events: int = 50) -> dict:
    """50 r2 events (as in validate_nonlinloc): HypoInverse vs NonLinLoc (r2 stage 04, with station delays)."""
    ref = pd.read_csv(PRAGUE / "04_locate_nonlinloc/full/events.csv")
    ref = ref[(ref.status == "LOCATED") & (ref.n_stations >= 10)].sort_values("event_id")
    ref = ref.iloc[np.linspace(0, len(ref) - 1, n_events).astype(int)].set_index("event_id")
    p = pd.read_csv(PRAGUE / "03_associate_gamma/full/picks.csv", keep_default_na=False)
    p[p.event_id.isin(ref.index)][["event_id", "pick_id", "station_id", "phase", "time_utc"]] \
        .to_csv(tmp / "prague_arrivals.csv", index=False)
    st = pd.read_csv(PRAGUE / "03_associate_gamma/full/stations.csv")
    st.assign(elevation_m=st.elevation_m - st.sensor_depth_m)[["station_id", "latitude", "longitude", "elevation_m"]] \
        .to_csv(tmp / "prague_stations.csv", index=False)
    inputs = json.loads((PRAGUE / "03_associate_gamma/full/inputs.json").read_text())
    (tmp / "prague_model.txt").write_text("".join(f"{r['top_of_layer_km']} {r['vp_km_s']} {r['vs_km_s']}\n"
                                                 for r in inputs["model_source"]["rows"]))
    # the Keranen model has small velocity inversions, which CRH models cannot represent
    out = run(tmp, "prague", tmp / "prague_arrivals.csv", tmp / "prague_stations.csv", tmp / "prague_model.txt",
              {"lvz_policy": "clip"})
    rr = json.loads((out / "run_result.json").read_text())
    e = pd.read_csv(out / "events.csv").set_index("event_id").loc[ref.index]
    dh = np.hypot((e.latitude - ref.latitude) * 111.195, (e.longitude - ref.longitude) * 111.195 *
                  np.cos(np.radians(ref.latitude)))
    dz = e.depth_km - ref.depth_km
    res = {"events": n_events, "located": int((e.status == "LOCATED").sum()), "lvz_clipped": rr["lvz_clipped"],
           "median_epi_vs_nll_km": round(float(dh.median()), 3), "p90_epi_vs_nll_km": round(float(dh.quantile(0.9)), 3),
           "median_abs_depth_vs_nll_km": round(float(dz.abs().median()), 3),
           "median_rms_s": round(float(e.rms_s.median()), 3)}
    assert res["located"] == n_events and res["median_epi_vs_nll_km"] < 0.5 and res["median_abs_depth_vs_nll_km"] < 1.0, res
    return res


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="hypoinverse-validation-") as tmp:
        tmp = Path(tmp)
        testone = check_testone(tmp)
        synthetic = check_synthetic(tmp)
        prague = check_prague(tmp)
    print(json.dumps({"status": "pass", "tool": "HypoInverse", "testone": testone, "synthetic": synthetic,
                      "prague": prague}, indent=2))


if __name__ == "__main__":
    main()
