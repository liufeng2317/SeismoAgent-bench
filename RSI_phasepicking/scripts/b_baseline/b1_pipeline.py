"""b1: run the baseline pipeline on the first batch, part by part, with figures.

Parts: 1 event window (network STA/LTA trigger), 2 channels, 3 picks (--picker:
B0 classical STA/LTA + AIC for P and S, B1 PhaseNet SCEDC, B8 the analyst's manual
picks), 4 association (PyOcto; skipped for B8), 5 location (HypoInverse, SCSN
Hadley-Kanamori model). Writes one folder per part under
results/b_baseline/b1_pipeline/<picker>/ plus overview.png, config.json and
summary.json. The catalog origin is used only to check and plot, never by a part.
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
from pickers import CLASSIC_DEFAULTS, PICKERS


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--picker", default="B0", choices=["B0", "B1", "B8"])
    ap.add_argument("--plot-events", type=int, default=3, help="events with per-event figures")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    out = RES_B / "b1_pipeline" / args.picker
    if out.exists():
        if not args.overwrite:
            sys.exit(f"{out} exists; use --overwrite")
        shutil.rmtree(out)
    dirs = {k: out / k for k in ("1_window", "2_channels", "3_picks", "4_association", "5_location")}
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
        if args.picker == "B8":
            p = ref[(ref.event_id == ev.event_id) & (ref["mode"] == "manual")]
            p = pd.DataFrame(dict(station=p.station, phase=p.phase, time_utc=p.time, score=np.nan, method="B8"))
        else:
            p = PICKERS[args.picker](chosen, w)
        p.insert(0, "event_id", ev.event_id)
        all_picks.append(p)
        dist = {s: pl.distance_km(ev.origin_lat, ev.origin_lon, *coord.loc[s]) for s in chosen}
        if ev.event_id in plot_ids:
            viz.fig_window(ev.event_id, chosen, w, origin, dirs["1_window"] / f"window_{ev.event_id}.png")
            viz.fig_picks(ev.event_id, chosen, w, p, ref[ref.event_id == ev.event_id], dist,
                          dirs["3_picks"] / f"picks_{ev.event_id}.png", title_method=args.picker)

    wins = pd.DataFrame(win_rows)
    wins.to_csv(dirs["1_window"] / "windows.csv", index=False)
    chans = pd.concat(chan_tabs)
    chans.to_csv(dirs["2_channels"] / "channels.csv", index=False)
    viz.fig_channels(stations, chans, events, pl.REGION_R2, dirs["2_channels"] / "channels_map.png")
    picks = pd.concat(all_picks, ignore_index=True)
    picks.to_csv(dirs["3_picks"] / "picks.csv", index=False)

    # Part 4: association (all events in one PyOcto run), then keep for each
    # window the PyOcto event with most of that window's picks.
    if args.picker == "B8":
        picks["assignment_status"], picks["residual_s"] = "assigned", np.nan
        arrivals = picks
    else:
        assoc, _ = pl.associate(picks, stations, dirs["4_association"])
        best = (assoc[assoc.assignment_status == "assigned"].groupby(["event_id", "event_index"]).size()
                .reset_index(name="n").sort_values("n").drop_duplicates("event_id", keep="last"))
        keep = assoc.merge(best[["event_id", "event_index"]], on=["event_id", "event_index"], how="left",
                           indicator=True)
        assoc["assignment_status"] = np.where(keep["_merge"] == "both", "assigned", "unassigned")
        assoc.to_csv(dirs["4_association"] / "picks_associated.csv", index=False)
        picks = assoc
        arrivals = assoc[assoc.assignment_status == "assigned"]
        for ev in events[events.event_id.isin(plot_ids)].itertuples():
            dist = {s: pl.distance_km(ev.origin_lat, ev.origin_lon, *coord.loc[s]) for s in coord.index}
            viz.fig_association(ev.event_id, assoc[assoc.event_id == ev.event_id], pl.utc(ev.origin_time), dist,
                                dirs["4_association"] / f"association_{ev.event_id}.png")

    # Part 5: location
    loc, _ = pl.locate(arrivals, stations, dirs["5_location"])
    loc = loc.merge(events[["event_id", "origin_time", "origin_lat", "origin_lon", "origin_depth_km", "magnitude"]]
                    .rename(columns={"origin_lat": "cat_lat", "origin_lon": "cat_lon", "origin_depth_km": "cat_depth"}),
                    on="event_id", how="right")
    loc["status"] = loc.status.fillna("NOT_LOCATED")
    loc["epi_shift_km"] = pl.distance_km(loc.cat_lat, loc.cat_lon, loc.latitude, loc.longitude)
    loc["depth_diff_km"] = loc.depth_km - loc.cat_depth
    loc["time_diff_s"] = [pl.utc(a) - pl.utc(b) if isinstance(a, str) else np.nan
                          for a, b in zip(loc.origin_time_utc, loc.origin_time)]
    loc.to_csv(dirs["5_location"] / "locations.csv", index=False)
    viz.fig_location(loc, dirs["5_location"] / "locations.png", label=args.picker)

    asg = picks[picks.assignment_status == "assigned"]
    counts = {"events in batch": len(events), "events with a window": int(wins.found.sum()),
              "P picks": int((picks.phase == "P").sum()), "S picks": int((picks.phase == "S").sum()),
              "P picks associated": int((asg.phase == "P").sum()), "S picks associated": int((asg.phase == "S").sum()),
              "events located": int((loc.status == "LOCATED").sum())}
    viz.fig_overview({"in batch": len(events), "with a window": int(wins.found.sum()),
                      "located": int((loc.status == "LOCATED").sum())},
                     {ph: {"picked": int((picks.phase == ph).sum()), "associated": int((asg.phase == ph).sum())}
                      for ph in ("P", "S")}, out / "overview.png", label=args.picker)
    ok = loc[loc.status == "LOCATED"]
    summary = dict(picker=args.picker, counts=counts,
                   trigger_minus_origin_s_median=float(wins.trigger_minus_origin_s.median()),
                   epicentre_shift_km_median=float(ok.epi_shift_km.median()),
                   depth_diff_km_median=float(ok.depth_diff_km.median()),
                   origin_time_diff_s_median=float(ok.time_diff_s.median()),
                   rms_s_median=float(ok.rms_s.median()))
    config = dict(window=pl.WINDOW_DEFAULTS, association=pl.ASSOCIATION_DEFAULTS, location=pl.LOCATION_DEFAULTS,
                  velocity_model=str(HK_MODEL.name), picker=args.picker,
                  classic=CLASSIC_DEFAULTS if args.picker == "B0" else None)
    (out / "config.json").write_text(json.dumps(config, indent=1))
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
