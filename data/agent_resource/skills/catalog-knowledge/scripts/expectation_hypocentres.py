#!/usr/bin/env python3
"""Report the expectation hypocentre for events whose depth the data do not constrain.

For an event without depth constraint the location PDF is flat in depth, and its maximum-likelihood point ends
at the edge of the search grid: many such events pile at one depth. The expectation hypocentre (the mean of
the PDF) is the standard value to report for them, with its uncertainty. This is a correction of how the
location is reported, not a change of the data.

Input: the ``events.csv`` of the NonLinLoc interface (``latitude, longitude, depth_km`` of the maximum-likelihood
point, ``x_km, y_km`` and ``expect_x_km, expect_y_km, expect_depth_km`` in the same frame, ``erz_km``). An
event is treated as unconstrained in depth when its maximum-likelihood depth lies within --edge-km of the
shallowest or deepest maximum-likelihood depth of the located events (or of --grid-top / --grid-bottom when
given, in the same frame as ``depth_km``), or when its ``erz_km`` exceeds --max-erz-km.

The change for each event is the difference expectation minus maximum likelihood, in that frame. With
--catalog it is added to the catalog's latitude, longitude and depth_km of the same event_id, so the catalog's
own depth datum is kept. Origin times are not changed (the expectation has none). The events changed are listed
with their changes in --changes.

Usage:
    expectation_hypocentres.py --events nll/events.csv [--catalog catalog.csv --output catalog_expectation.csv]
        [--edge-km 0.5] [--max-erz-km 10] [--grid-top Z --grid-bottom Z] --changes changes.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def select(ev: pd.DataFrame, edge_km: float, max_erz: float | None, top: float | None, bottom: float | None) -> pd.Series:
    z = ev.depth_km
    top = float(z.min()) if top is None else top
    bottom = float(z.max()) if bottom is None else bottom
    sel = (z <= top + edge_km) | (z >= bottom - edge_km)
    if max_erz is not None and "erz_km" in ev:
        sel |= ev.erz_km > max_erz
    return sel


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--events", type=Path, required=True, help="events.csv of the NonLinLoc interface")
    ap.add_argument("--catalog", type=Path, help="catalog to update by event_id")
    ap.add_argument("--output", type=Path, help="updated catalog (with --catalog)")
    ap.add_argument("--changes", type=Path, required=True, help="list of the events changed")
    ap.add_argument("--edge-km", type=float, default=0.5, help="distance to the depth edge counted as 'at the edge'")
    ap.add_argument("--max-erz-km", type=float, default=None, help="also treat events with a larger depth error as unconstrained")
    ap.add_argument("--grid-top", type=float, help="top of the depth search, same frame as depth_km")
    ap.add_argument("--grid-bottom", type=float, help="bottom of the depth search, same frame as depth_km")
    a = ap.parse_args()
    ev = pd.read_csv(a.events)
    if "status" in ev:
        ev = ev[ev.status == "LOCATED"]
    need = {"x_km", "y_km", "expect_x_km", "expect_y_km", "expect_depth_km", "depth_km", "latitude", "longitude"}
    if not need <= set(ev.columns):
        ap.error(f"events.csv lacks {sorted(need - set(ev.columns))}")
    ev = ev[select(ev, a.edge_km, a.max_erz_km, a.grid_top, a.grid_bottom)].copy()
    lat0 = np.radians(ev.latitude)
    ev["d_east_km"] = ev.expect_x_km - ev.x_km
    ev["d_north_km"] = ev.expect_y_km - ev.y_km
    ev["d_depth_km"] = ev.expect_depth_km - ev.depth_km
    ev["d_lat"] = ev.d_north_km / 111.195
    ev["d_lon"] = ev.d_east_km / (111.195 * np.cos(lat0))
    cols = ["event_id", "depth_km", "expect_depth_km", "d_east_km", "d_north_km", "d_depth_km"] + (["erz_km"] if "erz_km" in ev else [])
    ev[cols].round(4).to_csv(a.changes, index=False)
    print(f"{len(ev)} events unconstrained in depth; median depth change {ev.d_depth_km.median():+.2f} km, "
          f"median epicentre change {np.hypot(ev.d_east_km, ev.d_north_km).median():.2f} km")
    if a.catalog:
        if not a.output:
            ap.error("--catalog needs --output")
        cat = pd.read_csv(a.catalog, dtype={"event_id": str})
        d = ev.set_index(ev.event_id.astype(str))[["d_lat", "d_lon", "d_depth_km"]]
        hit = cat.event_id.isin(d.index)
        cat.loc[hit, "latitude"] = cat.loc[hit, "latitude"] + d.loc[cat.event_id[hit], "d_lat"].to_numpy()
        cat.loc[hit, "longitude"] = cat.loc[hit, "longitude"] + d.loc[cat.event_id[hit], "d_lon"].to_numpy()
        cat.loc[hit, "depth_km"] = cat.loc[hit, "depth_km"] + d.loc[cat.event_id[hit], "d_depth_km"].to_numpy()
        cat.to_csv(a.output, index=False)
        print(f"{int(hit.sum())} catalog events updated -> {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
