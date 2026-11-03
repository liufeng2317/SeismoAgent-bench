#!/usr/bin/env python3
"""Cross-correlation relocation of a human-in-loop final catalog (all six cases; generalises Ridgecrest stage 62).

Most events of the human-in-loop finals are Match&Locate detections placed on their template's search grid
(0.25 km horizontal, 0.5 km depth) and never relocated, and some finals keep unrelocated NonLinLoc cells; the
catalogs look gridded (docs/research/progress/checker_validation and 02_Paper_Outline §4.1). This relocates
every event with waveform cross-correlation differential times:

  inputs    events of the final (depth below the model datum); arrivals: the event's own located picks for picked
            events, the template's picks shifted by the origin difference for Match&Locate events (they position
            the cross-correlation windows only); stations; waveform links
  ccdt      seismotools/cross_correlation -> dt.cc (catalog differential times from template-derived arrivals
            are never used: they collapse detections onto their template, Ridgecrest stage 62)
  growclust seismotools/growclust with the case's expert model, depths from the model datum (stations sit at
            depth 0 in GrowClust), ngoodmin 4 (the tool's validation)
  evaluate  agreement with the references before and after (matched pairs), local thickness, share of events
            on a coordinate shared with another event
  export    a new round: accepted relocations replace the positions (location_source ``<source>_cc``); a relocation
            is accepted if it moved < 3 km horizontally, its origin changed < 1 s and its depth lies in the model;
            Match&Locate events left on the grid get location_precision_h_km / _z_km of half the grid step

Usage: cc_relocate.py CASE --step all|inputs|ccdt|growclust|evaluate|export [--workers 32]
Case settings: cases/<case>.yaml (paths relative to workflows/tasks/<case>/).
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PY = "/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python"
CCDT = ROOT / "seismotools/cross_correlation/interface/run.py"
GROWCLUST = ROOT / "seismotools/growclust/interface/run.py"
sys.path.insert(0, str(ROOT))
# one thread per worker process: NumPy/FFT threads inside each ccdt worker otherwise oversubscribe the cores
SINGLE_THREAD = {k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}


def _env() -> dict:
    import os
    return {**os.environ, **SINGLE_THREAD}


def ts(s):
    return pd.to_datetime(s, utc=True, format="ISO8601")


def load(case: str) -> tuple[dict, Path, Path]:
    cfg = yaml.safe_load((HERE / "cases" / f"{case}.yaml").read_text())
    task = ROOT / "workflows/tasks" / case
    out = task / "expert/export" / cfg["new_round"] / "68_cc_relocation"
    out.mkdir(parents=True, exist_ok=True)
    return cfg, task, out


def model_rows(cfg: dict) -> list[tuple[float, float, float]]:
    reg = json.loads((ROOT / cfg["model"]["registry"]).read_text())["models"][cfg["model"]["key"]]
    return [(r["top_of_layer_km"] + cfg["model"].get("top_offset_km", 0.0), r["vp_km_s"], r["vs_km_s"]) for r in reg["rows"]]


def step_inputs(cfg: dict, task: Path, out: Path) -> dict:
    f = pd.read_csv(task / cfg["final"], low_memory=False)
    f["t"] = ts(f.origin_time_utc)
    datum = cfg["datum_km"]
    ev = pd.DataFrame({"event_id": f.event_id, "origin_time_utc": f.t.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                       "latitude": f.latitude, "longitude": f.longitude, "depth_km": f.depth_bsl_km + datum,
                       "magnitude": f.magnitude, "location_source": f.location_source,
                       "template_id": f.get("ml_template_id")})
    ev = ev.dropna(subset=["latitude", "longitude", "depth_km"]).reset_index(drop=True)
    ev.to_csv(out / "events.csv", index=False)
    origin = dict(zip(ev.event_id, ts(ev.origin_time_utc)))
    # own picks of picked events: located picks (|residual| <= 0.5 s) joined to the picker's times
    lp = pd.read_csv(task / cfg["located_picks"])
    lp = lp[lp.residual_s.abs() <= 0.5]
    pk = pd.read_csv(task / cfg["picker_picks"], usecols=["pick_id", "station_id", "time_utc"])
    own = lp.merge(pk, on="pick_id")[["event_id", "station_id", "phase", "time_utc"]]
    own = own[own.event_id.isin(ev.event_id[~ev.location_source.eq("ml")])].assign(source="pick")
    # Match&Locate events: the template's picks shifted by (detection origin - template origin)
    tp = pd.read_csv(task / cfg["template_picks"])
    tm = pd.read_csv(task / cfg["templates"])
    t_origin = dict(zip(tm.event_id, ts(tm.origin_time_utc)))
    # a template kept in the final can have moved with the catalog's frame (Maple stage 64), and its detections
    # moved with it: the detection-template origin difference is consistent only in the final's own frame
    t_origin.update({e: origin[e] for e in t_origin if e in origin and not ev.location_source[ev.event_id.eq(e)].eq("ml").all()})
    ml = ev[ev.location_source.eq("ml")]
    rows = ml[["event_id", "template_id"]].merge(tp, left_on="template_id", right_on="event_id", suffixes=("", "_tmpl"))
    rows = rows[rows.template_id.isin(t_origin)]
    # physical arrivals = template pick + (detection origin - template origin), both origins in the same frame
    shift = [origin[e] - t_origin[k] for e, k in zip(rows.event_id, rows.template_id)]
    derived = pd.DataFrame({"event_id": rows.event_id, "station_id": rows.station_id, "phase": rows.phase,
                            "time_utc": (ts(rows.time_utc) + pd.Series(shift, index=rows.index)).dt.strftime(
                                "%Y-%m-%dT%H:%M:%S.%fZ"), "source": "template"})
    arr = pd.concat([own, derived], ignore_index=True).drop_duplicates(["event_id", "station_id", "phase"])
    arr.to_csv(out / "arrivals.csv", index=False)
    st = pd.read_csv(task / cfg["stations"])[["station_id", "latitude", "longitude", "elevation_m"]].drop_duplicates("station_id")
    st = st[st.station_id.isin(arr.station_id)]
    st.to_csv(out / "stations.csv", index=False)
    wav = out / "waveforms"
    if wav.exists():
        shutil.rmtree(wav)
    wav.mkdir()
    days = sorted({t.strftime("%Y%m%d") for t in ts(ev.origin_time_utc)})
    want = set(days) | {(pd.Timestamp(d) + pd.Timedelta(days=k)).strftime("%Y%m%d") for d in days for k in (-1, 1)}
    n = 0
    for sta in st.station_id:
        for p in sorted((ROOT / cfg["waveforms"] / sta).glob(f"{sta}.*.mseed")):
            if p.name.split("__")[1][:8] in want:
                (wav / p.name).symlink_to(p)
                n += 1
    res = {"events": int(len(ev)), "by_source": ev.location_source.value_counts().to_dict(),
           "arrivals_own": int(len(own)), "arrivals_template": int(len(derived)),
           "ml_without_arrivals": int(len(set(ml.event_id) - set(derived.event_id))),
           "events_without_arrivals": int(len(set(ev.event_id) - set(arr.event_id))),
           "stations": int(len(st)), "waveform_files": n}
    (out / "inputs.json").write_text(json.dumps(res, indent=1))
    return res


def step_ccdt(cfg: dict, out: Path, workers: int) -> dict:
    c = cfg.get("ccdt", {})
    conf = {"pairs": {"max_distance_km": c.get("max_distance_km", 5.0), "max_neighbors": c.get("max_neighbors", 80)},
            "accept": {"min_cc": c.get("min_cc", 0.6)}, "weight": "cc", "write_rejected": False}
    (out / "ccdt_config.json").write_text(json.dumps(conf, indent=2))
    with (out / "ccdt.log").open("w") as log:
        subprocess.run([PY, "-I", str(CCDT), "--events", str(out / "events.csv"), "--arrivals", str(out / "arrivals.csv"),
                        "--waveforms", str(out / "waveforms"), "--output-dir", str(out / "ccdt"), "--config",
                        str(out / "ccdt_config.json"), "--workers", str(workers), "--overwrite"],
                       stdout=log, stderr=subprocess.STDOUT, check=True, env=_env())
    return json.loads((out / "ccdt/run_result.json").read_text())


def step_growclust(cfg: dict, out: Path, ngoodmin: int | None = None, name: str = "growclust") -> dict:
    rows = model_rows(cfg)
    (out / "model.txt").write_text("".join(f"{z:.3f} {vp:.3f} {vs:.3f}\n" for z, vp, vs in rows))
    ev = pd.read_csv(out / "events.csv")
    st = pd.read_csv(out / "stations.csv")
    dist = 111.195 * math.hypot(st.latitude.max() - st.latitude.min(),
                                (st.longitude.max() - st.longitude.min()) * math.cos(math.radians(st.latitude.mean())))
    g = cfg.get("growclust", {})
    conf = {"velocity_layering": cfg["model"].get("layering", "step"),
            "table": {"depth_min_km": 0.0, "depth_max_km": float(math.ceil(ev.depth_km.max() + 5)), "depth_step_km": 0.5,
                      "distance_min_km": 0.0, "distance_max_km": float(math.ceil(dist + 20)), "distance_step_km": 1.0},
            "rmin": g.get("rmin", 0.6), "delmax_km": g.get("delmax_km", 80.0), "rmsmax_s": g.get("rmsmax_s", 0.2),
            "ngoodmin": g.get("ngoodmin", 4) if ngoodmin is None else ngoodmin, "nboot": 0}
    (out / f"{name}_config.json").write_text(json.dumps(conf, indent=2))
    with (out / f"{name}.log").open("w") as log:
        subprocess.run([PY, "-I", str(GROWCLUST), "--events", str(out / "events.csv"), "--stations", str(out / "stations.csv"),
                        "--dtcc", str(out / "ccdt"), "--velocity-model", str(out / "model.txt"), "--config",
                        str(out / f"{name}_config.json"), "--output-dir", str(out / name), "--overwrite"],
                       stdout=log, stderr=subprocess.STDOUT, check=True, env=_env())
    return json.loads((out / name / "run_result.json").read_text())


def relocation(cfg: dict, out: Path, keep_frame: bool | None = None) -> pd.DataFrame:
    """Events with the accepted GrowClust position (la, lo, de, t_new) or the old one, and a status.

    keep_frame: remove the median displacement of the relocated events (GrowClust, like hypoDD, ignores station
    elevations and can move the whole catalog: Kilauea r6), keeping only the relative improvement; default from
    the case config."""
    ev = pd.read_csv(out / "events.csv")
    r = pd.read_csv(out / cfg.get("growclust_run", "growclust") / "relocated.csv")
    m = ev.merge(r[["event_id", "origin_time_utc", "latitude", "longitude", "depth_km", "relocated", "n_pairs"]],
                 on="event_id", how="left", suffixes=("", "_new"))
    dh = np.hypot((m.latitude_new - m.latitude) * 111.195,
                  (m.longitude_new - m.longitude) * 111.195 * np.cos(np.radians(m.latitude)))
    dto = (ts(m.origin_time_utc_new) - ts(m.origin_time_utc)).dt.total_seconds().abs()
    top = model_rows(cfg)[-1][0]
    m["status"] = np.select(
        [m.relocated.isna(), ~m.relocated.astype(bool), dh >= 3, dto >= 1, ~m.depth_km_new.between(0, top)],
        ["not_in_output", "not_linked", "diverged_shift", "diverged_origin", "diverged_depth"], "relocated")
    ok = m.status.eq("relocated")
    if keep_frame is None:
        keep_frame = bool(cfg.get("keep_frame", False))
    if keep_frame and ok.any():
        shift = {c: float(np.median((m[c + "_new"] - m[c])[ok])) for c in ("latitude", "longitude", "depth_km")}
        dt0 = float(np.median((ts(m.origin_time_utc_new) - ts(m.origin_time_utc)).dt.total_seconds()[ok]))
        for c, v in shift.items():
            m.loc[ok, c + "_new"] = m.loc[ok, c + "_new"] - v
        m.loc[ok, "origin_time_utc_new"] = (ts(m.loc[ok, "origin_time_utc_new"]) - pd.Timedelta(seconds=dt0)).dt.strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ")
    m["la"] = np.where(ok, m.latitude_new, m.latitude)
    m["lo"] = np.where(ok, m.longitude_new, m.longitude)
    m["de"] = np.where(ok, m.depth_km_new, m.depth_km)
    m["t_new"] = np.where(ok, m.origin_time_utc_new, m.origin_time_utc)
    return m


def thickness(x, y, z, k=20, n=3000, seed=0):
    """Median local thickness (km): minor-axis SD, in map view, of each sampled event's k nearest neighbours (3-D)."""
    from scipy.spatial import cKDTree
    X = np.c_[x, y, z]
    X = X[np.isfinite(X).all(axis=1)]
    if len(X) <= k:
        return None
    X = X + np.random.default_rng(1).normal(0, 1e-4, X.shape)  # break exact ties of stacked positions
    tree = cKDTree(X)
    vals = []
    for i in np.random.default_rng(seed).choice(len(X), min(n, len(X)), replace=False):
        _, j = tree.query(X[i], k=k + 1)
        Y = X[j, :2] - X[j, :2].mean(axis=0)
        vals.append(math.sqrt(max(np.linalg.eigvalsh(np.cov(Y.T))[0], 0.0)))
    return round(float(np.median(vals)), 3)


