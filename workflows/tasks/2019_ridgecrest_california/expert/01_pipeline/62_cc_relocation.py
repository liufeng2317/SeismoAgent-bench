#!/usr/bin/env python3
"""Stage 62: cross-correlation double-difference relocation of the stage-60 union.

The Match&Locate events of stage 60 sit on their templates' search grids
(10,166 events on 4,975 positions) and were never relocated; the union is
visibly less sharp than Shelly or Ross, whose every detection is relocated
with waveform cross-correlation differential times. This stage measures CC
differential times with seismotools/cross_correlation (ccdt) and relocates
with hypoDD using the stage-53 CT+CC control (cc3_d1).

Steps (``--step``; ``all`` runs them in order):
  inputs   events of the scope's days from the stage-60 union; arrivals =
           NLL-associated picks (|residual| <= 0.5 s) for picked events, and the
           template's picks shifted by the origin difference for M&L events;
           waveform links (scope days plus neighbours, stations used)
  ccdt     seismotools/cross_correlation/interface/run.py -> dt.cc
  hypodd   event.dat (depth below the nominal 0.7-km surface), station.dat,
           dt.ct over every neighbour pair from picks only (``--ct picks``,
           default) or also from template-derived arrivals at weight 0.5
           (``--ct all``) — rejected: two detections of one template get
           catalog dt = 0 at every station, which collapses them onto the
           template position (local thickness 0.05 km, a third of Shelly's),
           dt.cc (re-referenced to the 0.01-s rounded origins hypoDD reads)
  build    hypoDD from the stage-13 native sources, MAXEVE/MAXCL and MAXDATA
           sized to the data
  relocate hypoDD with the stage-14 cc3_d1 control file (``--control cc3_d1``) or
           cc3_d1 plus a third, CC-dominated set (``cc3_d1_ccfinal``: 6 iterations,
           catalog weights 0.01, CC residuals beyond 6 SD down-weighted)
  evaluate local thickness (minor-axis SD, map view, of each event's 20
           nearest neighbours found in 3-D; orientation-free) and agreement with
           Shelly / Ross / Liu, before vs after, by row source
  export   the scope's catalog with accepted relocations (``relocation_status``
           ``relocated``; otherwise the stage-60 position is kept and the
           status says why)

A hypoDD row is accepted only if it parses, its depth is within 0–25 km, it
moved < 3 km horizontally and its origin changed < 1 s: without template-
derived catalog links, weakly constrained M&L events can diverge. No centroid
correction is applied: the hypoDD solution moves the catalog into the frame of
the Shelly Table-1 layered model (no station elevations) that Shelly's own
hypoDD catalog uses; removing that shift worsened agreement with Shelly on the
pilot day from 0.25 to 0.52 km.

Outputs: export/07_match_locate/62_cc_relocation/<scope>[_<tag>]/ and, for
``export``, export/07_match_locate/62_catalog/<scope>[_<tag>]/catalog_events.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EXPERT = Path(__file__).resolve().parents[1]
ROOT = EXPERT.parents[3]
UNION = EXPERT / "export/07_match_locate/60_catalog/catalog_events.csv"
TEMPLATES = EXPERT / "export/07_match_locate/60_match_locate/full/inputs/templates.csv"
TEMPLATE_PICKS = EXPERT / "export/07_match_locate/60_match_locate/full/inputs/picks.csv"
ASSOC = EXPERT / "export/01_baseline/04_locate_nonlinloc/full/picks.csv"
PICKS = EXPERT / "export/02_pick_phasenet/full/picks.csv"
STATIONS = EXPERT / "export/01_baseline/04_locate_nonlinloc/stations.csv"
WAVES = ROOT / "data/2019_ridgecrest_california/data/waveforms/data"
CCDT = ROOT / "seismotools/cross_correlation/interface/run.py"
HIST = EXPERT / "export/03_location_experiments/01_relative_location"
CONTROL = HIST / "14_tune_hypodd/runs/cc3_d1/hypoDD.inp"
NATIVE_SRC = HIST / "13_hypodd_cc_pilot/native"
SURFACE_KM = 0.7          # nominal surface above sea level (association.yaml reference_elevation_km)
SCOPES = {"pilot": ["2019-07-05"], "full": ["2019-07-04", "2019-07-05", "2019-07-06"]}
PY = "/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python"


def ts(s):
    return pd.to_datetime(s, utc=True, format="ISO8601")


def step_inputs(out: Path, days) -> dict:
    u = pd.read_csv(UNION, low_memory=False)
    u["t"] = ts(u.origin_time_utc)
    u = u[u.t.dt.strftime("%Y-%m-%d").isin(days)].reset_index(drop=True)
    ev = pd.DataFrame({"event_id": u.event_id, "origin_time_utc": u.t.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                       "latitude": u.latitude, "longitude": u.longitude, "depth_km": u.depth_bsl_km + SURFACE_KM,
                       "magnitude": u.magnitude, "location_source": u.location_source,
                       "template_id": u.ml_template_id})
    ev.to_csv(out / "events.csv", index=False)
    # picked events: NLL-associated PhaseNet picks
    a = pd.read_csv(ASSOC)
    a = a[a.residual_s.abs() <= 0.5].merge(pd.read_csv(PICKS, usecols=["pick_id", "station_id", "time_utc"]),
                                            on="pick_id")
    a = a[a.event_id.isin(ev.event_id[ev.location_source == "dd"])]
    picked = a[["event_id", "station_id", "phase", "time_utc"]].drop_duplicates(["event_id", "station_id", "phase"])
    picked = picked.assign(source="pick")
    # M&L events: template picks shifted by (detection origin - template origin)
    tm = pd.read_csv(TEMPLATES)
    t_origin = dict(zip(tm.event_id, ts(tm.origin_time_utc)))
    tp = pd.read_csv(TEMPLATE_PICKS)
    tp["t"] = ts(tp.time_utc)
    ml = ev[ev.location_source == "ml"]
    det_origin = dict(zip(ml.event_id, ts(ml.origin_time_utc)))
    rows = ml[["event_id", "template_id"]].merge(tp, left_on="template_id", right_on="event_id",
                                                  suffixes=("", "_tmpl"))
    rows["time"] = [t + (det_origin[e] - t_origin[k]) for e, k, t in zip(rows.event_id, rows.template_id, rows.t)]
    derived = pd.DataFrame({"event_id": rows.event_id, "station_id": rows.station_id, "phase": rows.phase,
                            "time_utc": pd.Series(rows.time).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                            "source": "template"})
    arr = pd.concat([picked, derived], ignore_index=True)
    arr.to_csv(out / "arrivals.csv", index=False)
    # waveform links: scope days and their neighbours, stations with arrivals
    wav = out / "waveforms"
    if wav.exists():
        shutil.rmtree(wav)
    wav.mkdir()
    d0, d1 = pd.Timestamp(days[0]) - pd.Timedelta("1D"), pd.Timestamp(days[-1]) + pd.Timedelta("1D")
    want = {(d0 + pd.Timedelta(days=k)).strftime("%Y%m%d") for k in range((d1 - d0).days + 1)}
    n = 0
    for st in sorted(arr.station_id.unique()):
        for f in sorted((WAVES / st).glob(f"{st}.*.mseed")):
            if f.name.split("__")[1][:8] in want:
                (wav / f.name).symlink_to(f)
                n += 1
    return {"events": len(ev), "picked_events": int((ev.location_source == "dd").sum()),
            "ml_events": int((ev.location_source == "ml").sum()), "arrivals_pick": int(len(picked)),
            "arrivals_template": int(len(derived)),
            "ml_events_without_arrivals": int(len(set(ml.event_id) - set(derived.event_id))),
            "waveform_files": n}


def step_ccdt(out: Path, workers: int, pairs_km: float, neighbors: int, min_cc: float, weight: str) -> dict:
    cfg = {"pairs": {"max_distance_km": pairs_km, "max_neighbors": neighbors}, "accept": {"min_cc": min_cc},
           "weight": weight, "write_rejected": False}
    (out / "ccdt_config.json").write_text(json.dumps(cfg, indent=2))
    with (out / "ccdt.log").open("w") as log:
        subprocess.run([PY, "-I", str(CCDT), "--events", str(out / "events.csv"), "--arrivals",
                        str(out / "arrivals.csv"), "--waveforms", str(out / "waveforms"), "--output-dir",
                        str(out / "ccdt"), "--config", str(out / "ccdt_config.json"), "--workers", str(workers),
                        "--overwrite"], stdout=log, stderr=subprocess.STDOUT, check=True)
    return json.loads((out / "ccdt" / "run_result.json").read_text())


def _rounded(t: pd.Timestamp) -> pd.Timestamp:
    """hypoDD event.dat keeps HHMMSSss: origin rounded to 0.01 s."""
    return t.round("10ms")


def step_hypodd(out: Path, ct: str) -> dict:
    h = out / f"hypodd_inputs_{ct}"
    h.mkdir(exist_ok=True)
    ev = pd.read_csv(out / "events.csv")
    ev["t"] = ts(ev.origin_time_utc)
    ids = pd.read_csv(out / "ccdt" / "event_ids.csv")
    cusp = dict(zip(ids.event_id, ids.cusp_id))
    ev["cusp"] = ev.event_id.map(cusp)
    ev["tr"] = ev.t.map(_rounded)
    with (h / "event.dat").open("w") as f:
        for r in ev.itertuples():
            f.write(f"{r.tr.strftime('%Y%m%d')} {r.tr.strftime('%H%M%S')}{int(round(r.tr.microsecond / 1e4)):02d} "
                    f"{r.latitude:.7f} {r.longitude:.7f} {r.depth_km:.5f} "
                    f"{0.0 if pd.isna(r.magnitude) else r.magnitude:.2f} 0 0 0 {r.cusp}\n")
    st = pd.read_csv(STATIONS).drop_duplicates("station_id")
    st["code"] = st.station_id.str.split(".").str[-1]
    assert st.code.is_unique
    with (h / "station.dat").open("w") as f:
        for r in st.itertuples():
            f.write(f"{r.code} {r.latitude:.7f} {r.longitude:.7f}\n")
    corr = dict(zip(ev.event_id, (ev.t - ev.tr).dt.total_seconds()))      # exact - rounded origin
    # dt.cc re-referenced to rounded origins: tt_r = tt + (o - o_r)
    n_cc = 0
    with (out / "ccdt" / "dt.cc").open() as src, (h / "dt.cc").open("w") as f:
        inv = {v: k for k, v in cusp.items()}
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
    # dt.ct over the ccdt pair set: arrival minus rounded origin per event
    arr = pd.read_csv(out / "arrivals.csv")
    arr["t"] = ts(arr.time_utc)
    o_r = dict(zip(ev.event_id, ev.tr))
    arr["tt"] = [(t - o_r[e]).total_seconds() for e, t in zip(arr.event_id, arr.t)]
    arr["code"] = arr.station_id.str.split(".").str[-1]
    if ct == "picks":
        arr = arr[arr.source == "pick"]
    tt = {(e, c, p): (v, s) for e, c, p, v, s in zip(arr.event_id, arr.code, arr.phase, arr.tt, arr.source)}
    by_event = {}
    for (e, c, p), v in tt.items():
        by_event.setdefault(e, []).append((c, p))
    sys.path.insert(0, str(ROOT / "seismotools/cross_correlation/runtime/python"))
    from ccdt import neighbour_pairs
    cfg = json.loads((out / "ccdt_config.json").read_text())["pairs"]
    ij = neighbour_pairs(ev[["latitude", "longitude", "depth_km"]].to_numpy(), cfg["max_distance_km"],
                         cfg["max_neighbors"])
    pairs = pd.DataFrame({"event_id_1": ev.event_id.to_numpy()[ij[:, 0]], "event_id_2": ev.event_id.to_numpy()[ij[:, 1]]})
    n_ct = 0
    with (h / "dt.ct").open("w") as f:
        for a, b in pairs.itertuples(index=False):
            common = [(c, p) for c, p in by_event.get(a, []) if (b, c, p) in tt]
            if not common:
                continue
            f.write(f"# {cusp[a]:9d} {cusp[b]:9d}\n")
            for c, p in common:
                (ta, sa), (tb, sb) = tt[(a, c, p)], tt[(b, c, p)]
                w = 1.0 if sa == sb == "pick" else 0.5
                f.write(f"{c:<7s} {ta:9.4f} {tb:9.4f} {w:.2f} {p}\n")
                n_ct += 1
    return {"events": len(ev), "stations": len(st), "dt_cc_lines": n_cc, "dt_ct_lines": n_ct}


def step_build(out: Path) -> Path:
    n = max(sum(1 for line in (h / "dt.cc").open() if not line.startswith("#")) +
            sum(1 for line in (h / "dt.ct").open() if not line.startswith("#"))
            for h in out.glob("hypodd_inputs_*"))
    dest = out / "native"
    for part in ["include", "src/hypoDD"]:
        shutil.copytree(NATIVE_SRC / part, dest / part, dirs_exist_ok=True)
    cap = int(n * 1.1) + 1000
    n_ev = sum(1 for _ in (out / "events.csv").open()) - 1
    maxeve = max(7000, n_ev + 100)
    (dest / "include/hypoDD.inc").write_text(
        "      integer*4 MAXEVE, MAXLAY, MAXDATA, MAXSTA, MAXEVE0,\n"
        "     & MAXDATA0, MAXCL\n"
        f"      parameter(MAXEVE={maxeve}, MAXLAY=15, MAXDATA={cap},\n"
        f"     & MAXSTA=100, MAXEVE0=2, MAXDATA0=1, MAXCL={maxeve})\n")
    cwd = dest / "src/hypoDD"
    with (dest / "build.log").open("w") as log:
        subprocess.run(["make", "clean"], cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run(["make", "-j4", "FC=gfortran", "FFLAGS=-O2 -I../../include -std=legacy -fallow-argument-mismatch"],
                       cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=True)
    return cwd / "hypoDD"


def write_control(dest: Path, variant: str) -> None:
    lines = CONTROL.read_text().splitlines()
    if variant == "cc3_d1_ccfinal":
        i = next(k for k, l in enumerate(lines) if l.split() == ["2", "2", "2"])
        lines[i] = "2 2 3"
        j = i + 2
        lines.insert(j + 1, "6 3 1.5 6 -9 0.01 0.005 -9 -9 40")
    elif variant != "cc3_d1":
        raise SystemExit(f"unknown control {variant}")
    dest.write_text("\n".join(lines) + "\n")


def step_relocate(out: Path, variant: str, ct: str) -> dict:
    run = out / f"hypodd_{variant}_{ct}"
    run.mkdir(exist_ok=True)
    for name in ["event.dat", "station.dat", "dt.ct", "dt.cc"]:
        p = run / name
        if not p.exists():
            p.symlink_to(Path(f"../hypodd_inputs_{ct}") / name)
    write_control(run / "hypoDD.inp", variant)
    with (run / "console.log").open("w") as log:
        subprocess.run([str(out / "native/src/hypoDD/hypoDD"), "hypoDD.inp"], cwd=run, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=6 * 3600)
    reloc = run / "hypoDD.reloc"
    n = sum(1 for _ in reloc.open()) if reloc.exists() else 0
    return {"relocated": n}


RELOC_COLS = ["cusp", "lat", "lon", "depth", "x", "y", "z", "ex", "ey", "ez", "yr", "mo", "dy", "hr", "mi", "sc",
              "mag", "nccp", "nccs", "nctp", "ncts", "rcc", "rct", "cid"]


def load_relocation(out: Path, variant: str, ct: str) -> pd.DataFrame:
    """Scope events with the accepted hypoDD solution (lat/lon/depth/t_new) or NaN, and a status."""
    ev = pd.read_csv(out / "events.csv")
    ev["t"] = ts(ev.origin_time_utc)
    r = pd.read_csv(out / f"hypodd_{variant}_{ct}/hypoDD.reloc", sep=r"\s+", header=None, names=RELOC_COLS, dtype=str)
    for c in RELOC_COLS:
        r[c] = pd.to_numeric(r[c], errors="coerce")
    r = r.merge(pd.read_csv(out / "ccdt/event_ids.csv"), left_on="cusp", right_on="cusp_id")
    r = r.merge(ev[["event_id", "latitude", "longitude", "t"]], on="event_id")
    r["t_new"] = pd.to_datetime(dict(year=r.yr, month=r.mo, day=r.dy, hour=r.hr, minute=r.mi), utc=True,
                                errors="coerce") + pd.to_timedelta(r.sc, unit="s")
    dh = np.hypot((r.lat - r.latitude) * 111.195, (r.lon - r.longitude) * 111.195 * np.cos(np.radians(r.latitude)))
    dto = (r.t_new - r.t).dt.total_seconds().abs()
    r["status"] = np.where(r.lat.isna() | r.depth.isna() | r.t_new.isna(), "diverged_unparsable",
                  np.where(~r.depth.between(0, 25), "diverged_depth",
                  np.where(dh >= 3, "diverged_shift", np.where(dto >= 1, "diverged_origin", "relocated"))))
    ok = r[r.status == "relocated"][["event_id", "lat", "lon", "depth", "t_new", "nccp", "nccs", "nctp", "ncts"]]
    m = ev.merge(ok, on="event_id", how="left")
    m = m.merge(r[["event_id", "status"]], on="event_id", how="left")
    m["status"] = m.status.fillna("not_in_hypodd_output")
    return m


def thickness(lat, lon, dep, k=20, n=3000, seed=0):
    """Median local thickness (km): minor-axis SD, in map view, of each sampled event's k nearest
    neighbours (found in 3-D)."""
    from scipy.spatial import cKDTree
    lat, lon, dep = (np.asarray(a, float) for a in (lat, lon, dep))
    ok = np.isfinite(lat) & np.isfinite(lon) & np.isfinite(dep) & (lat >= 35.45) & (lat <= 36.05) & \
        (lon >= -117.9) & (lon <= -117.2)
    X = np.c_[(lon[ok] + 117.55) * 111.195 * math.cos(math.radians(35.7)), (lat[ok] - 35.7) * 111.195, dep[ok]]
    X = X + np.random.default_rng(1).normal(0, 1e-4, X.shape)        # break exact ties (stacked M&L positions)
    tree = cKDTree(X)
    out = []
    for i in np.random.default_rng(seed).choice(len(X), min(n, len(X)), replace=False):
        _, j = tree.query(X[i], k=k + 1)
        Y = X[j, :2] - X[j, :2].mean(axis=0)
        out.append(math.sqrt(max(np.linalg.eigvalsh(np.cov(Y.T))[0], 0.0)))
    return round(float(np.median(out)), 3)


def step_evaluate(out: Path, days, variant: str, ct: str) -> dict:
    import importlib.util
    spec = importlib.util.spec_from_file_location("evaluation", EXPERT.parent / "evaluation/scripts/plot_evaluation_comparison.py")
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    _, _, refs, _ = E.house.load_data(E.CASE)
    refs = {p["key"]: p for p in refs}
    m = load_relocation(out, variant, ct)
    m["la"], m["lo"] = m.lat.fillna(m.latitude), m.lon.fillna(m.longitude)
    m["de"], m["tt"] = m.depth.fillna(m.depth_km), m.t_new.fillna(m.t)
    rel = m.lat.notna()
    res = {"events": len(m), "status": m.status.value_counts().to_dict(),
           "relocated_by_source": m[rel].location_source.value_counts().to_dict()}
    in_days = lambda p: [r for r in p["rows"] if r["time"].strftime("%Y-%m-%d") in days]
    th = {k: thickness(*zip(*[(r["latitude"], r["longitude"], r["depth_km"]) for r in in_days(refs[k])]))
          for k in ("shelly", "ross_relocated", "liu")}
    # "before"/"after_all" include M&L events stacked on template nodes, which read as thin
    th["before_all"] = thickness(m.latitude, m.longitude, m.depth_km)
    th["after_all"] = thickness(m.la, m.lo, m.de)
    for src in ("dd", "ml"):
        q = m[rel & (m.location_source == src)]
        th[f"relocated_{src}_before"] = thickness(q.latitude, q.longitude, q.depth_km)
        th[f"relocated_{src}_after"] = thickness(q.la, q.lo, q.de)
    res["local_thickness_km"] = th

    def rec(la, lo, z, t):
        rows = [{"time": a.to_pydatetime(), "latitude": b, "longitude": c, "depth_km": d, "magnitude": None}
                for a, b, c, d in zip(m[t], m[la], m[lo], m[z])]
        return E.as_record("x", "x", "k", sorted(rows, key=lambda r: r["time"]))
    before, after = rec("latitude", "longitude", "depth_km", "t"), rec("la", "lo", "de", "tt")
    agree = {}
    for key in ("shelly", "ross_relocated", "liu"):
        ref = dict(refs[key]); ref["rows"] = in_days(refs[key])
        for lab, pop in (("before", before), ("after", after)):
            pr = E.match(pop, ref)
            agree[f"{key}_{lab}"] = {"recall": round(len(pr) / len(ref["rows"]), 4),
                                     "epi_median_km": round(float(np.median([p[2] for p in pr])), 3)}
    res["agreement"] = agree
    return res


def step_export(out: Path, variant: str, ct: str, dest: Path) -> dict:
    m = load_relocation(out, variant, ct)
    u = pd.read_csv(UNION, low_memory=False).set_index("event_id")
    rel = m.lat.notna()
    cat = pd.DataFrame({
        "event_id": m.event_id,
        "origin_time_utc": np.where(rel, m.t_new.dt.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00"), m.origin_time_utc),
        "latitude": m.lat.fillna(m.latitude), "longitude": m.lon.fillna(m.longitude),
        "depth_bsl_km": np.where(rel, m.depth - SURFACE_KM, m.depth_km - SURFACE_KM),
        "magnitude": m.event_id.map(u.magnitude), "magnitude_source": m.event_id.map(u.magnitude_source),
        "location_source": m.location_source,
        "relocation_status": m.status, "n_cc_p": m.nccp, "n_cc_s": m.nccs, "n_ct_p": m.nctp, "n_ct_s": m.ncts,
        "ml_cc": m.event_id.map(u.ml_cc), "ml_nmad": m.event_id.map(u.ml_nmad),
        "ml_template_id": m.event_id.map(u.ml_template_id)})
    cat = cat.sort_values("origin_time_utc")
    dest.mkdir(parents=True, exist_ok=True)
    cat.to_csv(dest / "catalog_events.csv", index=False)
    return {"catalog": str(dest.relative_to(EXPERT)), "events": len(cat),
            "relocated": int(rel.sum()), "status": m.status.value_counts().to_dict(),
            "control": variant, "catalog_times": ct}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", choices=sorted(SCOPES), default="pilot")
    ap.add_argument("--step", choices=["all", "inputs", "ccdt", "hypodd", "build", "relocate", "evaluate", "export"],
                    default="all")
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--control", default="cc3_d1", choices=["cc3_d1", "cc3_d1_ccfinal"])
    ap.add_argument("--ct", default="picks", choices=["picks", "all"])
    ap.add_argument("--tag", default="", help="variant directory <scope>_<tag> (inputs linked from <scope>)")
    ap.add_argument("--pairs-km", type=float, default=3.0)
    ap.add_argument("--neighbors", type=int, default=30)
    ap.add_argument("--min-cc", type=float, default=0.7)
    ap.add_argument("--weight", default="cc", choices=["cc", "cc2"])
    args = ap.parse_args()
    base = EXPERT / "export/07_match_locate/62_cc_relocation" / args.scope
    out = base.with_name(f"{args.scope}_{args.tag}") if args.tag else base
    out.mkdir(parents=True, exist_ok=True)
    if args.tag:
        for name in ("events.csv", "arrivals.csv", "waveforms"):
            if not (out / name).exists() and (base / name).exists():
                (out / name).symlink_to(base / name)
    rp = out / "report.json"
    report = json.loads(rp.read_text()) if rp.exists() else {}
    steps = ["inputs", "ccdt", "hypodd", "build", "relocate", "evaluate"] if args.step == "all" else [args.step]
    tagname = f"{args.scope}_{args.tag}" if args.tag else args.scope
    for s in steps:
        if s == "inputs":
            report["inputs"] = step_inputs(out, SCOPES[args.scope])
        elif s == "ccdt":
            r = step_ccdt(out, args.workers, args.pairs_km, args.neighbors, args.min_cc, args.weight)
            report["ccdt"] = {k: r[k] for k in ("events", "pairs_considered", "pairs_with_dt", "dt_lines",
                                                "measurement_status", "window_status", "timing_s")}
        elif s == "hypodd":
            report[f"hypodd_inputs_{args.ct}"] = step_hypodd(out, args.ct)
        elif s == "build":
            report["build"] = str(step_build(out))
        elif s == "relocate":
            report[f"relocate_{args.control}_{args.ct}"] = step_relocate(out, args.control, args.ct)
        elif s == "evaluate":
            report[f"evaluation_{args.control}_{args.ct}"] = step_evaluate(out, SCOPES[args.scope], args.control,
                                                                            args.ct)
        elif s == "export":
            report["export"] = step_export(out, args.control, args.ct,
                                           EXPERT / "export/07_match_locate/62_catalog" / tagname)
        rp.write_text(json.dumps(report, indent=2, default=str) + "\n")
        key = {"hypodd": f"hypodd_inputs_{args.ct}", "relocate": f"relocate_{args.control}_{args.ct}",
               "evaluate": f"evaluation_{args.control}_{args.ct}", "export": "export"}.get(s, s)
        print(f"{s}: {json.dumps(report.get(key), default=str)[:600]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
