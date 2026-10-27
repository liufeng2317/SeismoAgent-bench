#!/usr/bin/env python3
"""Stage 66: restore large picked events removed by bulk quality rules.

The working-catalog rule (stage 52: depth_edge, poor azimuth coverage, ...) and
the round-08 location-quality rule (>= 1 CC link, gap <= 150 deg, NLL sigma_x
<= 0.8 km) were designed against scattered small events. They also removed
the M7.1, M6.4 and M5.4 (located at the grid top, so depth_edge) and M3.8-4.3
aftershocks in the minutes after the M7.1 (no CC partners in the coda). Large
events are well recorded; a bulk rule must not delete them.

A located picked event of --picks-round that is not in the catalog is
restored when stage 65 measured a direct ML >= --min-magnitude for it (>= 3
stations, MAD <= 0.5) and every stage-52 review reason is in
--restore-reasons (default depth_edge: the epicentre is constrained, only the
depth sits at the grid bound). Position and origin are its stage-04
NonLinLoc solution, its depth is left empty (location_source
nll_restored_depth_unresolved). Events removed by the location-quality rule
stay removed: restoring them too (round 54, rejected) brought back 15
events of which 10 lie 20-77 km from any ComCat event, among them a
spurious M6.0; the 38 depth-bound events matched ComCat 36 times. A Match&Locate
detection within 2 s and 10 km of a restored event is the same event and
is dropped.

Usage: 66_large_events.py --catalog-in A --direct-from A --picks-round 01_baseline --catalog-out B
Writes export/<catalog-out>/66_large_events/ and export/<catalog-out>/60_catalog/catalog_events.csv.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EXPERT = Path(__file__).resolve().parents[1]
MIN_STATIONS, MAX_MAD = 3, 0.5
SAME_EVENT_S, SAME_EVENT_KM = 2.0, 10.0


def km(lat0, lon0, lat, lon):
    return np.hypot((lat - lat0) * 111.195, (lon - lon0) * 111.195 * np.cos(np.radians(lat0)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog-in", required=True)
    ap.add_argument("--direct-from", required=True)
    ap.add_argument("--picks-round", required=True)
    ap.add_argument("--review-catalog", default="06_full_catalog/52_full_catalog/events.csv",
                    help="stage-52 table with v1_review_reasons (relative to export/)")
    ap.add_argument("--catalog-out", required=True)
    ap.add_argument("--min-magnitude", type=float, default=3.5)
    ap.add_argument("--restore-reasons", default="depth_edge",
                    help="semicolon-separated stage-52 review reasons that may be restored; 'any' restores all")
    a = ap.parse_args()
    base = EXPERT / "export" / a.catalog_out
    if base.exists():
        ap.error(f"export/{a.catalog_out} exists: rounds are immutable, choose a new round")
    cat = pd.read_csv(EXPERT / "export" / a.catalog_in / "60_catalog/catalog_events.csv", low_memory=False)
    direct = pd.read_csv(EXPERT / "export" / a.direct_from / "65_direct_magnitude/direct_ml.csv")
    pick = direct[~direct.in_catalog & (direct.stations >= MIN_STATIONS) & (direct.mad <= MAX_MAD)
                  & (direct.direct_ml >= a.min_magnitude)].set_index("event_id")
    loc = pd.read_csv(EXPERT / "export" / a.picks_round / "04_locate_nonlinloc/full/events.csv").set_index("event_id")
    review = pd.read_csv(EXPERT / "export" / a.review_catalog, low_memory=False,
                         usecols=["event_id", "v1_review_reasons"]).set_index("event_id")
    rows = []
    for eid, d in pick.iterrows():
        ev = loc.loc[eid]
        raw = review.v1_review_reasons.get(eid)
        reasons = "" if pd.isna(raw) else str(raw)
        if a.restore_reasons != "any" and (not reasons or not set(reasons.split(";")) <= set(a.restore_reasons.split(";"))):
            continue
        depth_only = set(reasons.split(";")) <= {"depth_edge"} and bool(reasons)
        rows.append({"event_id": eid,
                     "origin_time_utc": pd.Timestamp(ev.origin_time).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S.%f+00:00"),
                     "latitude": ev.latitude, "longitude": ev.longitude,
                     "depth_bsl_km": np.nan if depth_only else ev.depth_below_sea_level_km,
                     "magnitude": round(float(d.direct_ml), 3), "magnitude_source": "direct_ml",
                     "location_source": "nll_restored_depth_unresolved" if depth_only else "nll_restored",
                     "restore_reason": reasons or "location_quality_rule"})
    restored = pd.DataFrame(rows)
    # Match&Locate detections of a restored event are the same event.
    t_cat = pd.to_datetime(cat.origin_time_utc, format="ISO8601", utc=True).astype("int64").to_numpy() / 1e9
    drop = np.zeros(len(cat), dtype=bool)
    for r in restored.itertuples():
        t = pd.Timestamp(r.origin_time_utc).value / 1e9
        near = (np.abs(t_cat - t) <= SAME_EVENT_S) & (km(r.latitude, r.longitude, cat.latitude.to_numpy(),
                                                          cat.longitude.to_numpy()) <= SAME_EVENT_KM)
        drop |= near & cat.location_source.eq("ml").to_numpy()
    out = base / "66_large_events"
    out.mkdir(parents=True)
    restored.to_csv(out / "restored_events.csv", index=False)
    cat[drop].to_csv(out / "dropped_same_event_detections.csv", index=False)
    new = pd.concat([cat[~drop], restored.drop(columns="restore_reason")], ignore_index=True)
    new = new.sort_values("origin_time_utc").reset_index(drop=True)
    (base / "60_catalog").mkdir()
    new.to_csv(base / "60_catalog/catalog_events.csv", index=False)
    report = {"catalog_in": a.catalog_in, "catalog_out": a.catalog_out, "min_magnitude": a.min_magnitude,
              "candidates_measured_outside_catalog": int((~direct.in_catalog).sum()),
              "restored": int(len(restored)), "depth_unresolved": int(restored.location_source.str.endswith("unresolved").sum()),
              "dropped_same_event_detections": int(drop.sum()), "events_out": int(len(new)),
              "restored_events": restored.sort_values("magnitude", ascending=False)[
                  ["event_id", "origin_time_utc", "magnitude", "location_source", "restore_reason"]].to_dict("records")}
    (out / "report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
