"""Synthetic recovery test: how far could the catalog's depths and origin times be off if the real velocity
structure differed from the location model within a plausible range?

A velocity model that is too fast or slow on average moves every depth and origin time together; the
catalog's own picks cannot show it (the coupled hypocentre–velocity problem). What the station geometry
and the picks can show is how large such an error would be. For a sample of events, at their catalog
hypocentres and with the stations and phases actually picked, arrival times are computed in another
plausible model B, pick noise is added, and the events are located with the location model A exactly as
declared. The difference between the located and the true hypocentres is the bias that structure like B
would cause:

- B = A: the error from the station geometry and pick noise alone;
- A with velocities ±5 %, A with Vp/Vs ±0.05, A in the other representation (steps vs a linear gradient
  between its nodes), A with its layer tops shifted ±0.5 km, and the regional CRUST1.0 and LITHO1.0 columns.

The spread of the median biases over these models is the range within which the catalog's depths and
origin times are uncertain for this geometry. It is reported, never judged: it says how far a plausible
model error could move the catalog, not that it has.

The location model is declared in ``location_setup`` (run.py ``--location-setup``):
``{"model": [[top_km_below_sea_level, vp, vs], ...], "layering": "step" | "linear",
"reference_elevation_km": z, ...}``.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from .checks import Check, Data, _skip
from .ensemble import LOCATE, _model_rows
from .velocity import regional_models

RECOVERY_DEFAULTS = {"recovery_events": 100, "recovery_min_phases": 8, "recovery_noise_s": {"P": 0.05, "S": 0.10},
                     "recovery_scale": 0.05, "recovery_vpvs_step": 0.05, "recovery_top_shift_km": 0.5,
                     "recovery_workers": 8, "recovery_timeout_s": 3600, "recovery_seed": 0}


# ------------------------------------------------------------------ 1-D layered travel times

def _layers(rows: list, linear: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Layer tops (km below sea level) and velocities; a linear model is densified into 0.1 km steps."""
    tops = np.array([r[0] for r in rows], float)
    vp = np.array([r[1] for r in rows], float)
    vs = np.array([r[2] for r in rows], float)
    if linear and len(tops) > 1:
        z = np.arange(tops[0], tops[-1] + 1e-9, 0.1)
        return z, np.interp(z, tops, vp), np.interp(z, tops, vs)
    return tops, vp, vs


def _thicknesses(tops: np.ndarray, z1: float, z2: float) -> tuple[np.ndarray, np.ndarray]:
    """Thickness of every layer between depths z1 < z2 (the top layer extends upwards, the last downwards)."""
    edges = np.r_[-1e9, tops[1:], 1e9]
    lo, hi = np.maximum(edges[:-1], z1), np.minimum(edges[1:], z2)
    h = np.clip(hi - lo, 0.0, None)
    return h, np.arange(len(tops))


def first_arrival(tops: np.ndarray, v: np.ndarray, zs: float, zr: float, dist: float) -> float:
    """First-arrival time (s) from a source at depth zs to a receiver at depth zr (km below sea level, zr may be
    negative), epicentral distance dist (km), in flat step layers: the direct wave and every head wave."""
    a, b = (zr, zs) if zr <= zs else (zs, zr)
    h, _ = _thicknesses(tops, a, b)
    use = h > 0
    hv, vv = h[use], v[use]
    best = np.inf
    vmax = vv.max() if len(vv) else v[0]
    # direct wave: bisection on the ray parameter
    if dist < 1e-6:
        best = float(np.sum(hv / vv))
    elif hv.sum() < 1e-6:  # source and receiver at the same depth: a horizontal ray in that layer
        best = dist / float(v[max(int(np.searchsorted(tops, a, side="right")) - 1, 0)])
    else:
        lo, hi = 0.0, (1.0 - 1e-9) / vmax
        for _ in range(60):
            p = 0.5 * (lo + hi)
            x = np.sum(hv * p * vv / np.sqrt(1.0 - (p * vv) ** 2))
            lo, hi = (p, hi) if x < dist else (lo, p)
        p = 0.5 * (lo + hi)
        x = np.sum(hv * p * vv / np.sqrt(1.0 - (p * vv) ** 2))
        if abs(x - dist) < 0.01 * max(dist, 1.0):
            best = float(np.sum(hv / (vv * np.sqrt(1.0 - (p * vv) ** 2))))
    # head waves along each interface below both ends
    for k in range(1, len(tops)):
        zk = tops[k]
        if zk <= b or v[k] <= v[:k].max():
            continue
        p = 1.0 / v[k]
        t, x0 = 0.0, 0.0
        for z1 in (zs, zr):
            hh, _ = _thicknesses(tops[:k], z1, zk)
            vv2 = v[:k]
            q = np.sqrt(np.clip(1.0 - (p * vv2) ** 2, 1e-12, None))
            t += np.sum(hh * q / vv2)
            x0 += np.sum(hh * p * vv2 / q)
        if dist >= x0:
            best = min(best, dist * p + t)
    return best


