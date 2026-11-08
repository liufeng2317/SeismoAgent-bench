#!/usr/bin/env python3
"""Does a regional model, or a minimum 1-D model from VELEST, remove the origin-time and depth biases of a run?

For one development run (its own picks and catalog, the development window), following the expert procedure:

1. Starting models: the regional models of the library covering the stations (``--library``), the generic CRUST1.0
   column under the stations, and the first regional model scaled by 0.93 and 1.07.
2. VELEST (seismotools/velest, P and S, best-constrained events) from each starting model: final model and station
   corrections. Convergence: the spread of the final models' velocities at each depth.
3. Relocation of the whole catalog with NonLinLoc EDT_OT_WT (the replay helper) for: the first regional model alone
   (no station corrections) and each VELEST result (its model and station corrections).
4. Each against the primary location reference over the window: median origin-time offset, depth offset,
   common horizontal shift and scatter (matched pairs), next to the run's own catalog.

The references are read only to score. Usage:
    velest_offline.py <case> <run_id> [--library data/agent_resource/velocity_models] [--workers 12]
Writes outputs/velest_offline/<case>_<run_id>/summary.json.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "workflows/development/replay"))
sys.path.insert(0, str(ROOT / "seismo_checker/source"))
import horizontal_shift as H  # noqa: E402
from catalog_checker.io import read_stations  # noqa: E402
from catalog_checker.velocity import regional_models  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.case import load_case  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.matching import correspond  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.tables import Population, read_candidate_catalog  # noqa: E402

OUT = HERE / "outputs/velest_offline"
VELEST = ROOT / "seismotools/velest/interface/run.py"


def library_models(lib: Path, lat: float, lon: float) -> list[dict]:
    hits = []
    for p in sorted((lib / "models").glob("*.json")):
        m = json.loads(p.read_text()); r = m["region"]
        if r["lat_min"] <= lat <= r["lat_max"] and r["lon_min"] <= lon <= r["lon_max"]:
            hits.append(m)
    return sorted(hits, key=lambda m: (m["region"]["lat_max"] - m["region"]["lat_min"]) * (m["region"]["lon_max"] - m["region"]["lon_min"]))


def datum_km(m: dict) -> float:
    """Depth reference of a library model in km above sea level (0 when it is sea level or unknown)."""
    d = m["depth_datum"].lower()
    for token in d.replace("(", " ").split():
        try:
            v = float(token)
        except ValueError:
            continue
        if "above sea level" in d and v < 10:
            return v
    return 0.0


def rows_bsl(m: dict) -> list[tuple[float, float, float]]:
    ref = datum_km(m)
    out = []
    for L in m["layers"]:
        vp = L["vp_km_s"]; ratio = L.get("vp_vs") or m.get("vp_vs") or 1.73
        vs = L.get("vs_km_s") or vp / ratio
        out.append((L["top_km"] - ref, vp, vs))
    dedup = []
    for r in out:  # node models repeat a depth to mark a jump: keep the lower value as the layer
        if dedup and abs(dedup[-1][0] - r[0]) < 1e-6:
            dedup[-1] = r
        else:
            dedup.append(r)
    return dedup


def score(events: pd.DataFrame, c) -> dict:
    ref = c.refs[c.primary["location"]]
    pop = Population(key="c", events=events.reset_index(drop=True), depth_known=True)
    pr = correspond(pop, ref)["pairs"]
    if len(pr) < 10:
        return {"pairs": int(len(pr))}
    a, b = pop.events.iloc[np.asarray(pr.a)], ref.events.iloc[np.asarray(pr.b)]
    dt = a.time.to_numpy(float) - b.time.to_numpy(float)
    dz = a.depth_km.to_numpy(float) - b.depth_km.to_numpy(float)
    lat0 = np.radians(float(b.latitude.median()))
    de = 111.195 * (a.longitude.to_numpy() - b.longitude.to_numpy()) * np.cos(lat0)
    dn = 111.195 * (a.latitude.to_numpy() - b.latitude.to_numpy())
    se, sn = np.median(de), np.median(dn)
    return {"pairs": int(len(pr)), "dt_median_s": round(float(np.median(dt)), 3), "dz_median_km": round(float(np.nanmedian(dz)), 2),
            "shift_km": round(float(np.hypot(se, sn)), 2), "scatter_median_km": round(float(np.median(np.hypot(de - se, dn - sn))), 2)}


def from_loc(loc: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"event_id": loc.event_id, "time": loc.t, "latitude": loc.latitude, "longitude": loc.longitude,
                         "depth_km": loc.depth_bsl, "magnitude": np.nan})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case"); ap.add_argument("run_id")
    ap.add_argument("--variant", default="dev_knowledge")
    ap.add_argument("--library", type=Path, default=ROOT / "data/agent_resource/velocity_models")
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    task = ROOT / "workflows/tasks" / a.case
    c = load_case(task, "development" if a.variant.startswith("dev_") else "full")
    run = task / "runs" / a.variant / "claude/glm-5.3" / a.run_id / "work"
    base = run if (run / "catalog.csv").is_file() else run / "work"
    out = OUT / f"{a.case}_{a.run_id}"; out.mkdir(parents=True, exist_ok=True)
    st = read_stations(run / "input/waveforms/stations")[["station_id", "latitude", "longitude", "elevation_m"]].drop_duplicates("station_id")
    st.to_csv(out / "stations.csv", index=False)
    pk = pd.read_csv(base / "picks.csv", dtype={"event_id": str})
    pk = pk[pk.event_id.notna() & (pk.event_id != "") & (pk.get("status", "") != "rejected") & pk.phase.isin(["P", "S"])]
    pk = pk[pk.station_id.isin(st.station_id)][["event_id", "station_id", "phase", "time_utc"]].drop_duplicates(["event_id", "station_id", "phase"])
    pk.insert(1, "pick_id", [f"p{i}" for i in range(len(pk))])
    pk.to_csv(out / "arrivals.csv", index=False)
    cat = pd.read_csv(base / "catalog.csv", dtype={"event_id": str})
    if "status" in cat:
        cat = cat[cat.status != "rejected"]
    cat = cat[cat.event_id.isin(pk.event_id)].dropna(subset=["latitude", "longitude", "depth_km"])
    cat[["event_id", "origin_time_utc", "latitude", "longitude", "depth_km"]].to_csv(out / "events.csv", index=False)
    clat, clon = float(st.latitude.median()), float(st.longitude.median())
    res = {"case": a.case, "run": a.run_id, "events": int(len(cat)), "picks": int(len(pk))}
    own, _ = read_candidate_catalog(base / "catalog.csv")
    res["agent_catalog"] = score(own, c)
    lib = library_models(a.library, clat, clon)
    res["library_models"] = [m["id"] for m in lib]
    starts = {m["id"]: rows_bsl(m) for m in lib}
    crust = regional_models(np.r_[st.latitude, cat.latitude.median()], np.r_[st.longitude, cat.longitude.median()])["crust1"]["rows"]
    starts["crust1"] = [(float(z), float(vp), float(vs)) for z, vp, vs in crust]
    if lib:
        first = rows_bsl(lib[0])
        for f in (0.93, 1.07):
            starts[f"{lib[0]['id']}_x{f}"] = [(z, vp * f, vs * f) for z, vp, vs in first]
    ref_elev = float(st.elevation_m.mean()) / 1000.0
    region = {"latitude": c.config["mask"]["latitude"], "longitude": c.config["mask"]["longitude"]}
    res["relocations"] = {}
    if lib:  # the regional model alone
        loc = H.locate(pk, st, rows_bsl(lib[0]), ref_elev, region, out / "nll_regional", a.workers)
        res["relocations"][f"{lib[0]['id']} (no VELEST, no station corrections)"] = score(from_loc(loc), c)
    finals = {}
    for name, rows in starts.items():
        d = out / f"velest_{name}"
        (out / f"start_{name}.txt").write_text("".join(f"{z:.3f} {vp:.3f} {vs:.3f}\n" for z, vp, vs in rows))
        p = subprocess.run([sys.executable, "-I", str(VELEST), "--arrivals", str(out / "arrivals.csv"), "--events", str(out / "events.csv"),
                            "--stations", str(out / "stations.csv"), "--model", str(out / f"start_{name}.txt"), "--output-dir", str(d),
                            "--use-s", "--max-events", "500"], capture_output=True, text=True)
        if p.returncode or not (d / "model_final.txt").is_file():
            res.setdefault("velest_failed", {})[name] = (p.stdout + p.stderr)[-400:]
            continue
        summ = json.loads((d / "summary.json").read_text())
        model = np.loadtxt(d / "model_final.txt", ndmin=2)
        finals[name] = model
        corr = pd.read_csv(d / "station_corrections.csv")
        delays = pd.concat([corr.rename(columns={"p_correction_s": "delay_s"}).assign(phase="P")[["station_id", "phase", "delay_s"]],
                            corr.rename(columns={"s_correction_s": "delay_s"}).assign(phase="S")[["station_id", "phase", "delay_s"]]])
        delays.to_csv(d / "delays.csv", index=False)
        rows = [tuple(map(float, r)) for r in model]
        loc = H.locate(pk, st, rows, ref_elev, region, out / f"nll_velest_{name}", a.workers, delays=d / "delays.csv")
        res["relocations"][f"VELEST from {name}"] = {**score(from_loc(loc), c), "velest_events": summ["events_selected"],
                                                     "rms_first_last_s": [summ["rms_by_iteration_s"][0], summ["rms_by_iteration_s"][-1]] if summ["rms_by_iteration_s"] else None}
    if len(finals) >= 2:  # convergence: spread of the final models' Vp at fixed depths
        zs = np.arange(0, 31, 5.0)
        vals = np.array([[m[np.searchsorted(m[:, 0], z, side="right") - 1, 1] for z in zs] for m in finals.values()])
        res["convergence_vp_range_km_s"] = {f"{z:.0f} km": round(float(np.ptp(vals[:, i])), 2) for i, z in enumerate(zs)}
    (out / "summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
