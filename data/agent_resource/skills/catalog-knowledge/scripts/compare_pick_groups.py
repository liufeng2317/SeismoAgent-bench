#!/usr/bin/env python3
"""Test a group of picks before adopting it: picks from another picker, or from stations not used before.

Two measurements:

1. Residual spread of the group against the other stations, from a location run that includes the group
   (picks with the locator's ``residual_s``). Per station and phase with at least --min-picks picks: the median
   absolute deviation (MAD) of the residuals; then the median over the group and over the others, and the share
   of the group's residuals beyond 0.5 s and 1 s against the others'.
2. With --catalog-without and --catalog-with (the same events, from the same association so that event_id matches,
   located without and with the group): how far the
   group moves the events (epicentre and depth change for events in both catalogs, matched by event_id).

The group is --stations (comma-separated station ids, or a file with one per line), or --p-only: the stations
that have P picks but no S picks (single-component stations, P-only pickers).

Reading: a group whose residual spread is several times that of the other stations adds wrong times, and wrong
picks attached to real events move them even though they did not create them. If the group also moves many
events by kilometres, do not adopt it without other evidence; an unused station is a smaller loss than a
station that adds wrong times.

Usage:
    compare_pick_groups.py --picks picks_with_group.csv (--stations A.B,C.D | --p-only)
        [--catalog-without cat_without.csv --catalog-with cat_with.csv] [--output report.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def mad(x: pd.Series) -> float:
    return float(np.median(np.abs(x - np.median(x))))


def group_spread(picks: pd.DataFrame, group: set[str], min_picks: int) -> dict:
    p = picks.dropna(subset=["residual_s"])
    g = p.groupby(["station_id", "phase"]).residual_s
    st = pd.DataFrame({"n": g.size(), "mad_s": g.apply(mad)}).reset_index()
    st = st[st.n >= min_picks]
    st["group"] = st.station_id.isin(group)
    out = {"station_phases": {"group": int(st.group.sum()), "others": int((~st.group).sum())}}
    for name, sel in (("group", p.station_id.isin(group)), ("others", ~p.station_id.isin(group))):
        r = p.residual_s[sel].abs()
        out[name] = {"picks": int(len(r)),
                     "median_mad_s": round(float(st.mad_s[st.group == (name == "group")].median()), 3) if len(st) else None,
                     "share_above_0.5_s": round(float((r > 0.5).mean()), 3) if len(r) else None,
                     "share_above_1_s": round(float((r > 1.0).mean()), 3) if len(r) else None}
    a, b = out["group"]["median_mad_s"], out["others"]["median_mad_s"]
    out["spread_ratio"] = round(a / b, 2) if a is not None and b else None
    out["per_station"] = st[st.group].round(3).to_dict(orient="records")
    return out


def movement(without: Path, with_: Path) -> dict:
    a = pd.read_csv(without).set_index("event_id")
    b = pd.read_csv(with_).set_index("event_id")
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    lat0 = np.radians(float(a.latitude.median()))
    dh = 111.195 * np.hypot(b.latitude - a.latitude, (b.longitude - a.longitude) * np.cos(lat0))
    dz = b.depth_km - a.depth_km
    return {"events_in_both": int(len(common)),
            "epicentre_change_km": {"median": round(float(dh.median()), 2), "p90": round(float(dh.quantile(0.9)), 2),
                                    "share_above_2_km": round(float((dh > 2).mean()), 3),
                                    "share_above_5_km": round(float((dh > 5).mean()), 3)},
            "depth_change_km": {"median": round(float(dz.median()), 2), "p90_abs": round(float(dz.abs().quantile(0.9)), 2)}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--picks", type=Path, required=True, help="picks with residual_s from a location that includes the group")
    ap.add_argument("--stations", help="comma-separated station ids, or a file with one id per line")
    ap.add_argument("--p-only", action="store_true", help="the group is the stations with P picks but no S picks")
    ap.add_argument("--catalog-without", type=Path)
    ap.add_argument("--catalog-with", type=Path)
    ap.add_argument("--min-picks", type=int, default=10)
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    picks = pd.read_csv(a.picks)
    if "residual_s" not in picks:
        ap.error("the picks need a residual_s column (the locator's residuals)")
    if a.p_only:
        with_s = set(picks.station_id[picks.phase == "S"])
        group = set(picks.station_id) - with_s
    elif a.stations:
        src = Path(a.stations)
        group = set(src.read_text().split()) if src.is_file() else set(a.stations.split(","))
    else:
        ap.error("give --stations or --p-only")
    report = {"group_stations": sorted(group), "residuals": group_spread(picks, group, a.min_picks)}
    if a.catalog_without and a.catalog_with:
        report["movement"] = movement(a.catalog_without, a.catalog_with)
    text = json.dumps(report, indent=1)
    if a.output:
        a.output.write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
