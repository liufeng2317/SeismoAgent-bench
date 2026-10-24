"""Waveform preparation for MatchLocate2 (requires ObsPy).

The native program correlates raw SAC samples. Its own user guide (Q3) asks
that templates and continuous data share sampling rate and filtering, and
recommends cutting templates from the already processed continuous data so a
template's self-detection reaches CC = 1. This module follows that rule:

1. ``process_continuous`` filters and resamples one channel-day and lays it on
   the exact sample grid of the day, zero-filling gaps;
2. ``write_continuous_sac`` writes it with the day start as SAC reference and
   ``o = 0`` (the native program rejects continuous data with ``o != 0``);
3. ``cut_template`` cuts a template from that processed trace, with the
   template origin snapped to the sample grid as reference (``o = 0``), phase
   travel times in t-marks, and the event location/magnitude in the header.

Case-level policy (band, sampling rate, channel/phase selection, SNR gates,
template choice) stays with the calling workflow.
"""
from __future__ import annotations

import dataclasses
from typing import Dict, Optional

import numpy as np
from obspy import Stream, Trace, UTCDateTime
from obspy.io.sac import SACTrace

DAY_S = 86400.0


def day_start(time: UTCDateTime) -> UTCDateTime:
    time = UTCDateTime(time)
    return UTCDateTime(time.year, time.month, time.day)


@dataclasses.dataclass(frozen=True)
class Processing:
    sampling_rate: float
    freqmin: float
    freqmax: float
    corners: int = 4
    zerophase: bool = True
    taper_s: float = 5.0

    def __post_init__(self) -> None:
        if not 0 < self.freqmin < self.freqmax < 0.5 * self.sampling_rate:
            raise ValueError("require 0 < freqmin < freqmax < Nyquist of the output rate")


def process_continuous(stream: Stream, processing: Processing, start: UTCDateTime,
                       length_s: float = DAY_S) -> Trace:
    """Filter/resample one channel and return it on the grid start + k/sr.

    Each contiguous segment is demeaned, detrended, tapered and band-passed
    separately (no filtering across gaps), resampled to the target rate, then
    merged with zero fill and padded/trimmed to exactly ``length_s``.
    """
    ids = {tr.id for tr in stream}
    if len(ids) != 1:
        raise ValueError(f"process one channel at a time, got {sorted(ids)}")
    sr = processing.sampling_rate
    segments = stream.copy().merge(method=1, fill_value=None).split()
    out = Stream()
    for tr in segments:
        if tr.stats.npts < 2 * processing.taper_s * tr.stats.sampling_rate:
            continue
        tr.data = tr.data.astype(np.float64)
        tr.detrend("demean")
        tr.detrend("linear")
        tr.taper(max_percentage=0.5, type="cosine", max_length=processing.taper_s)
        tr.filter("bandpass", freqmin=processing.freqmin, freqmax=processing.freqmax,
                  corners=processing.corners, zerophase=processing.zerophase)
        ratio = tr.stats.sampling_rate / sr
        offset = ((tr.stats.starttime - start) * sr) % 1.0
        on_grid = min(offset, 1.0 - offset) < 1e-3
        if abs(ratio - round(ratio)) < 1e-9 and round(ratio) >= 1 and on_grid:
            if round(ratio) > 1:
                tr.decimate(int(round(ratio)), no_filter=True)  # band-limited above
        else:
            # target samples strictly inside the segment (tolerances point inward;
            # interpolation cannot extrapolate)
            first = start + np.ceil((tr.stats.starttime - start) * sr + 1e-6) / sr
            npts = int(np.floor((tr.stats.endtime - first) * sr - 1e-6)) + 1
            if npts < 2:
                continue
            tr.interpolate(sr, method="lanczos", a=12, starttime=first, npts=npts)
        # snap residual sub-millisample jitter onto the grid
        k = round((tr.stats.starttime - start) * sr)
        tr.stats.starttime = start + k / sr
        out.append(tr)
    template = segments[0] if segments else stream[0]
    npts = int(round(length_s * sr))
    data = np.zeros(npts, dtype=np.float32)
    for tr in out:
        k0 = int(round((tr.stats.starttime - start) * sr))
        a, b = max(k0, 0), min(k0 + tr.stats.npts, npts)
        if b > a:
            data[a:b] = tr.data[a - k0:b - k0].astype(np.float32)
    result = Trace(data=data, header={"network": template.stats.network, "station": template.stats.station,
                                      "location": template.stats.location, "channel": template.stats.channel,
                                      "sampling_rate": sr, "starttime": start})
    return result