# ------------------------------------------------------------------ models

def _alternatives(rows: list, linear: bool, d: Data, c: dict) -> dict[str, tuple[list, bool]]:
    s, dv, dz = c["recovery_scale"], c["recovery_vpvs_step"], c["recovery_top_shift_km"]
    out = {"same model": (rows, linear),
           f"velocities +{s:.0%}": ([(z, p * (1 + s), q * (1 + s)) for z, p, q in rows], linear),
           f"velocities −{s:.0%}": ([(z, p * (1 - s), q * (1 - s)) for z, p, q in rows], linear),
           f"Vp/Vs +{dv}": ([(z, p, p / (p / q + dv)) for z, p, q in rows], linear),
           f"Vp/Vs −{dv}": ([(z, p, p / (p / q - dv)) for z, p, q in rows], linear),
           "other representation": (rows, not linear),
           f"layer tops +{dz} km": ([(z + (dz if i else 0.0), p, q) for i, (z, p, q) in enumerate(rows)], linear),
           f"layer tops −{dz} km": ([(z - (dz if i else 0.0), p, q) for i, (z, p, q) in enumerate(rows)], linear)}
    try:
        ev = d.events.dropna(subset=["latitude"])
        reg = regional_models(np.r_[d.stations.latitude, ev.latitude.median()], np.r_[d.stations.longitude, ev.longitude.median()])
        for k in ("crust1", "litho1"):
            out[k.upper().replace("1", "1.0")] = (reg[k]["rows"], False)
    except Exception:  # the regional columns are optional
        pass
    return out


# ------------------------------------------------------------------ the test

def _sample(d: Data, c: dict) -> pd.DataFrame:
    p = d.picks
    n = p.groupby("event_id").size()
    ev = d.events[d.events.event_id.isin(n[n >= c["recovery_min_phases"]].index)].dropna(subset=["latitude", "longitude", "depth_km"])
    if len(ev) <= c["recovery_events"]:
        return ev
    idx = np.unique(np.linspace(0, len(ev) - 1, c["recovery_events"]).round().astype(int))
    return ev.sort_values("time").iloc[idx]  # spread over time


def _locate(work: Path, name: str, arrivals: pd.DataFrame, stations: pd.DataFrame, rows: list, linear: bool,
            ref_elev: float, c: dict) -> pd.DataFrame | None:
    tops, vp, vs = _layers(rows, linear)
    model = _model_rows(list(zip(tops, vp, vs)), ref_elev)
    (work / f"{name}_model.txt").write_text("".join(f"{z:.3f} {a:.3f} {b:.3f}\n" for z, a, b in model))
    (work / f"{name}_config.json").write_text(json.dumps({"reference_elevation_km": ref_elev, "velocity_layering": "step",
                                                          "grid_depth_km": [-3.0, 40.0]}))
    arrivals.to_csv(work / f"{name}_arrivals.csv", index=False)
    cmd = [sys.executable, "-I", str(LOCATE), "--arrivals", str(work / f"{name}_arrivals.csv"), "--stations", str(work / "stations.csv"),
           "--velocity-model", str(work / f"{name}_model.txt"), "--config", str(work / f"{name}_config.json"),
           "--output-dir", str(work / name), "--workers", str(c["recovery_workers"]), "--quiet", "--overwrite"]
    try:
        subprocess.run(cmd, check=False, capture_output=True, timeout=c["recovery_timeout_s"])
    except subprocess.TimeoutExpired:
        return None
    f = work / name / "events.csv"
    if not f.is_file():
        return None
    ev = pd.read_csv(f)
    ev = ev[ev.status == "LOCATED"].copy()
    ev["depth_bsl"] = ev.depth_km - ref_elev
    ev["t"] = (pd.to_datetime(ev.origin_time_utc, utc=True, format="ISO8601") - pd.Timestamp(0, tz="UTC")).dt.total_seconds()
    return ev


