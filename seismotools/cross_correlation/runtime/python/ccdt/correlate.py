"""Normalized cross-correlation of event pairs and the differential time.

For a pair (a, b) at one station and phase, the *template* is the central
``n_template`` samples of a's search window (``[t_a - before, t_a + after]``,
first sample at ``s_a``); it slides over b's whole search window (first sample
``u_b``, ``2 k_lag + 1`` lags). At every lag the correlation is the Pearson
coefficient of the two equal-length segments (both demeaned, each normalized
over the overlap itself), so it is unbiased at every lag. For several
components (S on two horizontals) the per-component curves are averaged over
the components present for both events.

The peak must be positive, not on the first or last lag, at least
``min_cc``, and larger than the magnitude of the most negative value (a
polarity-reversed pair has its strongest extreme negative at the true lag and
positive side lobes half a period away, which a plain maximum would accept).
It is also rejected as *ambiguous* when another local maximum, at least
``guard`` samples away, reaches ``ambiguity_ratio`` of it — typically a second
event inside the search window (overlapping aftershocks), where the curve
cannot tell which arrival is the partner. A pair whose template and search
windows overlap in absolute time is rejected outright (``self_overlap``): the
template would find its own signal inside the partner's window. A parabola through the peak and its neighbours gives the
fractional lag ``p`` (|p| <= 0.5 sample). The template's first sample then
aligns with ``s'_b = u_b + (L + p) * delta`` in b, and the differential
travel time in hypoDD/GrowClust convention (event a minus event b) is

    dt = (s_a - o_a) - (s'_b - o_b)

which depends only on the two waveforms and origin times: the arrival times
used to place the windows (picks or predictions) cancel, as long as both
windows contain the phase.
"""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def cc_curves(tmpl: np.ndarray, search: np.ndarray) -> np.ndarray:
    """Pearson CC of tmpl (P, m) against every m-segment of search (P, m + 2K).

    Returns (P, 2K + 1). Rows with a zero-variance segment give 0."""
    tmpl = tmpl.astype(np.float64)
    search = search.astype(np.float64)
    m = tmpl.shape[1]
    t = tmpl - tmpl.mean(axis=1, keepdims=True)
    tn = np.sqrt((t * t).sum(axis=1))
    seg = sliding_window_view(search, m, axis=1)            # (P, 2K+1, m)
    num = np.einsum("pkm,pm->pk", seg, t)                    # sum(t * y); t is zero-mean
    s1 = seg.sum(axis=2)
    s2 = (seg * seg).sum(axis=2)
    var = s2 - s1 * s1 / m
    den = tn[:, None] * np.sqrt(np.clip(var, 0.0, None))
    with np.errstate(invalid="ignore", divide="ignore"):
        cc = np.where(den > 0, num / den, 0.0)
    return cc


def pick_peak(cc: np.ndarray):
    """Integer peak, its value and the parabolic fractional offset per row.

    Returns (lag_index, cc_peak, frac, ok_edge) with ok_edge False when the
    peak is on the first or last lag (no bracketing neighbours)."""
    n = cc.shape[1]
    k = np.argmax(cc, axis=1)
    rows = np.arange(cc.shape[0])
    peak = cc[rows, k]
    ok_edge = (k > 0) & (k < n - 1)
    km = np.clip(k - 1, 0, n - 1)
    kp = np.clip(k + 1, 0, n - 1)
    y0, y1, y2 = cc[rows, km], peak, cc[rows, kp]
    den = y0 - 2.0 * y1 + y2
    with np.errstate(invalid="ignore", divide="ignore"):
        frac = np.where(ok_edge & (den < 0), 0.5 * (y0 - y2) / den, 0.0)
    frac = np.clip(frac, -0.5, 0.5)
    # the parabola's vertex value (slightly above the sampled peak)
    peak_interp = np.where(ok_edge & (den < 0), y1 - 0.25 * (y0 - y2) * frac, y1)
    return k, peak_interp, frac, ok_edge