def _sac(trace: Trace, reference: UTCDateTime) -> SACTrace:
    sac = SACTrace.from_obspy_trace(trace)
    sac.reftime = reference          # keeps absolute times, rewrites b
    sac.o = 0.0
    sac.iztype = "io"
    return sac


def write_continuous_sac(trace: Trace, path, *, reference: UTCDateTime, station_lat: float,
                         station_lon: float, station_elev_m: Optional[float] = None) -> None:
    """Write a processed continuous trace for MatchLocate2 (reference = segment start, o = 0)."""
    sac = _sac(trace, UTCDateTime(reference))
    sac.stla, sac.stlo = station_lat, station_lon
    if station_elev_m is not None:
        sac.stel = station_elev_m
    sac.write(str(path), byteorder="little")


@dataclasses.dataclass(frozen=True)
class TemplateCut:
    origin_snapped: UTCDateTime
    snap_offset_s: float           # snapped - catalog origin
    marks: Dict[int, float]        # t-mark index -> travel time on the sample grid


def cut_template(processed: Trace, origin: UTCDateTime, *, pre_s: float, post_s: float,
                 marks: Dict[int, float], event_lat: float, event_lon: float, event_depth_km: float,
                 magnitude: Optional[float], station_lat: float, station_lon: float,
                 path, station_elev_m: Optional[float] = None, event_name: str = "") -> TemplateCut:
    """Cut [origin - pre_s, origin + post_s] from a processed trace and write the template SAC.

    The origin is snapped to the nearest sample of ``processed`` so the template
    samples coincide with continuous samples; travel times in ``marks`` are
    rounded to whole samples (the native shift is an integer sample count).
    Raises ValueError when the window is not fully inside the processed trace.
    """
    sr = processed.stats.sampling_rate
    origin = UTCDateTime(origin)
    k0 = int(round((origin - processed.stats.starttime) * sr))
    snapped = processed.stats.starttime + k0 / sr
    a, b = k0 - int(round(pre_s * sr)), k0 + int(round(post_s * sr)) + 1
    if a < 0 or b > processed.stats.npts:
        raise ValueError("template window extends beyond the processed trace")
    piece = processed.copy()
    piece.data = processed.data[a:b].copy()
    piece.stats.starttime = processed.stats.starttime + a / sr
    sac = _sac(piece, snapped)
    grid_marks = {}
    for index, travel_time in marks.items():
        if travel_time is None:
            continue
        value = round(travel_time * sr) / sr
        if not -pre_s <= value <= post_s:
            raise ValueError(f"mark t{index}={value:.3f} s outside the template window")
        setattr(sac, f"t{index}", value)
        grid_marks[index] = value
    sac.evla, sac.evlo, sac.evdp = event_lat, event_lon, event_depth_km
    if magnitude is not None:
        sac.mag = magnitude
        sac.user0 = magnitude     # MatchLocate2 reads the template magnitude from user0
    sac.stla, sac.stlo = station_lat, station_lon
    if station_elev_m is not None:
        sac.stel = station_elev_m
    if event_name:
        sac.kevnm = event_name[:16]
    sac.write(str(path), byteorder="little")
    return TemplateCut(snapped, float(snapped - origin), grid_marks)


def window_snr(processed: Trace, arrival: UTCDateTime, *, signal_s: float, noise_s: float,
               gap_s: float = 0.5) -> float:
    """Peak |amplitude| in [arrival, arrival+signal_s] over RMS of the noise
    window ending ``gap_s`` before the arrival; NaN if either window is empty."""
    sr = processed.stats.sampling_rate
    k = int(round((UTCDateTime(arrival) - processed.stats.starttime) * sr))
    sig = processed.data[max(k, 0):max(k + int(signal_s * sr), 0)]
    n1 = k - int(gap_s * sr)
    noise = processed.data[max(n1 - int(noise_s * sr), 0):max(n1, 0)]
    if sig.size == 0 or noise.size == 0:
        return float("nan")
    rms = float(np.sqrt(np.mean(noise.astype(np.float64) ** 2)))
    # zero RMS means the noise window is a zero-filled gap, not a quiet trace
    return float(np.max(np.abs(sig))) / rms if rms > 0 else float("nan")


def zero_fraction(processed: Trace, start: UTCDateTime, length_s: float) -> float:
    """Fraction of exactly-zero samples (zero-filled gaps) in [start, start+length_s]."""
    sr = processed.stats.sampling_rate
    k = int(round((UTCDateTime(start) - processed.stats.starttime) * sr))
    seg = processed.data[max(k, 0):max(k + int(round(length_s * sr)), 0)]
    return 1.0 if seg.size == 0 else float(np.mean(seg == 0))
