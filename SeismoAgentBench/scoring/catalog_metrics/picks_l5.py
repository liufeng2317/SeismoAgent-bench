"""L5 phase picks against a reference pick set (docs/framework/03_EVALUATION_METRICS.md §5 L5).

Picks are compared on the stations present in both sets, within the case's
evaluation window. Within each (station, phase) group candidate and
reference picks are paired one-to-one, greedily by |dt| <= 0.5 s; the 0.1 s
figures are the subset of those pairs. A reference pick set covers only the
events of its own catalog, so precision is a lower bound and recall and the
residuals are the informative numbers.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .tables import epoch_seconds

TOLERANCES_S = (0.5, 0.1)


def read_reference_picks(path: Path, fmt: str) -> pd.DataFrame:
    """Reference picks as station (NET.STA), phase (P/S), time (epoch s)."""
    if fmt == "baker_csv":
        raw = pd.read_csv(path, usecols=["network", "station", "phase", "arrival_time"], dtype=str)
        time = epoch_seconds(raw.arrival_time)
    elif fmt == "shelly_phase_csv":
        raw = _collapse_shelly(pd.read_csv(path, usecols=["match_id", "network", "station", "phase", "arrival", "weight"],
                                           dtype={"network": str, "station": str}))
        time = raw.arrival.to_numpy(dtype=float)
    else:
        raise ValueError(f"unknown pick reference format {fmt!r}")
    out = pd.DataFrame({"station": raw.network.str.strip() + "." + raw.station.str.strip(),
                        "phase": raw.phase.str.strip().str.upper().str[0], "time": time})
    return out[out.phase.isin(["P", "S"]) & np.isfinite(out.time)].reset_index(drop=True)


def _collapse_shelly(raw: pd.DataFrame, merge_s: float = 0.5) -> pd.DataFrame:
    """One arrival per event, station and phase from a template-pair phase release.

    Shelly & Hardebeck (2019) list one row per (template, detection) pair: each
    detection's arrival at a station appears once per matching template
    (~12 times in the Maple Creek window, spread median 0.21 s). Keep the
    highest-weight row per (match_id, station, phase), then merge arrivals of
    the same station and phase closer than ``merge_s`` (several match_ids of
    one earthquake), again keeping the highest weight.
    """
    raw = raw.dropna(subset=["arrival"])
    best = raw.loc[raw.groupby(["match_id", "network", "station", "phase"]).weight.idxmax()]
    best = best.sort_values(["network", "station", "phase", "arrival"]).reset_index(drop=True)
    same = (best[["network", "station", "phase"]].eq(best[["network", "station", "phase"]].shift()).all(axis=1)
            & (best.arrival.diff() <= merge_s))
    best["cluster"] = (~same).cumsum()
    return best.loc[best.groupby("cluster").weight.idxmax()].reset_index(drop=True)


def read_candidate_picks(path: Path) -> pd.DataFrame:
    """Agent picks.csv (station_id, phase, time_utc, status); rejected rows dropped."""
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    if "status" in raw:
        raw = raw[raw.status.str.strip().str.lower() != "rejected"]
    station = raw.station_id.str.strip() if "station_id" in raw else raw.instrument_id.str.split(".").str[:2].str.join(".")
    out = pd.DataFrame({"station": station.to_numpy(), "phase": raw.phase.str.strip().str.upper().str[0].to_numpy(),
                        "time": epoch_seconds(raw.time_utc)})
    return out[out.phase.isin(["P", "S"]) & np.isfinite(out.time)].reset_index(drop=True)


def _pair(tc: np.ndarray, tr: np.ndarray, tol: float) -> np.ndarray:
    """Signed residuals (candidate - reference) of greedy one-to-one pairs within tol."""
    order_r = np.argsort(tr)
    tr = tr[order_r]
    lo = np.searchsorted(tr, tc - tol, side="left")
    hi = np.searchsorted(tr, tc + tol, side="right")
    counts = hi - lo
    if counts.sum() == 0:
        return np.array([])
    ci = np.repeat(np.arange(len(tc)), counts)
    ri = np.arange(counts.sum()) - np.repeat(np.cumsum(counts) - counts, counts) + np.repeat(lo, counts)
    dt = tc[ci] - tr[ri]
    order = np.lexsort((ri, ci, np.abs(dt)))
    used_c = np.zeros(len(tc), bool)
    used_r = np.zeros(len(tr), bool)
    out = []
    for k in order:
        if not used_c[ci[k]] and not used_r[ri[k]]:
            used_c[ci[k]] = used_r[ri[k]] = True
            out.append(dt[k])
    return np.asarray(out)


def score_picks_l5(cand: pd.DataFrame, ref: pd.DataFrame, window: tuple[float, float]) -> dict:
    start, end = window
    ref = ref[(ref.time >= start) & (ref.time < end)]
    cand = cand[(cand.time >= start) & (cand.time < end)]
    common = sorted(set(cand.station) & set(ref.station))
    out = {"stations_common": len(common), "stations_reference": int(ref.station.nunique()),
           "stations_candidate": int(cand.station.nunique()), "phases": {}}
    for phase in ("P", "S"):
        c = cand[(cand.phase == phase) & cand.station.isin(common)]
        r = ref[(ref.phase == phase) & ref.station.isin(common)]
        residuals = [_pair(g.time.to_numpy(), r_g.time.to_numpy(), max(TOLERANCES_S))
                     for st, g in c.groupby("station") if len(r_g := r[r.station == st])]
        res = np.concatenate(residuals) if residuals else np.array([])
        entry = {"candidate": int(len(c)), "reference": int(len(r))}
        for tol in TOLERANCES_S:
            m = int((np.abs(res) <= tol + 1e-9).sum())
            entry[f"matched_{tol:g}s"] = m
            entry[f"recall_{tol:g}s"] = round(m / len(r), 4) if len(r) else None
            entry[f"precision_{tol:g}s"] = round(m / len(c), 4) if len(c) else None
        if len(res):
            entry["residual_median_s"] = round(float(np.median(res)), 4)
            entry["residual_mad_s"] = round(float(np.median(np.abs(res - np.median(res)))), 4)
        out["phases"][phase] = entry
    return out
