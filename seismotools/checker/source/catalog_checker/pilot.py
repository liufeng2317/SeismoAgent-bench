"""Pilot batches: a small part of the data, chosen by a fixed rule, on which to test a workflow before the full run.

A pilot batch has three parts, each for a different question:
- ``representative``: events (or time windows) drawn evenly over time and over how well events are
  recorded. It estimates what a change does to the whole catalog (how far depths and origin times move)
  and shows errors of code and tool use (units, conventions, datum), which affect every event alike.
- ``busiest``: the period with the most events. It shows how picking, association and run time behave
  at the highest event rate, which a sample spread over quiet periods does not reach.
- ``largest``: the largest events. Clipped records, long S trains and magnitudes of large events only
  show up there.
Only the representative part stands for the whole catalog. The events recorded best are not a
representative sample: in replays they moved differently from the full catalog, sometimes in the
opposite direction. A pilot batch does not show the distribution of the full catalog (pile-ups,
layers, completeness); the checker reports those checks without a verdict on a pilot (``--pilot``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PILOT_DEFAULTS = {"events": 300, "representative_share": 0.6, "busiest_share": 0.2, "time_strata": 30,
                  "pick_strata": 5, "busiest_window_s": 3600.0, "seed": 0}


def select_events(events: pd.DataFrame, picks: pd.DataFrame, config: dict | None = None) -> dict[str, list[str]]:
    """Event ids of the three parts. ``events``: event_id, time, magnitude (may be NaN); ``picks``: event_id, station_id."""
    c = {**PILOT_DEFAULTS, **(config or {})}
    rng = np.random.default_rng(c["seed"])
    nsta = picks[picks.event_id != ""].groupby("event_id").station_id.nunique()
    ev = events[events.event_id.isin(nsta.index)].copy()
    ev["n_sta"] = ev.event_id.map(nsta)
    n = int(c["events"])
    if len(ev) <= n:
        return {"representative": list(ev.event_id), "busiest": [], "largest": []}
    n_rep = int(round(n * c["representative_share"]))
    n_busy = int(round(n * c["busiest_share"]))
    n_large = n - n_rep - n_busy
    taken: set[str] = set()

    # largest: the events picked at the most stations, then the largest catalog magnitudes
    by_sta = list(ev.sort_values(["n_sta", "time"], ascending=[False, True]).event_id)
    by_mag = list(ev.dropna(subset=["magnitude"]).sort_values("magnitude", ascending=False).event_id)
    largest = []
    for a, b in zip(by_sta, by_mag + [None] * max(0, len(by_sta) - len(by_mag))):
        for e in (a, b):
            if e is not None and e not in taken and len(largest) < n_large:
                largest.append(e)
                taken.add(e)
        if len(largest) >= n_large:
            break

    # busiest: the window with the most events, all of them (or a random part if too many)
    w = c["busiest_window_s"]
    t = np.sort(ev.time.to_numpy())
    j = np.searchsorted(t, t + w)
    i = int(np.argmax(j - np.arange(len(t))))
    in_busy = ev[(ev.time >= t[i]) & (ev.time < t[i] + w) & ~ev.event_id.isin(taken)]
    busiest = list(in_busy.event_id.sample(min(n_busy, len(in_busy)), random_state=c["seed"]).sort_values()) if len(in_busy) else []
    taken.update(busiest)

    # representative: equal numbers from equal-duration time strata x quantiles of stations per event
    rest = ev[~ev.event_id.isin(taken)].copy()
    rest["ts"] = pd.cut(rest.time, int(c["time_strata"]), labels=False)
    rest["ps"] = pd.qcut(rest.n_sta.rank(method="first"), int(c["pick_strata"]), labels=False)
    cells = [g for _, g in rest.groupby(["ts", "ps"])]
    per = max(1, int(np.ceil(n_rep / max(len(cells), 1))))
    take = pd.concat([g.sample(min(per, len(g)), random_state=int(rng.integers(1 << 30))) for g in cells])
    if len(take) > n_rep:
        take = take.sample(n_rep, random_state=c["seed"])
    representative = list(take.sort_values("time").event_id)
    return {"representative": representative, "busiest": busiest, "largest": largest}


def select_windows(index: pd.DataFrame, stations: pd.DataFrame, span: tuple[float, float], config: dict | None = None,
                   reader=None, picks: pd.DataFrame | None = None) -> tuple[list[dict], dict]:
    """Time windows for a pilot run before any catalog exists.

    ``representative``: one window at a random start inside each of ``n_windows`` equal-duration strata;
    ``busiest``: with ``picks`` (picks of a first picking pass, associated or not) the window with the
    most picks, otherwise the window with the most 20-s bins in which ≥ 3 stations show a transient well
    above their running 10-min noise level (an event-rate proxy); ``largest``: the window around the bin
    where the most stations show a transient at once, with the highest median energy. The scan uses up
    to ``scan_stations`` stations nearest the network centre."""
    from .waveforms import Reader, activity_scan
    c = {"n_windows": 6, "window_s": 1800.0, "scan_stations": 6, "seed": 0, **(config or {})}
    rng = np.random.default_rng(c["seed"])
    t0, t1 = span
    w = float(c["window_s"])
    edges = np.linspace(t0, t1, int(c["n_windows"]) + 1)
    windows = []
    for a, b in zip(edges[:-1], edges[1:]):
        start = a if b - a <= w else float(a + rng.uniform(0, b - a - w))
        windows.append({"part": "representative", "start": start, "end": min(start + w, t1)})
    have = stations[stations.station_id.isin(index.station_id.unique())]
    lat0, lon0 = float(have.latitude.median()), float(have.longitude.median())
    near = have.assign(d=np.hypot(have.latitude - lat0, (have.longitude - lon0) * np.cos(np.deg2rad(lat0))))
    scan_sta = list(near.sort_values("d").station_id[:int(c["scan_stations"])])
    reader = reader or Reader(index)
    names, _, _, count, medr = activity_scan(reader, index, span, scan_sta, background_s=c.get("background_s", 600.0))
    info = {"scan_stations": names, "bins": int(len(count))}
    if picks is not None and len(picks):
        t = np.sort(picks.time.to_numpy())
        j = np.searchsorted(t, t + w)
        i = int(np.argmax(j - np.arange(len(t))))
        windows.append({"part": "busiest", "start": float(t[i]), "end": float(t[i]) + w, "picks": int(j[i] - i), "from": "picks"})
    if len(count):
        bin_s = 20.0
        per_window = max(1, int(w // bin_s))
        if picks is None or not len(picks):
            busy = np.convolve((count >= 3).astype(float), np.ones(per_window), mode="valid")
            b0 = int(np.argmax(busy))
            windows.append({"part": "busiest", "start": t0 + b0 * bin_s, "end": t0 + b0 * bin_s + w,
                            "energetic_bins": int(busy[b0]), "from": "waveform scan"})
        order = np.lexsort((np.arange(len(count)), -np.nan_to_num(medr), -count))
        big = int(order[0])
        tb = t0 + big * bin_s
        windows.append({"part": "largest", "start": max(t0, tb - 0.25 * w), "end": min(t1, tb + 0.75 * w),
                        "energetic_stations": int(count[big])})
        info["bins_with_3plus_energetic_stations"] = int((count >= 3).sum())
    return windows, info
