#!/usr/bin/env python3
"""Locate a catalog of arrival groups with HypoInverse 1.40 (interface version 2).

HypoInverse (Klein 2002, USGS OFR 02-171) is the linearised (Geiger) locator
of the USGS/ANSS networks, with distance and residual weighting. This adapter
writes its station file (format #2), CRE (or CRH) layer models for P and S (SAL), a
Y2000 archive phase file and a command file, runs hyp1.40 and returns the
seismotools locator contract (events.csv, arrivals.csv). See interface/README.md.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import subprocess
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
BIN = HERE.parents[1] / "runtime" / "bin" / "hyp1.40"
INTERFACE_VERSION = 2
DEFAULT_CONFIG = {
    "model_type": "CRE",               # CRE: stations at their elevations, model depth 0 at reference_elevation_km;
                                       # CRH: all stations at the model top (elevations ignored; interface v1)
    "reference_elevation_km": 0.0,     # CRE: elevation (km above sea level) of the model's depth 0;
                                       # output depths are km below it
    "velocity_layering": "step",       # rows are constant layers (step) or nodes of a linear profile
    "linear_sublayer_km": 0.5,         # linear profiles become constant sublayers (CRH is constant layers)
    "lvz_policy": "error",             # CRH needs velocities increasing with depth: "error", or "clip"
                                       # (raise a layer to 0.01 km/s above the one over it; reported)
    "trial_depth_km": 5.0,             # ZTR
    "min_stations": 4,                 # MIN
    "timing_error_s": 0.10,            # ERR
    "residual_weighting": [4, 0.10, 2, 3],          # RMS (NCSN defaults)
    "distance_weighting": [4, 15, 3.5, 7],          # DIS (NCSN defaults)
    "initial_distance_weighting": [1, 50, 3, 6],    # DI1 (NCSN defaults)
    "weight_factors": [1.0, 0.5, 0.2, 0.1],         # WET: factors of weight codes 0-3
    "pick_weight_code": {"P": 0, "S": 1},           # used when arrivals carry no uncertainty_s
    "uncertainty_codes_s": [0.05, 0.10, 0.20, 0.40],  # uncertainty_s <= these -> codes 0-3, else 4 (unused)
}

# ---------------------------------------------------------------- fixed columns
# (start column 1-based, width): from the HypoInverse 1.40 manual (OFR 02-171 rev. 2014)
STA2 = {"site": (1, 5), "net": (7, 2), "comp3": (11, 3), "latdeg": (16, 2), "latmin": (19, 7), "ns": (26, 1),
        "londeg": (27, 3), "lonmin": (31, 7), "ew": (38, 1), "elev": (39, 4), "period": (43, 3)}
PHASE = {"site": (1, 5), "net": (6, 2), "comp3": (10, 3), "prem": (14, 2), "pfm": (16, 1), "pwt": (17, 1),
         "year": (18, 4), "mdhm": (22, 8), "psec": (30, 5), "pres": (35, 4), "pwused": (39, 3), "ssec": (42, 5),
         "srem": (47, 2), "swt": (50, 1), "sres": (51, 4), "swused": (64, 3), "dist": (75, 4)}
SUM = {"year": (1, 4), "mdhm": (5, 8), "sec": (13, 4), "latdeg": (17, 2), "ns": (19, 1), "latmin": (20, 4),
       "londeg": (24, 3), "ew": (27, 1), "lonmin": (28, 4), "depth": (32, 5), "nph": (40, 3), "gap": (43, 3),
       "dmin": (46, 3), "rms": (49, 4), "remark2": (82, 1), "ns_s": (83, 3), "erh": (86, 4), "erz": (90, 4),
       "id": (137, 10)}


def put(line: list, spec: dict, key: str, text: str) -> None:
    start, width = spec[key]
    if len(text) > width:
        raise ValueError(f"{key}: {text!r} wider than {width}")
    line[start - 1:start - 1 + width] = list(text.rjust(width) if text.strip().lstrip("-").replace(".", "").isdigit()
                                             else text.ljust(width))


def get(line: str, spec: dict, key: str) -> str:
    start, width = spec[key]
    return line[start - 1:start - 1 + width]


def implied(text: str, decimals: int) -> float:
    """F-format field: an explicit point wins, otherwise the last `decimals` digits are decimals."""
    t = text.strip()
    if not t:
        return math.nan
    return float(t) if "." in t else int(t) / 10 ** decimals


def merge(base: dict, user: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in user.items():
        if k not in out:
            raise ValueError(f"unknown config key: {k}")
        out[k] = {**out[k], **v} if isinstance(out[k], dict) and isinstance(v, dict) else v
    if out["velocity_layering"] not in ("step", "linear"):
        raise ValueError("velocity_layering must be step or linear")
    if out["lvz_policy"] not in ("error", "clip"):
        raise ValueError("lvz_policy must be error or clip")
    if out["model_type"] not in ("CRH", "CRE"):
        raise ValueError("model_type must be CRH or CRE")
    return out


def crh_rows(path: Path, cfg: dict):
    rows = []
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            rows.append(tuple(map(float, line.split()[:3])))
    if not rows or rows[0][0] != 0.0 or any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("velocity model: rows of increasing depth_km vp_km_s vs_km_s starting at 0")
    if cfg["velocity_layering"] == "linear":
        h, dense = cfg["linear_sublayer_km"], []
        for (z0, p0, s0), (z1, p1, s1) in zip(rows, rows[1:]):
            for z in np.arange(z0, z1 - 1e-9, h):
                f = (min(z + h, z1) + z) / 2
                dense.append((z, p0 + (p1 - p0) * (f - z0) / (z1 - z0), s0 + (s1 - s0) * (f - z0) / (z1 - z0)))
        rows = dense + [rows[-1]]
    changes, out = [], [rows[0]]
    for z, vp, vs in rows[1:]:
        new = (z, max(vp, out[-1][1] + 0.01), max(vs, out[-1][2] + 0.01))
        if new[1:] != (vp, vs):
            if cfg["lvz_policy"] == "error":
                raise ValueError(f"velocity does not increase at {z} km: CRH models cannot have low-velocity "
                                 "zones or equal adjacent layers (lvz_policy 'clip' raises the layer)")
            changes.append({"depth_km": z, "vp": [vp, round(new[1], 4)], "vs": [vs, round(new[2], 4)]})
        out.append(new)
    return out, changes


def cre_top(stations: pd.DataFrame, cfg: dict) -> tuple[float, float]:
    """CRE model top (km above sea level) and how far it lies above the model's depth 0 (0 for CRH)."""
    if cfg["model_type"] != "CRE":
        return 0.0, 0.0
    ref = float(cfg["reference_elevation_km"])
    top = max(ref, math.ceil(float(stations.elevation_m.max()) / 10.0) / 100.0)
    return round(top - ref, 3), top


