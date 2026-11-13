"""a1 round 3: choose the stations and the first batch of events for one region.

Stations: CI/AZ stations with HH or EH channels operating since 2020 within
--station-radius-deg of the region centre, ranked by the number of manual P
picks they carry in the region's M>=2.5 events; the top --n-stations are kept.
Events: M>=--min-mag, outside the PhaseNet periods, with at least --min-manual-p
manual P and --min-manual-s manual S picks at the chosen stations; at most
--n-events, spread over years (round robin, fixed seed).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py
import argparse
import json

import numpy as np
import pandas as pd
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

from paths import RES_A


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--region", default="R2")
    ap.add_argument("--station-radius-deg", type=float, default=0.6)
    ap.add_argument("--n-stations", type=int, default=30)
    ap.add_argument("--min-mag", type=float, default=3.0)
    ap.add_argument("--min-manual-p", type=int, default=8)
    ap.add_argument("--min-manual-s", type=int, default=4)
    ap.add_argument("--n-events", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(RES_A / "a1_first_batch"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cand = pd.read_csv(RES_A / "a1_candidate_regions" / "candidate_regions.csv").set_index("candidate")
    lat, lon = cand.loc[args.region, ["lat", "lon"]]
    picks = pd.read_csv(RES_A / "a2_labels" / "picks.csv", parse_dates=["time"])
    picks = picks[picks.region == args.region]

    inv = Client("SCEDC").get_stations(network="CI,AZ", channel="HH?,EH?", level="channel",
                                       latitude=lat, longitude=lon, maxradius=args.station_radius_deg,
                                       starttime=UTCDateTime(2020, 1, 1))
    rows = []
    for net in inv:
        for sta in net:
            fams = sorted({ch.code[:2] for ch in sta.channels})
            locs = sorted({ch.location_code for ch in sta.channels})
            rows.append(dict(station=f"{net.code}.{sta.code}", network=net.code, code=sta.code,
                             lat=sta.latitude, lon=sta.longitude, elevation_m=sta.elevation,
                             families=",".join(fams), locations=",".join(locs) or "--"))
    st = pd.DataFrame(rows).drop_duplicates("station")
    manual_p = picks[(picks.phase == "P") & (picks["mode"] == "manual")]
    st["manual_p_picks"] = st.station.map(manual_p.station.value_counts()).fillna(0).astype(int)
    st = st.sort_values(["manual_p_picks", "station"], ascending=[False, True]).head(args.n_stations)
    st.to_csv(out / "stations.csv", index=False)

    chosen = set(st.station)
    sub = picks[picks.station.isin(chosen) & (picks["mode"] == "manual")]
    cnt = sub.groupby(["event_id", "phase"]).size().unstack(fill_value=0)
    ev = picks.groupby("event_id").agg(time=("time", "first"), mag=("mag", "first"),
                                       phasenet_period=("phasenet_period", "max"))
    ev = ev.join(cnt.rename(columns={"P": "manual_p", "S": "manual_s"})[["manual_p", "manual_s"]]).fillna(0)
    ok = ev[(ev.mag >= args.min_mag) & (~ev.phasenet_period.astype(bool))
            & (ev.manual_p >= args.min_manual_p) & (ev.manual_s >= args.min_manual_s)].copy()
    ok["year"] = ok.time.dt.year
    rng = np.random.default_rng(args.seed)
    pools = {y: list(rng.permutation(g.index.values)) for y, g in ok.groupby("year")}
    batch = []
    while len(batch) < args.n_events and any(pools.values()):
        for y in sorted(pools):
            if pools[y] and len(batch) < args.n_events:
                batch.append(pools[y].pop())
    sel = ok.loc[batch].sort_values("time")
    sel.drop(columns="year").to_csv(out / "events.csv")

    summary = dict(region=args.region, centre=[float(lat), float(lon)], stations=len(st),
                   eligible_events=len(ok), selected_events=len(sel),
                   selected_by_year=sel.year.value_counts().sort_index().to_dict(),
                   selected_mag_range=[float(sel.mag.min()), float(sel.mag.max())],
                   args=vars(args))
    (out / "selection.json").write_text(json.dumps(summary, indent=1, default=int))
    print(json.dumps(summary, indent=1, default=int))
    print(st[["station", "families", "locations", "manual_p_picks"]].to_string(index=False))


if __name__ == "__main__":
    main()