def step_evaluate(cfg: dict, task: Path, out: Path) -> dict:
    from SeismoAgentBench.scoring.catalog_metrics.case import load_case
    from SeismoAgentBench.scoring.catalog_metrics.matching import correspond
    from SeismoAgentBench.scoring.catalog_metrics.tables import Population
    case = load_case(task)
    res_all = {}
    for keep in (False, True):
        res_all["frame_kept" if keep else "as_relocated"] = _evaluate(cfg, case, relocation(cfg, out, keep))
    (out / f"evaluation_{cfg.get('growclust_run', 'growclust')}.json").write_text(json.dumps(res_all, indent=1, default=str))
    return res_all


def _evaluate(cfg: dict, case, m: pd.DataFrame) -> dict:
    from SeismoAgentBench.scoring.catalog_metrics.matching import correspond
    from SeismoAgentBench.scoring.catalog_metrics.tables import Population
    lat0, lon0 = case.center[1], case.center[0]
    k = 111.195 * math.cos(math.radians(lat0))
    res = {"events": int(len(m)), "status": m.status.value_counts().to_dict(),
           "relocated_by_source": m[m.status.eq("relocated")].location_source.value_counts().to_dict()}

    def pop(lat, lon, dep, t):
        e = pd.DataFrame({"event_id": m.event_id, "time": ts(pd.Series(t)).astype("int64").to_numpy() / 1e9,
                          "latitude": lat, "longitude": lon, "depth_km": np.asarray(dep) - cfg["datum_km"],
                          "magnitude": m.magnitude})
        return Population(key="c", events=e, depth_known=True)

    before = pop(m.latitude.to_numpy(), m.longitude.to_numpy(), m.depth_km.to_numpy(), m.origin_time_utc)
    after = pop(m.la.to_numpy(), m.lo.to_numpy(), m.de.to_numpy(), m.t_new)
    agree = {}
    for key, ref in case.refs.items():
        if not ref.events.latitude.notna().any():
            continue
        row = {}
        for name, p in (("before", before), ("after", after)):
            pr = correspond(p, ref)["pairs"]
            a, b = p.events.iloc[pr.a], ref.events.iloc[pr.b]
            epi = np.hypot((a.latitude.to_numpy() - b.latitude.to_numpy()) * 111.195,
                           (a.longitude.to_numpy() - b.longitude.to_numpy()) * 111.195 * math.cos(math.radians(lat0)))
            dz = a.depth_km.to_numpy() - b.depth_km.to_numpy()
            row[name] = {"pairs": int(len(pr)), "epi_median_km": round(float(np.median(epi)), 3),
                         "dz_median_km": round(float(np.nanmedian(dz)), 3) if np.isfinite(dz).any() else None}
        agree[key] = row
    res["agreement_with_references"] = agree
    th = {}
    for name, (la, lo, de) in {"before": (m.latitude, m.longitude, m.depth_km), "after": (m.la, m.lo, m.de)}.items():
        th[name] = thickness((lo - lon0) * k, (la - lat0) * 111.195, de)
        key = la.round(5).astype(str) + "," + lo.round(5).astype(str)
        th[f"{name}_share_on_shared_coordinate"] = round(float(key.duplicated(keep=False).mean()), 3)
    for key, ref in case.refs.items():
        e = ref.events.dropna(subset=["latitude", "depth_km"])
        if len(e) > 50:
            th[f"reference_{key}"] = thickness((e.longitude - lon0) * k, (e.latitude - lat0) * 111.195, e.depth_km)
    res["local_thickness_km"] = th
    return res


