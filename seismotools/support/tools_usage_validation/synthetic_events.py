#!/usr/bin/env python3
"""Shared synthetic known-answer case for association and location validations.

Uniform half-space (straight rays, analytic travel times): every tool's
travel-time table can be checked against the exact answer. Stations at
elevation 0 on a 40 x 40 km area around (lat0, lon0); events in the central
box, separated in time. Picks carry the true ``event_id`` ('' for false picks).

Library use: ``make_case(**options) -> dict`` of DataFrames; CLI: writes
stations.csv, events.csv, picks.csv and velocity_model.txt to --out.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Proj


def travel_time(dist_km: np.ndarray, depth_km: np.ndarray, v: float) -> np.ndarray:
    return np.hypot(dist_km, depth_km) / v


def make_case(seed: int = 0, n_stations: int = 15, n_events: int = 40, vp: float = 6.0, vs: float = 3.46,
              lat0: float = 35.5, lon0: float = -97.0, station_half_km: float = 20.0, event_half_km: float = 8.0,
              depth_km: tuple = (2.0, 12.0), t0: str = "2020-01-01T00:00:00Z", spacing_s: float = 20.0,
              noise_s: float = 0.0, false_per_station: int = 0, drop_frac: float = 0.0,
              outlier_s: float | None = None) -> dict:
    rng = np.random.default_rng(seed)
    proj = Proj(proj="aeqd", lon_0=lon0, lat_0=lat0, datum="WGS84", units="km")
    sx, sy = rng.uniform(-station_half_km, station_half_km, (2, n_stations))
    slon, slat = proj(sx, sy, inverse=True)
    stations = pd.DataFrame({"station_id": [f"SY.S{i:02d}" for i in range(n_stations)], "latitude": slat,
                             "longitude": slon, "elevation_m": 0.0})
    ex, ey = rng.uniform(-event_half_km, event_half_km, (2, n_events))
    ez = rng.uniform(*depth_km, n_events)
    elon, elat = proj(ex, ey, inverse=True)
    origin = pd.Timestamp(t0) + pd.to_timedelta(spacing_s * (1 + np.arange(n_events))
                                                + rng.uniform(-2, 2, n_events), unit="s")
    events = pd.DataFrame({"event_id": [f"syn{i:03d}" for i in range(n_events)],
                           "origin_time_utc": origin.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                           "latitude": elat, "longitude": elon, "depth_km": ez, "x_km": ex, "y_km": ey})
    rows = []
    for i in range(n_events):
        d = np.hypot(sx - ex[i], sy - ey[i])
        for phase, v in (("P", vp), ("S", vs)):
            tt = travel_time(d, np.full_like(d, ez[i]), v) + rng.normal(0, noise_s, n_stations) * (noise_s > 0)
            keep = rng.uniform(size=n_stations) >= drop_frac
            for j in np.where(keep)[0]:
                rows.append((stations.station_id[j], phase, origin[i] + pd.Timedelta(seconds=float(tt[j])),
                             events.event_id[i]))
    if outlier_s is not None and rows:          # one large error on the first event's first pick
        s, p, t, e = rows[0]
        rows[0] = (s, p, t + pd.Timedelta(seconds=outlier_s), e)
    t_end = origin[-1] + pd.Timedelta(seconds=spacing_s)
    for st in stations.station_id:
        for _ in range(false_per_station):
            t = pd.Timestamp(t0) + pd.Timedelta(seconds=float(rng.uniform(0, (t_end - pd.Timestamp(t0)).total_seconds())))
            rows.append((st, rng.choice(["P", "S"]), t, ""))
    picks = pd.DataFrame(rows, columns=["station_id", "phase", "t", "event_id"]).sort_values("t").reset_index(drop=True)
    picks.insert(0, "pick_id", [f"pk{i:06d}" for i in range(len(picks))])
    picks["time_utc"] = picks.t.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    picks["probability"] = np.where(picks.event_id != "", 0.9, 0.5)
    picks = picks.drop(columns="t")[["pick_id", "station_id", "phase", "time_utc", "probability", "event_id"]]
    return {"stations": stations, "events": events, "picks": picks,
            "velocity_model": f"# depth_km vp_km_s vs_km_s (uniform half-space)\n0.0 {vp} {vs}\n",
            "vp": vp, "vs": vs, "projection_center": [lon0, lat0]}


def write_case(case: dict, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    for k in ("stations", "events", "picks"):
        case[k].to_csv(out / f"{k}.csv", index=False)
    (out / "velocity_model.txt").write_text(case["velocity_model"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--noise-s", type=float, default=0.0)
    ap.add_argument("--false-per-station", type=int, default=0)
    ap.add_argument("--drop-frac", type=float, default=0.0)
    a = ap.parse_args()
    write_case(make_case(seed=a.seed, noise_s=a.noise_s, false_per_station=a.false_per_station,
                         drop_frac=a.drop_frac), a.out)


if __name__ == "__main__":
    main()
