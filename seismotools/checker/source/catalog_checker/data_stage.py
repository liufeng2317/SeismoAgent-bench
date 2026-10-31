"""Stage 1, data and preprocessing: which stations and channels have data, how complete it is, and how
the Agent's preprocessing changes representative records. Needs station metadata and the waveform
folder; the processed waveforms are optional. Symptoms only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .checks import Check, _skip
from .io import local_km
from .waveforms import BAND_HZ, Reader, bandpass, energetic_windows, file_index, peak_frequency, station_channels

DATA_DEFAULTS = {
    "low_station_day_fraction": 0.5, "coverage_min": 0.9, "gap_station_day_share_max": 0.05,
    "data_windows": 4, "data_window_s": 40.0, "data_window_pre_s": 8.0, "data_window_stations": 6, "processing_lag_max_samples": 2, "processing_lag_floor_s": 0.02,
}
INSTRUMENT = {"H": "seismometer", "L": "seismometer (low gain)", "N": "accelerometer", "P": "geophone", "G": "gravimeter"}


def _day(t):
    return np.floor(np.asarray(t, dtype=float) / 86400.0) * 86400.0


def _date(t: float) -> str:
    return f"{pd.Timestamp(t, unit='s'):%Y-%m-%d}"


def _in_window(streams: pd.DataFrame, window) -> pd.DataFrame:
    if window is None:
        return streams
    return streams[(streams.file_start < window[1]) & (streams.file_end > window[0])]


def _component_class(comps: set[str]) -> str:
    if {"Z", "N", "E"} <= comps:
        return "ZNE"
    if {"Z", "1", "2"} <= comps or {"Z", "2", "3"} <= comps:
        return "Z12"
    if comps <= {"Z"} or comps <= {"3"}:
        return "Z only"
    return "other (" + "".join(sorted(comps)) + ")"


def station_table(stations: pd.DataFrame, channels: pd.DataFrame, streams: pd.DataFrame) -> pd.DataFrame:
    """One row per station with data: component class, instrument types, sample rates, position."""
    rows = []
    for sta, s in streams.groupby("station_id"):
        best = station_channels(s, sta)
        best_cha = s[s.seed_id.isin(best.values())]
        rows.append({"station_id": sta, "components": _component_class(set(best)),
                     "channel_codes": ",".join(sorted(s.channel.unique())),
                     "instrument": ",".join(sorted({INSTRUMENT.get(c[1], c[1]) for c in s.channel.unique() if len(c) == 3})),
                     "sample_rates": ",".join(f"{r:g}" for r in sorted(best_cha.sample_rate.unique())),
                     "mixed_rates": bool(best_cha.sample_rate.nunique() > 1 or (best_cha.n_rates > 1).any())})
    t = pd.DataFrame(rows, columns=["station_id", "components", "channel_codes", "instrument", "sample_rates", "mixed_rates"])
    return t.merge(stations, on="station_id", how="left")


def data_checks(stations: pd.DataFrame, channels: pd.DataFrame, streams: pd.DataFrame, window, c: dict) -> tuple[list[Check], dict]:
    c = {**DATA_DEFAULTS, **c}
    s = _in_window(streams, window)
    extras: dict = {}
    if s.empty:
        why = "no waveform files in the processing window"
        return [_skip(i, "data", u, "", 0, why) for i, u in (("stations_with_data", "share"), ("daily_station_count", "days"),
                                                            ("data_gaps", "share"), ("channel_sample_rates", "stations"))], extras
    table = station_table(stations, channels, s)
    extras["station_table"] = table
    checks = []

    # coverage: stations with data, stations whose data cannot be placed (no metadata)
    meta = set(stations.station_id)
    have = set(s.station_id)
    no_meta = sorted(have - meta)
    exp = "every station with waveform data has station metadata"
    checks.append(Check("stations_with_data", "data", len(have & meta) / max(len(meta), 1), "share", exp, len(meta), bool(no_meta),
                        f"{len(no_meta)} stations have waveform data but no station metadata ({', '.join(no_meta[:12])})." if no_meta else None,
                        {"stations_with_metadata": len(meta), "stations_with_data": len(have),
                         "metadata_without_data": sorted(meta - have)[:50], "data_without_metadata": no_meta}))

    # stations per day
    days = s.assign(day=_day(s.file_start + 1.0)).groupby("day").station_id.nunique()
    if window is not None:
        days = days[(days.index + 86400 > window[0]) & (days.index < window[1])]
    med = float(days.median())
    low = days[days < c["low_station_day_fraction"] * med]
    exp = f"every day has ≥ {c['low_station_day_fraction']:.0%} of the median number of stations with data"
    checks.append(Check("daily_station_count", "data", float(len(low)), "days", exp, len(days), bool(len(low)),
                        (f"{len(low)} of {len(days)} days have fewer than half the median {med:.0f} stations with data "
                         f"({', '.join(_date(d) + f' {n}' for d, n in low.items())}).") if len(low) else None,
                        {"stations_per_day": {f"{pd.Timestamp(d, unit='s'):%Y-%m-%d}": int(n) for d, n in days.items()}}))

    # network geometry (reported; the azimuthal gap per event belongs to the location stage)
    st = table.dropna(subset=["latitude"])
    if len(st) >= 2:
        lat0, lon0 = float(st.latitude.median()), float(st.longitude.median())
        x, y = local_km(st.latitude, st.longitude, lat0, lon0)
        dmat = np.hypot(x[:, None] - x[None], y[:, None] - y[None])
        np.fill_diagonal(dmat, np.inf)
        az = np.sort(np.degrees(np.arctan2(x, y)) % 360)
        gap = float(np.max(np.diff(np.r_[az, az[0] + 360]))) if len(az) > 1 else 360.0
        np.fill_diagonal(dmat, 0)
        checks.append(Check("network_geometry", "data", float(dmat.max()), "km", "reported", len(st), False, None,
                            {"aperture_km": round(float(dmat.max()), 2),
                             "median_nearest_station_km": round(float(np.median(np.where(dmat > 0, dmat, np.inf).min(axis=1))), 2),
                             "azimuthal_gap_from_network_centre_deg": round(gap, 1)}))

    # components and sample rates
    classes = table.components.value_counts().to_dict()
    mixed = sorted(table[table.mixed_rates].station_id)
    exp = "one sample rate per station across its components"
    details = {"component_classes": classes, "stations_by_class": {k: sorted(v.station_id) for k, v in table.groupby("components")},
               "instrument_types": table.instrument.value_counts().to_dict()}
    if not channels.empty:
        ch = channels[channels.station_id.isin(have)]
        horiz12 = ch[ch.channel.str[-1].isin(["1", "2"])]
        details["z12_channels_without_azimuth"] = sorted(set(horiz12[horiz12.azimuth.isna()].station_id + "." + horiz12[horiz12.azimuth.isna()].channel))
        ne = ch[ch.channel.str[-1].isin(["N", "E"])]
        off = ne[(((ne.channel.str[-1] == "N") & ~np.isclose(ne.azimuth % 360, 0, atol=5) & ~np.isclose(ne.azimuth % 360, 360, atol=5))
                  | ((ne.channel.str[-1] == "E") & ~np.isclose(ne.azimuth % 360, 90, atol=5)))]
        details["ne_channels_off_nominal_azimuth"] = sorted(set(off.station_id + "." + off.channel + f" az" + off.azimuth.round(1).astype(str)))
        used = s[["station_id", "location", "channel"]].drop_duplicates()
        resp = ch.groupby(["station_id", "location", "channel"]).has_response.any().reset_index()
        m = used.merge(resp, on=["station_id", "location", "channel"], how="left")
        details["channels_without_response"] = sorted(set((m[m.has_response != True].station_id + "." + m[m.has_response != True].channel)))  # noqa: E712
    checks.append(Check("channel_sample_rates", "data", float(len(mixed)), "stations", exp, len(table), bool(mixed),
                        f"{len(mixed)} stations mix sample rates across or within their components ({', '.join(mixed[:12])})." if mixed else None,
                        details))

    # gaps: station-day-channel coverage inside the window
    span0 = np.maximum(s.file_start, window[0]) if window is not None else s.file_start
    span1 = np.minimum(s.file_end, window[1]) if window is not None else s.file_end
    expected = (span1 - span0).clip(lower=1.0)
    cover = (s.coverage_s.clip(upper=expected) / expected).clip(upper=1.0)
    g = s.assign(cover=cover.values, day=_day(s.file_start + 1.0))
    low = g[g.cover < c["coverage_min"]]
    share = len(low) / len(g)
    exp = f"share ≤ {c['gap_station_day_share_max']:.0%} of channel-days covering < {c['coverage_min']:.0%} of their span"
    worst = low.station_id.value_counts().head(6)
    checks.append(Check("data_gaps", "data", share, "share", exp, len(g), share > c["gap_station_day_share_max"],
                        (f"{len(low)} of {len(g)} channel-days cover less than {c['coverage_min']:.0%} of their span "
                         f"(most: {', '.join(f'{k} {v}' for k, v in worst.items())}).") if share > c["gap_station_day_share_max"] else None,
                        {"overlap_seconds_total": round(float(s.overlap_s.sum()), 1), "gap_seconds_total": round(float(s.gap_s.sum()), 1)}))
    return checks, extras


def _window_traces(reader: Reader, index: pd.DataFrame, sta: str, t0: float, t1: float):
    out = {}
    for comp, seed in sorted(station_channels(index, sta).items(), key=lambda kv: "Z123NE".find(kv[0])):
        w = reader.window(seed, t0, t1)
        if w is not None and np.isfinite(w[1]).sum() > 10:
            out[comp] = (seed, *w)
    return out


def _lag(a: np.ndarray, b: np.ndarray, rate: float, max_s: float = 1.0) -> float:
    """Time by which b lags a (s), from the cross-correlation peak within ±max_s."""
    m = int(max_s * rate)
    a, b = a - a.mean(), b - b.mean()
    if not np.any(a) or not np.any(b):
        return np.nan
    cc = np.correlate(b, a, mode="full")[len(a) - 1 - m:len(a) + m]
    return float((np.argmax(cc) - m) / rate)


def representative_windows(streams: pd.DataFrame, window, processed: Path | None, output_dir: Path, c: dict,
                           figures: bool = True) -> tuple[list[Check], dict, list[str]]:
    """Energetic windows, the raw and processed records of the most energetic stations, and their numbers."""
    c = {**DATA_DEFAULTS, **c}
    index = streams[["file", "seed_id", "station_id", "location", "channel", "component", "file_start", "file_end"]].drop_duplicates("file")
    if window is None:
        window = (float(index.file_start.min()), float(index.file_end.max()))
    reader = Reader(index)
    wins, scan = energetic_windows(reader, index, window, n=c["data_windows"])
    pindex = file_index(processed) if processed else None
    preader = Reader(pindex) if pindex is not None and not pindex.empty else None
    summary, needed, names = [], set(), []
    for k, w in enumerate(wins):
        t0 = min(w["onsets"].values()) - c["data_window_pre_s"] if w["onsets"] else w["start"]
        t1 = t0 + c["data_window_s"]
        stas = [s for s in w["stations_ranked"] if s in w["onsets"]][:c["data_window_stations"]]
        panel = []
        for sta in stas:
            raw = _window_traces(reader, index, sta, t0, t1)
            onset = w["onsets"][sta]
            for comp, (seed, t, x, rate) in raw.items():
                needed.add(f"{seed} {pd.Timestamp(_day(t0), unit='s'):%Y-%m-%d}")
                std = bandpass(x, rate)
                proc, label = None, "standard"
                if preader is not None:
                    pw = preader.window(seed, t0, t1)
                    if pw is not None and np.isfinite(pw[1]).sum() > 10:
                        proc = np.interp(t, pw[0], np.nan_to_num(pw[1]))
                        label = "agent"
                if proc is None:
                    proc = std
                i = int(np.clip((onset - t0) * rate, 1, len(t) - 2))
                n0, n1 = slice(0, max(i - int(rate), 1)), slice(i, min(i + int(5 * rate), len(t)))

                def snr(y):
                    yy = np.nan_to_num(y - np.nanmean(y))
                    nb = np.sqrt(np.mean(yy[n0] ** 2))
                    return float(np.sqrt(np.mean(yy[n1] ** 2)) / nb) if nb > 0 else np.nan

                row = {"window": k, "station": sta, "component": comp, "seed_id": seed, "processed_from": label, "rate_hz": float(rate),
                       "snr_raw": round(snr(x), 2), "snr_standard": round(snr(std), 2), "snr_processed": round(snr(proc), 2),
                       "peak_hz_raw": round(peak_frequency(np.nan_to_num(x - np.nanmean(x))[n1], rate), 2),
                       "peak_hz_processed": round(peak_frequency(proc[n1], rate), 2),
                       "lag_processed_vs_standard_s": round(_lag(std, proc, rate), 3) if label == "agent" else None}
                summary.append(row)
                panel.append((sta, comp, t - t0, x, proc, rate, onset - t0, label))
        if figures and panel:
            names.append(_window_figure(panel, k, w, t0, output_dir))
    checks = []
    agent_rows = [r for r in summary if r["processed_from"] == "agent" and r["snr_standard"] and r["snr_standard"] >= 3]
    rates = [r["rate_hz"] for r in agent_rows] if agent_rows else []
    lag_max = max(c["processing_lag_floor_s"], c["processing_lag_max_samples"] / float(np.median(rates))) if rates else c["processing_lag_floor_s"]
    exp = (f"|median time shift of processed records against a zero-phase {BAND_HZ[0]:g}–{BAND_HZ[1]:g} Hz filter| ≤ "
           f"{c['processing_lag_max_samples']} samples (≥ {c['processing_lag_floor_s']} s; {lag_max:.3f} s here): zero-phase processing shifts nothing, "
           "and a shift of a few samples already biases cross-correlation times")
    if processed is None:
        checks.append(_skip("processing_time_shift", "data", "s", exp, 0, "no processed waveforms given"))
    elif not agent_rows:
        checks.append(_skip("processing_time_shift", "data", "s", exp, 0, "no processed record found for the selected windows"))
    else:
        lag = float(np.median([r["lag_processed_vs_standard_s"] for r in agent_rows]))
        flag = abs(lag) > lag_max
        checks.append(Check("processing_time_shift", "data", lag, "s", exp, len(agent_rows), flag,
                            f"Processed records are shifted by {lag:+.2f} s (median of {len(agent_rows)} records) against the same records filtered zero-phase." if flag else None))
    details = {"scan": scan, "windows": [{"start_utc": f"{pd.Timestamp(w['start'], unit='s', tz='UTC'):%Y-%m-%dT%H:%M:%S}Z",
                                          "energetic_stations": w["energetic_stations"]} for w in wins],
               "records": summary, "processed_waveforms": str(processed) if processed else None,
               "processed_files_needed": sorted(needed),
               "note": ("Upper rows: raw records (mean removed). Lower rows: the Agent's processed records"
                        if processed else f"Lower rows: a standard processing (demean, detrend, {BAND_HZ[0]:g}–{BAND_HZ[1]:g} Hz zero-phase band-pass), not the Agent's")}
    return checks, details, names


def _window_figure(panel, k, w, t0, output_dir: Path) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    stas = list(dict.fromkeys(p[0] for p in panel))
    fig, ax = plt.subplots(len(stas), 3, figsize=(14, 1.6 * len(stas) + 1), squeeze=False,
                           gridspec_kw={"width_ratios": [3, 3, 1.6]})
    colors = {"Z": "k", "N": "tab:blue", "1": "tab:blue", "E": "tab:red", "2": "tab:red", "3": "k"}
    labels = set(p[7] for p in panel)
    for r, sta in enumerate(stas):
        rows = [p for p in panel if p[0] == sta]
        for col, idx in ((0, 3), (1, 4)):
            a = ax[r, col]
            scale = max(np.nanmax(np.abs(np.nan_to_num(p[idx] - np.nanmean(p[idx])))) for p in rows) or 1.0
            for j, p in enumerate(rows):
                y = np.nan_to_num(p[idx] - np.nanmean(p[idx])) / scale
                a.plot(p[2], y - 2.2 * j, lw=0.5, c=colors.get(p[1], "gray"))
                a.text(p[2][0], -2.2 * j + 0.5, p[1], fontsize=7)
            a.axvline(rows[0][6], c="orange", lw=0.8, ls="--")
            a.set_yticks([])
            a.set_xlim(0, p[2][-1])
            if r == 0:
                a.set_title("raw (mean removed)" if col == 0 else ("processed by the Agent" if labels == {"agent"} else
                            f"standard {BAND_HZ[0]:g}–{BAND_HZ[1]:g} Hz (no Agent processing given)" if labels == {"standard"} else "processed (Agent where given, else standard)"), fontsize=9)
            if col == 0:
                a.set_ylabel(sta, fontsize=8)
        a = ax[r, 2]
        z = rows[0]
        i = int(z[6] * z[5])
        for y, cc, lab in ((z[3], "gray", "raw"), (z[4], "tab:green", "processed")):
            sig = np.nan_to_num(y - np.nanmean(y))[i:i + int(10 * z[5])]
            noi = np.nan_to_num(y - np.nanmean(y))[:max(i - int(z[5]), 2)]
            for seg, ls in ((sig, "-"), (noi, ":")):
                if len(seg) > 16:
                    f = np.fft.rfftfreq(len(seg), 1 / z[5])
                    amp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) / np.sqrt(len(seg))
                    a.loglog(f[1:], amp[1:], c=cc, ls=ls, lw=0.7, label=f"{lab} {'signal' if ls == '-' else 'noise'}")
        a.set_xlim(0.2, z[5] / 2)
        if r == 0:
            a.set_title(f"{z[1]} spectra", fontsize=9)
            a.legend(fontsize=6)
    ax[-1, 0].set_xlabel("s after window start")
    ax[-1, 1].set_xlabel("s after window start")
    ax[-1, 2].set_xlabel("Hz")
    fig.suptitle(f"Window {k + 1}: {pd.Timestamp(t0, unit='s', tz='UTC'):%Y-%m-%d %H:%M:%S} UTC, {w['energetic_stations']} energetic stations "
                 f"(dashed: energy onset at each station)", fontsize=10)
    fig.tight_layout()
    name = f"data_window_{k + 1}.png"
    fig.savefig(output_dir / name, dpi=110)
    plt.close(fig)
    return name


def data_figures(table: pd.DataFrame, streams: pd.DataFrame, window, output_dir: Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = []
    st = table.dropna(subset=["latitude"])
    fig, a = plt.subplots(figsize=(7, 7))
    lat0, lon0 = float(st.latitude.median()), float(st.longitude.median())
    x, y = local_km(st.latitude, st.longitude, lat0, lon0)
    markers = {"seismometer": "^", "accelerometer": "s", "geophone": "v"}
    for (cls, inst), g in st.assign(x=x, y=y).groupby(["components", "instrument"]):
        a.scatter(g.x, g.y, marker=markers.get(inst, "s" if "accelerometer" in inst else "o"), s=50,
                  label=f"{cls}, {inst.replace(',', ' + ')} ({len(g)})", edgecolor="k")
        for _, r in g.iterrows():
            a.annotate(r.station_id.split(".")[-1], (r.x, r.y), fontsize=6, xytext=(3, 3), textcoords="offset points")
    rmax = float(np.hypot(x, y).max()) * 1.1 or 1.0
    for ang in range(0, 360, 30):
        a.plot([0, rmax * np.sin(np.radians(ang))], [0, rmax * np.cos(np.radians(ang))], c="lightgray", lw=0.5, zorder=0)
    a.plot(0, 0, "k+", ms=12, label="network centre")
    a.set(xlabel="east (km)", ylabel="north (km)", aspect="equal", title="Stations with data: components and instrument type")
    a.legend(fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(output_dir / "data_stations.png", dpi=110)
    plt.close(fig)
    names.append("data_stations.png")

    s = _in_window(streams, window)
    s = s.assign(day=_day(s.file_start + 1.0), frac=(s.coverage_s / (s.file_end - s.file_start).clip(lower=1)).clip(upper=1))
    m = s.groupby(["station_id", "day"]).frac.min().unstack()
    fig, a = plt.subplots(figsize=(max(6, 0.35 * m.shape[1] + 3), max(4, 0.18 * m.shape[0] + 1.5)))
    im = a.imshow(m.to_numpy(), aspect="auto", cmap="viridis", vmin=0, vmax=1, interpolation="nearest")
    a.set_yticks(range(m.shape[0]), m.index, fontsize=6)
    a.set_xticks(range(m.shape[1]), [f"{pd.Timestamp(d, unit='s'):%m-%d}" for d in m.columns], fontsize=7, rotation=90)
    a.set_title("Data coverage per station-day (lowest channel; white = no file)")
    fig.colorbar(im, ax=a, label="covered fraction")
    fig.tight_layout()
    fig.savefig(output_dir / "data_availability.png", dpi=110)
    plt.close(fig)
    names.append("data_availability.png")
    return names
