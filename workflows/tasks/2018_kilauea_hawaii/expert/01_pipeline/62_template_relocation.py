#!/usr/bin/env python3
"""Stage 62: relocate the Match&Locate templates by CC double differences, then re-export.

r5's stage 60 placed ~160 pre-Mw 6.9 detections ~6 km from the Shelly cluster:
their template (gamma_0000094, a P-dominated event admitted by r5) was
mislocated by NonLinLoc (10 stations, gap 165°, σx 1.0 km), and an M&L
detection inherits its template's position (PLAN.md r5). This stage
relocates the source round's located summit events, templates included, with
hypoDD on catalog (pick) and waveform cross-correlation (seismotools ccdt)
differential times, and rebuilds the catalog with relocated templates:

  inputs   located r5 events in the summit box; arrivals = NLL-associated
           PhaseNet picks (|residual| <= 0.5 s); waveform links
  pairs    nearest neighbours (--neighbors within --pairs-km) plus
           co-detection pairs: each template with the located events its own
           M&L detections (N×MAD >= final) coincide with (±1.5 s). A
           mislocated template's nearest neighbours are the wrong events; its
           detections name its waveform neighbours wherever they were located
  ccdt     differential times over those pairs
  hypodd   event.dat (depth below the 1.07-km reference elevation, the
           stations' datum in stages 03/04), station.dat, dt.ct (same pairs,
           picks), dt.cc
  build    hypoDD (seismotools/hypodd source), limits sized to the data
  relocate hypoDD; the HVO linear model as 0.5-km constant layers to 5 km,
           1 km below; Ridgecrest cc3_d1 weighting
  evaluate template moves; agreement of relocated events with Shelly / Wei
  export   catalog round: picked events and templates take an accepted
           relocation; M&L detections move with their template; templates
           neither relocated nor passing the location-quality rule (gap <=
           150°, σx <= 0.8 km) are dropped and the detections re-merged

A relocation is accepted when hypoDD returns it, its depth is 0–15 km and
its origin moved < 3 s, and it rests on >= --min-cc-links CC differential
times (P + S). There is no limit on horizontal moves: correcting large
template errors is the purpose. ``--frame nll`` (default) removes the median
displacement of relocated events that pass the location-quality rule: hypoDD
ignores station elevations (summit to coast ~1 km) and moved the whole set
~1 km south, a frame change that improved Wei and worsened Shelly agreement;
the absolute frame stays NonLinLoc's, hypoDD supplies relative positions.
References are used only in ``evaluate``.

Outputs: export/<round>/62_template_relocation/ and export/<round>/60_catalog/.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EXPERT = Path(__file__).resolve().parents[1]
ROOT = EXPERT.parents[3]
spec = importlib.util.spec_from_file_location("s60", EXPERT / "01_pipeline/60_match_locate.py")
S60 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S60)
SRC = EXPERT / S60.CFG["source_export"]
ML_RUN = EXPERT / S60.CFG["export_root"] / "full"
WAVES = (EXPERT / S60.CFG["waveforms"]).resolve()
CCDT = ROOT / "seismotools/cross_correlation/interface/run.py"
HYPODD_SRC = ROOT / "seismotools/hypodd/source"
DATUM_KM = float(S60.CFG["model_datum_elevation_km"])
MODEL = json.loads((EXPERT / S60.CFG["velocity_model"]["registry"]).read_text())["models"][
    S60.CFG["velocity_model"]["key"]]
QUALITY = {"min_cc_links": 1, "max_gap_deg": 150.0, "max_sigma_x_km": 0.8}   # Ridgecrest/Maple rule
PY = sys.executable


def ts(s):
    return pd.to_datetime(s, utc=True, format="ISO8601")


def layers():
    """HVO points (linear between) -> constant layers: 0.5 km to 5 km, 1 km to 15 km, then the rows."""
    z = np.array([r["top_of_layer_km"] for r in MODEL["rows"]])
    v = np.array([r["vp_km_s"] for r in MODEL["rows"]])
    tops = list(np.arange(0, 5, 0.5)) + list(np.arange(5, 15, 1.0)) + [15.0, 16.5]
    bottoms = tops[1:] + [None]
    vel = [float(np.interp((a + b) / 2, z, v)) if b is not None else float(v[-1]) for a, b in zip(tops, bottoms)]
    vel[-2] = float(np.interp(15.75, z, v))
    return tops, vel


def step_inputs(out: Path) -> dict:
    e = pd.read_csv(SRC / "10_validate_catalog/events.csv", low_memory=False)
    e = e[e.latitude.notna()]
    e = e[[S60.in_box({"latitude": a, "longitude": b}) for a, b in zip(e.latitude, e.longitude)]]
    e["t"] = ts(e.origin_time)
    ev = pd.DataFrame({"event_id": e.event_id, "origin_time_utc": e.t.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                       "latitude": e.latitude, "longitude": e.longitude,
                       "depth_km": e.depth_below_sea_level_km + DATUM_KM, "magnitude": e.magnitude,
                       "azimuth_gap_deg": e.azimuth_gap_deg, "sigma_x_km": e.posterior_sigma_x_km})
    templates = set(pd.read_csv(ML_RUN / "dataset/templates.csv").template_id)
    ev["is_template"] = ev.event_id.isin(templates)
    ev.to_csv(out / "events.csv", index=False)
    a = pd.read_csv(SRC / "04_locate_nonlinloc/full/picks.csv")
    a = a[a.residual_s.abs() <= 0.5].merge(
        pd.read_csv(SRC / "02_pick_phasenet/full/picks.csv", usecols=["pick_id", "station_id", "time_utc"]),
        on="pick_id")
    arr = a[a.event_id.isin(ev.event_id)][["event_id", "station_id", "phase", "time_utc"]]
    arr = arr.drop_duplicates(["event_id", "station_id", "phase"])
    arr.to_csv(out / "arrivals.csv", index=False)
    wav = out / "waveforms"
    if wav.exists():
        shutil.rmtree(wav)
    wav.mkdir()
    n = 0
    for st in sorted(arr.station_id.unique()):
        for f in sorted((WAVES / st).glob(f"{st}.*.mseed")):
            (wav / f.name).symlink_to(f)
            n += 1
    return {"events": len(ev), "templates_in_events": int(ev.is_template.sum()),
            "templates_total": len(templates), "arrivals": len(arr), "waveform_files": n}


def step_pairs(out: Path, pairs_km: float, neighbors: int, window_s: float = 1.5) -> dict:
    ev = pd.read_csv(out / "events.csv")
    sys.path.insert(0, str(ROOT / "seismotools/cross_correlation/runtime/python"))
    from ccdt import neighbour_pairs
    ids = ev.event_id.to_numpy()
    ij = neighbour_pairs(ev[["latitude", "longitude", "depth_km"]].to_numpy(), pairs_km, neighbors)
    near = {(ids[i], ids[j]) for i, j in ij}
    t_ev = ts(ev.origin_time_utc).astype("int64").to_numpy() / 1e9
    order = np.argsort(t_ev)
    t_sorted, id_sorted = t_ev[order], ids[order]
    det = pd.read_csv(ML_RUN / "run/template_detections.csv")
    det = det[det.nmad >= float(S60.CFG["final"]["mad_threshold"])]
    seg0 = pd.to_datetime(det.segment.astype(str), format="%Y%m%d", utc=True).astype("int64").to_numpy() / 1e9
    det = det.assign(t=seg0 + det.time_s.to_numpy()).sort_values("nmad", ascending=False)
    known = set(ids)
    co = set()
    for tid, g in det.groupby("template_id"):
        if tid not in known:
            continue
        mates = []
        for t in g.t.to_numpy():
            a, b = np.searchsorted(t_sorted, [t - window_s, t + window_s])
            mates += [e for e in id_sorted[a:b] if e != tid and e not in mates]
            if len(mates) >= neighbors:
                break
        co |= {tuple(sorted((tid, e))) for e in mates[:neighbors]}
    pairs = sorted({tuple(sorted(p)) for p in near} | co)
    pd.DataFrame(pairs, columns=["event_id_1", "event_id_2"]).to_csv(out / "pairs.csv", index=False)
    return {"distance_pairs": len(near), "codetection_pairs": len(co),
            "codetection_only": len(co - {tuple(sorted(p)) for p in near}), "pairs": len(pairs)}


def step_ccdt(out: Path, workers: int) -> dict:
    (out / "ccdt_config.json").write_text(json.dumps({"write_rejected": False}, indent=2))
    with (out / "ccdt.log").open("w") as log:
        subprocess.run([PY, "-I", str(CCDT), "--events", str(out / "events.csv"), "--arrivals",
                        str(out / "arrivals.csv"), "--waveforms", str(out / "waveforms"), "--pairs",
                        str(out / "pairs.csv"), "--output-dir", str(out / "ccdt"), "--config",
                        str(out / "ccdt_config.json"), "--workers", str(workers), "--overwrite"],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    r = json.loads((out / "ccdt/run_result.json").read_text())
    return {k: r.get(k) for k in ("events", "pairs_considered", "pairs_with_dt", "dt_lines", "measurement_status")}


def step_hypodd(out: Path) -> dict:
    h = out / "hypodd"
    h.mkdir(exist_ok=True)
    ev = pd.read_csv(out / "events.csv")
    ev["t"] = ts(ev.origin_time_utc)
    ids = pd.read_csv(out / "ccdt/event_ids.csv")
    cusp = dict(zip(ids.event_id, ids.cusp_id))
    ev["cusp"] = ev.event_id.map(cusp)
    ev["tr"] = ev.t.dt.round("10ms")                        # event.dat keeps HHMMSSss
    with (h / "event.dat").open("w") as f:
        for r in ev.itertuples():
            f.write(f"{r.tr.strftime('%Y%m%d')} {r.tr.strftime('%H%M%S')}{int(round(r.tr.microsecond / 1e4)):02d} "
                    f"{r.latitude:.7f} {r.longitude:.7f} {max(r.depth_km, 0.0):.5f} "
                    f"{0.0 if pd.isna(r.magnitude) else r.magnitude:.2f} 0 0 0 {r.cusp}\n")
    st = pd.read_csv(SRC / "04_locate_nonlinloc/stations.csv").drop_duplicates("station_id")
    st["code"] = st.station_id.str.split(".").str[-1]
    assert st.code.is_unique
    with (h / "station.dat").open("w") as f:
        for r in st.itertuples():
            f.write(f"{r.code} {r.latitude:.7f} {r.longitude:.7f}\n")
    corr = dict(zip(ev.event_id, (ev.t - ev.tr).dt.total_seconds()))
    inv = {v: k for k, v in cusp.items()}
    n_cc = 0
    with (out / "ccdt/dt.cc").open() as src, (h / "dt.cc").open("w") as f:
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
    o_r = dict(zip(ev.event_id, ev.tr))
    arr["tt"] = [(t - o_r[e]).total_seconds() for e, t in zip(arr.event_id, ts(arr.time_utc))]
    arr["code"] = arr.station_id.str.split(".").str[-1]
    tt = {(e, c, p): v for e, c, p, v in zip(arr.event_id, arr.code, arr.phase, arr.tt)}
    by_event = {}
    for e, c, p in tt:
        by_event.setdefault(e, []).append((c, p))
    n_ct = 0
    with (h / "dt.ct").open("w") as f:
        for a, b in pd.read_csv(out / "pairs.csv").itertuples(index=False):
            common = [(c, p) for c, p in by_event.get(a, []) if (b, c, p) in tt]
            if not common:
                continue
            f.write(f"# {cusp[a]:9d} {cusp[b]:9d}\n")
            for c, p in common:
                f.write(f"{c:<7s} {tt[(a, c, p)]:9.4f} {tt[(b, c, p)]:9.4f} 1.00 {p}\n")
                n_ct += 1
    return {"events": len(ev), "stations": len(st), "dt_cc_lines": n_cc, "dt_ct_lines": n_ct}


def step_build(out: Path) -> str:
    h = out / "hypodd"
    n = sum(1 for p in ("dt.cc", "dt.ct") for line in (h / p).open() if not line.startswith("#"))
    n_ev = sum(1 for _ in (h / "event.dat").open())
    dest = out / "native"
    for part in ("include", "src/hypoDD"):
        shutil.copytree(HYPODD_SRC / part, dest / part, dirs_exist_ok=True)
    maxeve = n_ev + 100
    (dest / "include/hypoDD.inc").write_text(
        "      integer*4 MAXEVE, MAXLAY, MAXDATA, MAXSTA, MAXEVE0,\n"
        "     & MAXDATA0, MAXCL\n"
        f"      parameter(MAXEVE={maxeve}, MAXLAY=30, MAXDATA={int(n * 1.1) + 1000},\n"
        f"     & MAXSTA=100, MAXEVE0=2, MAXDATA0=1, MAXCL={maxeve})\n")
    cwd = dest / "src/hypoDD"
    with (dest / "build.log").open("w") as log:
        subprocess.run(["make", "clean"], cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run(["make", "-j4", "FC=gfortran",
                        "FFLAGS=-O2 -I../../include -std=legacy -fallow-argument-mismatch"],
                       cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
    return str((cwd / "hypoDD").relative_to(out))


def step_relocate(out: Path) -> dict:
    h = out / "hypodd"
    tops, vel = layers()
    ctrl = ["dt.cc", "dt.ct", "event.dat", "station.dat", "hypoDD.loc", "hypoDD.reloc", "hypoDD.sta",
            "hypoDD.res", "hypoDD.src",
            "3 3 200",                     # IDAT (cc+ct), IPHA (P+S), DIST
            "0 0",                         # OBSCC OBSCT
            "2 2 2",                       # ISTART (catalog), ISOLV (LSQR), NSET
            "4 3 1.5 -9 -9 1 .5 -9 -9 80",  # Ridgecrest cc3_d1 weighting
            "8 3 1.5 -9 -9 1 .5 -9 -9 40",
            f"{len(tops)} {MODEL['vp_vs_ratio']}",
            " ".join(f"{t:.2f}" for t in tops),
            " ".join(f"{v:.3f}" for v in vel),
            "0"]
    (h / "hypoDD.inp").write_text("\n".join(ctrl) + "\n")
    with (h / "console.log").open("w") as log:
        subprocess.run([str(out / "native/src/hypoDD/hypoDD"), "hypoDD.inp"], cwd=h, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=6 * 3600)
    reloc = h / "hypoDD.reloc"
    return {"relocated_rows": sum(1 for _ in reloc.open()) if reloc.exists() else 0, "layers": len(tops)}


RELOC_COLS = ["cusp", "lat", "lon", "depth", "x", "y", "z", "ex", "ey", "ez", "yr", "mo", "dy", "hr", "mi", "sc",
              "mag", "nccp", "nccs", "nctp", "ncts", "rcc", "rct", "cid"]


def load_relocation(out: Path, min_cc_links: int, frame: str = "nll") -> pd.DataFrame:
    ev = pd.read_csv(out / "events.csv")
    ev["t"] = ts(ev.origin_time_utc)
    r = pd.read_csv(out / "hypodd/hypoDD.reloc", sep=r"\s+", header=None, names=RELOC_COLS, dtype=str)
    for c in RELOC_COLS:
        r[c] = pd.to_numeric(r[c], errors="coerce")
    r = r.merge(pd.read_csv(out / "ccdt/event_ids.csv"), left_on="cusp", right_on="cusp_id")
    r = r.merge(ev[["event_id", "t"]], on="event_id")
    r["t_new"] = pd.to_datetime(dict(year=r.yr, month=r.mo, day=r.dy, hour=r.hr, minute=r.mi), utc=True,
                                errors="coerce") + pd.to_timedelta(r.sc, unit="s")
    dto = (r.t_new - r.t).dt.total_seconds().abs()
    ncc = r.nccp.fillna(0) + r.nccs.fillna(0)
    r["status"] = np.select(
        [r.lat.isna() | r.depth.isna() | r.t_new.isna(), ~r.depth.between(0, 15), dto >= 3, ncc < min_cc_links],
        ["unparsable", "depth", "origin_shift", "few_cc_links"], "relocated")
    m = ev.merge(r[["event_id", "lat", "lon", "depth", "t_new", "nccp", "nccs", "nctp", "ncts", "status"]],
                 on="event_id", how="left")
    m["status"] = m.status.fillna("not_in_hypodd_output")
    ok = m.status.eq("relocated")
    for c in ("lat", "lon", "depth", "t_new"):
        m.loc[~ok, c] = pd.NaT if c == "t_new" else np.nan
    links = {}
    with (out / "ccdt/dt.cc").open() as f:              # CC-linked pairs per event (cusp ids)
        for line in f:
            if line.startswith("#"):
                _, a, b, _ = line.split()
                links[int(a)] = links.get(int(a), 0) + 1
                links[int(b)] = links.get(int(b), 0) + 1
    cusp = dict(zip(*pd.read_csv(out / "ccdt/event_ids.csv")[["event_id", "cusp_id"]].T.values))
    m["cc_links"] = [links.get(cusp.get(e), 0) for e in m.event_id]
    m["passes_quality"] = ((m.cc_links >= QUALITY["min_cc_links"]) & (m.azimuth_gap_deg <= QUALITY["max_gap_deg"])
                           & (m.sigma_x_km <= QUALITY["max_sigma_x_km"]))
    if frame == "nll":
        ref = ok & m.passes_quality
        d = {"lat": (m.lat - m.latitude)[ref].median(), "lon": (m.lon - m.longitude)[ref].median(),
             "depth": (m.depth - m.depth_km)[ref].median(), "t": (m.t_new - m.t)[ref].median()}
        for c in ("lat", "lon", "depth"):
            m[c] = m[c] - d[c]
        m["t_new"] = m.t_new - d["t"]
        m.attrs["frame_correction"] = {k: (v.total_seconds() if k == "t" else float(v)) for k, v in d.items()}
    m["shift_km"] = np.hypot((m.lat - m.latitude) * 111.195,
                             (m.lon - m.longitude) * 111.195 * np.cos(np.radians(m.latitude)))
    return m


def step_evaluate(out: Path, min_cc_links: int, frame: str) -> dict:
    m = load_relocation(out, min_cc_links, frame)
    ok = m.status.eq("relocated")
    tp = m[m.is_template]
    res = {"frame": frame, "frame_correction": m.attrs.get("frame_correction"),
           "status": m.status.value_counts().to_dict(),
           "templates": {"total": int(len(tp)), "relocated": int(tp.status.eq("relocated").sum()),
                         "kept_nll_quality": int((~tp.status.eq("relocated") & tp.passes_quality).sum()),
                         "dropped": int((~tp.status.eq("relocated") & ~tp.passes_quality).sum())},
           "shift_km_quantiles": {q: round(float(m.shift_km[ok].quantile(q)), 3) for q in (0.5, 0.9, 0.99)},
           "template_shift_km_quantiles": {q: round(float(tp.shift_km[tp.status.eq('relocated')].quantile(q)), 3)
                                           for q in (0.5, 0.9, 0.99)},
           "median_displacement": {"north_km": round(float(((m.lat - m.latitude) * 111.195)[ok].median()), 3),
                                   "east_km": round(float(((m.lon - m.longitude) * 104.9)[ok].median()), 3),
                                   "down_km": round(float((m.depth - m.depth_km)[ok].median()), 3)}}
    big = tp[tp.shift_km > 2].sort_values("shift_km", ascending=False)
    res["templates_moved_gt_2km"] = big[["event_id", "shift_km", "nccp", "nccs", "azimuth_gap_deg",
                                         "sigma_x_km"]].round(3).to_dict("records")[:20]
    # agreement with references (evaluation only): events before vs after, matched 2 s / 15 km
    days = [S60.utc(d) for d in S60.CFG["scopes"]["full"]["days"]]
    refs = S60.load_references(days)
    for name in ("shelly", "wei"):
        ref = refs[name]
        out_ = {}
        for lab, la, lo in (("before", "latitude", "longitude"), ("after", "la", "lo")):
            mm = m.assign(la=m.lat.fillna(m.latitude), lo=m.lon.fillna(m.longitude))
            rows = [{"time": t.to_pydatetime(), "latitude": a, "longitude": b}
                    for t, a, b in zip(mm.t, mm[la], mm[lo])]
            pairs = S60.match(rows, ref, 2.0, 15.0)
            d = [np.hypot((rows[i]["latitude"] - ref[j]["latitude"]) * 111.195,
                          (rows[i]["longitude"] - ref[j]["longitude"]) * 104.9) for i, j in pairs]
            tmpl = [np.hypot((rows[i]["latitude"] - ref[j]["latitude"]) * 111.195,
                             (rows[i]["longitude"] - ref[j]["longitude"]) * 104.9)
                    for i, j in pairs if mm.is_template.iloc[i]]
            out_[lab] = {"matched": len(pairs), "epi_median_km": round(float(np.median(d)), 3),
                         "templates_matched": len(tmpl),
                         "template_epi_median_km": round(float(np.median(tmpl)), 3) if tmpl else None,
                         "template_epi_p90_km": round(float(np.quantile(tmpl, 0.9)), 3) if tmpl else None}
        res[f"vs_{name}"] = out_
    return res


def step_export(out: Path, min_cc_links: int, frame: str, catalog_round: str, positions: str) -> dict:
    m = load_relocation(out, min_cc_links, frame).set_index("event_id")
    if positions == "nll":
        # no relocation: the location-quality rule decides for templates and picked events alike
        m.loc[:, "status"] = "not_used"
        for c in ("lat", "lon", "depth"):
            m[c] = np.nan
        m["t_new"] = pd.Series(pd.NaT, index=m.index, dtype="datetime64[ns, UTC]")
    ok = m.status.eq("relocated")
    tmpl = pd.read_csv(ML_RUN / "dataset/templates.csv").set_index("template_id")
    tm = m.reindex(tmpl.index)
    keep_t = tm.status.eq("relocated") | tm.passes_quality.fillna(False)
    shift = pd.DataFrame({"dlat": (tm.lat - tm.latitude).where(tm.status.eq("relocated"), 0.0),
                          "dlon": (tm.lon - tm.longitude).where(tm.status.eq("relocated"), 0.0),
                          "ddep": (tm.depth - tm.depth_km).where(tm.status.eq("relocated"), 0.0),
                          "dt": (tm.t_new - tm.t).dt.total_seconds().where(tm.status.eq("relocated"), 0.0)})
    # unknown templates (not in this stage's events) keep their position only if they pass quality
    keep_t = keep_t & tm.status.notna()
    allowed = set(keep_t.index[keep_t])
    final = S60.CFG["final"]
    by_seg = {s: [d for d in v if d.template_id in allowed] for s, v in S60.read_detections(ML_RUN).items()}
    ml = S60.merged_rows(by_seg, float(final["cc_threshold"]), float(final["mad_threshold"]),
                         float(final["min_separation_s"]))
    for r in ml:
        s = shift.loc[r["template_id"]]
        r["latitude"] += s.dlat
        r["longitude"] += s.dlon
        r["depth_km"] += s.ddep
        r["time"] += pd.Timedelta(seconds=float(s["dt"])).to_pytimedelta()
    chain = S60.chain_magnitudes(ML_RUN, ml)
    for r, (mag, _) in zip(ml, chain["per_event"]):
        r["magnitude"] = mag
    e = pd.read_csv(SRC / "10_validate_catalog/events.csv", low_memory=False)
    w0, w1 = S60.utc(S60.VAL["window"]["start_utc"]), S60.utc(S60.VAL["window"]["end_utc"])
    base = []
    low = []
    for r in e.itertuples():
        if pd.isna(r.latitude) or not (w0 <= S60.utc(r.origin_time) < w1):
            continue
        if positions == "nll" and r.event_id in m.index and not bool(m.passes_quality.get(r.event_id)):
            low.append(r.event_id)
            continue
        rel = r.event_id in m.index and bool(ok.get(r.event_id, False))
        q = m.loc[r.event_id] if rel else None
        base.append({"time": q.t_new.to_pydatetime() if rel else S60.utc(r.origin_time),
                     "latitude": q.lat if rel else r.latitude, "longitude": q.lon if rel else r.longitude,
                     "depth_km": q.depth - DATUM_KM if rel else r.depth_below_sea_level_km,
                     "event_id": r.event_id, "location_source": "nll_dd" if rel else "nll",
                     "magnitude": None if pd.isna(r.magnitude) else float(r.magnitude),
                     "magnitude_source": "" if pd.isna(r.magnitude) else "source_ml"})
    base.sort(key=lambda r: r["time"])
    pairs = S60.dedupe_pairs(ml, base)
    for i, j in pairs:
        if base[j]["magnitude"] is None and ml[i]["magnitude"] is not None:
            base[j]["magnitude"], base[j]["magnitude_source"] = ml[i]["magnitude"], "ml_chain"
    in_base = {i for i, _ in pairs}
    new = [{**r, "event_id": f"ml_{k:06d}", "location_source": "ml",
            "magnitude_source": "ml_chain" if r["magnitude"] is not None else ""}
           for k, r in enumerate((r for i, r in enumerate(ml) if i not in in_base), 1)]
    union = sorted(base + new, key=lambda r: r["time"])
    dest = EXPERT / "export" / catalog_round / "60_catalog"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"event_id": r["event_id"], "origin_time_utc": r["time"].isoformat(),
                   "latitude": r["latitude"], "longitude": r["longitude"], "depth_bsl_km": r["depth_km"],
                   "magnitude": "" if r["magnitude"] is None else round(r["magnitude"], 3),
                   "magnitude_source": r["magnitude_source"], "location_source": r["location_source"],
                   "ml_cc": r.get("cc", ""), "ml_nmad": r.get("nmad", ""), "ml_template_id": r.get("template_id", "")}
                  for r in union]).to_csv(dest / "catalog_events.csv", index=False)
    if positions == "nll":
        cols = ["cc_links", "azimuth_gap_deg", "sigma_x_km"]
        m.loc[low, cols].rename_axis("event_id").reset_index().to_csv(dest / "low_quality_events.csv", index=False)
    return {"catalog": str((dest / "catalog_events.csv").relative_to(EXPERT)), "events": len(union),
            "picked": len(base), "picked_relocated": int(sum(r["location_source"] == "nll_dd" for r in base)),
            "ml_new": len(new), "templates_allowed": len(allowed), "templates_total": int(len(tmpl)),
            "positions": positions, "picked_low_quality_dropped": len(low)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", choices=["all", "inputs", "pairs", "ccdt", "hypodd", "build", "relocate", "evaluate",
                                       "export"],
                    default="all")
    ap.add_argument("--round", default="r6", help="output round (export/<round>/...)")
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--pairs-km", type=float, default=8.0)
    ap.add_argument("--neighbors", type=int, default=40)
    ap.add_argument("--min-cc-links", type=int, default=6)
    ap.add_argument("--frame", choices=["nll", "hypodd"], default="nll")
    ap.add_argument("--positions", choices=["hypodd", "nll"], default="hypodd",
                    help="export: relocated positions, or NLL positions with the location-quality rule only")
    args = ap.parse_args()
    out = EXPERT / "export" / args.round / "62_template_relocation"
    out.mkdir(parents=True, exist_ok=True)
    rp = out / "report.json"
    report = json.loads(rp.read_text()) if rp.exists() else {}
    report["source_round"] = str(SRC.relative_to(EXPERT))
    steps = ["inputs", "pairs", "ccdt", "hypodd", "build", "relocate", "evaluate"] if args.step == "all" \
        else [args.step]
    for s in steps:
        if s == "inputs":
            report[s] = step_inputs(out)
        elif s == "pairs":
            report[s] = step_pairs(out, args.pairs_km, args.neighbors)
        elif s == "ccdt":
            report[s] = step_ccdt(out, args.workers)
        elif s == "hypodd":
            report[s] = step_hypodd(out)
        elif s == "build":
            report[s] = step_build(out)
        elif s == "relocate":
            report[s] = step_relocate(out)
        elif s == "evaluate":
            report[s] = step_evaluate(out, args.min_cc_links, args.frame)
        elif s == "export":
            report[s] = step_export(out, args.min_cc_links, args.frame, args.round, args.positions)
        rp.write_text(json.dumps(report, indent=2, default=str) + "\n")
        print(f"{s}: {json.dumps(report[s], default=str)[:1500]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
