"""Checks that help attribute a symptom: what the data can constrain, and which errors have a structure.

An error with a structure (one station, one phase, a step in time, a dependence on distance) can be
traced in the data; an error shared by all stations or events is absorbed by origin times, station
terms or the magnitude constant and cannot. These checks measure such structures. They describe; the
Agent decides what they mean. Sources for each rule are in docs/research/reference/seismology_qc/.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .checks import Check, Data, _skip

DIAGNOSTIC_DEFAULTS = {
    "s_within_depth_factor": 1.4,          # a correct S within 1.4 focal depths constrains depth to about ±1.5 km
    "gt_min_stations": 10, "gt_gap_max": 110.0, "gt_secondary_gap_max": 160.0, "gt_nearest_km_max": 30.0,
    "pile_feature_tolerance_km": 0.1,
    "delay_min_picks": 20, "delay_min_s": 0.1,
    "step_min_picks_side": 30, "step_min_days_side": 2,
    "wadati_vpvs_plausible": [1.5, 2.1], "wadati_pick_outlier_s": 0.5, "wadati_event_min_pairs": 6, "wadati_event_min_span_s": 2.0,
    "day_hours": [9, 17], "night_hours": [21, 5], "day_night_min_days": 14,
    "b_positive_delta": 0.2, "b_positive_min_pairs": 100,
}


def _gaps(az: np.ndarray) -> tuple[float, float]:
    """Largest azimuthal gap and the secondary gap (largest gap when any one station is removed)."""
    s = np.unique(np.round(az % 360, 3))
    if len(s) < 3:
        return 360.0, 360.0
    d = np.diff(np.r_[s, s[0] + 360])
    pair = d + np.roll(d, -1)  # removing station i+1 joins gaps i and i+1
    return float(d.max()), float(pair.max())


def depth_constraint(d: Data, c: dict) -> tuple[Check, pd.DataFrame]:
    """Per event: is depth constrained (a S pick within 1.4 focal depths), and a GT5-like geometry class."""
    c = {**DIAGNOSTIC_DEFAULTS, **c}
    expected = "reported: share of located events with an S pick at a station closer than 1.4× the focal depth"
    p = d.picks.dropna(subset=["x", "depth_km"])
    if p.empty:
        return _skip("depth_constraint", "space", "share", expected, 0, "no located events with picks at known stations"), pd.DataFrame()
    p = p.assign(az=np.degrees(np.arctan2(p.x_sta - p.x, p.y_sta - p.y)))
    rows = []
    for eid, g in p.groupby("event_id"):
        z = float(g.dz_km.iloc[0])
        s_near = bool(((g.phase == "S") & (g.epi_km <= c["s_within_depth_factor"] * max(z, 0.0))).any())
        gap, gap2 = _gaps(g.az.to_numpy())
        nsta = int(g.station_id.nunique())
        nearest = float(g.epi_km.min())
        gt = nsta >= c["gt_min_stations"] and gap < c["gt_gap_max"] and gap2 < c["gt_secondary_gap_max"] and nearest < c["gt_nearest_km_max"]
        rows.append({"event_id": eid, "depth_km": float(g.depth_km.iloc[0]), "s_within_depth": s_near, "gap": gap,
                     "secondary_gap": gap2, "nearest_km": nearest, "stations": nsta, "gt_like": gt})
    ev = pd.DataFrame(rows)
    share = float(ev.s_within_depth.mean())
    z = ev.depth_km.round(2)
    mode = float(z.value_counts().idxmax())
    in_pile = ev[z == mode]
    details = {"share_gt_like": round(float(ev.gt_like.mean()), 3),
               "median_nearest_km": round(float(ev.nearest_km.median()), 2),
               "median_secondary_gap_deg": round(float(ev.secondary_gap.median()), 1),
               "most_common_depth_km": mode, "events_at_most_common_depth": int(len(in_pile)),
               "share_constrained_at_most_common_depth": round(float(in_pile.s_within_depth.mean()), 3) if len(in_pile) else None,
               "most_common_depth_is_round": bool(abs(mode * 2 - round(mode * 2)) < 0.011),
               "note": "a pile-up at a round value (whole or half kilometre) is often a fixed or trial depth; a pile-up of events "
                       "without depth constraint points to the location set-up (grid, interface, search bound); a pile-up of "
                       "constrained events at a value that is not round points to the velocity model or to real structure"}
    return Check("depth_constraint", "space", share, "share", expected, len(ev), False, None, details), ev


def pile_against_setup(d: Data, c: dict) -> Check | None:
    """Where the most common depth lies relative to the location set-up the Agent declares (``location_setup``).

    ``location_setup``: {"interfaces_km_bsl": [...], "search_depth_km_bsl": [top, bottom],
    "grid_spacing_km": g, "grid_origin_km_bsl": z0, "trial_depth_km_bsl": z} (any subset; km below sea level)."""
    c = {**DIAGNOSTIC_DEFAULTS, **c}
    setup = c.get("location_setup")
    expected = "reported: distance of the most common depth to each feature of the declared location set-up"
    z = d.events.depth_km.dropna().round(2)
    if not setup or len(z) < 20:
        return None
    mode = float(z.value_counts().idxmax())
    share = float((z == mode).mean())
    tol = c["pile_feature_tolerance_km"]
    g = setup.get("grid_spacing_km")
    # an interface pile can sit on the grid node next to the interface, up to one grid spacing away
    found = [("layer interface", float(zi), max(tol, g or 0.0)) for zi in setup.get("interfaces_km_bsl", [])]
    found += [("search bound", float(zi), tol) for zi in setup.get("search_depth_km_bsl", [])]
    if setup.get("trial_depth_km_bsl") is not None:
        found.append(("trial depth", float(setup["trial_depth_km_bsl"]), tol))
    if g:
        z0 = float(setup.get("grid_origin_km_bsl", 0.0))
        found.append(("travel-time grid node", float(z0 + round((mode - z0) / g) * g), tol))
    near = sorted(((abs(mode - v), name, v, t) for name, v, t in found))
    matches = [{"feature": n, "depth_km": round(v, 3), "distance_km": round(dist, 3)} for dist, n, v, t in near if dist <= t]
    return Check("pile_against_setup", "space", share, "share", expected, int(len(z)), False, None,
                 {"most_common_depth_km": mode, "nearest_features": [{"feature": n, "depth_km": round(v, 3), "distance_km": round(dist, 3)} for dist, n, v, t in near[:4]],
                  "within_tolerance": matches,
                  "note": "a pile next to a layer interface that sits on a grid node is the signature of a step model with a coarse "
                          "travel-time grid: relocating the piled events with a gradient version or a finer grid moves it"})


def _residuals(d: Data) -> pd.DataFrame:
    """Pick residuals about the catalog's own median travel-time curve per phase, event median removed."""
    p = d.picks[np.isfinite(d.picks.hyp_km) & np.isfinite(d.picks.tt)].copy()
    p["res"] = np.nan
    for ph, g in p.groupby("phase"):
        if len(g) < 50:
            continue
        edges = np.unique(np.quantile(g.hyp_km, np.linspace(0, 1, min(40, len(g) // 25) + 1)))
        mid = 0.5 * (edges[1:] + edges[:-1])
        med = [np.median(g.tt[(g.hyp_km >= lo) & (g.hyp_km <= hi)]) for lo, hi in zip(edges[:-1], edges[1:])]
        p.loc[g.index, "res"] = g.tt - np.interp(g.hyp_km, mid, med)
    p = p.dropna(subset=["res"])
    p["res"] -= p.groupby(["event_id", "phase"]).res.transform("median")
    return p


def station_delays(d: Data, c: dict, res: pd.DataFrame | None = None) -> Check:
    """Per station: median P and S residuals and their ratio.

    A clock or instrument delay shifts P and S by the same time (δS/δP ≈ 1); a slow or fast path shifts S
    by about Vp/Vs times more (δS/δP ≈ 1.7). The residuals are relative to the catalog's own travel-time
    curve, so they carry 3-D structure as well (reported, not judged)."""
    c = {**DIAGNOSTIC_DEFAULTS, **c}
    expected = "reported: stations with |median P residual| ≥ 0.1 s and their δS/δP"
    res = _residuals(d) if res is None else res
    if res.empty:
        return _skip("station_delays", "time", "stations", expected, 0, "no located picks")
    st = res.groupby(["station_id", "phase"]).res.agg(["median", "size"]).unstack("phase")
    rows = {}
    for sta, r in st.iterrows():
        dp, np_ = r.get(("median", "P")), r.get(("size", "P"))
        ds, ns = r.get(("median", "S")), r.get(("size", "S"))
        if not (np.isfinite(np_) and np_ >= c["delay_min_picks"]) or abs(dp) < c["delay_min_s"]:
            continue
        ratio = float(ds / dp) if np.isfinite(ns) and ns >= c["delay_min_picks"] else None
        kind = None if ratio is None else ("same in P and S (clock or instrument-like)" if 0.7 <= ratio <= 1.3 else
                                            ("about Vp/Vs (path-like)" if 1.4 <= ratio <= 2.2 else "neither"))
        rows[sta] = {"dP_s": round(float(dp), 3), "dS_s": None if ratio is None else round(float(ds), 3), "dS_over_dP": None if ratio is None else round(ratio, 2),
                     "pattern": kind, "n_P": int(np_), "n_S": int(ns) if np.isfinite(ns) else 0}
    return Check("station_delays", "time", float(len(rows)), "stations", expected, int(len(st)), False, None,
                 {"stations": rows, "clock_like": sorted(s for s, r in rows.items() if r["pattern"] and r["pattern"].startswith("same"))})


def station_time_steps(d: Data, c: dict, res: pd.DataFrame | None = None) -> Check:
    """Per station: the largest step in its daily median P residual, with the S step at the same time.

    A clock jump or an instrument swap is a step that is equal in P and S; seismicity moving to another
    part of the source region changes residuals gradually and more in S."""
    c = {**DIAGNOSTIC_DEFAULTS, **c}
    expected = "reported: largest step in a station's P residual between two periods of ≥ 2 days, with the S step"
    res = _residuals(d) if res is None else res
    if res.empty or np.ptp(res.time) < 4 * 86400:
        return _skip("station_time_steps", "time", "s", expected, 0, "less than four days of located picks")
    res = res.assign(day=np.floor(res.time / 86400))
    out = {}
    for sta, g in res.groupby("station_id"):
        gp, gs = g[g.phase == "P"], g[g.phase == "S"]
        days = np.unique(gp.day)
        best = None
        for k in days[c["step_min_days_side"]:len(days) - c["step_min_days_side"] + 1]:
            a, b = gp.res[gp.day < k], gp.res[gp.day >= k]
            if len(a) < c["step_min_picks_side"] or len(b) < c["step_min_picks_side"]:
                continue
            step = float(b.median() - a.median())
            if best is None or abs(step) > abs(best[1]):
                sa, sb = gs.res[gs.day < k], gs.res[gs.day >= k]
                s_step = float(sb.median() - sa.median()) if len(sa) >= 10 and len(sb) >= 10 else None
                best = (k, step, s_step)
        if best is not None:
            out[sta] = {"day_utc": pd.Timestamp(best[0] * 86400, unit="s", tz="UTC").strftime("%Y-%m-%d"),
                        "P_step_s": round(best[1], 3), "S_step_s": None if best[2] is None else round(best[2], 3)}
    if not out:
        return _skip("station_time_steps", "time", "s", expected, 0, "no station with enough picks on both sides of a split")
    worst = max(out, key=lambda s: abs(out[s]["P_step_s"]))
    top = dict(sorted(out.items(), key=lambda kv: -abs(kv[1]["P_step_s"]))[:8])
    return Check("station_time_steps", "time", abs(out[worst]["P_step_s"]), "s", expected, len(out), False, None,
                 {"largest": {worst: out[worst]}, "top_stations": top})


def wadati_events(d: Data, c: dict) -> Check:
    """Per-event Wadati lines: share of events with an implausible Vp/Vs, and S picks off their event's line."""
    c = {**DIAGNOSTIC_DEFAULTS, **c}
    lo, hi = c["wadati_vpvs_plausible"]
    expected = f"reported: share of events (≥ {c['wadati_event_min_pairs']} P–S pairs over ≥ {c['wadati_event_min_span_s']} s of P times) whose Wadati Vp/Vs lies outside [{lo}, {hi}]; share of S picks > {c['wadati_pick_outlier_s']} s off their event's line"
    p = d.picks
    pp = p[p.phase == "P"].groupby(["event_id", "station_id"]).time.min()
    ss = p[p.phase == "S"].groupby(["event_id", "station_id"]).time.min()
    pairs = pd.concat({"tp": pp, "ts": ss}, axis=1).dropna().reset_index()
    if pairs.empty:
        return _skip("wadati_events", "time", "share", expected, 0, "no P–S pairs")
    bad, n_ev, off, n_pairs = 0, 0, 0, 0
    for _, g in pairs.groupby("event_id"):
        if len(g) < c["wadati_event_min_pairs"] or np.ptp(g.tp) < c["wadati_event_min_span_s"]:
            continue
        x, y = (g.tp - g.tp.min()).to_numpy(), (g.ts - g.tp).to_numpy()
        a, b = np.polyfit(x, y, 1)
        r = y - (a * x + b)
        n_ev += 1
        bad += not lo <= 1 + a <= hi
        off += int((np.abs(r) > c["wadati_pick_outlier_s"]).sum())
        n_pairs += len(g)
    if n_ev < 20:
        return _skip("wadati_events", "time", "share", expected, n_ev, f"{n_ev} events with enough P–S pairs")
    return Check("wadati_events", "time", bad / n_ev, "share", expected, n_ev, False, None,
                 {"share_s_picks_off_line": round(off / n_pairs, 4), "pairs": n_pairs,
                  "note": "the Wadati line uses only the event's own P and S times, so it is independent of the velocity model and of the location"})


def day_night(d: Data, c: dict) -> Check:
    """Ratio of daytime to night-time event rates (local solar time), above and below the median magnitude.

    Blasting adds daytime events (ratio ≥ 1.5 in quarry areas); cultural noise hides small daytime events
    (ratio below 1 for small events only)."""
    c = {**DIAGNOSTIC_DEFAULTS, **c}
    expected = "reported: median over days of the daytime event rate over the rate of the nights before and after (local solar time)"
    e = d.events.dropna(subset=["longitude"])
    if len(e) < 100:
        return _skip("day_night_ratio", "reality", "ratio", expected, len(e), "fewer than 100 located events")
    if np.ptp(e.time) < c["day_night_min_days"] * 86400:
        # in shorter windows a decaying sequence and single bursts dominate the daily counts
        return _skip("day_night_ratio", "reality", "ratio", expected, len(e), f"less than {c['day_night_min_days']} days of events")
    local = (e.time + e.longitude / 15.0 * 3600.0).to_numpy()  # local solar time in seconds
    hour = (local / 3600.0) % 24
    day_no = np.floor(local / 86400.0)
    d0, d1 = c["day_hours"]
    n0, n1 = c["night_hours"]
    m = e.magnitude.to_numpy()
    has_m = np.isfinite(m).any()
    big = np.isfinite(m) & (m >= np.nanmedian(m)) if has_m else np.ones(len(e), bool)
    small = np.isfinite(m) & (m < np.nanmedian(m)) if has_m else np.ones(len(e), bool)

    def ratio(mask):
        """Median over days of the daytime rate over the mean rate of the nights before and after: a decaying
        aftershock rate cancels, a daily cycle does not."""
        out = []
        for k in np.unique(day_no):
            dmask = mask & (day_no == k) & (hour >= d0) & (hour < d1)
            before = mask & (((day_no == k - 1) & (hour >= n0)) | ((day_no == k) & (hour < n1)))
            after = mask & (((day_no == k) & (hour >= n0)) | ((day_no == k + 1) & (hour < n1)))
            nb, na = before.sum(), after.sum()
            nights = (nb + na) / (2 * ((24 - n0) + n1))
            if nights * ((24 - n0) + n1) < 3:  # too few night events for a ratio
                continue
            out.append((dmask.sum() / (d1 - d0)) / nights)
        return round(float(np.median(out)), 3) if len(out) >= 3 else None

    r = ratio(np.ones(len(e), bool))
    return Check("day_night_ratio", "reality", r, "ratio", expected, len(e), False, None,
                 {"larger_half": ratio(big) if has_m else None, "smaller_half": ratio(small) if has_m else None,
                  "hourly_counts": np.bincount(hour.astype(int) % 24, minlength=24).tolist(),
                  "note": "a daytime excess in the larger events points to blasting; a night-time excess in the smaller events only points to daytime noise"})


def b_positive(d: Data, c: dict, standard: Check | None = None) -> Check:
    """b-value from positive magnitude differences of consecutive events (van der Elst, 2021), robust to
    the changing completeness early in a sequence; shown next to the standard estimate."""
    c = {**DIAGNOSTIC_DEFAULTS, **c}
    expected = "reported: b from magnitude differences ≥ δ between consecutive events"
    m = d.events.sort_values("time").magnitude.dropna().to_numpy()
    dm = np.diff(m)
    delta = c["b_positive_delta"]
    pos = dm[dm >= delta]
    if len(pos) < c["b_positive_min_pairs"] or pos.mean() - delta <= 0:
        return _skip("b_positive", "strength", "b", expected, len(pos), f"{len(pos)} positive differences ≥ {delta}")
    b = float(np.log10(np.e) / (pos.mean() - delta))
    std = None if standard is None else {"b": None if standard.measured is None else round(float(standard.measured), 3),
                                          "mc": (standard.details or {}).get("mc"), "n": int(standard.n)}
    return Check("b_positive", "strength", b, "b", expected, len(pos), False, None,
                 {"delta": delta, "standard_b_value": std,
                  "note": "a standard b-value much lower than b-positive points to incompleteness rather than physics"})


def duplicate_pick_overlap(d: Data, c: dict) -> dict:
    """For pairs of events within the duplicate window: share that share picks (same station, phase and time)."""
    e = d.events.sort_values("time")
    t, ids = e.time.to_numpy(), e.event_id.to_numpy()
    hi = np.searchsorted(t, t + c["duplicate_dt_s"], side="right")
    picks = {eid: set(zip(g.station_id, g.phase, np.round(g.time, 2))) for eid, g in d.all_picks[d.all_picks.event_id != ""].groupby("event_id")}
    pairs, shared = 0, 0
    for i in range(len(e)):
        for j in range(i + 1, hi[i]):
            a, b = picks.get(ids[i], set()), picks.get(ids[j], set())
            if not a or not b:
                continue
            pairs += 1
            shared += len(a & b) >= 2
    return {"close_pairs": pairs, "pairs_sharing_picks": shared,
            "note": "pairs that share picks are the same event entered twice; pairs that do not may be real doublets"}
