#!/usr/bin/env python3
"""Stage 63: move a stage-60 catalog into the layered (published Shelly Table 1) model frame.

The pipeline's GaMMA/NonLinLoc runs interpolate Shelly Table 1 linearly; the
paper publishes constant layers (hypoDD convention). Stage 62's hypoDD
relocation with the layered model put the picked events 0.36 km deeper
relative to Shelly's depths (median dZ −0.52 → −0.16 km, MAD 0.73 → 0.52) and
closer horizontally to Shelly and Liu, without changing sharpness. This stage
applies that frame to a stage-60 catalog round:

- picked events with an accepted stage-62 relocation take it (``hypodd``);
- M&L events move with their template's stage-62 displacement, origin time
  included (``template_shift``) — their position is template-relative;
- everything else takes the median displacement of the relocated picked
  events (``median_shift``).

Usage: 63_layered_frame.py --source-round 09_close_events --catalog-round 10_layered_frame
Writes export/<catalog-round>/60_catalog/catalog_events.csv (+ frame_source).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EXPERT = Path(__file__).resolve().parents[1]
SURFACE_KM = 0.7


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source-round", default="09_close_events")
    ap.add_argument("--catalog-round", default="10_layered_frame")
    ap.add_argument("--relocation", default="full", help="stage-62 scope directory")
    args = ap.parse_args()
    spec = importlib.util.spec_from_file_location("s62", EXPERT / "01_pipeline/62_cc_relocation.py")
    s62 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s62)
    rel = s62.load_relocation(EXPERT / "export/07_match_locate/62_cc_relocation" / args.relocation, "cc3_d1", "picks")
    rel = rel[rel.lat.notna() & (rel.location_source == "dd")].set_index("event_id")
    disp = pd.DataFrame({"dlat": rel.lat - rel.latitude, "dlon": rel.lon - rel.longitude,
                         "ddep": rel.depth - rel.depth_km, "dt": (rel.t_new - rel.t).dt.total_seconds()})
    med = disp.median()
    cat = pd.read_csv(EXPERT / "export" / args.source_round / "60_catalog/catalog_events.csv")
    t = pd.to_datetime(cat.origin_time_utc, utc=True, format="ISO8601")
    key = np.where(cat.location_source == "ml", cat.ml_template_id, cat.event_id)
    d = disp.reindex(key)
    source = np.where(d.dlat.notna(), np.where(cat.location_source == "ml", "template_shift", "hypodd"), "median_shift")
    d = d.fillna(med)
    out = cat.copy()
    out["latitude"] = cat.latitude + d.dlat.to_numpy()
    out["longitude"] = cat.longitude + d.dlon.to_numpy()
    out["depth_bsl_km"] = cat.depth_bsl_km + d.ddep.to_numpy()
    out["origin_time_utc"] = (t + pd.to_timedelta(d.dt.to_numpy(), unit="s")).dt.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
    out["frame_source"] = source
    out = out.sort_values("origin_time_utc")
    dest = EXPERT / "export" / args.catalog_round / "60_catalog"
    dest.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest / "catalog_events.csv", index=False)
    report = {"source_round": args.source_round, "events": len(out),
              "frame_source": pd.Series(source).value_counts().to_dict(),
              "median_displacement": {"north_km": round(med["dlat"] * 111.195, 3),
                                      "east_km": round(med["dlon"] * 111.195 * np.cos(np.radians(35.7)), 3),
                                      "depth_km": round(med["ddep"], 3), "origin_s": round(med["dt"], 3)},
              "relocated_picked_events": len(disp)}
    (dest / "frame_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
