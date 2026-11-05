#!/usr/bin/env python3
"""Cross-correlation relocation of a human-in-loop final catalog (all six cases; generalises Ridgecrest stage 62).

Most events of the human-in-loop finals are Match&Locate detections placed on their template's search grid
(0.25 km horizontal, 0.5 km depth) and never relocated, and some finals keep unrelocated NonLinLoc cells; the
catalogs look gridded (docs/research/progress/records and progress/results_summary.md §1.1). This relocates
every event with waveform cross-correlation differential times:

  inputs    events of the final (depth below the model datum); arrivals: the event's own located picks for picked
            events, the template's picks shifted by the origin difference for Match&Locate events (they position
            the cross-correlation windows only); stations; waveform links
  ccdt      seismotools/cross_correlation -> dt.cc (catalog differential times from template-derived arrivals
            are never used: they collapse detections onto their template, Ridgecrest stage 62)
  hypodd    alternative to growclust (Ridgecrest stage 62): hypoDD 1.3, dt.cc plus dt.ct from the picked events' own
            picks, control cc3_d1; ``--step hypodd --run-name hypodd``, then evaluate/export with the same run name
  growclust seismotools/growclust with the case's expert model, depths from the model datum (stations sit at
            depth 0 in GrowClust), ngoodmin 4 (the tool's validation)
  evaluate  agreement with the references before and after (matched pairs), local thickness, share of events
            on a coordinate shared with another event
  export    a new round: accepted relocations replace the positions (location_source ``<source>_cc``); a relocation
            is accepted if it moved < 3 km horizontally, its origin changed < 1 s and its depth lies in the model;
            Match&Locate events left on the grid get location_precision_h_km / _z_km of half the grid step;
            ``--label-only`` keeps every position and adds only the precision (relocation not adopted)

Usage: cc_relocate.py CASE --step all|inputs|ccdt|growclust|hypodd|evaluate|export [--workers 32]
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


def load(case: str, tag: str = "") -> tuple[dict, Path, Path]:
    cfg = yaml.safe_load((HERE / "cases" / f"{case}.yaml").read_text())
    task = ROOT / "workflows/tasks" / case
    out = task / "expert/export" / cfg["new_round"] / ("68_cc_relocation" + (f"_{tag}" if tag else ""))
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
    ev = pd.read_csv(out / "events.csv")
    depth_max = float(math.ceil(ev.depth_km.max() + 15))  # events move during clustering: leave room below
    rows = model_rows(cfg)
    deep = [r for r in rows if r[0] > depth_max]
    rows = [r for r in rows if r[0] <= depth_max] + deep[:1]  # GrowClust interpolates at most 1000 model points
    (out / "model.txt").write_text("".join(f"{z:.3f} {vp:.3f} {vs:.3f}\n" for z, vp, vs in rows))
    st = pd.read_csv(out / "stations.csv")
    # largest event-station distance (events can lie outside the network, Kilauea's lower rift)
    k = math.cos(math.radians(st.latitude.mean()))
    dist = 111.195 * float(np.max(np.hypot(ev.latitude.to_numpy()[:, None] - st.latitude.to_numpy()[None],
                                           (ev.longitude.to_numpy()[:, None] - st.longitude.to_numpy()[None]) * k)))
    step = float(max(1, math.ceil((dist + 20) / 480)))  # GrowClust tables hold at most 501 distance points
    g = cfg.get("growclust", {})
    conf = {"velocity_layering": cfg["model"].get("layering", "step"),
            "table": {"depth_min_km": 0.0, "depth_max_km": depth_max, "depth_step_km": 0.5,
                      "distance_min_km": 0.0, "distance_max_km": float(math.ceil((dist + 20) / step) * step), "distance_step_km": step},
            "rmin": g.get("rmin", 0.6), "delmax_km": g.get("delmax_km", 80.0), "rmsmax_s": g.get("rmsmax_s", 0.2),
            "ngoodmin": g.get("ngoodmin", 4) if ngoodmin is None else ngoodmin, "nboot": 0}
    (out / f"{name}_config.json").write_text(json.dumps(conf, indent=2))
    with (out / f"{name}.log").open("w") as log:
        subprocess.run([PY, "-I", str(GROWCLUST), "--events", str(out / "events.csv"), "--stations", str(out / "stations.csv"),
                        "--dtcc", str(out / "ccdt"), "--velocity-model", str(out / "model.txt"), "--config",
                        str(out / f"{name}_config.json"), "--output-dir", str(out / name), "--overwrite"],
                       stdout=log, stderr=subprocess.STDOUT, check=True, env=_env())
    return json.loads((out / name / "run_result.json").read_text())


HYPODD_SRC = ROOT / "seismotools/hypodd/source"
# Ridgecrest stage-14 control cc3_d1: CT+CC, LSQR, two sets (4 iterations damping 80, 8 iterations damping 40), CC
# weights 3 (P) / 1.5 (S), catalog 1 / 0.5, no residual trimming; columns NITER WTCCP WTCCS WRCC WDCC WTCTP WTCTS WRCT WDCT DAMP
HYPODD_SETS = ["4 3 1.5 -9 -9 1 .5 -9 -9 80", "8 3 1.5 -9 -9 1 .5 -9 -9 40"]
RELOC_COLS = ["cusp", "lat", "lon", "depth", "x", "y", "z", "ex", "ey", "ez", "yr", "mo", "dy", "hr", "mi", "sc",
              "mag", "nccp", "nccs", "nctp", "ncts", "rcc", "rct", "cid"]


def step_hypodd(cfg: dict, out: Path, name: str = "hypodd") -> dict:
    """hypoDD 1.3 (Ridgecrest stage 62): dt.cc from ccdt, dt.ct from the picked events' own picks only (template-
    derived arrivals would collapse detections onto their template), over the ccdt neighbour pairs; a single
    Vp/Vs ratio (hypoDD 1.3), the vertical travel-time ratio of the model down to the deepest event."""
    run = out / name
    run.mkdir(exist_ok=True)
    ev = pd.read_csv(out / "events.csv")
    ev["t"] = ts(ev.origin_time_utc)
    ev["tr"] = ev.t.dt.round("10ms")                  # event.dat keeps HHMMSSss
    idt = pd.read_csv(out / "ccdt/event_ids.csv")
    cusp = {e: int(c) for e, c in zip(idt.event_id, idt.cusp_id)}
    ev["cusp"] = ev.event_id.map(cusp)
    with (run / "event.dat").open("w") as f:
        for r in ev.itertuples():
            f.write(f"{r.tr.strftime('%Y%m%d')} {r.tr.strftime('%H%M%S')}{int(round(r.tr.microsecond / 1e4)):02d} "
                    f"{r.latitude:.7f} {r.longitude:.7f} {r.depth_km:.5f} "
                    f"{0.0 if pd.isna(r.magnitude) else r.magnitude:.2f} 0 0 0 {r.cusp}\n")
    st = pd.read_csv(out / "stations.csv")
    st["code"] = st.station_id.str.split(".").str[-1]
    assert st.code.is_unique, "hypoDD station codes must be unique"
    with (run / "station.dat").open("w") as f:
        for r in st.itertuples():
            f.write(f"{r.code} {r.latitude:.7f} {r.longitude:.7f}\n")
    # dt.cc re-referenced to the rounded origins: tt_r = tt + (o - o_r)
    corr = dict(zip(ev.event_id, (ev.t - ev.tr).dt.total_seconds()))
    inv = {v: k for k, v in cusp.items()}
    n_cc = 0
    with (out / "ccdt/dt.cc").open() as src, (run / "dt.cc").open("w") as f:
        a = b = None
        for line in src:
            if line.startswith("#"):
                _, i1, i2, _ = line.split()
                a, b = inv[int(i1)], inv[int(i2)]
                f.write(line)
            else:
                sta, dt, w, ph = line.split()
                f.write(f"{sta:<7s} {float(dt) + corr[a] - corr[b]:10.5f} {w} {ph}\n")
                n_cc += 1
    arr = pd.read_csv(out / "arrivals.csv")
    arr = arr[arr.source.eq("pick")]
    o_r = dict(zip(ev.event_id, ev.tr))
    arr["tt"] = [(t - o_r[e]).total_seconds() for e, t in zip(arr.event_id, ts(arr.time_utc))]
    arr["code"] = arr.station_id.str.split(".").str[-1]
    tt = {(e, c, p): v for e, c, p, v in zip(arr.event_id, arr.code, arr.phase, arr.tt)}
    by_event: dict = {}
    for e, c, p in tt:
        by_event.setdefault(e, []).append((c, p))
    sys.path.insert(0, str(ROOT / "seismotools/cross_correlation/runtime/python"))
    from ccdt.pipeline import neighbour_pairs
    pc = json.loads((out / "ccdt_config.json").read_text())["pairs"]
    ij = neighbour_pairs(ev[["latitude", "longitude", "depth_km"]].to_numpy(), pc["max_distance_km"], pc["max_neighbors"])
    ids = ev.event_id.to_numpy()
    n_ct = 0
    with (run / "dt.ct").open("w") as f:
        for i, j in ij:
            a, b = ids[i], ids[j]
            common = [(c, p) for c, p in by_event.get(a, []) if (b, c, p) in tt]
            if not common:
                continue
            f.write(f"# {cusp[a]:9d} {cusp[b]:9d}\n")
            for c, p in common:
                f.write(f"{c:<7s} {tt[(a, c, p)]:9.4f} {tt[(b, c, p)]:9.4f} 1.00 {p}\n")
                n_ct += 1
    # native build sized to the data
    nat = out / "hypodd_native"
    for part in ("include", "src/hypoDD"):
        shutil.copytree(HYPODD_SRC / part, nat / part, dirs_exist_ok=True)
    maxeve = max(7000, len(ev) + 100)
    (nat / "include/hypoDD.inc").write_text(
        "      integer*4 MAXEVE, MAXLAY, MAXDATA, MAXSTA, MAXEVE0,\n"
        "     & MAXDATA0, MAXCL\n"
        f"      parameter(MAXEVE={maxeve}, MAXLAY=15, MAXDATA={int((n_cc + n_ct) * 1.1) + 1000},\n"
        f"     & MAXSTA={max(100, len(st) + 10)}, MAXEVE0=2, MAXDATA0=1, MAXCL={maxeve})\n")
    cwd = nat / "src/hypoDD"
    with (nat / "build.log").open("w") as log:
        subprocess.run(["make", "clean"], cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run(["make", "-j4", "FC=gfortran", "FFLAGS=-O2 -I../../include -std=legacy -fallow-argument-mismatch"],
                       cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
    # control: model layers (hypoDD 1.3 takes P velocities and one Vp/Vs ratio)
    rows = model_rows(cfg)
    zmax = float(ev.depth_km.max())
    tp = ts_ = 0.0
    for k, (z, vp, vs) in enumerate(rows):
        bot = min(rows[k + 1][0] if k + 1 < len(rows) else zmax, zmax)
        if bot > z:
            tp += (bot - z) / vp
            ts_ += (bot - z) / vs
    ratio = ts_ / tp
    assert len(rows) <= 15, "hypoDD 1.3 MAXLAY 15: resample the model"
    k = math.cos(math.radians(st.latitude.mean()))
    dist = 111.195 * float(np.max(np.hypot(ev.latitude.to_numpy()[:, None] - st.latitude.to_numpy()[None],
                                           (ev.longitude.to_numpy()[:, None] - st.longitude.to_numpy()[None]) * k)))
    ctl = ["dt.cc", "dt.ct", "event.dat", "station.dat", "hypoDD.loc", "hypoDD.reloc", "hypoDD.sta", "hypoDD.res",
           "hypoDD.src", f"3 3 {math.ceil(dist + 20)}", "0 0", f"2 2 {len(HYPODD_SETS)}", *HYPODD_SETS,
           f"{len(rows)} {ratio:.3f}", " ".join(f"{z:.2f}" for z, _, _ in rows), " ".join(f"{vp:.3f}" for _, vp, _ in rows), "0"]
    (run / "hypoDD.inp").write_text("\n".join(ctl) + "\n")
    with (run / "console.log").open("w") as log:
        subprocess.run([str(cwd / "hypoDD"), "hypoDD.inp"], cwd=run, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=12 * 3600, env=_env())
    # relocated.csv in the GrowClust layout, so relocation() / evaluate / export read either
    r = pd.read_csv(run / "hypoDD.reloc", sep=r"\s+", header=None, names=RELOC_COLS, dtype=str)
    for c in RELOC_COLS:
        r[c] = pd.to_numeric(r[c], errors="coerce")
    r["event_id"] = r.cusp.map(inv)
    t_new = pd.to_datetime(dict(year=r.yr, month=r.mo, day=r.dy, hour=r.hr, minute=r.mi), utc=True,
                           errors="coerce") + pd.to_timedelta(r.sc, unit="s")
    rel = pd.DataFrame({"event_id": r.event_id, "origin_time_utc": t_new.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        "latitude": r.lat, "longitude": r.lon, "depth_km": r.depth,
                        "relocated": r[["lat", "lon", "depth"]].notna().all(axis=1) & t_new.notna(),
                        "n_pairs": r[["nccp", "nccs", "nctp", "ncts"]].sum(axis=1)})
    rel.to_csv(run / "relocated.csv", index=False)
    res = {"events": int(len(ev)), "dt_cc_lines": n_cc, "dt_ct_lines": n_ct, "vp_vs": round(ratio, 3),
           "in_output": int(len(rel)), "relocated": int(rel.relocated.sum())}
    (run / "run_result.json").write_text(json.dumps(res, indent=1))
    return res


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
    anchors = m.location_source.isin(cfg.get("anchor_sources", []))
    if anchors.any():
        # events already relocated with picks and CC (double difference) keep their positions; the others are moved
        # into their frame by removing the anchors' median GrowClust displacement
        moved = m.status.eq("relocated") & anchors
        if moved.sum() >= 20:
            for c in ("latitude", "longitude", "depth_km"):
                m[c + "_new"] = m[c + "_new"] - float(np.median((m[c + "_new"] - m[c])[moved]))
            dt0 = float(np.median((ts(m.origin_time_utc_new) - ts(m.origin_time_utc)).dt.total_seconds()[moved]))
            new_t = ts(m.origin_time_utc_new) - pd.Timedelta(seconds=dt0)
            m["origin_time_utc_new"] = new_t.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ").where(new_t.notna(), None)
        m.loc[anchors & m.status.eq("relocated"), "status"] = "anchor_kept"
        keep_frame = False
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


def step_export(cfg: dict, task: Path, out: Path, label_only: bool = False) -> dict:
    """label_only: keep every position (the relocation was not adopted, docs/research/progress/
    analyses/2026-11-04_hil_relocation.md) and only add the grid precision of the Match&Locate events."""
    f = pd.read_csv(task / cfg["final"], low_memory=False)
    m = relocation(cfg, out).set_index("event_id")
    ok = m.index[m.status.eq("relocated")]
    sel = f.event_id.isin(ok) & (not label_only)
    idx = f.loc[sel, "event_id"]
    f.loc[sel, "latitude"] = m.loc[idx, "la"].to_numpy()
    f.loc[sel, "longitude"] = m.loc[idx, "lo"].to_numpy()
    f.loc[sel, "depth_bsl_km"] = (m.loc[idx, "de"] - cfg["datum_km"]).round(4).to_numpy()
    f.loc[sel, "origin_time_utc"] = ts(m.loc[idx, "t_new"]).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ").to_numpy()
    f.loc[sel, "location_source"] = f.loc[sel, "location_source"].astype(str) + "_cc"
    grid = f.location_source.eq("ml")
    f["location_precision_h_km"] = np.where(grid, cfg["grid"]["step_km"] / 2, np.nan)
    f["location_precision_z_km"] = np.where(grid, cfg["grid"]["step_depth_km"] / 2, np.nan)
    f["relocation_status"] = "not_applied" if label_only else f.event_id.map(m.status).fillna("not_in_inputs")
    dest = task / "expert/export" / cfg["new_round"] / "60_catalog"
    dest.mkdir(parents=True, exist_ok=True)
    f.to_csv(dest / "catalog_events.csv", index=False)
    res = {"events": int(len(f)), "label_only": label_only, "relocated": int(sel.sum()), "left_on_grid": int(grid.sum()),
           "catalog": str((dest / "catalog_events.csv").relative_to(task))}
    (out / "export.json").write_text(json.dumps(res, indent=1))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--step", default="all", choices=["all", "inputs", "ccdt", "growclust", "hypodd", "evaluate", "export"])
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--ngoodmin", type=int, default=None, help="GrowClust ngoodmin (default: case config, else 4)")
    ap.add_argument("--run-name", default="growclust", help="GrowClust or hypoDD output folder written, evaluated and exported")
    ap.add_argument("--min-cc", type=float, default=None, help="ccdt and GrowClust minimum CC (default: case config, else 0.6)")
    ap.add_argument("--label-only", action="store_true", help="export: keep the positions, add the grid precision only")
    ap.add_argument("--tag", default="", help="variant: separate working folder 68_cc_relocation_<tag>")
    a = ap.parse_args()
    cfg, task, out = load(a.case, a.tag)
    if a.min_cc is not None:
        cfg.setdefault("ccdt", {})["min_cc"] = a.min_cc
        cfg.setdefault("growclust", {})["rmin"] = a.min_cc
    cfg["growclust_run"] = a.run_name
    steps = ["inputs", "ccdt", "growclust", "evaluate", "export"] if a.step == "all" else [a.step]
    for s in steps:
        r = {"inputs": lambda: step_inputs(cfg, task, out), "ccdt": lambda: step_ccdt(cfg, out, a.workers),
             "growclust": lambda: step_growclust(cfg, out, a.ngoodmin, a.run_name),
             "hypodd": lambda: step_hypodd(cfg, out, a.run_name), "evaluate": lambda: step_evaluate(cfg, task, out),
             "export": lambda: step_export(cfg, task, out, a.label_only)}[s]()
        print(s, json.dumps(r, default=str)[:1500], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