def write_inputs(arr: pd.DataFrame, stations: pd.DataFrame, rows, cfg: dict, out: Path):
    alias = {s: f"S{i:04d}" for i, s in enumerate(stations.station_id, 1)}
    with (out / "stations.sta").open("w") as f:
        for r in stations.itertuples():
            line = [" "] * 50
            la, lo = abs(r.latitude), abs(r.longitude)
            put(line, STA2, "site", alias[r.station_id])
            put(line, STA2, "net", "XX")
            put(line, STA2, "comp3", "HHZ")
            put(line, STA2, "latdeg", f"{int(la):2d}")
            put(line, STA2, "latmin", f"{(la - int(la)) * 60:7.4f}")
            put(line, STA2, "ns", "S" if r.latitude < 0 else " ")
            put(line, STA2, "londeg", f"{int(lo):3d}")
            put(line, STA2, "lonmin", f"{(lo - int(lo)) * 60:7.4f}")
            put(line, STA2, "ew", "E" if r.longitude >= 0 else " ")
            put(line, STA2, "elev", f"{int(round(r.elevation_m)):4d}")
            put(line, STA2, "period", "1.0")
            f.write("".join(line).rstrip() + "\n")
    shift, top = cre_top(stations, cfg)
    if shift:  # CRE: the model top must not lie below a station; the first layer extends up to it
        rows = [rows[0]] + [(z + shift, vp, vs) for z, vp, vs in rows[1:]]
    # hyp1.40 reads CRH and CRE layers with FORMAT(2F5.2): velocity in columns 1-5, layer-top depth in columns 6-10.
    # A wider depth field shifts the digits and truncates the depth (1.17 km was read as 1 km).
    if any(not 0.0 <= r[0] < 99.995 for r in rows):
        raise ValueError("CRH layer tops must lie in [0, 99.99] km below the reference elevation")
    for k, col in (("p", 1), ("s", 2)):
        (out / f"{k}.crh").write_text(f"{k.upper()}MD {k.upper()} model\n" +
                                      "".join(f"{r[col]:5.2f}{r[0]:5.2f}\n" for r in rows))
    ids = {e: i for i, e in enumerate(arr.event_id.drop_duplicates(), 1)}
    lim = cfg["uncertainty_codes_s"]

    def code(r):
        if "uncertainty_s" in arr and pd.notna(r.uncertainty_s):
            return next((i for i, v in enumerate(lim) if r.uncertainty_s <= v), 4)
        return cfg["pick_weight_code"][r.phase]
    with (out / "phases.arc").open("w") as f:
        for eid, g in arr.groupby("event_id", sort=False):
            base = g.t.min().floor("min")
            head = [" "] * 146
            put(head, SUM, "year", f"{base.year:4d}")
            put(head, SUM, "mdhm", base.strftime("%m%d%H%M"))
            put(head, SUM, "id", f"{ids[eid]:10d}")
            f.write("".join(head).rstrip() + "\n")
            for sid, s in g.groupby("station_id", sort=False):
                line = [" "] * 54
                put(line, PHASE, "site", alias[sid])
                put(line, PHASE, "net", "XX")
                put(line, PHASE, "comp3", "HHZ")
                put(line, PHASE, "year", f"{base.year:4d}")
                put(line, PHASE, "mdhm", base.strftime("%m%d%H%M"))
                put(line, PHASE, "pwt", "4")
                put(line, PHASE, "psec", "0")
                put(line, PHASE, "swt", "4")
                for r in s.itertuples():
                    hund = int(round((r.t - base).total_seconds() * 100))
                    if r.phase == "P":
                        put(line, PHASE, "prem", "IP")
                        put(line, PHASE, "pwt", str(code(r)))
                        put(line, PHASE, "psec", f"{hund:5d}")
                    else:
                        put(line, PHASE, "srem", "ES")
                        put(line, PHASE, "swt", str(code(r)))
                        put(line, PHASE, "ssec", f"{hund:5d}")
                f.write("".join(line).rstrip() + "\n")
            term = [" "] * 72
            put(term, {"id": (63, 10)}, "id", f"{ids[eid]:10d}")
            f.write("".join(term).rstrip() + "\n")
    rs, ds, di = cfg["residual_weighting"], cfg["distance_weighting"], cfg["initial_distance_weighting"]
    if cfg["model_type"] == "CRE":  # depths in hyp1.40 are then relative to sea level
        models = [f"CRE 1 'p.crh' {top:.3f} T", f"CRE 2 's.crh' {top:.3f} T"]
        trial = cfg["trial_depth_km"] - cfg["reference_elevation_km"]
    else:
        models, trial = ["CRH 1 'p.crh'", "CRH 2 's.crh'"], cfg["trial_depth_km"]
    cmd = ["200 T 1900 0", "LET 5 2 3 0 0", "H71 1 1 3", "STA 'stations.sta'", *models,
           "SAL 1 2", f"ERR {cfg['timing_error_s']}", f"RMS {rs[0]} {rs[1]} {rs[2]} {rs[3]}",
           f"MIN {cfg['min_stations']}", f"ZTR {trial:.2f} F",
           f"DI1 {di[0]} {di[1]} {di[2]} {di[3]}", f"DIS {ds[0]} {ds[1]} {ds[2]} {ds[3]}",
           "WET " + " ".join(str(w) for w in cfg["weight_factors"]),
           "JUN T", "ERF T", "TOP F", "LST 0 0 0", "KPR 1", "REP F F",
           "COP 3", "CAR 1", "PHS 'phases.arc'", "PRT 'out.prt'", "SUM 'out.sum'", "ARC 'out.arc'", "LOC"]
    (out / "locate.hyp").write_text("\n".join(cmd) + "\n")
    return alias, ids


