#!/usr/bin/env python3
"""Check depths and origin times against evidence that does not come from the velocity model.

Three measurements, from the catalog and its picks:

1. Near-station S−P depths. The ratio K = Vp·Vs/(Vp−Vs) is taken from stations farther than twice the focal depth
   (S−P time against hypocentral distance); at stations closer than one focal depth, K·(S−P) is then almost the
   hypocentral distance, so it gives the depth with little dependence on the velocity model. Reported: the median
   and spread of (S−P depth − catalog depth) over events, and the same in thirds of the catalog's depth range.
   An offset that is the same at all depths points to the datum or a near-surface layer; one that grows with depth
   points to the velocity of the crust.
2. Vp/Vs from near stations only (Wadati: S−P against P travel time, per event with its own origin time), against
   the same from all stations. Distant first arrivals are refracted and bias the all-station value.
3. With --candidates (catalogs of the same events located with other models): the range of the median depth and
   origin time over the candidates, relative to this catalog: a lower bound on the uncertainty from the model.

The output gives directions and ranges. Do not treat any number as a target to reach: K and the near-station
geometry have their own errors, and the size of a depth correction is not the size of this offset.

Usage:
    depth_time_check.py --checker $CHECKER_PATH --catalog catalog.csv --picks picks.csv --stations <StationXML or CSV>
        [--candidates cat_modelA.csv cat_modelB.csv ...] [--output check.json]
Depths are km below sea level (the output convention); station elevations come from the station metadata.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def epoch(s: pd.Series) -> np.ndarray:
    return pd.to_datetime(s, utc=True, format="mixed").astype("int64").to_numpy() / 1e9


def load(catalog: Path, picks: Path, stations: Path, checker: Path):
    sys.path.insert(0, str(Path(checker) / "source"))
    from catalog_checker.io import read_stations  # noqa: E402
    st = read_stations(stations)
    cat = pd.read_csv(catalog, dtype={"event_id": str})
    if "status" in cat:
        cat = cat[cat.status.astype(str) != "rejected"]
    cat = cat.dropna(subset=["latitude", "longitude", "depth_km"]).copy()
    cat["t0"] = epoch(cat.origin_time_utc)
    pk = pd.read_csv(picks, dtype={"event_id": str})
    pk = pk[pk.event_id.isin(cat.event_id) & pk.phase.isin(["P", "S"])].copy()
    pk["t"] = epoch(pk.time_utc)
    pk = pk.groupby(["event_id", "station_id", "phase"]).t.min().unstack("phase").dropna().reset_index()
    pk = pk.merge(cat[["event_id", "latitude", "longitude", "depth_km", "t0"]], on="event_id")
    pk = pk.merge(st[["station_id", "latitude", "longitude", "elevation_m"]].rename(
        columns={"latitude": "slat", "longitude": "slon"}), on="station_id")
    lat0 = np.radians(pk.latitude.to_numpy())
    pk["delta_km"] = 111.195 * np.hypot(pk.slat - pk.latitude, (pk.slon - pk.longitude) * np.cos(lat0))
    pk["z_km"] = pk.depth_km + pk.elevation_m / 1000.0  # source depth below the station
    pk["sp"] = pk.S - pk.P
    return cat, pk[(pk.sp > 0) & (pk.z_km > 0)]


def sp_depths(pk: pd.DataFrame) -> dict:
    far = pk[pk.delta_km > 2 * pk.z_km]
    if len(far) < 30:
        return {"not_evaluated": "fewer than 30 S−P times at stations farther than twice the focal depth"}
    k = float(np.median(np.hypot(far.delta_km, far.z_km) / far.sp))
    near = pk[pk.delta_km < pk.z_km].copy()
    if len(near) < 10:
        return {"K_km_s": round(k, 3), "not_evaluated": "fewer than 10 S−P times at stations closer than one focal depth"}
    near["h"] = np.sqrt(np.clip((k * near.sp) ** 2 - near.delta_km ** 2, 0, None)) - near.elevation_m / 1000.0
    ev = near.groupby("event_id").agg(diff=("h", "median"), depth=("depth_km", "first"))
    ev["diff"] = ev["diff"] - ev.depth
    out = {"K_km_s": round(k, 3), "events": int(len(ev)), "station_pairs": int(len(near)),
           "median_offset_km": round(float(ev["diff"].median()), 2),
           "iqr_km": [round(float(ev["diff"].quantile(0.25)), 2), round(float(ev["diff"].quantile(0.75)), 2)]}
    if len(ev) >= 30:
        bins = pd.qcut(ev.depth, 3, duplicates="drop")
        out["by_depth_third"] = [{"catalog_depth_km": [round(float(b.left), 1), round(float(b.right), 1)],
                                  "median_offset_km": round(float(g["diff"].median()), 2), "events": int(len(g))}
                                 for b, g in ev.groupby(bins, observed=True)]
    m = out["median_offset_km"]
    out["reading"] = ("near-station S−P times put the events deeper than the catalog" if m > 0.5 else
                      "near-station S−P times put the events shallower than the catalog" if m < -0.5 else
                      "near-station S−P depths agree with the catalog within 0.5 km") + \
        f" (median {m:+.2f} km over {len(ev)} events); this is a direction, not the size of a correction"
    if "by_depth_third" in out and len(out["by_depth_third"]) == 3:
        a, c = out["by_depth_third"][0]["median_offset_km"], out["by_depth_third"][2]["median_offset_km"]
        out["reading"] += ("; the offset is about the same at all depths (datum or near-surface layer)" if abs(c - a) < 0.5
                           else "; the offset changes with depth (velocity of the crust)")
    return out


def wadati(pk: pd.DataFrame, near_only: bool) -> dict:
    sel = pk[pk.delta_km < 2 * pk.z_km] if near_only else pk
    vals = []
    for _, g in sel.groupby("event_id"):
        if len(g) < 3:
            continue
        x, y = (g.P - g.P.min()).to_numpy(), g.sp.to_numpy()  # slope of S−P against P time = Vp/Vs − 1
        if np.ptp(x) < 0.3:
            continue
        vals.append(np.polyfit(x, y, 1)[0] + 1.0)
    if len(vals) < 10:
        return {"not_evaluated": "fewer than 10 events with three or more stations"}
    v = np.array(vals)
    return {"events": int(len(v)), "median_vp_vs": round(float(np.median(v)), 3),
            "iqr": [round(float(np.quantile(v, 0.25)), 3), round(float(np.quantile(v, 0.75)), 3)]}


def candidates(cat: pd.DataFrame, paths: list[Path]) -> dict:
    rows = []
    for p in paths:
        c = pd.read_csv(p, dtype={"event_id": str})
        if "status" in c:
            c = c[c.status.astype(str) != "rejected"]
        m = cat.merge(c[["event_id", "depth_km", "origin_time_utc"]], on="event_id", suffixes=("", "_c"))
        if len(m) < 10:
            continue
        rows.append({"catalog": Path(p).name, "events": int(len(m)),
                     "median_depth_change_km": round(float((m.depth_km_c - m.depth_km).median()), 2),
                     "median_origin_time_change_s": round(float(np.median(epoch(m.origin_time_utc_c) - m.t0)), 3)})
    if not rows:
        return {"not_evaluated": "no candidate shares 10 events with the catalog"}
    dz = [r["median_depth_change_km"] for r in rows] + [0.0]
    dt = [r["median_origin_time_change_s"] for r in rows] + [0.0]
    return {"per_candidate": rows, "depth_range_km": [min(dz), max(dz)], "origin_time_range_s": [min(dt), max(dt)],
            "reading": "report these ranges as the model uncertainty; they do not say which model is right"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checker", type=Path, default=os.environ.get("CHECKER_PATH"))
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--picks", type=Path, required=True)
    ap.add_argument("--stations", type=Path, required=True)
    ap.add_argument("--candidates", type=Path, nargs="*", default=[])
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    if a.checker is None:
        ap.error("give --checker (the CHECKER_PATH of the task)")
    cat, pk = load(a.catalog, a.picks, a.stations, a.checker)
    report = {"sp_depths": sp_depths(pk), "vp_vs_near_stations": wadati(pk, True), "vp_vs_all_stations": wadati(pk, False)}
    if a.candidates:
        report["model_range"] = candidates(cat, a.candidates)
    text = json.dumps(report, indent=1)
    if a.output:
        a.output.write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
