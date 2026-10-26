#!/usr/bin/env python3
"""Relative relocation with GrowClust from ccdt differential times (interface version 1).

GrowClust (Trugman & Shearer 2017) relocates events by hierarchical cluster
growth with an L1 misfit on waveform cross-correlation differential times.
This adapter converts a catalog, stations and a ccdt output directory (dt.cc
+ event_ids.csv) into GrowClust inputs, runs it and returns relocated.csv.
See interface/README.md.
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import traceback
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve()
BIN = HERE.parents[1] / "runtime" / "bin" / "growclust"
INTERFACE_VERSION = 1
DEFAULT_CONFIG = {
    "velocity_layering": "step",          # rows are constant layers (step) or nodes of a linear profile
    "table": {"depth_min_km": 0.0, "depth_max_km": 30.0, "depth_step_km": 1.0,
              "distance_min_km": 0.0, "distance_max_km": 200.0, "distance_step_km": 2.0,
              "rayparam_min": 0.0},
    # upstream EXAMPLE values (Spanish Springs)
    "rmin": 0.6, "delmax_km": 80.0, "rmsmax_s": 0.2,
    "rpsavgmin": 0.0, "rmincut": 0.0, "ngoodmin": 0, "iponly": 0,
    "nboot": 0, "nbranch_min": 1,
}
CAT_COLS = ["yr", "mo", "dy", "hr", "mi", "sc", "evid", "latR", "lonR", "depR", "mag", "qID", "cID", "nbranch",
            "qnpair", "qndiffP", "qndiffS", "rmsP", "rmsS", "eh", "ez", "et", "latC", "lonC", "depC"]


def merge(base: dict, user: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in user.items():
        if k not in out:
            raise ValueError(f"unknown config key: {k}")
        out[k] = {**out[k], **v} if isinstance(out[k], dict) and isinstance(v, dict) else v
    if out["velocity_layering"] not in ("step", "linear"):
        raise ValueError("velocity_layering must be step or linear")
    if not 0 <= out["nboot"] <= 100:
        raise ValueError("nboot must be 0-100 (GrowClust maxboot)")
    return out


def vz_lines(path: Path, layering: str):
    rows = []
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            rows.append(tuple(map(float, line.split()[:3])))
    if not rows or any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("velocity model: need rows of increasing depth_km vp_km_s vs_km_s")
    out = []
    for i, (z, vp, vs) in enumerate(rows):          # GrowClust interpolates linearly between rows:
        if layering == "step" and i:                 # a repeated depth makes a step
            out.append((z, rows[i - 1][1], rows[i - 1][2]))
        out.append((z, vp, vs))
    return out


def relocate(events: pd.DataFrame, stations: pd.DataFrame, dtcc: Path, model: Path, cfg: dict, out: Path) -> dict:
    for col in ("event_id", "origin_time_utc", "latitude", "longitude", "depth_km"):
        if col not in events:
            raise ValueError(f"events: missing column {col}")
    ids = pd.read_csv(dtcc / "event_ids.csv")
    cusp = dict(zip(ids.event_id, ids.cusp_id))
    missing = set(events.event_id) - set(cusp)
    if missing:
        raise ValueError(f"events not in {dtcc / 'event_ids.csv'}: {sorted(missing)[:5]}")
    if ids.cusp_id.max() >= 100_000_000 or len(events) > 100_000:
        raise ValueError("GrowClust limits: event ids < 1e8, <= 100,000 events")
    inp = out / "IN"
    inp.mkdir(exist_ok=True)
    (out / "TT").mkdir(exist_ok=True)
    (out / "OUT").mkdir(exist_ok=True)
    t = pd.to_datetime(events.origin_time_utc, utc=True, format="ISO8601")
    mag = events.magnitude.fillna(0.0) if "magnitude" in events else pd.Series(0.0, index=events.index)
    with (inp / "evlist.txt").open("w") as f:
        for r, ti, m in zip(events.itertuples(), t, mag):
            f.write(f"{ti.year:4d} {ti.month:2d} {ti.day:2d} {ti.hour:2d} {ti.minute:2d} "
                    f"{ti.second + ti.microsecond / 1e6:6.3f} {r.latitude:10.5f} {r.longitude:11.5f} {r.depth_km:8.3f} "
                    f"{m:6.2f} 0.000 0.000 0.000 {cusp[r.event_id]:10d}\n")
    code = stations.station_id.str.split(".").str[-1]
    if not code.is_unique:
        raise ValueError("station codes (after the network) must be unique, as in ccdt dt.cc")
    alias = {c: f"S{i:04d}" for i, c in enumerate(code, 1)}       # GrowClust station names: 5 characters
    with (inp / "stlist.txt").open("w") as f:
        for c, r in zip(code, stations.itertuples()):
            f.write(f"{alias[c]:<5s} {r.latitude:9.5f} {r.longitude:10.5f}\n")
    keep = set(cusp[e] for e in events.event_id)
    n_pairs = n_dt = 0
    with (dtcc / "dt.cc").open() as src, (inp / "xcordata.txt").open("w") as f:
        use = False
        for line in src:
            if line.startswith("#"):
                _, a, b, otc = line.split()
                use = int(a) in keep and int(b) in keep
                if use:
                    f.write(f"# {int(a):9d} {int(b):9d} {float(otc):.3f}\n")
                    n_pairs += 1
            elif use:
                sta, dt, w, ph = line.split()
                if sta not in alias:
                    raise ValueError(f"dt.cc station {sta} not in the station table")
                f.write(f"{alias[sta]:<5s} {float(dt):9.5f} {float(w):6.4f} {ph}\n")
                n_dt += 1
    with (inp / "vzmodel.txt").open("w") as f:
        for z, vp, vs in vz_lines(model, cfg["velocity_layering"]):
            f.write(f"{z:8.3f} {vp:7.4f} {vs:7.4f}\n")
    tb = cfg["table"]
    vpvs = 1.73
    ctl = f"""* GrowClust control file written by seismotools/growclust/interface/run.py
