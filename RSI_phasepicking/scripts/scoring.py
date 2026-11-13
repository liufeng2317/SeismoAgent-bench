"""Scoring shared by the baselines and the agent (docs/design.md section 6).

Picks are scored against the analyst's manual picks: each manual pick is paired
with the nearest method pick of the same event, station and phase within the
tolerance, each method pick used once. Recall is over all manual picks;
precision only over (event, station, phase) cells the analyst also picked, so
a station the analyst skipped never counts against a method. Confidence
intervals resample events (cluster bootstrap).
"""
import numpy as np
import pandas as pd
from obspy import UTCDateTime

TOLERANCE_S = {"P": 0.5, "S": 1.0}


def _sec(x):
    return np.array([UTCDateTime(str(v)).timestamp for v in x])


def match(method, ref, tolerance=None, search_s=3.0):
    """Pair manual picks with method picks.

    Returns one row per manual pick: residual_s (method - manual) of the
    nearest method pick within search_s, and matched (within the tolerance).
    Also returns the method picks in analyst-picked cells with a matched flag.
    """
    tol = {**TOLERANCE_S, **(tolerance or {})}
    ref = ref[ref["mode"] == "manual"].copy()
    ref["t"] = _sec(ref.time)
    m = method.copy()
    m["t"] = _sec(m.time_utc)
    m["mid"] = np.arange(len(m))
    rows, used = [], set()
    pairs = []
    for (eid, sta, ph), g in ref.groupby(["event_id", "station", "phase"]):
        cand = m[(m.event_id == eid) & (m.station == sta) & (m.phase == ph)]
        for r in g.itertuples():
            d = cand.t.values - r.t
            pairs += [(abs(x), r.Index, mid, x) for x, mid in zip(d, cand.mid.values) if abs(x) <= search_s]
    best = {}
    for ad, ri, mid, d in sorted(pairs):
        if ri in best or mid in used:
            continue
        best[ri] = (mid, d)
        used.add(mid)
    for r in ref.itertuples():
        mid, d = best.get(r.Index, (None, np.nan))
        rows.append(dict(event_id=r.event_id, station=r.station, phase=r.phase, channel=r.channel,
                         weight_code=r.weight_code, onset=r.onset, distance_km=r.distance_km,
                         residual_s=d, matched=bool(np.isfinite(d) and abs(d) <= tol[r.phase])))
    scored = pd.DataFrame(rows)
    cells = set(zip(ref.event_id, ref.station, ref.phase))
    in_cell = m[[c in cells for c in zip(m.event_id, m.station, m.phase)]].copy()
    good = {best[ri][0] for ri in best if abs(best[ri][1]) <= tol[ref.loc[ri, "phase"]]}
    in_cell["matched"] = in_cell.mid.isin(good)
    return scored, in_cell


def summarize(scored, in_cell):
    """Metrics of one method for one subset of manual picks."""
    hit = scored[scored.matched]
    a = hit.residual_s.abs()
    return dict(n_ref=len(scored), recall=hit.shape[0] / max(len(scored), 1),
                precision=in_cell.matched.mean() if len(in_cell) else np.nan,
                mae_s=a.mean() if len(a) else np.nan, bias_s=hit.residual_s.median() if len(hit) else np.nan,
                within_005=(a <= 0.05).mean() if len(a) else np.nan,
                within_01=(a <= 0.1).mean() if len(a) else np.nan,
                within_02=(a <= 0.2).mean() if len(a) else np.nan)


def bootstrap(scored, in_cell, n=1000, seed=0):
    """95% intervals of each metric, resampling events."""
    rng = np.random.default_rng(seed)
    ev = scored.event_id.unique()
    by_s = dict(tuple(scored.groupby("event_id")))
    by_m = dict(tuple(in_cell.groupby("event_id")))
    draws = []
    for _ in range(n):
        pick = rng.choice(ev, len(ev))
        s = pd.concat([by_s[e] for e in pick])
        m = pd.concat([by_m[e] for e in pick if e in by_m]) if any(e in by_m for e in pick) else in_cell.iloc[:0]
        draws.append(summarize(s, m))
    d = pd.DataFrame(draws)
    return {k: (float(d[k].quantile(0.025)), float(d[k].quantile(0.975))) for k in d.columns if k != "n_ref"}


def location_shift(loc, ref_loc):
    """Per-event difference of a method's location from a reference location (e.g. B8)."""
    from pipeline import distance_km
    a = loc[loc.status == "LOCATED"].set_index("event_id")
    b = ref_loc[ref_loc.status == "LOCATED"].set_index("event_id")
    j = a.join(b, rsuffix="_ref", how="inner")
    return pd.DataFrame(dict(
        event_id=j.index,
        epi_km=distance_km(j.latitude_ref, j.longitude_ref, j.latitude, j.longitude),
        depth_km=j.depth_km - j.depth_km_ref,
        time_s=[UTCDateTime(x) - UTCDateTime(y) for x, y in zip(j.origin_time_utc, j.origin_time_utc_ref)]))
