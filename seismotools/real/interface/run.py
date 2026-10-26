#!/usr/bin/env python3
"""Associate phase picks into events with REAL (interface version 1).

REAL (Zhang et al. 2019) counts P and S picks inside theoretical travel-time
windows on a grid around the station with the initiating pick, then refines the
best grid node. This adapter writes REAL's station and pick files, builds the
travel-time table from a 1-D model (first arrivals, fast marching, so head
waves are included), runs REAL on time chunks with a buffer (each event belongs
to exactly one chunk) and writes the seismotools association contract.
See interface/README.md.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import subprocess
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
BIN = HERE.parents[1] / "runtime" / "bin" / "REAL"
INTERFACE_VERSION = 1
DEG_KM = 111.19                          # REAL's degree length
DEFAULT_CONFIG = {
    "reference_elevation_km": 0.0,       # depth datum; station elevation is taken relative to it
    "velocity_layering": "step",         # rows are constant layers (step) or nodes of a linear profile
    "region": None,                      # optional output filter {latitude, longitude, depth_km}
    # -R: search around the station with the initiating pick (upstream demo_real values)
    "search": {"rx_deg": 0.1, "rh_km": 20.0, "dx_deg": 0.04, "dh_km": 2.0, "event_interval_s": 5.0,
               "max_gap_deg": 360.0, "max_distance_deg": 1.4},
    # -S: thresholds (upstream demo_real, large-grid variant)
    "thresholds": {"np0": 3, "ns0": 2, "nps0": 12, "npsboth0": 3, "std0": 0.5, "dtps": 0.2, "nrt": 1.0,
                   "drt": 0.25, "nxd": 0.2, "rsel": 4.0, "ires": 0},
    # -G: travel-time table (must cover max_distance_deg and rh_km)
    "table": {"max_distance_deg": 1.5, "max_depth_km": 30.0, "dist_step_deg": 0.01, "depth_step_km": 1.0,
              "fmm_spacing_km": 0.1},
    "chunk_hours": 24.0,                 # REAL run length; events are kept in the chunk owning their origin
    "buffer_s": 120.0,                   # picks added on both sides of a chunk
}


def merge(base: dict, user: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in user.items():
        if k not in out:
            raise ValueError(f"unknown config key: {k}")
        if isinstance(out[k], dict) and isinstance(v, dict):
            unknown = set(v) - set(out[k])
            if unknown:
                raise ValueError(f"unknown {k} keys: {sorted(unknown)}")
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    if out["velocity_layering"] not in ("step", "linear"):
        raise ValueError("velocity_layering must be step or linear")
    s, t = out["search"], out["table"]
    if s["max_distance_deg"] > t["max_distance_deg"] - 0.05 or s["rh_km"] > t["max_depth_km"]:
        raise ValueError("table must cover search.max_distance_deg (+0.05) and search.rh_km")
    return out


def read_model(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            rows.append(tuple(map(float, line.split()[:3])))
    if not rows or any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("velocity model: need rows of increasing depth_km vp_km_s vs_km_s")
    return rows


def velocity_at(rows, z: np.ndarray, col: int, layering: str) -> np.ndarray:
    zs = np.array([r[0] for r in rows])
    vs = np.array([r[col] for r in rows])
    if layering == "linear":
        return np.interp(z, zs, vs)
    return vs[np.clip(np.searchsorted(zs, z, side="right") - 1, 0, len(vs) - 1)]


def build_table(rows, cfg: dict, path: Path) -> dict:
    """REAL ttdb rows (depth outer, distance inner, both from 0): gdist dep ptime stime prayp srayp phslow shslow."""
    from pyrocko.modelling import eikonal
    t, lay = cfg["table"], cfg["velocity_layering"]
    h = t["fmm_spacing_km"]
    nx = int(math.ceil(t["max_distance_deg"] * DEG_KM / h)) + 3
    nz = int(math.ceil(t["max_depth_km"] / h)) + 3
    zc = np.arange(nz) * h
    grids = {}
    for name, col in (("P", 1), ("S", 2)):
        speeds = np.tile(velocity_at(rows, zc, col, lay), (nx, 1))
        times = -np.ones((nx, nz))
        times[0, 0] = 0.0                      # station at the surface, reciprocity
        eikonal.eikonal_solver_fmm_cartesian(speeds, times, h)
        grids[name] = times

    def sample(g, x, z):
        ix, iz = min(int(x / h), nx - 2), min(int(z / h), nz - 2)
        ax, az = x / h - ix, z / h - iz
        return (g[ix, iz] * (1 - ax) * (1 - az) + g[ix + 1, iz] * ax * (1 - az)
                + g[ix, iz + 1] * (1 - ax) * az + g[ix + 1, iz + 1] * ax * az)

    n_dist = int(round(t["max_distance_deg"] / t["dist_step_deg"]))
    n_dep = int(round(t["max_depth_km"] / t["depth_step_km"])) + 1
    with path.open("w") as f:
        for ih in range(n_dep):
            z = ih * t["depth_step_km"]
            for k in range(n_dist):
                gd = k * t["dist_step_deg"]
                x = gd * DEG_KM
                vals = []
                for name in ("P", "S"):
                    g = grids[name]
                    tt = sample(g, x, z)
                    dx = (sample(g, x + h, z) - sample(g, max(x - h, 0.0), z)) / (x + h - max(x - h, 0.0))
                    dz = (sample(g, x, z + h) - sample(g, x, max(z - h, 0.0))) / (z + h - max(z - h, 0.0))
                    vals.append((tt, dx * DEG_KM, dz))
                (tp, rp, sp), (ts, rs, ss) = vals
                f.write(f"{gd:.4f} {z:.3f} {tp:.6f} {ts:.6f} {rp:.6f} {rs:.6f} {sp:.6f} {ss:.6f} P S\n")
    return {"rows": n_dist * n_dep, "n_dist": n_dist, "n_depth": n_dep, "fmm_spacing_km": h}


def run_chunk(picks: pd.DataFrame, stations: pd.DataFrame, cfg: dict, rows, table: Path, folder: Path,
              t0: pd.Timestamp, t1: pd.Timestamp, workers: int, lat_center: float):
    """Run REAL on picks in [t0 - buffer, t1 + buffer); keep events with origin in [t0, t1)."""
    buf = pd.Timedelta(seconds=cfg["buffer_s"])
    ref = (t0 - buf).floor("D")
    sel = picks[(picks.t >= t0 - buf) & (picks.t < t1 + buf)]
    folder.mkdir(parents=True, exist_ok=True)
    pickdir = folder / "picks"
    pickdir.mkdir(exist_ok=True)
    keys = {}
    for (sid, ph), g in sel.groupby(["station_id", "phase"]):
        sec = ((g.t - ref).dt.total_seconds()).round(4)
        if len(g) >= 20000:
            raise ValueError(f"{sid} {ph}: {len(g)} picks in one chunk (REAL limit 20000); use smaller chunk_hours")
        if sec.duplicated().any():
            raise ValueError(f"{sid} {ph}: duplicate pick times")
        net, sta = sid.split(".", 1)
        w = g.probability.fillna(1.0) if "probability" in g else pd.Series(1.0, index=g.index)
        pd.DataFrame({"s": sec.map("{:.4f}".format), "w": w.map("{:.4f}".format), "a": "0.0"}) \
            .sort_values("s").to_csv(pickdir / f"{net}.{sta}.{ph}.txt", sep=" ", header=False, index=False)
        keys.update({(sid, ph, f"{s:.4f}"): pid for s, pid in zip(sec, g.pick_id)})
    ref_elev = cfg["reference_elevation_km"]
    with (folder / "station.dat").open("w") as f:
        for r in stations.itertuples():
            net, sta = r.station_id.split(".", 1)
            f.write(f"{r.longitude:.6f} {r.latitude:.6f} {net} {sta} XXZ {r.elevation_m / 1000.0 - ref_elev:.4f}\n")
    s, th, tb = cfg["search"], cfg["thresholds"], cfg["table"]
    vp0 = float(np.mean([r[1] for r in rows]))
    vs0 = float(np.mean([r[2] for r in rows]))
    args = [str(BIN), f"-D{ref.year}/{ref.month}/{ref.day}/{lat_center:.4f}",
            f"-R{s['rx_deg']}/{s['rh_km']}/{s['dx_deg']}/{s['dh_km']}/{s['event_interval_s']}/{s['max_gap_deg']}/"
            f"{s['max_distance_deg']}",
            f"-G{tb['max_distance_deg']}/{tb['max_depth_km']}/{tb['dist_step_deg']}/{tb['depth_step_km']}",
            f"-V{vp0:.4f}/{vs0:.4f}/{rows[0][1]}/{rows[0][2]}/1",
            "-S" + "/".join(str(th[k]) for k in ("np0", "ns0", "nps0", "npsboth0", "std0", "dtps", "nrt", "drt",
                                                 "nxd", "rsel", "ires")),
            "station.dat", "picks", str(table)]
    env = {**os.environ, "OMP_NUM_THREADS": str(max(1, workers))}
    with (folder / "real.log").open("w") as log:
        log.write(" ".join(args) + "\n")
        log.flush()
        proc = subprocess.run(args, cwd=folder, stdout=log, stderr=subprocess.STDOUT, env=env)
    if proc.returncode != 0 or not (folder / "phase_sel.txt").exists():
        raise RuntimeError(f"REAL failed ({proc.returncode}); see {folder / 'real.log'}")
    events, links = [], []
    current = None
    for line in (folder / "phase_sel.txt").read_text().splitlines():
        tok = line.split()
        if len(tok) == 17:                     # event header
            origin = ref + pd.Timedelta(seconds=float(tok[5]))
            current = None
            if t0 <= origin < t1:
                current = {"origin": origin, "std_s": float(tok[6]), "latitude": float(tok[7]),
                           "longitude": float(tok[8]), "depth_km": float(tok[9]), "gap_deg": float(tok[16]),
                           "picks": []}
                events.append(current)
        elif len(tok) == 9 and current is not None:
            key = (f"{tok[0]}.{tok[1]}", tok[2], f"{float(tok[3]):.4f}")
            if key not in keys:
                raise RuntimeError(f"REAL returned an unknown pick {key}")
            current["picks"].append((keys[key], tok[2], float(tok[6])))
    return events


def associate(picks, stations, model_path: Path, cfg: dict, out: Path, workers: int) -> dict:
    for col in ("pick_id", "station_id", "phase", "time_utc"):
        if col not in picks:
            raise ValueError(f"picks: missing column {col}")
    for col in ("station_id", "latitude", "longitude", "elevation_m"):
        if col not in stations:
            raise ValueError(f"stations: missing column {col}")
    if not set(picks.phase) <= {"P", "S"}:
        raise ValueError("picks: phase must be P or S")
    unknown = set(picks.station_id) - set(stations.station_id)
    if unknown:
        raise ValueError(f"picks: stations not in the station table: {sorted(unknown)[:5]}")
    if len(stations) > 500 or not stations.station_id.str.count(r"\.").ge(1).all():
        raise ValueError("stations: at most 500, ids NET.STA")
    rows = read_model(model_path)
    table = out / "ttdb.txt"
    tinfo = build_table(rows, cfg, table)
    p = picks.reset_index(drop=True).copy()
    p["t"] = pd.to_datetime(p.time_utc, utc=True, format="ISO8601")
    lat_center = float(stations.latitude.mean())
    start = p.t.min().floor("D")
    step = pd.Timedelta(hours=cfg["chunk_hours"])
    events, n_chunks = [], 0
    t0 = start
    while t0 <= p.t.max():
        t1 = t0 + step
        if ((p.t >= t0) & (p.t < t1)).any():
            events += run_chunk(p, stations, cfg, rows, table, out / "chunks" / t0.strftime("%Y%m%dT%H%M%S"),
                                t0, t1, workers, lat_center)
            n_chunks += 1
        t0 = t1
    reg = cfg["region"]
    if reg:
        events = [e for e in events if reg["latitude"][0] <= e["latitude"] <= reg["latitude"][1]
                  and reg["longitude"][0] <= e["longitude"] <= reg["longitude"][1]
                  and reg["depth_km"][0] <= e["depth_km"] <= reg["depth_km"][1]]
    events.sort(key=lambda e: e["origin"])
    owner, resid, ev_rows = {}, {}, []
    for i, e in enumerate(events):
        for pid, ph, res in e["picks"]:
            if pid in owner:                    # REAL removes duplicates inside a chunk; chunks own disjoint origins
                raise RuntimeError(f"pick {pid} assigned twice")
            owner[pid], resid[pid] = i, res
        n_p = sum(ph == "P" for _, ph, _ in e["picks"])
        n_s = len(e["picks"]) - n_p
        ev_rows.append({"event_index": i, "time_utc": e["origin"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        "latitude": e["latitude"], "longitude": e["longitude"], "depth_km": e["depth_km"],
                        "num_picks": n_p + n_s, "num_p_picks": n_p, "num_s_picks": n_s, "std_s": e["std_s"],
                        "gap_deg": e["gap_deg"]})
    pd.DataFrame(ev_rows, columns=["event_index", "time_utc", "latitude", "longitude", "depth_km", "num_picks",
                                   "num_p_picks", "num_s_picks", "std_s", "gap_deg"]).to_csv(out / "events.csv",
                                                                                             index=False)
    pd.DataFrame({"pick_index": p.index, "pick_id": p.pick_id,
                  "event_index": [owner.get(x, "") for x in p.pick_id], "assignment_probability": "",
                  "assignment_status": ["assigned" if x in owner else "unassigned" for x in p.pick_id],
                  "residual_s": [resid.get(x, "") for x in p.pick_id]}).to_csv(out / "assignments.csv", index=False)
    return {"picks": len(p), "events": len(ev_rows), "assigned_picks": len(owner), "chunks": n_chunks,
            "table": tinfo}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--picks", type=Path, required=True, help="CSV pick_id, station_id, phase, time_utc[, probability]")
    ap.add_argument("--stations", type=Path, required=True, help="CSV station_id (NET.STA), latitude, longitude, elevation_m")
    ap.add_argument("--velocity-model", type=Path, required=True, help="text: depth_km vp_km_s vs_km_s")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None, help="JSON, deep-merged over the defaults")
    ap.add_argument("--workers", type=int, default=8, help="OpenMP threads")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    out = a.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()) and not a.overwrite:
        print(f"output directory not empty (use --overwrite): {out}", file=sys.stderr)
        return 2
    result = {"status": "failed", "interface_version": INTERFACE_VERSION, "tool": "REAL"}
    try:
        if not BIN.is_file():
            raise FileNotFoundError(f"{BIN} missing: python seismotools/support/build_native.py --tool real")
        cfg = merge(DEFAULT_CONFIG, json.loads(a.config.read_text()) if a.config else {})
        (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
        summary = associate(pd.read_csv(a.picks), pd.read_csv(a.stations), a.velocity_model, cfg, out, a.workers)
        result.update(status="success", **summary,
                      inputs={"picks": str(a.picks), "stations": str(a.stations),
                              "velocity_model": str(a.velocity_model)},
                      outputs=["events.csv", "assignments.csv", "ttdb.txt", "chunks/", "config.json"])
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    (out / "run_result.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    if not a.quiet or result["status"] != "success":
        print(json.dumps({k: v for k, v in result.items() if k != "traceback"}, indent=2, default=str))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
