#!/usr/bin/env python3
"""Event-time table from the Shelly & Hardebeck (2019) phase-arrival release.

The release has no origins: each row is one template's correlation-derived
arrival for a detected event (``match_id``) at one station. This script turns
it into a time-only detection reference:

1. per match_id and station-phase, the median arrival over templates;
2. origin time = median over station-phases of (arrival - travel time from a
   fixed swarm centroid) in the UUSS Yellowstone 1-D model (case registry
   ``data/models/velocity_models.json``). The swarm is compact (ComCat: 89% of
   events within 3 km of the Mw 4.4 epicentre), so the centroid costs only a
   few tenths of a second;
3. duplicates merged: match_ids whose common station-phase arrivals agree to
   within ``--dup-arrival-s`` (median) are one waveform arrival and are
   merged (union-find). Two earthquakes that close in time cannot be
   separated by any catalog either.

No location is derived. ComCat is used only to report the origin-time
accuracy (not to calibrate it). Outputs go below analysis/; raw files are
never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
CASE = HERE.parents[2]
REPO = CASE.parents[1]
sys.path.insert(0, str(REPO / "seismotools/match_and_locate/runtime/python/MatchLocatepy"))
from matchlocate_runner.traveltime import LayeredModel, first_arrival  # noqa: E402

RAW = HERE / "raw/Yellowstone_2017_correlation_phase_arrivals.csv"
OUT = HERE / "analysis/derived/detection_events/SHELLY2019_GL081607__detection_events_v1.csv"
STATS = HERE / "analysis/stats/detection_events/detection_events_v1.json"
COMCAT = CASE / "data/catalogs/USGS_UUSS_COMCAT_2017/USGS_UUSS_COMCAT_2017__catalog_operational_benchmark.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--centroid-depth-km", type=float, default=8.0,
                    help="below the model datum (local surface); Pang et al. 2019: 97%% at 6-14 km")
    ap.add_argument("--dup-arrival-s", type=float, default=0.05)
    args = ap.parse_args()

    anchor = json.loads((CASE / "analysis/mainshock_anchor.json").read_text())["anchor"]
    lat0, lon0 = anchor["latitude"], anchor["longitude"]
    reg = json.loads((CASE / "data/models/velocity_models.json").read_text())["models"]["uuss_yellowstone_1d"]
    model = LayeredModel.from_rows(reg["rows"])
    datum_km = 2.3      # registry depth_reference: layer tops below the local surface (~2.3 km ASL)
    stations = {}
    for e in json.loads((CASE / "data/waveforms/stations/station_inventory.json").read_text())["channel_epochs"]:
        stations.setdefault(f"{e['network']}.{e['station']}", (e["latitude"], e["longitude"], e["elevation_m"] / 1000))

    ph = pd.read_csv(RAW, usecols=["template_id", "match_id", "network", "station", "phase", "arrival", "mag"])
    ph["sid"] = ph.network + "." + ph.station
    missing = sorted(set(ph.sid) - set(stations))
    ph = ph[ph.sid.isin(stations)]
    tt = {}
    for sid in ph.sid.unique():
        la, lo, el = stations[sid]
        d = math.hypot((lo - lon0) * 111.19 * math.cos(math.radians(lat0)), (la - lat0) * 111.19)
        for p in ("P", "S"):
            tt[(sid, p)] = first_arrival(model, p, d, args.centroid_depth_km, datum_km - el).travel_time_s

    arr = ph.groupby(["match_id", "sid", "phase"]).arrival.median().reset_index()
    arr["o"] = arr.arrival - [tt[k] for k in zip(arr.sid, arr.phase)]
    arr["key"] = arr.sid + "." + arr.phase
    per = arr.groupby("match_id").agg(origin=("o", "median"),
                                      origin_mad_s=("o", lambda v: float(np.median(np.abs(v - np.median(v))))),
                                      n_station_phases=("o", "size"),
                                      n_p=("phase", lambda v: int((v == "P").sum())),
                                      n_s=("phase", lambda v: int((v == "S").sum())))
    meta = ph.groupby("match_id").agg(n_templates=("template_id", "nunique"), mag=("mag", "first"))
    per = per.join(meta).sort_values("origin")
    per.loc[~np.isfinite(per.mag) | (per.mag < -10), "mag"] = np.nan   # -inf / sentinel values

    # union-find over near-identical arrivals
    ids = per.index.to_numpy()
    t = per.origin.to_numpy()
    by_id = {m: g.set_index("key").arrival for m, g in arr.groupby("match_id")}
    parent = {m: m for m in ids}

    def root(m):
        while parent[m] != m:
            parent[m] = parent[parent[m]]
            m = parent[m]
        return m

    merges = 0
    for i in range(len(ids)):
        j = i + 1
        while j < len(ids) and t[j] - t[i] < 2.0:
            a, b = by_id[ids[i]], by_id[ids[j]]
            common = a.index.intersection(b.index)
            if len(common) and np.median(np.abs(a[common].to_numpy() - b[common].to_numpy())) < args.dup_arrival_s:
                ra, rb = root(ids[i]), root(ids[j])
                if ra != rb:
                    parent[rb] = ra
                    merges += 1
            j += 1
    per["group"] = [root(m) for m in ids]
    ev = per.reset_index().groupby("group").agg(
        origin=("origin", "median"), origin_mad_s=("origin_mad_s", "median"),
        n_station_phases=("n_station_phases", "max"), n_p=("n_p", "max"), n_s=("n_s", "max"),
        n_templates=("n_templates", "sum"), magnitude=("mag", "max"),
        n_match_ids=("match_id", "size"),
        match_ids=("match_id", lambda v: " ".join(str(x) for x in sorted(v)))).sort_values("origin")
    out = pd.DataFrame({
        "event_id": ev.index.astype(str),
        "origin_time_utc": pd.to_datetime(ev.origin, unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "origin_mad_s": ev.origin_mad_s.round(3), "n_station_phases": ev.n_station_phases,
        "n_p": ev.n_p, "n_s": ev.n_s, "n_templates": ev.n_templates,
        "magnitude": ev.magnitude.round(2), "n_match_ids": ev.n_match_ids, "match_ids": ev.match_ids})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    # accuracy vs ComCat (report only)
    cc = np.sort(pd.to_datetime(pd.read_csv(COMCAT).time).astype("int64").to_numpy() / 1e9)
    w0, w1 = cc.min() - 1, cc.max() + 1
    o = ev.origin.to_numpy()
    o = o[(o >= w0) & (o <= w1)]
    k = np.clip(np.searchsorted(o, cc), 1, len(o) - 1)
    near = np.where(np.abs(o[k] - cc) < np.abs(o[k - 1] - cc), o[k], o[k - 1])
    dt = near - cc
    ok = np.abs(dt) <= 1.5
    stats = {
        "raw_sha256": sha256(RAW), "match_ids": int(len(per)), "events_after_merge": int(len(ev)),
        "merged_pairs": merges, "dup_arrival_s": args.dup_arrival_s,
        "centroid": {"latitude": lat0, "longitude": lon0, "depth_below_surface_km": args.centroid_depth_km,
                     "model": "uuss_yellowstone_1d", "datum_km_asl": datum_km},
        "stations_without_metadata": missing,
        "origin_within_event_mad_s_median": float(ev.origin_mad_s.median()),
        "vs_comcat_benchmark": {"comcat_events": int(len(cc)), "with_shelly_event_within_1_5_s": int(ok.sum()),
                                "dt_median_s": round(float(np.median(dt[ok])), 3),
                                "dt_mad_s": round(float(np.median(np.abs(dt[ok] - np.median(dt[ok])))), 3)},
        "outputs": {"events": str(OUT.relative_to(HERE)), "rows": int(len(out))}}
    STATS.parent.mkdir(parents=True, exist_ok=True)
    STATS.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
