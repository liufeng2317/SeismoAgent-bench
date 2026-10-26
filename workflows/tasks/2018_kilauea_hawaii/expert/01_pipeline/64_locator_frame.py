#!/usr/bin/env python3
"""Stage 64: carry a final catalog over to a relocated NonLinLoc round (same associations).

A catalog round built on stage 04 of round A (picked events) plus Match&Locate
detections of A's templates is moved to the stage-04 solutions of round B
(same stage-03 associations, e.g. another LOCMETH method):

- picked rows (location_source nll) take B's solution — position and origin;
- M&L rows move with their template's A -> B displacement, origin included
  (an M&L position is template-relative);
- rows whose event (or template) has no LOCATED solution in B keep their
  position (frame_source "kept").

Membership and magnitudes are those of the source catalog. Depths in the
catalog are below sea level; stage-04 depths are below the reference
elevation of association.yaml.

Usage: 64_locator_frame.py --catalog-in r4 --nll-from r2 --nll-to r5 --catalog-out r5
Writes export/<catalog-out>/60_catalog/catalog_events.csv and frame_report.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

EXPERT = Path(__file__).resolve().parents[1]


def nll(round_: str) -> pd.DataFrame:
    e = pd.read_csv(EXPERT / "export" / round_ / "04_locate_nonlinloc/full/events.csv")
    e = e[e.status == "LOCATED"].set_index("event_id")
    e["t"] = pd.to_datetime(e.origin_time, utc=True, format="ISO8601")
    return e


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog-in", required=True)
    ap.add_argument("--nll-from", required=True)
    ap.add_argument("--nll-to", required=True)
    ap.add_argument("--catalog-out", required=True)
    a = ap.parse_args()
    datum = float(yaml.safe_load((EXPERT / "00_config/association.yaml").read_text())["reference_elevation_km"])
    old, new = nll(a.nll_from), nll(a.nll_to)
    both = old.index.intersection(new.index)
    disp = pd.DataFrame({"dlat": new.loc[both, "latitude"] - old.loc[both, "latitude"],
                         "dlon": new.loc[both, "longitude"] - old.loc[both, "longitude"],
                         "ddep": new.loc[both, "depth_km"] - old.loc[both, "depth_km"],
                         "dt": (new.loc[both, "t"] - old.loc[both, "t"]).dt.total_seconds()})
    cat = pd.read_csv(EXPERT / "export" / a.catalog_in / "60_catalog/catalog_events.csv")
    t = pd.to_datetime(cat.origin_time_utc, utc=True, format="ISO8601")
    picked = cat.location_source.eq("nll").to_numpy()
    out = cat.copy()
    src = np.full(len(cat), "kept", dtype=object)
    # picked events: B's solution
    has = picked & cat.event_id.isin(new.index).to_numpy()
    ids = cat.event_id[has]
    out.loc[has, "latitude"] = new.loc[ids, "latitude"].to_numpy()
    out.loc[has, "longitude"] = new.loc[ids, "longitude"].to_numpy()
    out.loc[has, "depth_bsl_km"] = (new.loc[ids, "depth_km"] - datum).to_numpy()
    t.loc[has] = new.loc[ids, "t"].to_numpy()
    src[has] = "nll_relocated"
    # M&L events: template displacement
    ml = ~picked & cat.ml_template_id.isin(disp.index).to_numpy()
    d = disp.loc[cat.ml_template_id[ml]]
    out.loc[ml, "latitude"] = cat.latitude[ml].to_numpy() + d.dlat.to_numpy()
    out.loc[ml, "longitude"] = cat.longitude[ml].to_numpy() + d.dlon.to_numpy()
    out.loc[ml, "depth_bsl_km"] = cat.depth_bsl_km[ml].to_numpy() + d.ddep.to_numpy()
    t.loc[ml] = t[ml] + pd.to_timedelta(d.dt.to_numpy(), unit="s")
    src[ml] = "template_shift"
    out["origin_time_utc"] = t.dt.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
    out["frame_source"] = src
    out = out.sort_values("origin_time_utc")
    dest = EXPERT / "export" / a.catalog_out / "60_catalog"
    dest.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest / "catalog_events.csv", index=False)
    h = np.hypot(disp.dlat * 111.195, disp.dlon * 111.195 * np.cos(np.radians(old.loc[both, "latitude"])))
    rep = {"catalog_in": a.catalog_in, "nll_from": a.nll_from, "nll_to": a.nll_to, "events": len(out),
           "frame_source": pd.Series(src).value_counts().to_dict(),
           "nll_displacement_km": {"median": round(float(h.median()), 3), "p90": round(float(h.quantile(0.9)), 3),
                                   "depth_median": round(float(disp.ddep.median()), 3),
                                   "origin_median_s": round(float(disp.dt.median()), 3)}}
    (dest / "frame_report.json").write_text(json.dumps(rep, indent=2) + "\n")
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
