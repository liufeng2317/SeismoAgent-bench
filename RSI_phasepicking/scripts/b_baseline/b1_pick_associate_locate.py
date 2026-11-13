"""b1: pick, associate and locate the first batch with one method, part by part, with figures.

Parts: 1 event window (network STA/LTA trigger), 2 channel selection, 3 phase
picks (--method: B0_STALTA_AIC classical STA/LTA + AIC for P and S,
B1_PhaseNet_SCEDC, B8_Analyst_Picks the analyst's manual picks), 4 association
(PyOcto; skipped for the analyst picks), 5 location (HypoInverse, SCSN
Hadley-Kanamori model). Writes one folder per part under
results/b_baseline/b1_pick_associate_locate/<method>/ plus overview.png,
config.json and summary.json. The catalog origin is used only to check and plot,
never by a part.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py; part-b modules sit beside this file
import argparse
import json
import shutil

import numpy as np
import pandas as pd

import pipeline as pl
import viz
from paths import HK_MODEL, RES_B
from pickers import ANALYST, CLASSIC, CLASSIC_DEFAULTS, PHASENET, PICKERS


STEP = "b1_pick_associate_locate"
# One folder per pipeline part: number (order) + what the part does.
PART_DIRS = {"window": "1_event_window", "channels": "2_channel_selection", "picks": "3_phase_picks",
             "association": "4_association_PyOcto", "location": "5_location_HypoInverse"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--method", default=CLASSIC, choices=[CLASSIC, PHASENET, ANALYST])
    ap.add_argument("--plot-events", type=int, default=3, help="events with per-event figures")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    out = RES_B / STEP / args.method
    if out.exists():
        if not args.overwrite:
            sys.exit(f"{out} exists; use --overwrite")
        shutil.rmtree(out)
    dirs = {k: out / v for k, v in PART_DIRS.items()}
    for d in dirs.values():
        d.mkdir(parents=True)

    stations, events, ref = pl.load_batch()
    events = events.sort_values("time").reset_index(drop=True)
    plot_ids = set(events.event_id.iloc[np.linspace(0, len(events) - 1, args.plot_events).round().astype(int)])
    coord = stations.set_index("station")[["lat", "lon"]]

    win_rows, chan_tabs, all_picks, windows, chosen_by_ev = [], [], [], {}, {}
    for ev in events.itertuples():
        st = pl.read_event(ev.event_id)
        chosen, chan = pl.select_channels(st, stations, ref)
        chan.insert(0, "event_id", ev.event_id)
        chan_tabs.append(chan)
        origin = pl.utc(ev.origin_time)
        w = pl.event_window(chosen)
        win_rows.append(dict(event_id=ev.event_id, found=w is not None,
                             trigger_utc=str(w["trigger"]) if w else "",
                             trigger_minus_origin_s=(w["trigger"] - origin) if w else np.nan,
                             stations=len(chosen)))
        if w is None:
            continue
        windows[ev.event_id], chosen_by_ev[ev.event_id] = w, chosen
        if args.method == ANALYST:
            p = ref[(ref.event_id == ev.event_id) & (ref["mode"] == "manual")]
            p = pd.DataFrame(dict(station=p.station, phase=p.phase, time_utc=p.time, score=np.nan, method=ANALYST))
        else:
            p = PICKERS[args.method](chosen, w)
        p.insert(0, "event_id", ev.event_id)
        all_picks.append(p)
        dist = {s: pl.distance_km(ev.origin_lat, ev.origin_lon, *coord.loc[s]) for s in chosen}
        if ev.event_id in plot_ids:
            viz.fig_window(ev.event_id, chosen, w, origin, dirs["window"] / f"window_{ev.event_id}.png")
            viz.fig_picks(ev.event_id, chosen, w, p, ref[ref.event_id == ev.event_id], dist,
                          dirs["picks"] / f"picks_{ev.event_id}.png", title_method=args.method)

    wins = pd.DataFrame(win_rows)
    wins.to_csv(dirs["window"] / "windows.csv", index=False)
    chans = pd.concat(chan_tabs)
    chans.to_csv(dirs["channels"] / "channels.csv", index=False)
    viz.fig_channels(stations, chans, events, pl.REGION_R2, dirs["channels"] / "channels_map.png")
    picks = pd.concat(all_picks, ignore_index=True)
    picks.to_csv(dirs["picks"] / "picks.csv", index=False)

    # Part 4: association (all events in one PyOcto run), then keep for each
    # window the PyOcto event with most of that window's picks.
    if args.method == ANALYST:
        picks["assignment_status"], picks["residual_s"] = "assigned", np.nan
        arrivals = picks
    else:
        assoc, _ = pl.associate(picks, stations, dirs["association"])
        best = (assoc[assoc.assignment_status == "assigned"].groupby(["event_id", "event_index"]).size()
                .reset_index(name="n").sort_values("n").drop_duplicates("event_id", keep="last"))
        keep = assoc.merge(best[["event_id", "event_index"]], on=["event_id", "event_index"], how="left",
                           indicator=True)
        assoc["assignment_status"] = np.where(keep["_merge"] == "both", "assigned", "unassigned")
        assoc.to_csv(dirs["association"] / "picks_associated.csv", index=False)
        picks = assoc
        arrivals = assoc[assoc.assignment_status == "assigned"]
        for ev in events[events.event_id.isin(plot_ids)].itertuples():
            dist = {s: pl.distance_km(ev.origin_lat, ev.origin_lon, *coord.loc[s]) for s in coord.index}
            viz.fig_association(ev.event_id, assoc[assoc.event_id == ev.event_id], pl.utc(ev.origin_time), dist,
                                dirs["association"] / f"association_{ev.event_id}.png")

    # Part 5: location
    loc, _ = pl.locate(arrivals, stations, dirs["location"])
    loc = loc.merge(events[["event_id", "origin_time", "origin_lat", "origin_lon", "origin_depth_km", "magnitude"]]
                    .rename(columns={"origin_lat": "cat_lat", "origin_lon": "cat_lon", "origin_depth_km": "cat_depth"}),
                    on="event_id", how="right")
    loc["status"] = loc.status.fillna("NOT_LOCATED")
    loc["epi_shift_km"] = pl.distance_km(loc.cat_lat, loc.cat_lon, loc.latitude, loc.longitude)
    loc["depth_diff_km"] = loc.depth_km - loc.cat_depth
    loc["time_diff_s"] = [pl.utc(a) - pl.utc(b) if isinstance(a, str) else np.nan
                          for a, b in zip(loc.origin_time_utc, loc.origin_time)]
    loc.to_csv(dirs["location"] / "locations.csv", index=False)
    viz.fig_location(loc, dirs["location"] / "locations.png", label=args.method)

    asg = picks[picks.assignment_status == "assigned"]
    counts = {"events in batch": len(events), "events with a window": int(wins.found.sum()),
              "P picks": int((picks.phase == "P").sum()), "S picks": int((picks.phase == "S").sum()),
              "P picks associated": int((asg.phase == "P").sum()), "S picks associated": int((asg.phase == "S").sum()),
              "events located": int((loc.status == "LOCATED").sum())}
    viz.fig_overview({"in batch": len(events), "with a window": int(wins.found.sum()),
                      "located": int((loc.status == "LOCATED").sum())},
                     {ph: {"picked": int((picks.phase == ph).sum()), "associated": int((asg.phase == ph).sum())}
                      for ph in ("P", "S")}, out / "overview.png", label=args.method)
    ok = loc[loc.status == "LOCATED"]
    summary = dict(method=args.method, counts=counts,
                   trigger_minus_origin_s_median=float(wins.trigger_minus_origin_s.median()),
                   epicentre_shift_km_median=float(ok.epi_shift_km.median()),
                   depth_diff_km_median=float(ok.depth_diff_km.median()),
                   origin_time_diff_s_median=float(ok.time_diff_s.median()),
                   rms_s_median=float(ok.rms_s.median()))
    config = dict(window=pl.WINDOW_DEFAULTS, association=pl.ASSOCIATION_DEFAULTS, location=pl.LOCATION_DEFAULTS,
                  velocity_model=str(HK_MODEL.name), method=args.method,
                  classic=CLASSIC_DEFAULTS if args.method == CLASSIC else None)
    (out / "config.json").write_text(json.dumps(config, indent=1))
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