* evlist_fmt
1
* fin_evlist
IN/evlist.txt
* stlist_fmt
1
* fin_stlist
IN/stlist.txt
* xcordat_fmt tdif_fmt (12 = tt1-tt2, as ccdt)
1  12
* fin_xcordat
IN/xcordata.txt
* fin_vzmdl
IN/vzmodel.txt
* fout_vzfine
TT/vzfine.txt
* fout_pTT
TT/tt.pg
* fout_sTT
TT/tt.sg
* vpvs_factor rayparam_min
{vpvs} {tb['rayparam_min']}
* tt_dep0 tt_dep1 tt_ddep
{tb['depth_min_km']} {tb['depth_max_km']} {tb['depth_step_km']}
* tt_del0 tt_del1 tt_ddel
{tb['distance_min_km']} {tb['distance_max_km']} {tb['distance_step_km']}
* rmin delmax rmsmax
{cfg['rmin']} {cfg['delmax_km']} {cfg['rmsmax_s']}
* rpsavgmin rmincut ngoodmin iponly
{cfg['rpsavgmin']} {cfg['rmincut']} {cfg['ngoodmin']} {cfg['iponly']}
* nboot nbranch_min
{cfg['nboot']} {cfg['nbranch_min']}
* fout_cat
OUT/out.growclust_cat
* fout_clust
OUT/out.growclust_clust
* fout_log
OUT/out.growclust_log
* fout_boot
OUT/out.growclust_boot
"""
    (out / "growclust.inp").write_text(ctl)
    with (out / "growclust.log").open("w") as log:
        proc = subprocess.run([str(BIN), "growclust.inp"], cwd=out, stdout=log, stderr=subprocess.STDOUT)
    cat_path = out / "OUT" / "out.growclust_cat"
    if proc.returncode != 0 or not cat_path.exists():
        raise RuntimeError(f"growclust failed ({proc.returncode}); see {out / 'growclust.log'}")
    cat = pd.read_csv(cat_path, sep=r"\s+", header=None, names=CAT_COLS)
    eid = {v: k for k, v in cusp.items()}
    origin = pd.to_datetime(dict(year=cat.yr, month=cat.mo, day=cat.dy, hour=cat.hr, minute=cat.mi), utc=True) + \
        pd.to_timedelta(cat.sc, unit="s")
    moved = (cat.nbranch > 1)
    rel = pd.DataFrame({"event_id": cat.evid.map(eid), "origin_time_utc": origin.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        "latitude": cat.latR, "longitude": cat.lonR, "depth_km": cat.depR,
                        "cluster_id": cat.cID, "n_branch": cat.nbranch, "n_pairs": cat.qnpair,
                        "n_dt_p": cat.qndiffP, "n_dt_s": cat.qndiffS, "rms_p_s": cat.rmsP, "rms_s_s": cat.rmsS,
                        "eh_km": cat.eh, "ez_km": cat.ez, "et_s": cat.et, "latitude_initial": cat.latC,
                        "longitude_initial": cat.lonC, "depth_km_initial": cat.depC, "relocated": moved})
    rel.to_csv(out / "relocated.csv", index=False)
    return {"events": len(rel), "relocated": int(moved.sum()), "clusters_multi": int(cat[moved].cID.nunique()),
            "pairs": n_pairs, "dt_lines": n_dt}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events", type=Path, required=True,
                    help="CSV event_id, origin_time_utc, latitude, longitude, depth_km[, magnitude]")
    ap.add_argument("--stations", type=Path, required=True, help="CSV station_id (NET.STA), latitude, longitude")
    ap.add_argument("--dtcc", type=Path, required=True, help="ccdt output directory (dt.cc, event_ids.csv)")
    ap.add_argument("--velocity-model", type=Path, required=True, help="text: depth_km vp_km_s vs_km_s")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None, help="JSON, deep-merged over the defaults")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    out = a.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()) and not a.overwrite:
        print(f"output directory not empty (use --overwrite): {out}", file=sys.stderr)
        return 2
    result = {"status": "failed", "interface_version": INTERFACE_VERSION, "tool": "GrowClust"}
    try:
        if not BIN.is_file():
            raise FileNotFoundError(f"{BIN} missing: python seismotools/support/build_native.py --tool growclust")
        cfg = merge(DEFAULT_CONFIG, json.loads(a.config.read_text()) if a.config else {})
        (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
        summary = relocate(pd.read_csv(a.events), pd.read_csv(a.stations), a.dtcc.resolve(),
                           a.velocity_model.resolve(), cfg, out)
        result.update(status="success", **summary,
                      inputs={"events": str(a.events), "stations": str(a.stations), "dtcc": str(a.dtcc),
                              "velocity_model": str(a.velocity_model)},
                      outputs=["relocated.csv", "OUT/", "IN/", "TT/", "growclust.inp", "config.json"])
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    (out / "run_result.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    if not a.quiet or result["status"] != "success":
        print(json.dumps({k: v for k, v in result.items() if k != "traceback"}, indent=2, default=str))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
