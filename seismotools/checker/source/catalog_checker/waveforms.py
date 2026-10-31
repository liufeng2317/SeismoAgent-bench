"""Waveform access shared by the data and picks stages: reading windows, finding energetic windows,
onsets (AIC) and amplitude ratios. Everything is deterministic: the same files give the same windows.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .io import _file_span

BAND_HZ = (2.0, 20.0)  # the standard band used whenever the checker filters on its own
SCAN_RATIO = 8.0       # 1-s peak over the station's median 1-s peak that counts as energetic
SCAN_BIN_S = 20


def file_index(path: Path) -> pd.DataFrame:
    """MiniSEED files by name ``NET.STA.LOC.CHA__start__end.mseed`` (fast, no reading)."""
    rows = []
    for f in sorted(Path(path).rglob("*.mseed")):
        seed = f.name.split("__")[0]
        parts = seed.split(".")
        span = _file_span(f.name)
        if len(parts) != 4 or span is None:
            continue
        rows.append({"file": str(f), "seed_id": seed, "station_id": f"{parts[0]}.{parts[1]}", "location": parts[2],
                     "channel": parts[3], "component": parts[3][-1], "file_start": span[0], "file_end": span[1]})
    return pd.DataFrame(rows, columns=["file", "seed_id", "station_id", "location", "channel", "component", "file_start", "file_end"])


def station_channels(index: pd.DataFrame, station: str) -> dict[str, str]:
    """Component letter -> seed id for one station, preferring the highest sample-rate band and the first location."""
    s = index[index.station_id == station]
    if s.empty:
        return {}
    rank = {"H": 0, "E": 1, "B": 2, "S": 3, "C": 4, "D": 5}
    s = s.assign(r=s.channel.str[0].map(rank).fillna(9), inst=s.channel.str[1] == "N").sort_values(["inst", "r", "location", "channel"])
    best = s.iloc[0]
    same = s[(s.location == best.location) & (s.channel.str[:2] == best.channel[:2])]
    return dict(zip(same.component, same.seed_id))


class Reader:
    """Reads windows from a file index, caching the last few decoded files."""

    def __init__(self, index: pd.DataFrame, cache: int = 24):
        self.index, self.cache, self._files = index, cache, {}

    def _read(self, path: str):
        from obspy import read
        if path not in self._files:
            if len(self._files) >= self.cache:
                self._files.pop(next(iter(self._files)))
            try:
                st = read(path)
                st.merge(method=1, fill_value=None)
            except Exception:
                st = None
            self._files[path] = st
        return self._files[path]

    def window(self, seed_id: str, t0: float, t1: float):
        """(time array in epoch s, float samples, sample rate) or None; gaps become NaN."""
        from obspy import UTCDateTime
        f = self.index[(self.index.seed_id == seed_id) & (self.index.file_start < t1) & (self.index.file_end > t0)]
        pieces = []
        for path in f.file:
            st = self._read(path)
            if st is None:
                continue
            for tr in st.slice(UTCDateTime(t0), UTCDateTime(t1)):
                data = tr.data
                if np.ma.isMaskedArray(data):
                    data = data.astype(float).filled(np.nan)
                pieces.append((float(tr.stats.starttime.timestamp), float(tr.stats.sampling_rate), np.asarray(data, dtype=float)))
        if not pieces:
            return None
        rate = max(p[1] for p in pieces)
        n = int(round((t1 - t0) * rate))
        out = np.full(n, np.nan)
        for start, r, data in pieces:
            if r != rate:
                continue
            i0 = int(round((start - t0) * rate))
            a, b = max(i0, 0), min(i0 + len(data), n)
            if b > a:
                out[a:b] = data[a - i0:b - i0]
        return t0 + np.arange(n) / rate, out, rate


def bandpass(x: np.ndarray, rate: float, band=BAND_HZ) -> np.ndarray:
    """Demean, detrend, taper and zero-phase band-pass; NaN gaps are zeroed first."""
    from scipy.signal import butter, sosfiltfilt
    y = np.nan_to_num(x - np.nanmean(x)) if np.isfinite(x).any() else np.zeros_like(x)
    y = y - np.linspace(y[0], y[-1], len(y)) if len(y) > 1 else y
    taper = np.ones(len(y))
    m = max(1, int(0.05 * len(y)))
    taper[:m] = taper[-m:][::-1] = 0.5 * (1 - np.cos(np.linspace(0, np.pi, m)))
    hi = min(band[1], 0.45 * rate)
    if len(y) < 30 or hi <= band[0]:
        return y * taper
    sos = butter(4, [band[0], hi], btype="band", fs=rate, output="sos")
    return sosfiltfilt(sos, y * taper)


def aic_onset(y: np.ndarray, rate: float, lo: int, hi: int) -> int | None:
    """Sample index of the AIC minimum (Maeda, 1985) searched in [lo, hi)."""
    n = len(y)
    if n < 20 or hi - lo < 4:
        return None
    k = np.arange(1, n - 1)
    c1, c2 = np.cumsum(y ** 2), np.cumsum((y ** 2)[::-1])[::-1]
    s1 = np.cumsum(y)
    s2 = np.cumsum(y[::-1])[::-1]
    var1 = c1[k - 1] / k - (s1[k - 1] / k) ** 2
    var2 = c2[k] / (n - k) - (s2[k] / (n - k)) ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        aic = k * np.log(np.maximum(var1, 1e-30)) + (n - k - 1) * np.log(np.maximum(var2, 1e-30))
    sel = (k >= max(lo, 2)) & (k < min(hi, n - 2))
    if not sel.any():
        return None
    return int(k[sel][np.argmin(aic[sel])])


def amplitude_ratio(y: np.ndarray, rate: float, at: int, seconds: float = 2.0) -> float:
    """RMS in ``seconds`` after sample ``at`` over RMS in ``seconds`` before it."""
    m = int(seconds * rate)
    before, after = y[max(at - m, 0):at], y[at:at + m]
    if len(before) < m // 2 or len(after) < m // 2:
        return np.nan
    nb = np.sqrt(np.mean(before ** 2))
    return float(np.sqrt(np.mean(after ** 2)) / nb) if nb > 0 else np.nan


def peak_frequency(y: np.ndarray, rate: float) -> float:
    if len(y) < 16 or not np.isfinite(y).all():
        return np.nan
    f = np.fft.rfftfreq(len(y), 1 / rate)
    a = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    keep = f >= 0.2
    return float(f[keep][np.argmax(a[keep])]) if keep.any() else np.nan


def energetic_windows(reader: Reader, index: pd.DataFrame, window: tuple[float, float], n: int = 4,
                      min_separation_s: float = 3600.0) -> tuple[list[dict], dict]:
    """Windows where most stations show energy well above their own noise at the same time.

    Each station's vertical channel is reduced to 1-s peaks of the first difference; a station is
    energetic in a 20-s bin when its peak exceeds ``SCAN_RATIO`` times its median 1-s peak. The bins
    with the most energetic stations (ties: higher median ratio, then earlier) are returned, at least
    ``min_separation_s`` apart.
    """
    t0, t1 = window
    names, ratios, pair, count, medr = activity_scan(reader, index, window)
    if not names:
        return [], {"stations_scanned": 0}
    order = np.lexsort((np.arange(len(count)), -np.nan_to_num(medr), -count))
    chosen = []
    for b in order:
        if count[b] < 3 or len(chosen) >= n:
            break
        t = t0 + b * SCAN_BIN_S
        if all(abs(t - c["bin_start"]) >= min_separation_s for c in chosen):
            ranked = sorted(names, key=lambda s: -np.nan_to_num(pair[names.index(s), b]))
            onsets = {}
            for s in ranked:
                seg = ratios[s][b * SCAN_BIN_S:(b + 2) * SCAN_BIN_S]
                hit = np.where(seg >= SCAN_RATIO)[0]
                if len(hit):
                    onsets[s] = t + float(hit[0])
            chosen.append({"bin_start": t, "energetic_stations": int(count[b]), "stations_ranked": ranked,
                           "onsets": onsets, "start": min(onsets.values()) - 10.0 if onsets else t})
    return chosen, {"stations_scanned": len(names), "bins": int(len(count)),
                    "bins_with_3plus_energetic_stations": int((count >= 3).sum())}


def activity_scan(reader: Reader, index: pd.DataFrame, window: tuple[float, float], stations: list[str] | None = None,
                  background_s: float | None = None):
    """Per 20-s bin, how many stations show energy well above their own noise (see energetic_windows).

    The noise level is each station's median 1-s peak over the whole window, or with ``background_s`` a
    running median over that many seconds (transients only: a slowly rising noise level, e.g. by day, does
    not count). Returns (station names, per-station 1-s peak ratios, per-station 40-s maxima,
    energetic-station count per bin, median ratio per bin)."""
    t0, t1 = window
    nsec = int(np.ceil(t1 - t0))
    stations = sorted(index.station_id.unique()) if stations is None else stations
    ratios = {}
    for sta in stations:
        ch = station_channels(index, sta)
        seed = ch.get("Z") or ch.get("3") or (next(iter(ch.values())) if ch else None)
        if seed is None:
            continue
        peaks = np.full(nsec, np.nan)
        for path in index[(index.seed_id == seed) & (index.file_start < t1) & (index.file_end > t0)].file:
            st = reader._read(path)
            if st is None:
                continue
            for tr in st:
                x = np.asarray(tr.data, dtype=float)
                r = float(tr.stats.sampling_rate)
                start = float(tr.stats.starttime.timestamp)
                i0 = int(np.ceil(start - t0))
                skip = int(round((t0 + i0 - start) * r))
                d = np.abs(np.diff(x[skip:]))
                w = int(round(r))
                m = len(d) // w
                if m <= 0 or w <= 0:
                    continue
                p = d[:m * w].reshape(m, w).max(axis=1)
                a, b = max(i0, 0), min(i0 + m, nsec)
                if b > a:
                    peaks[a:b] = p[a - i0:b - i0]
            reader._files.pop(path, None)
        med = np.nanmedian(peaks) if np.isfinite(peaks).any() else np.nan
        if np.isfinite(med) and med > 0:
            if background_s:
                local = pd.Series(peaks).rolling(int(background_s), center=True, min_periods=int(background_s) // 4).median()
                ratios[sta] = peaks / np.where(local.to_numpy() > 0, local.to_numpy(), med)
            else:
                ratios[sta] = peaks / med
    if not ratios:
        return [], {}, None, np.zeros(0, int), np.zeros(0)
    names = sorted(ratios)
    nb = nsec // SCAN_BIN_S
    r = np.stack([ratios[s][:nb * SCAN_BIN_S].reshape(nb, SCAN_BIN_S) for s in names])  # station x bin x s
    binmax = np.nanmax(np.where(np.isfinite(r), r, -np.inf), axis=2)
    pair = np.maximum(binmax[:, :-1], binmax[:, 1:])  # a 40-s span covers the moveout across the network
    count = (pair >= SCAN_RATIO).sum(axis=0)
    with np.errstate(all="ignore"):
        medr = np.nanmedian(np.where(np.isfinite(pair), pair, np.nan), axis=0)
    return names, ratios, pair, count, medr