def parse(out: Path, arr: pd.DataFrame, alias: dict, ids: dict):
    eid = {v: k for k, v in ids.items()}
    station_of = {v: k for k, v in alias.items()}
    events = []
    for line in (out / "out.sum").read_text().splitlines():
        line = line.ljust(146)
        i = int(get(line, SUM, "id"))
        t = pd.Timestamp(f"{get(line, SUM, 'year')}-{get(line, SUM, 'mdhm')[:2]}-{get(line, SUM, 'mdhm')[2:4]}T"
                         f"{get(line, SUM, 'mdhm')[4:6].replace(' ', '0')}:{get(line, SUM, 'mdhm')[6:8].replace(' ', '0')}",
                         tz="UTC") + pd.Timedelta(seconds=implied(get(line, SUM, "sec"), 2))
        lat = float(get(line, SUM, "latdeg")) + implied(get(line, SUM, "latmin"), 2) / 60
        lon = float(get(line, SUM, "londeg")) + implied(get(line, SUM, "lonmin"), 2) / 60
        events.append({"event_id": eid[i], "status": "LOCATED", "origin_time_utc": t.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                       "latitude": -lat if get(line, SUM, "ns") == "S" else lat,
                       "longitude": lon if get(line, SUM, "ew") == "E" else -lon,
                       "depth_km": implied(get(line, SUM, "depth"), 2), "rms_s": implied(get(line, SUM, "rms"), 2),
                       "n_phases": int(get(line, SUM, "nph") or 0), "n_s_phases": int(get(line, SUM, "ns_s") or 0),
                       "gap_deg": float(get(line, SUM, "gap") or "nan"), "erh_km": implied(get(line, SUM, "erh"), 2),
                       "erz_km": implied(get(line, SUM, "erz"), 2), "min_distance_km": float(get(line, SUM, "dmin") or "nan"),
                       "remark": get(line, SUM, "remark2").strip()})
    n_sta = arr.groupby("event_id").station_id.nunique()
    ev = pd.DataFrame(events)
    if len(ev):
        ev["n_stations"] = ev.event_id.map(n_sta)
    key = {(e, s, p): pid for e, s, p, pid in zip(arr.event_id, arr.station_id, arr.phase, arr.pick_id)}
    links, current = [], None
    for line in (out / "out.arc").read_text().splitlines():
        if line[:4].isdigit() and len(line) > 140:                 # event header (summary format)
            current = eid[int(get(line.ljust(146), SUM, "id"))]
            continue
        if current is None or not line.strip() or line.startswith(" " * 5):
            continue
        sid = station_of.get(get(line, PHASE, "site").strip())
        if sid is None:
            continue
        dist = implied(get(line.ljust(80), PHASE, "dist"), 1)
        for ph, rem, res, w in (("P", "prem", "pres", "pwused"), ("S", "srem", "sres", "swused")):
            if get(line, PHASE, rem).strip() and (current, sid, ph) in key:
                links.append({"event_id": current, "pick_id": key[(current, sid, ph)], "station_id": sid, "phase": ph,
                              "residual_s": implied(get(line, PHASE, res), 2),
                              "weight": implied(get(line.ljust(70), PHASE, w), 2), "distance_km": dist})
    return ev, pd.DataFrame(links, columns=["event_id", "pick_id", "station_id", "phase", "residual_s", "weight",
                                            "distance_km"])


