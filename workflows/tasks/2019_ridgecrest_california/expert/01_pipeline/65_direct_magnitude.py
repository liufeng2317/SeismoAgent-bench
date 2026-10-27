#!/usr/bin/env python3
"""Stage 65: direct ML for picked events that only carry a chained (relative) magnitude.

Relative-amplitude chains are precise for small events but compress large
ones (amplitude ratios against clipped or coda-contaminated neighbours), and
stage 09 never measured the mainshock nor events whose S windows overlap
other events. This stage measures a direct ML for every picked event of a
round catalog without one, with the stage-09 measurement itself (same
response removal, Wood-Anderson simulation, calibration and station
corrections) and a large-event acceptance policy:

- clipped traces (digitizer plateau), low SNR and processing errors are rejected;
- a station window that overlaps another event's S arrival is accepted when its
  SNR is >= 10 (the event dominates the window);
- a missing S pick is replaced by the S time predicted from P and the origin
  (Vp/Vs 1.73).

The event ML is the median of >= 3 accepted stations with MAD <= 0.5. It
replaces the catalog magnitude when the catalog has none or when the direct
ML is >= 3.5 (the regime where chains compress); Match&Locate detections
move with their template's change. Membership and locations are unchanged.

With --include-excluded, located picked events of --picks-round that are not
in the catalog are measured too (direct_ml.csv); stage 66 uses them to
restore large events that bulk quality rules removed. They are not added here.

Usage: 65_direct_magnitude.py --catalog-in r8 --picks-round r8 --catalog-out r9 [--workers 16] [--include-excluded]
Writes export/<catalog-out>/65_direct_magnitude/ (direct_ml.csv: every measured event)
and export/<catalog-out>/60_catalog/catalog_events.csv.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EXPERT = Path(__file__).resolve().parents[1]
VPVS = 1.73
OVERLAP_SNR = 10.0
OVERLAP_FLAGS = {"overlapping_associated_S", "noise_contains_associated_S"}
MIN_STATIONS = 3
MAX_MAD = 0.5
ADOPT_FROM = 3.5
DIRECT_SOURCES = {"source_ml", "r6_ml", "direct_ml"}


def stage09():
    spec = importlib.util.spec_from_file_location("stage09", EXPERT / "01_pipeline/09_estimate_magnitude.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage09"] = module  # workers unpickle measure() by module name
    spec.loader.exec_module(module)
    return module


S09 = stage09()
if not (S09.ROOT / "data").is_dir():  # stale relative data root: use the task's read-only input root
    S09.ROOT = Path(json.loads((EXPERT.parent / "input.json").read_text())["entries"][0]["path"])


def jobs_for(targets: pd.DataFrame, picks_round: str):
    """Stage-09 measurement rows for the target events (P and an observed or predicted S)."""
    exp = EXPERT / "export" / picks_round
    picks = pd.read_csv(exp / "03_associate_gamma/full/picks.csv")
    picks = picks[picks.event_id.isin(targets.index)].copy()
    picks["epoch"] = pd.to_datetime(picks.time_utc, format="ISO8601", utc=True).astype("int64") / 1e9
    all_picks = pd.read_csv(exp / "03_associate_gamma/full/picks.csv", usecols=["event_id", "instrument_id", "phase", "time_utc"])
    all_s = all_picks[all_picks.phase.eq("S") & all_picks.event_id.notna()].copy()
    all_s["epoch"] = pd.to_datetime(all_s.time_utc, format="ISO8601", utc=True).astype("int64") / 1e9
    all_s["number"] = all_s.event_id.str.split("_").str[-1].astype(int)
    stations = pd.read_csv(exp / "03_associate_gamma/full/stations.csv").set_index("id")
    jobs, plan = [], []
    for instrument, group in picks.groupby("instrument_id"):
        if instrument not in stations.index:
            continue
        st = stations.loc[instrument]
        s_here = all_s[all_s.instrument_id.eq(instrument)][["number", "epoch"]].to_numpy(dtype=float)
        rows = []
        for event_id, pair in group.groupby("event_id"):
            ev = targets.loc[event_id]
            p = pair[pair.phase.eq("P")]
            s = pair[pair.phase.eq("S")]
            if len(p) != 1 or len(s) > 1:
                plan.append((event_id, instrument, "requires_one_P")); continue
            p_epoch = float(p.epoch.iloc[0])
            s_epoch = float(s.epoch.iloc[0]) if len(s) else ev.origin_epoch + (p_epoch - ev.origin_epoch) * VPVS
            epi = float(np.hypot(ev.x_km - st["x(km)"], ev.y_km - st["y(km)"]))
            hypo = float(np.hypot(epi, ev.depth_km - st["z(km)"]))
            if not (0.5 <= s_epoch - p_epoch <= 30 and epi <= S09.SETTINGS["maximum_epicentral_km"]
                    and hypo >= S09.SETTINGS["minimum_hypocentral_km"]):
                plan.append((event_id, instrument, "distance_or_SP_gate")); continue
            plan.append((event_id, instrument, "scheduled" + ("" if len(s) else "_predicted_S")))
            rows.append(dict(event_id=event_id, instrument_id=instrument, event_number=int(event_id.split("_")[-1]),
                             p_pick_id=p.pick_id.iloc[0], s_pick_id=s.pick_id.iloc[0] if len(s) else "",
                             p_epoch=p_epoch, s_epoch=s_epoch, window_start_epoch=p_epoch - .5,
                             window_end_epoch=p_epoch - .5 + 2 * (s_epoch - p_epoch),
                             epicentral_km=epi, hypocentral_km=hypo, gamma_hypocentral_km=hypo))
        if rows:
            jobs.append((instrument, rows, s_here))
    return jobs, pd.DataFrame(plan, columns=["event_id", "instrument_id", "reason"])


def accept(row) -> bool:
    if pd.isna(row.get("ml_station")):
        return False
    raw = row.get("flags")
    flags = set() if pd.isna(raw) else set(filter(None, str(raw).split(";")))  # empty CSV cell reads as NaN
    if not flags:
        return True
    return flags <= OVERLAP_FLAGS and float(row.get("snr_min", 0)) >= OVERLAP_SNR


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog-in", required=True)
    ap.add_argument("--picks-round", required=True)
    ap.add_argument("--catalog-out", required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--include-excluded", action="store_true")
    a = ap.parse_args()
    if (EXPERT / "export" / a.catalog_out).exists():
        ap.error(f"export/{a.catalog_out} exists: rounds are immutable, choose a new round")
    out = EXPERT / "export" / a.catalog_out / "65_direct_magnitude"
    (out / "stations").mkdir(parents=True)
    S09.OUT = out  # stage-09 measure() writes its per-instrument tables here
    cat = pd.read_csv(EXPERT / "export" / a.catalog_in / "60_catalog/catalog_events.csv", low_memory=False)
    loc = pd.read_csv(EXPERT / "export" / a.picks_round / "04_locate_nonlinloc/full/events.csv")
    loc = loc[loc.status.eq("LOCATED")].set_index("event_id")
    loc["origin_epoch"] = pd.to_datetime(loc.origin_time, format="ISO8601", utc=True).astype("int64") / 1e9
    picked = cat[cat.location_source.ne("ml") & ~cat.magnitude_source.isin(DIRECT_SOURCES)]
    wanted = loc.index.intersection(picked.event_id)
    if a.include_excluded:
        wanted = wanted.union(loc.index.difference(cat.event_id))
    targets = loc.loc[wanted, ["x_km", "y_km", "depth_km", "origin_epoch"]]
    jobs, plan = jobs_for(targets, a.picks_round)
    plan.to_csv(out / "measurement_plan.csv", index=False)
    print(f"{len(targets)} target events, {len(jobs)} instruments, {sum(len(j[1]) for j in jobs)} measurements", flush=True)
    with cf.ProcessPoolExecutor(max_workers=a.workers, initializer=S09.init) as pool:
        for k, (instrument, n, ok, _) in enumerate(pool.map(S09.measure, jobs), 1):
            if k % 20 == 0 or k == len(jobs):
                print(f"[{k}/{len(jobs)}] {instrument}: {ok}/{n} accepted by stage-09 rules", flush=True)
    station = pd.concat([pd.read_csv(out / "stations" / f"{j[0]}.csv") for j in jobs], ignore_index=True)
    station["accepted_large_event"] = station.apply(accept, axis=1)
    station.to_csv(out / "station_magnitudes.csv", index=False)
    good = station[station.accepted_large_event]
    agg = good.groupby("event_id").ml_station.agg(["median", "count"])
    agg["mad"] = good.groupby("event_id").ml_station.apply(lambda v: (v - v.median()).abs().median())
    agg["in_catalog"] = agg.index.isin(cat.event_id)
    agg.rename(columns={"median": "direct_ml", "count": "stations"}).to_csv(out / "direct_ml.csv", index_label="event_id")
    direct = agg[(agg["count"] >= MIN_STATIONS) & (agg["mad"] <= MAX_MAD) & agg["in_catalog"]]["median"]

    new = cat.copy()
    old = new.set_index("event_id").magnitude
    adopt = direct[(direct >= ADOPT_FROM) | old.reindex(direct.index).isna()]
    rows = new.event_id.isin(adopt.index)
    new.loc[rows, "magnitude"] = new.loc[rows, "event_id"].map(adopt).to_numpy()
    new.loc[rows, "magnitude_source"] = "direct_ml"
    # Match&Locate detections are relative to their template: move them with its change.
    change = (adopt - old.reindex(adopt.index)).dropna()
    ml_rows = new.location_source.eq("ml") & new.ml_template_id.isin(change.index)
    new.loc[ml_rows, "magnitude"] = new.loc[ml_rows, "magnitude"] + new.loc[ml_rows, "ml_template_id"].map(change)
    dest = EXPERT / "export" / a.catalog_out / "60_catalog"
    dest.mkdir(parents=True, exist_ok=True)
    new.to_csv(dest / "catalog_events.csv", index=False)

    both = pd.DataFrame({"direct": direct, "chain": old.reindex(direct.index)}).dropna()
    both["difference"] = both.direct - both.chain
    bins = pd.cut(both.direct, [-9, 1, 2, 3, 3.5, 4, 5, 9])
    report = {"catalog_in": a.catalog_in, "catalog_out": a.catalog_out, "target_events": int(len(targets)),
              "measurements": int(len(station)), "accepted_measurements": int(station.accepted_large_event.sum()),
              "events_with_direct_ml": int(len(direct)), "adopted": int(len(adopt)),
              "adopted_without_previous": int(old.reindex(adopt.index).isna().sum()),
              "templates_moved": int(len(change)), "detections_moved": int(ml_rows.sum()),
              "direct_minus_chain_by_direct_ml": {str(k): {"n": int(len(g)), "median": round(float(g.difference.median()), 3)}
                                                  for k, g in both.groupby(bins, observed=True)},
              "largest": {str(k): round(float(v), 2) for k, v in direct.sort_values(ascending=False).head(10).items()}}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