def step_export(cfg: dict, task: Path, out: Path) -> dict:
    f = pd.read_csv(task / cfg["final"], low_memory=False)
    m = relocation(cfg, out).set_index("event_id")
    ok = m.index[m.status.eq("relocated")]
    sel = f.event_id.isin(ok)
    idx = f.loc[sel, "event_id"]
    f.loc[sel, "latitude"] = m.loc[idx, "la"].to_numpy()
    f.loc[sel, "longitude"] = m.loc[idx, "lo"].to_numpy()
    f.loc[sel, "depth_bsl_km"] = (m.loc[idx, "de"] - cfg["datum_km"]).round(4).to_numpy()
    f.loc[sel, "origin_time_utc"] = ts(m.loc[idx, "t_new"]).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ").to_numpy()
    f.loc[sel, "location_source"] = f.loc[sel, "location_source"].astype(str) + "_cc"
    grid = f.location_source.eq("ml")
    f["location_precision_h_km"] = np.where(grid, cfg["grid"]["step_km"] / 2, np.nan)
    f["location_precision_z_km"] = np.where(grid, cfg["grid"]["step_depth_km"] / 2, np.nan)
    f["relocation_status"] = f.event_id.map(m.status).fillna("not_in_inputs")
    dest = task / "expert/export" / cfg["new_round"] / "60_catalog"
    dest.mkdir(parents=True, exist_ok=True)
    f.to_csv(dest / "catalog_events.csv", index=False)
    res = {"events": int(len(f)), "relocated": int(sel.sum()), "left_on_grid": int(grid.sum()),
           "catalog": str((dest / "catalog_events.csv").relative_to(task))}
    (out / "export.json").write_text(json.dumps(res, indent=1))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--step", default="all", choices=["all", "inputs", "ccdt", "growclust", "evaluate", "export"])
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--ngoodmin", type=int, default=None, help="GrowClust ngoodmin (default: case config, else 4)")
    ap.add_argument("--run-name", default="growclust", help="GrowClust output folder evaluated and exported")
    a = ap.parse_args()
    cfg, task, out = load(a.case)
    cfg["growclust_run"] = a.run_name
    steps = ["inputs", "ccdt", "growclust", "evaluate", "export"] if a.step == "all" else [a.step]
    for s in steps:
        r = {"inputs": lambda: step_inputs(cfg, task, out), "ccdt": lambda: step_ccdt(cfg, out, a.workers),
             "growclust": lambda: step_growclust(cfg, out, a.ngoodmin, a.run_name), "evaluate": lambda: step_evaluate(cfg, task, out),
             "export": lambda: step_export(cfg, task, out)}[s]()
        print(s, json.dumps(r, default=str)[:1500], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
