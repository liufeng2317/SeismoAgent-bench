"""Waveform index and per-channel window extraction.

Every channel is read file by file (with ``pad_s`` of the neighbouring files so
windows near a file boundary — e.g. UTC midnight — are complete), split at
gaps, demeaned, detrended, tapered and band-pass filtered (zero phase) as a
long trace, and only then cut into windows. Filtering the long trace keeps
filter start-up transients out of the windows.

For each arrival the stored window is the *search* window
``[t - before - max_lag, t + after + max_lag]`` on the trace's own sample
grid; ``start`` records the exact UTC epoch of its first sample (float64), so
no sub-sample offset is lost to rounding. A window is valid only when the
trace covers it plus ``edge_guard_s`` on both sides without gaps.
"""
from __future__ import annotations

import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

EXTENSIONS = (".mseed", ".miniseed", ".ms", ".msd")


def _header_spans(path: str) -> List[Tuple[str, float, float, float]]:
    from obspy import read
    try:
        st = read(path, headonly=True)
    except Exception:
        return []
    return [(tr.id, float(tr.stats.starttime), float(tr.stats.endtime), float(tr.stats.sampling_rate)) for tr in st]


def index_waveforms(root, workers: int = 1) -> Dict[str, List[Tuple[float, float, float, str]]]:
    """trace id -> sorted [(start, end, sampling_rate, path)] from MiniSEED headers."""
    files = sorted(str(p) for p in Path(root).rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS)
    if not files:
        raise ValueError(f"no MiniSEED files ({', '.join(EXTENSIONS)}) under {root}")
    index: Dict[str, List[Tuple[float, float, float, str]]] = {}
    with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
        for path, spans in zip(files, pool.map(_header_spans, files, chunksize=16)):
            for tid, t0, t1, sr in spans:
                index.setdefault(tid, []).append((t0, t1, sr, path))
    for spans in index.values():
        spans.sort()
    return index


def choose_channels(index, station: str, phase: str, cfg: dict) -> List[str]:
    """Trace ids used for one station and phase: the first channel family (in
    ``channels.families`` order) that has at least one of the phase's
    components; lowest location code first."""
    comps = cfg["channels"][phase]
    by_family: Dict[str, Dict[str, str]] = {}
    for tid in index:
        net, sta, loc, cha = tid.split(".")
        if f"{net}.{sta}" != station or len(cha) != 3:
            continue
        by_family.setdefault(cha[:2], {})
        if cha[2] in comps:
            # keep the lowest location code per component
            prev = by_family[cha[:2]].get(cha[2])
            if prev is None or tid < prev:
                by_family[cha[:2]][cha[2]] = tid
    for fam in cfg["channels"]["families"]:
        if by_family.get(fam):
            return [by_family[fam][c] for c in comps if c in by_family[fam]]
    return []


def _process(tr, cfg):
    tr.detrend("demean")
    tr.detrend("linear")
    tr.taper(max_percentage=0.5, max_length=float(cfg["taper_s"]))
    f = cfg["filter"]
    nyq = 0.5 * tr.stats.sampling_rate
    tr.data = tr.data.astype(np.float64)
    tr.filter("bandpass", freqmin=f["freqmin"], freqmax=min(f["freqmax"], 0.9 * nyq),
              corners=int(f["corners"]), zerophase=True)
    return tr


def extract_channel(task) -> dict:
    """Windows of one trace id for all its arrivals.

    task = (trace_id, spans, arrivals, phase, cfg) with arrivals a list of
    (row, t_arrival). Returns arrays aligned with ``rows``."""
    from obspy import Stream, UTCDateTime, read
    tid, spans, arrivals, phase, cfg = task
    w = cfg["window"][phase]
    lag = float(cfg["max_lag_s"][phase])
    pad = float(cfg["pad_s"])
    guard = float(cfg["edge_guard_s"])
    noise_s = float(cfg["snr"]["noise_s"])
    rates = {round(s[2], 6) for s in spans}
    sr = max(rates, key=lambda r: sum(1 for s in spans if round(s[2], 6) == r))
    dt = 1.0 / sr
    n_long = int(round((w["before_s"] + w["after_s"] + 2 * lag) / dt)) + 1
    n_tmpl = int(round((w["before_s"] + w["after_s"]) / dt)) + 1
    k_lag = int(round(lag / dt))
    rows = np.array([a[0] for a in arrivals], dtype=np.int64)
    times = np.array([a[1] for a in arrivals], dtype=np.float64)
    data = np.zeros((len(rows), n_long), dtype=np.float32)
    start = np.full(len(rows), np.nan)
    snr = np.full(len(rows), np.nan)
    valid = np.zeros(len(rows), dtype=bool)
    reason = np.array(["no_data"] * len(rows), dtype=object)
    # assign each arrival to the span (file) that contains it
    owner = np.full(len(rows), -1)
    for k, (t0, t1, r, _) in enumerate(spans):
        if round(r, 6) != sr:
            continue
        inside = (times >= t0) & (times <= t1) & (owner < 0)
        owner[inside] = k
    for k in np.unique(owner[owner >= 0]):
        t0, t1, _, path = spans[k]
        lo, hi = t0 - pad, t1 + pad
        st = Stream()
        for s0, s1, r, p in spans:
            if s1 >= lo and s0 <= hi and round(r, 6) == sr:
                st += read(p, starttime=UTCDateTime(lo), endtime=UTCDateTime(hi)).select(id=tid)
        if not len(st):
            continue
        st.merge(method=1, fill_value=None)
        st = st.split()
        traces = [_process(tr, cfg) for tr in st if tr.stats.npts > 10]
        for i in np.nonzero(owner == k)[0]:
            t = times[i]
            w0 = t - w["before_s"] - lag
            w1 = w0 + (n_long - 1) * dt
            host = next((tr for tr in traces if float(tr.stats.starttime) <= w0 - max(guard, noise_s)
                         and float(tr.stats.endtime) >= w1 + guard), None)
            if host is None:
                reason[i] = "gap_or_edge"
                continue
            tr0 = float(host.stats.starttime)
            j0 = int(round((w0 - tr0) / dt))
            seg = host.data[j0:j0 + n_long]
            if seg.size != n_long or not np.isfinite(seg).all():
                reason[i] = "gap_or_edge"
                continue
            # SNR: RMS of the template part over RMS of the noise_s before it
            jt = j0 + k_lag
            sig = host.data[jt:jt + n_tmpl]
            jn = jt - int(round(noise_s / dt))
            noise = host.data[max(jn, 0):jt]
            rn = float(np.sqrt(np.mean(noise ** 2))) if noise.size else 0.0
            rs = float(np.sqrt(np.mean(sig ** 2)))
            if rs == 0.0:
                reason[i] = "zero_signal"
                continue
            data[i] = seg
            start[i] = tr0 + j0 * dt
            snr[i] = rs / rn if rn > 0 else np.inf
            valid[i] = True
            reason[i] = "ok"
    return {"trace_id": tid, "phase": phase, "delta": dt, "n_template": n_tmpl, "k_lag": k_lag,
            "rows": rows, "start": start, "snr": snr, "valid": valid, "data": data,
            "reason": reason.astype(str)}