def locate(arrivals: pd.DataFrame, stations: pd.DataFrame, model: Path, cfg: dict, out: Path) -> dict:
    arr = arrivals.copy()
    missing = {"event_id", "pick_id", "station_id", "phase", "time_utc"} - set(arr.columns)
    if missing:
        raise ValueError(f"arrivals: missing columns {sorted(missing)}")
    if not set(arr.phase) <= {"P", "S"} or arr.duplicated(["event_id", "station_id", "phase"]).any():
        raise ValueError("arrivals: phase P/S, one row per (event_id, station_id, phase)")
    unknown = set(arr.station_id) - set(stations.station_id)
    if unknown:
        raise ValueError(f"arrivals: stations not in the station table: {sorted(unknown)[:5]}")
    if len(stations) > 9999 or arr.event_id.nunique() > 9_999_999_999:
        raise ValueError("too many stations or events")
    arr["t"] = pd.to_datetime(arr.time_utc, utc=True, format="ISO8601")
    span = arr.groupby("event_id").t.agg(lambda t: (t.max() - t.min().floor("min")).total_seconds()).max()
    if span >= 999.99:
        raise ValueError("an event's arrivals span more than 999 s from its first minute (phase format limit)")
    rows, lvz_changes = crh_rows(model, cfg)
    alias, ids = write_inputs(arr, stations, rows, cfg, out)
    with (out / "hyp.log").open("w") as log:
        proc = subprocess.run([str(BIN)], input="@locate.hyp\nSTO\n", text=True, cwd=out, stdout=log,
                              stderr=subprocess.STDOUT, timeout=3600)
    if proc.returncode != 0 or not (out / "out.sum").exists():
        raise RuntimeError(f"hyp1.40 failed ({proc.returncode}); see {out / 'hyp.log'}")
    ev, links = parse(out, arr, alias, ids)
    if cfg["model_type"] == "CRE" and len(ev):  # hyp1.40 reports CRE depths below sea level
        ev["depth_km"] = (ev.depth_km + cfg["reference_elevation_km"]).round(3)
    located = set(ev.event_id) if len(ev) else set()
    missing_ev = [e for e in ids if e not in located]
    ev = pd.concat([ev, pd.DataFrame({"event_id": missing_ev, "status": "NOT_LOCATED"})], ignore_index=True)
    cols = ["event_id", "status", "origin_time_utc", "latitude", "longitude", "depth_km", "rms_s", "n_phases",
            "n_s_phases", "n_stations", "gap_deg", "erh_km", "erz_km", "min_distance_km", "remark"]
    ev.reindex(columns=cols).sort_values("origin_time_utc").to_csv(out / "events.csv", index=False)
    links.to_csv(out / "arrivals.csv", index=False)
    shift, top = cre_top(stations, cfg)
    return {"events_in": len(ids), "located": len(located), "crh_layers": len(rows), "lvz_clipped": lvz_changes,
            "model_type": cfg["model_type"], "model_top_elevation_km": top if cfg["model_type"] == "CRE" else None,
            "time_resolution_s": 0.01}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arrivals", type=Path, required=True,
                    help="CSV event_id, pick_id, station_id, phase, time_utc[, uncertainty_s]")
    ap.add_argument("--stations", type=Path, required=True, help="CSV station_id, latitude, longitude, elevation_m")
    ap.add_argument("--velocity-model", type=Path, required=True, help="text: depth_km vp_km_s vs_km_s")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=None, help="JSON, merged over the defaults")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    out = a.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()) and not a.overwrite:
        print(f"output directory not empty (use --overwrite): {out}", file=sys.stderr)
        return 2
    result = {"status": "failed", "interface_version": INTERFACE_VERSION, "tool": "HypoInverse"}
    try:
        if not BIN.is_file():
            raise FileNotFoundError(f"{BIN} missing: python seismotools/support/build_native.py --tool hypoinverse")
        cfg = merge(DEFAULT_CONFIG, json.loads(a.config.read_text()) if a.config else {})
        (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
        summary = locate(pd.read_csv(a.arrivals), pd.read_csv(a.stations), a.velocity_model.resolve(), cfg, out)
        result.update(status="success", **summary,
                      inputs={"arrivals": str(a.arrivals), "stations": str(a.stations),
                              "velocity_model": str(a.velocity_model)},
                      outputs=["events.csv", "arrivals.csv", "out.sum", "out.arc", "out.prt", "locate.hyp",
                               "config.json"])
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    (out / "run_result.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    if not a.quiet or result["status"] != "success":
        print(json.dumps({k: v for k, v in result.items() if k != "traceback"}, indent=2, default=str))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
