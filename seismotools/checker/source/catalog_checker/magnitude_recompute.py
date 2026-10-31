"""Magnitude stage: recompute local magnitudes for a sample of events from the waveforms and compare.

An independent ML is computed for an even sample of events (by number of picks): the instrument
response is removed to displacement, the record is filtered with the IASPEI standard Wood-Anderson
response (static magnification 1), the largest half peak-to-peak amplitude of each horizontal
component between the first pick and the end of the S train is read in nm, and the IASPEI standard
relation gives a station ML (hypocentral distance from the catalog); the event value is the median.
The check reports the catalog minus recomputed magnitude. Regional calibrations differ from the
standard relation by a few tenths, so only a larger difference is flagged.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from .checks import Check, Data, _skip

RECOMPUTE_DEFAULTS = {"recompute_events": 20, "recompute_offset_max": 0.5, "recompute_min_events": 8,
                      "largest_events_n": 5, "largest_offset_max": 0.5, "largest_missing_max": 1, "clip_run_samples": 5}
WA_IASPEI = {"zeros": [0j, 0j], "poles": [-5.49779 - 5.60886j, -5.49779 + 5.60886j], "gain": 1.0028, "sensitivity": 1.0}


def standard_ml(amplitude_nm, hypocentral_km):
    a, r = np.asarray(amplitude_nm, float), np.asarray(hypocentral_km, float)
    return np.log10(a) + 1.11 * np.log10(r) + 0.00189 * r - 2.09


def half_peak_to_peak(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return float("nan")
    d = np.diff(x)
    turn = np.where(np.sign(d[1:]) != np.sign(d[:-1]))[0] + 1
    vals = x[np.r_[0, turn, len(x) - 1]]
    return float(np.max(np.abs(np.diff(vals))) / 2.0)


def _inventory(path: Path):
    from obspy import read_inventory
    path = Path(path)
    files = sorted(p for p in path.rglob("*") if p.suffix.lower() in (".xml", ".stationxml")) if path.is_dir() else \
        ([path] if path.suffix.lower() in (".xml", ".stationxml") else [])
    inv = None
    for f in files:
        inv = read_inventory(str(f)) if inv is None else inv + read_inventory(str(f))
    return inv


def clipped(raw: np.ndarray, run: int) -> bool:
    """A record that sits at its own extreme value for more than ``run`` samples has hit the digitiser rail."""
    x = np.abs(np.asarray(raw, float))
    if not len(x):
        return False
    top = x.max()
    return top > 0 and int((x >= 0.999 * top).sum()) > run


def station_amplitudes(d: Data, index: pd.DataFrame, stations_path: Path, event_ids: list[str],
                       long_window: bool = False, clip_run: int | None = None) -> pd.DataFrame:
    """Standard-ML inputs (amplitude in nm, hypocentral distance in km) per event, station and horizontal channel.

    ``long_window`` extends the window to S + max(30 s, 4 (S − P)) for the long S trains of large events;
    ``clip_run`` drops records that sit at their extreme value for more than that many samples."""
    from obspy import UTCDateTime, read
    inv = _inventory(stations_path)
    rows = []
    if inv is None:
        return pd.DataFrame(rows)
    ev = d.events.set_index("event_id")
    picks = d.picks[d.picks.event_id.isin(event_ids)]
    for (eid, sta), sp in picks.groupby(["event_id", "station_id"]):
        e = ev.loc[eid]
        tp = sp[sp.phase == "P"].time.min()
        ts = sp[sp.phase == "S"].time.min()
        first = tp if np.isfinite(tp) else ts
        last = ts if np.isfinite(ts) else tp + 0.7 * (tp - e.time)
        t0, t1 = first - 1.0, last + max(3.0, 0.5 * (last - e.time)) + 2.0
        if long_window:
            t1 = last + max(30.0, 4.0 * (last - first if np.isfinite(tp) and np.isfinite(ts) else last - e.time))
        r = float(sp.hyp_km.iloc[0])
        files = index[(index.station_id == sta) & index.component.isin(list("NE12")) & (index.file_start < t1) & (index.file_end > t0)]
        for seed, f in files.groupby("seed_id"):
            try:
                st = read(str(f.file.iloc[0]), starttime=UTCDateTime(t0 - 30), endtime=UTCDateTime(t1 + 30))
                st.merge(fill_value=0)
                tr = st[0]
                if clip_run is not None and clipped(tr.slice(UTCDateTime(t0), UTCDateTime(t1)).data, clip_run):
                    continue
                tr.detrend("demean")
                tr.detrend("linear")
                fs = tr.stats.sampling_rate
                tr.remove_response(inventory=inv, output="DISP", pre_filt=(0.05, 0.1, 0.4 * fs, 0.45 * fs), water_level=60)
                tr.simulate(paz_simulate=WA_IASPEI, simulate_sensitivity=False)
                tr.trim(UTCDateTime(t0), UTCDateTime(t1))
                a = half_peak_to_peak(tr.data * 1e9)
            except Exception:
                continue
            if np.isfinite(a) and a > 0 and r > 0:
                rows.append({"event_id": eid, "station_id": sta, "seed_id": seed, "amplitude_nm": a, "hypocentral_km": r})
    return pd.DataFrame(rows, columns=["event_id", "station_id", "seed_id", "amplitude_nm", "hypocentral_km"])


def magnitude_recompute(d: Data, index: pd.DataFrame, stations_path: Path, c: dict) -> Check:
    c = {**RECOMPUTE_DEFAULTS, **c}
    lim = c["recompute_offset_max"]
    expected = (f"|median catalog magnitude − recomputed standard ML| ≤ {lim} over {c['recompute_events']} sampled events "
                "(regional calibrations differ from the standard relation by a few tenths)")
    p = d.picks[np.isfinite(d.picks.hyp_km)]
    n = p.groupby("event_id").size()
    ev = d.events[d.events.event_id.isin(n.index) & d.events.magnitude.notna()].assign(n=lambda x: x.event_id.map(n))
    if ev.empty:
        return _skip("magnitude_recompute", "strength", "magnitude", expected, 0, "no located events with magnitudes and picks")
    ev = ev.sort_values(["n", "time"], ascending=[False, True])
    take = np.unique(np.linspace(0, len(ev) - 1, min(c["recompute_events"], len(ev))).round().astype(int))
    sample = ev.iloc[take]
    amps = station_amplitudes(d, index, stations_path, list(sample.event_id))
    if amps.empty:
        return _skip("magnitude_recompute", "strength", "magnitude", expected, 0,
                     "no amplitude measured (needs horizontal records and StationXML with responses)")
    amps["ml"] = standard_ml(amps.amplitude_nm, amps.hypocentral_km)
    em = amps.groupby("event_id").ml.median().rename("recomputed").to_frame().join(sample.set_index("event_id").magnitude)
    if len(em) < c["recompute_min_events"]:
        return _skip("magnitude_recompute", "strength", "magnitude", expected, len(em), f"{len(em)} events recomputed")
    diff = em.magnitude - em.recomputed
    med = float(diff.median())
    flag = abs(med) > lim
    slope = float(np.polyfit(em.recomputed, em.magnitude, 1)[0]) if em.recomputed.nunique() > 2 else None
    return Check("magnitude_recompute", "strength", med, "magnitude", expected, len(em), flag,
                 (f"Catalog magnitudes are {abs(med):.2f} units {'below' if med < 0 else 'above'} the standard local magnitude "
                  f"recomputed from the records (median of {len(em)} events, spread {float((diff - med).abs().median()):.2f}).") if flag else None,
                 {"events": em.reset_index().round(3).to_dict("records"), "amplitudes": int(len(amps)),
                  "slope_catalog_vs_recomputed": None if slope is None else round(slope, 3),
                  "mad": round(float((diff - med).abs().median()), 3)})


def largest_events_magnitude(d: Data, index: pd.DataFrame, stations_path: Path, c: dict) -> Check:
    """The largest events: recomputed standard ML from unclipped records over a long window, against the catalog.

    Candidates are the events picked at the most stations and the events with the largest catalog
    magnitudes. Near records of large events are often clipped and short windows miss the S-wave
    maximum, which makes their magnitudes too small; events without a magnitude are counted too.
    """
    c = {**RECOMPUTE_DEFAULTS, **c}
    n, lim = c["largest_events_n"], c["largest_offset_max"]
    expected = (f"|median catalog magnitude − recomputed standard ML| ≤ {lim} for the {n} events picked at the most stations and the "
                f"{n} largest catalog magnitudes, and at most {c['largest_missing_max']} of them without a magnitude")
    p = d.picks[np.isfinite(d.picks.hyp_km)]
    nsta = p.groupby("event_id").station_id.nunique()
    ev = d.events[d.events.event_id.isin(nsta.index)]
    if ev.empty:
        return _skip("largest_events_magnitude", "strength", "magnitude", expected, 0, "no located events with picks")
    by_sta = list(nsta.loc[ev.event_id].sort_values(ascending=False).index[:n])
    by_mag = list(ev.dropna(subset=["magnitude"]).sort_values("magnitude", ascending=False).event_id[:n])
    cand = list(dict.fromkeys(by_sta + by_mag))
    amps = station_amplitudes(d, index, stations_path, cand, long_window=True, clip_run=c["clip_run_samples"])
    if amps.empty:
        return _skip("largest_events_magnitude", "strength", "magnitude", expected, 0,
                     "no unclipped amplitude measured (needs horizontal records and StationXML with responses)")
    amps["ml"] = standard_ml(amps.amplitude_nm, amps.hypocentral_km)
    rec = amps.groupby("event_id").ml.agg(["median", "size"]).rename(columns={"median": "recomputed", "size": "n_records"})
    rec = rec[rec.n_records >= 3]
    em = rec.join(ev.set_index("event_id")[["magnitude", "time"]], how="left")
    missing = int(em.magnitude.isna().sum())
    both = em.dropna(subset=["magnitude"])
    diff = both.magnitude - both.recomputed
    med = float(diff.median()) if len(diff) else float("nan")
    flag = (len(diff) > 0 and abs(med) > lim) or missing > c["largest_missing_max"]
    parts = []
    if len(diff) and abs(med) > lim:
        parts.append(f"the catalog magnitudes are {abs(med):.2f} units {'below' if med < 0 else 'above'} the standard ML "
                     f"recomputed from unclipped records (median of {len(diff)}; largest recomputed {both.recomputed.max():.1f}, "
                     f"catalog {both.magnitude.max():.1f})")
    if missing > c["largest_missing_max"]:
        parts.append(f"{missing} of the {len(em)} largest events have no magnitude")
    return Check("largest_events_magnitude", "strength", med if len(diff) else None, "magnitude", expected, len(em), flag,
                 ("For the largest events " + "; ".join(parts) + ".") if flag else None,
                 {"events": em.reset_index().assign(time=lambda x: pd.to_datetime(x.time, unit="s", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
                  .round(3).to_dict("records"), "without_magnitude": missing})
