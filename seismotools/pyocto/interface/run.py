#!/usr/bin/env python3
"""Associate phase picks into events with PyOcto (interface version 1).

PyOcto (Münchmeyer 2024) partitions space-time into octree nodes and keeps
those whose predicted arrivals explain enough picks. This adapter builds the
1-D travel-time table from a layered model, projects stations, runs the
associator and writes the seismotools association contract. See
interface/README.md.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve()
SITE = HERE.parents[1] / "runtime" / "build" / "site"
INTERFACE_VERSION = 1
DEFAULT_CONFIG = {
    "region": None,                     # required: {latitude: [a, b], longitude: [a, b], depth_km: [top, bottom]}
    "reference_elevation_km": 0.0,      # depth datum; station z = reference - elevation
    "velocity_layering": "step",        # rows are constant layers (step) or nodes of a linear profile
    "travel_time_table": {"delta_km": 0.25, "max_distance_km": None, "max_depth_km": None, "tolerance_s": 2.0,
                          "association_cutoff_distance_km": None, "location_cutoff_distance_km": None},
    "time_before_s": 300.0,             # overlap of consecutive time slices (> largest travel time)
    "associator": {},                   # OctoAssociator keyword arguments (upstream defaults otherwise)
}


def merge(base: dict, user: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in user.items():
        if k not in out:
            raise ValueError(f"unknown config key: {k}")
        out[k] = {**out[k], **v} if isinstance(out[k], dict) and isinstance(v, dict) else v
    if not out["region"]:
        raise ValueError("config.region is required: {latitude: [a, b], longitude: [a, b], depth_km: [top, bottom]}")
    if out["region"]["depth_km"][0] < 0:
        raise ValueError("region.depth_km must start at >= 0 (PyOcto 1-D models do not search above the datum)")
    if out["velocity_layering"] not in ("step", "linear"):
        raise ValueError("velocity_layering must be step or linear")
    return out


def model_frame(path: Path, layering: str, eps_km: float):
    """PyOcto interpolates linearly between rows; for step layers add a node just above each top."""
    import pandas as pd
    rows = []
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            rows.append(tuple(map(float, line.split()[:3])))
    if not rows or any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("velocity model: need rows of increasing depth_km vp_km_s vs_km_s")
    out = []
    for i, (z, vp, vs) in enumerate(rows):
        if layering == "step" and i:
            out.append((z - eps_km, rows[i - 1][1], rows[i - 1][2]))
        out.append((z, vp, vs))
    return pd.DataFrame(out, columns=["depth", "vp", "vs"]), rows


def associate(picks, stations, model_path: Path, cfg: dict, out: Path, workers: int) -> dict:
    import numpy as np
    import pandas as pd
    sys.path.insert(0, str(SITE))
    import pyocto

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
    reg, tt = cfg["region"], cfg["travel_time_table"]
    ref = float(cfg["reference_elevation_km"])
    model, rows = model_frame(model_path, cfg["velocity_layering"], min(1e-3, tt["delta_km"] / 10))
    assoc_kw = dict(cfg["associator"])
    assoc_kw.setdefault("n_threads", workers)
    # station projection first (the associator CRS is a local transverse Mercator about the region)
    probe = pyocto.OctoAssociator.from_area(lat=tuple(reg["latitude"]), lon=tuple(reg["longitude"]),
                                            zlim=tuple(reg["depth_km"]), velocity_model=pyocto.VelocityModel0D(
                                                p_velocity=6.0, s_velocity=3.5, tolerance=1.0),
                                            time_before=cfg["time_before_s"])
    st = stations[["station_id", "latitude", "longitude", "elevation_m"]].rename(
        columns={"station_id": "id", "elevation_m": "elevation"}).copy()
    st = probe.transform_stations(st)
    st["z"] = ref - st.elevation / 1000.0                      # km below the datum (negative above it)
    corners = [(x, y) for x in probe.xlim for y in probe.ylim]
    max_dist = tt["max_distance_km"] or float(max(np.hypot(x - st.x, y - st.y).max() for x, y in corners)) + 10.0
    max_depth = tt["max_depth_km"] or float(reg["depth_km"][1]) + 5.0
    table = out / "travel_time_table.bin"
    pyocto.VelocityModel1D.create_model(model, tt["delta_km"], max_dist, max_depth, table)
    vm = pyocto.VelocityModel1D(table, tolerance=tt["tolerance_s"],
                                association_cutoff_distance=tt["association_cutoff_distance_km"],
                                location_cutoff_distance=tt["location_cutoff_distance_km"],
                                surface_p_velocity=rows[0][1], surface_s_velocity=rows[0][2])
    associator = pyocto.OctoAssociator.from_area(lat=tuple(reg["latitude"]), lon=tuple(reg["longitude"]),
                                                 zlim=tuple(reg["depth_km"]), velocity_model=vm,
                                                 time_before=cfg["time_before_s"], **assoc_kw)
    p = picks.reset_index(drop=True)
    t = pd.to_datetime(p.time_utc, utc=True, format="ISO8601")
    oc_picks = pd.DataFrame({"station": p.station_id, "phase": p.phase,
                             "time": (t - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds()})
    events, assign = associator.associate(oc_picks, st[["id", "x", "y", "z"]])
    ev = associator.transform_events(events) if len(events) else events
    if len(assign):
        assign = assign[["event_idx", "pick_idx", "residual"]]
    a = assign.merge(p[["pick_id", "phase"]], left_on="pick_idx", right_index=True) if len(assign) else None
    counts = (a.groupby("event_idx").phase.value_counts().unstack(fill_value=0)
              if a is not None else pd.DataFrame(columns=["P", "S"]))
    rows_out = []
    for r in ev.itertuples() if len(ev) else []:
        c = counts.loc[r.idx] if r.idx in counts.index else {}
        n_p, n_s = int(c.get("P", 0)), int(c.get("S", 0))
        rows_out.append({"event_index": int(r.idx),
                         "time_utc": pd.Timestamp(r.time, unit="s", tz="UTC").strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                         "latitude": r.latitude, "longitude": r.longitude, "depth_km": r.depth,
                         "num_picks": n_p + n_s, "num_p_picks": n_p, "num_s_picks": n_s, "x_km": r.x, "y_km": r.y})
    ev_out = pd.DataFrame(rows_out, columns=["event_index", "time_utc", "latitude", "longitude", "depth_km",
                                             "num_picks", "num_p_picks", "num_s_picks", "x_km", "y_km"])
    ev_out.sort_values("time_utc").to_csv(out / "events.csv", index=False)
    who = dict(zip(assign.pick_idx, assign.event_idx)) if len(assign) else {}
    res = dict(zip(assign.pick_idx, assign.residual)) if len(assign) else {}
    pd.DataFrame({"pick_index": p.index, "pick_id": p.pick_id,
                  "event_index": [who.get(i, "") for i in p.index], "assignment_probability": "",
                  "assignment_status": ["assigned" if i in who else "unassigned" for i in p.index],
                  "residual_s": [res.get(i, "") for i in p.index]}).to_csv(out / "assignments.csv", index=False)
    return {"picks": len(p), "events": len(ev_out), "assigned_picks": len(who),
            "travel_time_table": {"delta_km": tt["delta_km"], "max_distance_km": max_dist, "max_depth_km": max_depth},
            "pyocto_version": getattr(pyocto, "__version__", "0.1.9")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--picks", type=Path, required=True, help="CSV pick_id, station_id, phase, time_utc[, probability]")
    ap.add_argument("--stations", type=Path, required=True, help="CSV station_id, latitude, longitude, elevation_m")
    ap.add_argument("--velocity-model", type=Path, required=True, help="text: depth_km vp_km_s vs_km_s")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True, help="JSON; must contain region")
    ap.add_argument("--workers", type=int, default=8, help="associator threads (config associator.n_threads wins)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    out = a.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()) and not a.overwrite:
        print(f"output directory not empty (use --overwrite): {out}", file=sys.stderr)
        return 2
    result = {"status": "failed", "interface_version": INTERFACE_VERSION, "tool": "pyocto"}
    try:
        import pandas as pd
        cfg = merge(DEFAULT_CONFIG, json.loads(a.config.read_text()))
        (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
        summary = associate(pd.read_csv(a.picks), pd.read_csv(a.stations), a.velocity_model, cfg, out, a.workers)
        result.update(status="success", **summary,
                      inputs={"picks": str(a.picks), "stations": str(a.stations),
                              "velocity_model": str(a.velocity_model)},
                      outputs=["events.csv", "assignments.csv", "travel_time_table.bin", "config.json"])
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    (out / "run_result.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    if not a.quiet or result["status"] != "success":
        print(json.dumps({k: v for k, v in result.items() if k != "traceback"}, indent=2, default=str))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