def second_peak(cc: np.ndarray, k: np.ndarray, guard: int) -> np.ndarray:
    """Largest interior local maximum at least ``guard`` lags from k (0 if none)."""
    n = cc.shape[1]
    loc = np.zeros_like(cc, dtype=bool)
    loc[:, 1:-1] = (cc[:, 1:-1] > cc[:, :-2]) & (cc[:, 1:-1] >= cc[:, 2:])
    far = np.abs(np.arange(n)[None, :] - k[:, None]) >= guard
    return np.where(loc & far, cc, 0.0).max(axis=1)


def measure_pairs(windows: Sequence[dict], ia: np.ndarray, ib: np.ndarray, origin: np.ndarray,
                  min_cc: float, min_snr: float, ambiguity_ratio: float = 0.9,
                  guard_s: float = 0.1) -> Dict[str, np.ndarray]:
    """Differential times for pairs (ia[i], ib[i]) (event row indices) at one
    station and phase. ``windows`` holds one extract_channel result per
    component (same station/phase); rows index ``origin``."""
    P = len(ia)
    n_comp = np.zeros(P, dtype=np.int64)
    acc = None
    s_a = np.full(P, np.nan)
    u_b = np.full(P, np.nan)
    snr_a = np.full(P, np.nan)
    snr_b = np.full(P, np.nan)
    delta = windows[0]["delta"]
    n_long = windows[0]["data"].shape[1]
    m_tmpl = windows[0]["n_template"]
    for w in windows:
        if abs(w["delta"] - delta) > 1e-9:
            raise ValueError("components of one station/phase must share the sampling rate")
        pos = {int(r): j for j, r in enumerate(w["rows"])}
        ja = np.array([pos.get(int(r), -1) for r in ia])
        jb = np.array([pos.get(int(r), -1) for r in ib])
        use = (ja >= 0) & (jb >= 0)
        use[use] &= w["valid"][ja[use]] & w["valid"][jb[use]]
        if not use.any():
            continue
        k = w["k_lag"]
        m = w["n_template"]
        tmpl = w["data"][ja[use], k:k + m]
        srch = w["data"][jb[use]]
        cc = cc_curves(tmpl, srch)
        if acc is None:
            acc = np.zeros((P, cc.shape[1]))
        acc[use] += cc
        n_comp[use] += 1
        # window starts and SNRs are shared by the components of one
        # instrument up to sample timing; keep the first component's
        first = use & np.isnan(s_a)
        s_a[first] = w["start"][ja[first]] + k * delta
        u_b[first] = w["start"][jb[first]]
        snr_a[first] = w["snr"][ja[first]]
        snr_b[first] = w["snr"][jb[first]]
    out = {"dt": np.full(P, np.nan), "cc": np.full(P, np.nan), "lag_s": np.full(P, np.nan),
           "n_components": n_comp, "snr_a": snr_a, "snr_b": snr_b,
           "status": np.array(["no_common_data"] * P, dtype=object)}
    if acc is None:
        return out
    have = n_comp > 0
    cc = np.zeros_like(acc)
    cc[have] = acc[have] / n_comp[have, None]
    k, peak, frac, ok_edge = pick_peak(cc)
    K = (cc.shape[1] - 1) // 2
    lag_samples = (k - K) + frac
    sb = u_b + (k + frac) * delta
    dt = (s_a - origin[ia]) - (sb - origin[ib])
    trough = -cc.min(axis=1)
    second = second_peak(cc, k, max(1, int(round(guard_s / delta))))
    overlap = (s_a < u_b + (n_long - 1) * delta) & (u_b < s_a + (m_tmpl - 1) * delta)
    status = np.where(~have, "no_common_data",
             np.where(overlap, "self_overlap",
             np.where(trough >= peak, "anticorrelated",
             np.where(second >= ambiguity_ratio * peak, "ambiguous",
             np.where(~ok_edge, "edge_peak",
             np.where(peak < min_cc, "low_cc",
             np.where((snr_a < min_snr) | (snr_b < min_snr), "low_snr", "accepted")))))))
    out.update(dt=np.where(have, dt, np.nan), cc=np.where(have, np.minimum(peak, 1.0), np.nan),
               lag_s=np.where(have, lag_samples * delta, np.nan), status=status.astype(object))
    return out
