#!/usr/bin/env python3
"""Stage 67: remove Match&Locate ghosts of larger events.

In the coda of a larger event a template can lock onto that event's phases
at a shifted time: the detection has no arrivals of its own, a low CC and an
inflated chained magnitude. A blind waveform review of 40 Ridgecrest
detections (M >= 1.5; expert/03_experiments/67_coda_duplicates_audit/)
labelled detections within 15 s of an event >= 0.5 units larger:

  CC <= 0.35: 12 not earthquakes, 3 earthquakes, 1 undecidable;
  CC  > 0.35: 3 not earthquakes, 9 earthquakes, 2 undecidable;
  control, no larger neighbour, CC 0.30-0.40: 1 not, 7 earthquakes.

So a Match&Locate detection of magnitude >= --min-magnitude is removed when
a catalog event >= --margin units larger lies within --window s and its CC
is <= --cc. Smaller detections were not reviewed and are kept. (An automatic
onset test - RMS jump at the predicted P - failed: 39 % of M2-3 control
detections failed it in the dense aftershock coda.)

Usage: 67_coda_duplicates.py --catalog-in A --catalog-out B
Writes export/<catalog-out>/67_coda_duplicates/ and export/<catalog-out>/60_catalog/catalog_events.csv.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EXPERT = Path(__file__).resolve().parents[1]


def larger_neighbour(t: np.ndarray, m: np.ndarray, window: float) -> np.ndarray:
    """Largest magnitude of any other event within +-window s (NaN if none)."""
    lo = np.searchsorted(t, t - window, side="left")
    hi = np.searchsorted(t, t + window, side="right")
    out = np.full(len(t), np.nan)
    for i, (a, b) in enumerate(zip(lo, hi)):
        others = np.delete(m[a:b], i - a)
        if np.isfinite(others).any():
            out[i] = np.nanmax(others)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog-in", required=True)
    ap.add_argument("--catalog-out", required=True)
    ap.add_argument("--window", type=float, default=15.0)
    ap.add_argument("--margin", type=float, default=0.5)
    ap.add_argument("--cc", type=float, default=0.35)
    ap.add_argument("--min-magnitude", type=float, default=1.5)
    a = ap.parse_args()
    base = EXPERT / "export" / a.catalog_out
    if base.exists():
        ap.error(f"export/{a.catalog_out} exists: rounds are immutable, choose a new round")
    cat = pd.read_csv(EXPERT / "export" / a.catalog_in / "60_catalog/catalog_events.csv", low_memory=False)
    t = pd.to_datetime(cat.origin_time_utc, format="ISO8601", utc=True).astype("int64").to_numpy() / 1e9
    order = np.argsort(t, kind="mergesort")
    cat, t = cat.iloc[order].reset_index(drop=True), t[order]
    m = cat.magnitude.to_numpy(dtype=float)
    big = larger_neighbour(t, m, a.window)
    ghost = (cat.location_source.eq("ml").to_numpy() & (m >= a.min_magnitude) & (big >= m + a.margin)
             & (cat.ml_cc.to_numpy(dtype=float) <= a.cc))
    out = base / "67_coda_duplicates"
    out.mkdir(parents=True)
    removed = cat[ghost].assign(larger_neighbour_magnitude=big[ghost])
    removed.to_csv(out / "removed_detections.csv", index=False)
    (base / "60_catalog").mkdir()
    cat[~ghost].to_csv(base / "60_catalog/catalog_events.csv", index=False)
    bins = pd.cut(removed.magnitude, [1.5, 2, 2.5, 3, 4, 9], right=False)
    report = {"catalog_in": a.catalog_in, "catalog_out": a.catalog_out,
              "settings": {"window_s": a.window, "margin": a.margin, "cc": a.cc, "min_magnitude": a.min_magnitude},
              "events_in": int(len(cat)), "removed": int(ghost.sum()), "events_out": int((~ghost).sum()),
              "removed_by_magnitude": {str(k): int(v) for k, v in removed.groupby(bins, observed=True).size().items()},
              "detections_at_or_above_min_magnitude": int((cat.location_source.eq("ml") & (cat.magnitude >= a.min_magnitude)).sum())}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