def recovery_test(d: Data, c: dict, workdir: Path | None = None) -> Check:
    c = {**RECOVERY_DEFAULTS, **c}
    expected = "reported: median depth and origin-time bias of synthetic events located with the declared model, for arrival times computed in plausible other models"
    setup = c.get("location_setup") or {}
    if not setup.get("model"):
        return _skip("recovery_test", "space", "km", expected, 0, "no location model declared (--location-setup with \"model\")")
    rows = [tuple(map(float, r[:3])) for r in setup["model"]]
    linear = setup.get("layering", "step") == "linear"
    ref_elev = float(setup.get("reference_elevation_km", math.ceil(float(d.stations.elevation_m.max()) / 100.0) / 10.0))
    sample = _sample(d, c)
    if len(sample) < 20:
        return _skip("recovery_test", "space", "km", expected, len(sample), f"{len(sample)} events with ≥ {c['recovery_min_phases']} picks")
    rng = np.random.default_rng(c["recovery_seed"])
    picks = d.picks[d.picks.event_id.isin(sample.event_id)].drop_duplicates(["event_id", "station_id", "phase"])
    st = d.stations.set_index("station_id")
    tmp = tempfile.TemporaryDirectory() if workdir is None else None
    work = Path(tmp.name) if tmp else Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    d.stations[["station_id", "latitude", "longitude", "elevation_m"]].to_csv(work / "stations.csv", index=False)
    truth = sample.set_index("event_id")
    results = {}
    for name, (brow, blin) in _alternatives(rows, linear, d, c).items():
        tops, vp, vs = _layers(brow, blin)
        times = []
        for r in picks.itertuples():
            e = truth.loc[r.event_id]
            v = vp if r.phase == "P" else vs
            zr = -float(st.loc[r.station_id, "elevation_m"]) / 1000.0
            tt = first_arrival(tops, v, float(e.depth_km), zr, float(r.epi_km))
            if not np.isfinite(tt):
                continue
            noise = rng.normal(0.0, c["recovery_noise_s"].get(r.phase, 0.1))
            times.append((r.event_id, r.station_id, r.phase, float(e.time) + tt + noise))
        arr = pd.DataFrame(times, columns=["event_id", "station_id", "phase", "t"])
        arr = pd.DataFrame({"event_id": arr.event_id, "pick_id": np.arange(len(arr)).astype(str), "station_id": arr.station_id,
                            "phase": arr.phase, "time_utc": pd.to_datetime(arr.t, unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")})
        key = "m" + str(len(results))
        loc = _locate(work, key, arr, d.stations, rows, linear, ref_elev, c)
        if loc is None or loc.empty:
            results[name] = None
            continue
        true = truth[["time", "depth_km", "x", "y"]].rename(columns={"time": "t_true", "depth_km": "z_true", "x": "x_true", "y": "y_true"})
        j = loc.set_index("event_id")[["depth_bsl", "t", "latitude", "longitude"]].join(true, how="inner")
        from .io import local_km
        lx, ly = local_km(j.latitude, j.longitude, d.lat0, d.lon0)
        dz = j.depth_bsl - j.z_true
        results[name] = {"events": int(len(j)), "depth_bias_km": round(float(np.median(dz)), 3),
                         "depth_mad_km": round(float(np.median(np.abs(dz - np.median(dz)))), 3),
                         "time_bias_s": round(float(np.median(j.t - j.t_true)), 3),
                         "horizontal_median_km": round(float(np.median(np.hypot(lx - j.x_true, ly - j.y_true))), 3)}
    if tmp:
        tmp.cleanup()
    ok = {k: v for k, v in results.items() if v}
    if "same model" not in ok or len(ok) < 3:
        return _skip("recovery_test", "space", "km", expected, len(ok), "the synthetic locations failed for most models")
    others = {k: v for k, v in ok.items() if k != "same model"}
    dz = [v["depth_bias_km"] for v in others.values()]
    dt = [v["time_bias_s"] for v in others.values()]
    return Check("recovery_test", "space", float(max(abs(min(dz)), abs(max(dz)))), "km", expected, len(sample), False, None,
                 {"depth_bias_range_km": [round(min(dz), 3), round(max(dz), 3)],
                  "time_bias_range_s": [round(min(dt), 3), round(max(dt), 3)],
                  "geometry_and_noise_only": ok["same model"], "models": results,
                  "note": "the range is how far depths and origin times would move if the structure were like one of the "
                          "alternatives; it is not an estimate of the catalog's actual error"})
