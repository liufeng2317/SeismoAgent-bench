"""Checks of the picking and association stages, available before any event is located.

Picks stage: only ``picks.csv`` (associated or not) and, optionally, the waveform folder, whose file
names tell which station-days have data. Association stage: picks plus the event table; locations may
still be missing. Symptoms only, as everywhere in the checker.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .checks import Check, Data, _skip

STAGE_DEFAULTS = {
    "silent_station_share_max": 0.10, "station_day_gap_share_max": 0.05,
    "duplicate_pick_s": 0.3, "duplicate_pick_share_max": 0.02,
    "s_to_p_min": 0.3, "s_to_p_max": 1.5,
    "associated_share_min": 0.1, "busy_hour_quantile": 0.9, "busy_hour_ratio_min": 0.5,
}


def _span(d: Data) -> tuple[float, float]:
    t = d.all_picks.time
    return float(t.min()), float(t.max())


def silent_stations(d: Data, c: dict) -> Check:
    expected = f"share ≤ {c['silent_station_share_max']:.0%} of stations with waveform data but no pick"
    if d.waveforms is None or d.waveforms.empty or d.all_picks.empty:
        return _skip("silent_stations", "reality", "share", expected, 0, "no waveform folder given or no picks")
    t0, t1 = _span(d)
    w = d.waveforms[(d.waveforms.day <= t1) & (d.waveforms.day + 86400 > t0)]
    with_data = sorted(w.station_id.unique())
    picked = set(d.all_picks.station_id)
    silent = [s for s in with_data if s not in picked]
    share = len(silent) / len(with_data) if with_data else 0.0
    vertical_only = sorted(s for s in silent if set(w[w.station_id == s].channel.str[-1]) <= {"Z"})
    flag = share > c["silent_station_share_max"]
    return Check("silent_stations", "reality", share, "share", expected, len(with_data), flag,
                 (f"{len(silent)} of {len(with_data)} stations with waveform data in the processed period have no pick "
                  f"({', '.join(silent[:12])}{' …' if len(silent) > 12 else ''})"
                  + (f"; {len(vertical_only)} of them have vertical channels only." if vertical_only else ".")) if flag else None,
                 {"silent": silent, "vertical_only": vertical_only})


def station_day_gaps(d: Data, c: dict) -> Check:
    expected = f"share ≤ {c['station_day_gap_share_max']:.0%} of station-days with data but no pick, at stations picked on other days"
    if d.waveforms is None or d.waveforms.empty or d.all_picks.empty:
        return _skip("station_day_gaps", "reality", "share", expected, 0, "no waveform folder given or no picks")
    t0, t1 = _span(d)
    days = d.waveforms[(d.waveforms.day <= t1) & (d.waveforms.day + 86400 > t0)][["station_id", "day"]].drop_duplicates()
    picks = d.all_picks.assign(day=np.floor(d.all_picks.time / 86400) * 86400)
    picked_days = set(zip(picks.station_id, picks.day))
    days = days[days.station_id.isin(set(picks.station_id))]
    if days.empty:
        return _skip("station_day_gaps", "reality", "share", expected, 0, "no station-days with data at picked stations")
    missing = days[[(s, dd) not in picked_days for s, dd in zip(days.station_id, days.day)]]
    share = len(missing) / len(days)
    flag = share > c["station_day_gap_share_max"]
    worst = missing.station_id.value_counts().head(5)
    return Check("station_day_gaps", "reality", share, "share", expected, len(days), flag,
                 (f"{len(missing)} of {len(days)} station-days with waveform data have no pick at stations that are picked on other days "
                  f"(most: {', '.join(f'{s} {n} d' for s, n in worst.items())}).") if flag else None)


def duplicate_picks(d: Data, c: dict) -> Check:
    expected = f"share ≤ {c['duplicate_pick_share_max']:.0%} of picks within {c['duplicate_pick_s']} s of another pick of the same station and phase"
    p = d.all_picks.sort_values(["station_id", "phase", "time"])
    if len(p) < 2:
        return _skip("duplicate_picks", "reality", "share", expected, len(p), "fewer than 2 picks")
    same = (p.station_id.values[1:] == p.station_id.values[:-1]) & (p.phase.values[1:] == p.phase.values[:-1])
    close = same & (np.diff(p.time.values) <= c["duplicate_pick_s"])
    dup = np.zeros(len(p), dtype=bool)
    dup[1:] |= close
    dup[:-1] |= close
    share = float(dup.mean())
    flag = share > c["duplicate_pick_share_max"]
    return Check("duplicate_picks", "reality", share, "share", expected, len(p), flag,
                 f"{share:.1%} of picks have another pick of the same station and phase within {c['duplicate_pick_s']} s." if flag else None)


def s_to_p(d: Data, c: dict) -> Check:
    expected = f"S picks between {c['s_to_p_min']} and {c['s_to_p_max']} × P picks"
    n_p = int((d.all_picks.phase == "P").sum())
    n_s = int((d.all_picks.phase == "S").sum())
    if n_p == 0:
        return _skip("s_to_p_ratio", "reality", "ratio", expected, 0, "no P picks")
    ratio = n_s / n_p
    flag = ratio < c["s_to_p_min"] or ratio > c["s_to_p_max"]
    no_s = sorted(set(d.all_picks[d.all_picks.phase == "P"].station_id) - set(d.all_picks[d.all_picks.phase == "S"].station_id))
    symptom = (f"There are {ratio:.2f} S picks per P pick ({n_s:,} S, {n_p:,} P); {len(no_s)} stations have P picks but no S pick."
               if ratio < c["s_to_p_min"] else f"There are {ratio:.2f} S picks per P pick ({n_s:,} S, {n_p:,} P): more S than P picks.")
    return Check("s_to_p_ratio", "reality", ratio, "ratio", expected, n_p, flag, symptom if flag else None,
                 {"stations_without_s": no_s})


def picks_checks(d: Data, c: dict) -> list[Check]:
    c = {**STAGE_DEFAULTS, **c}
    return [silent_stations(d, c), station_day_gaps(d, c), duplicate_picks(d, c), s_to_p(d, c)]


def associated_share(d: Data, c: dict) -> Check:
    expected = f"share ≥ {c['associated_share_min']:.0%} of picks associated with an event"
    p = d.all_picks
    if p.empty:
        return _skip("associated_share", "reality", "share", expected, 0, "no picks")
    share = float((p.event_id != "").mean())
    flag = share < c["associated_share_min"]
    return Check("associated_share", "reality", share, "share", expected, len(p), flag,
                 f"Only {share:.1%} of {len(p):,} picks are associated with an event." if flag else None)


def association_busy_hours(d: Data, c: dict) -> Check:
    expected = f"associated share in the busiest {1 - c['busy_hour_quantile']:.0%} of hours ≥ {c['busy_hour_ratio_min']}× the overall share"
    p = d.all_picks
    if len(p) < 1000:
        return _skip("association_busy_hours", "reality", "ratio", expected, len(p), "fewer than 1000 picks")
    hour = np.floor(p.time / 3600)
    g = pd.DataFrame({"hour": hour, "assoc": p.event_id != ""}).groupby("hour").assoc.agg(["size", "mean"])
    overall = float((p.event_id != "").mean())
    busy = g[g["size"] >= g["size"].quantile(c["busy_hour_quantile"])]
    if overall == 0 or busy.empty:
        return _skip("association_busy_hours", "reality", "ratio", expected, len(g), "no associated picks")
    busy_share = float((busy["size"] * busy["mean"]).sum() / busy["size"].sum())
    ratio = busy_share / overall
    flag = ratio < c["busy_hour_ratio_min"]
    return Check("association_busy_hours", "reality", ratio, "ratio", expected, len(busy), flag,
                 f"In the busiest hours {busy_share:.1%} of picks are associated, against {overall:.1%} overall." if flag else None,
                 {"busy_hours": int(len(busy)), "overall_share": round(overall, 4)})


def association_checks(d: Data, c: dict) -> list[Check]:
    c = {**STAGE_DEFAULTS, **c}
    return [associated_share(d, c), association_busy_hours(d, c)]
