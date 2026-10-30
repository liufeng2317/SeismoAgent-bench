"""Stage 2 checks and figures that look at the waveforms under the picks.

A fixed sample of picks (evenly spaced station-days, evenly spaced picks within each) is compared
with the records: the AIC onset near each pick and the amplitude ratio across it. Figures show
representative windows with all picks overlaid and per-station stacks aligned on the picks.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .checks import Check, Data, _skip
from .waveforms import BAND_HZ, Reader, aic_onset, amplitude_ratio, bandpass, station_channels

PICK_WAVEFORM_DEFAULTS = {
    "pick_sample_station_days": 40, "pick_sample_per_day": 10, "pick_search_s": 3.0,
    "onset_min_snr": 3.0, "pick_onset_offset_max_s": {"P": 0.2}, "pick_snr_low": 2.0,
    "pick_figure_windows_dense": 3, "pick_figure_windows_sparse": 2, "pick_figure_stations": 8,
    "stack_stations": 4, "stack_picks": 40,
}
HORIZONTAL = ("N", "E", "1", "2")


def _even(items, n):
    items = list(items)
    if len(items) <= n:
        return items
    return [items[int(i)] for i in np.linspace(0, len(items) - 1, n).round().astype(int)]


def sample_picks(picks: pd.DataFrame, c: dict) -> pd.DataFrame:
    p = picks.sort_values(["station_id", "time", "phase"]).assign(day=lambda x: np.floor(x.time / 86400) * 86400)
    days = _even(sorted(set(zip(p.station_id, p.day))), c["pick_sample_station_days"])
    parts = [_even_df(p[(p.station_id == s) & (p.day == d)], c["pick_sample_per_day"]) for s, d in days]
    return pd.concat(parts) if parts else p.iloc[:0]


def _even_df(df: pd.DataFrame, n: int) -> pd.DataFrame:
    if len(df) <= n:
        return df
    return df.iloc[np.linspace(0, len(df) - 1, n).round().astype(int)]


def _measure(reader: Reader, index: pd.DataFrame, pick: pd.Series, c: dict, p_time: float | None = None) -> dict:
    """AIC onset and amplitude ratio near one pick. An S pick's search starts just after the same
    event's P pick at the station, so that a short S−P time does not return the P onset."""
    ch = station_channels(index, pick.station_id)
    comps = ["Z"] if pick.phase == "P" else [k for k in HORIZONTAL if k in ch]
    if pick.phase == "P" and "Z" not in ch:
        comps = ["3"] if "3" in ch else []
    best = None
    pad = c["pick_search_s"] + 1.0
    for comp in comps:
        if comp not in ch:
            continue
        start = pick.time - pad - 2.0
        if pick.phase == "S" and p_time is not None and np.isfinite(p_time) and p_time < pick.time:
            start = max(start, p_time + 0.2 - 1.0)  # one second of P coda before the search
        w = reader.window(ch[comp], start, pick.time + pad + 2.0)
        if w is None or not np.isfinite(w[1]).all():
            continue
        t, x, rate = w
        y = bandpass(x, rate)
        i_pick = int(round((pick.time - t[0]) * rate))
        lo, hi = int(round((pick.time - c["pick_search_s"] - t[0]) * rate)), int(round((pick.time + c["pick_search_s"] - t[0]) * rate))
        if start > pick.time - pad - 2.0:
            lo = max(lo, int(round(1.0 * rate)))
        k = aic_onset(y, rate, lo, hi)
        if k is None:
            continue
        r = {"component": comp, "snr_at_pick": amplitude_ratio(y, rate, i_pick), "snr_at_onset": amplitude_ratio(y, rate, k),
             "offset_s": (i_pick - k) / rate}
        if best is None or np.nan_to_num(r["snr_at_onset"]) > np.nan_to_num(best["snr_at_onset"]):
            best = r
    return best or {}


def pick_waveform_checks(d: Data, index: pd.DataFrame, c: dict) -> tuple[list[Check], dict]:
    c = {**PICK_WAVEFORM_DEFAULTS, **c}
    lim = c["pick_onset_offset_max_s"]
    exp_off = (f"|median P pick − AIC onset| ≤ {lim['P']} s for picks whose onset has SNR ≥ {c['onset_min_snr']:g} (S reported only); "
               "a zero-phase filter moves the AIC onset slightly early, so clean P picks lie a few hundredths of a second after it")
    exp_snr = f"reported: share of picks with amplitude ratio < {c['pick_snr_low']:g} across the pick"
    picks = d.all_picks[d.all_picks.station_id.isin(set(index.station_id))]
    if picks.empty:
        why = "no picks at stations with waveform files"
        return [_skip("pick_onset_offset", "time", "s", exp_off, 0, why), _skip("pick_snr", "reality", "share", exp_snr, 0, why)], {}
    reader = Reader(index)
    sample = sample_picks(picks, c)
    p_first = picks[(picks.phase == "P") & (picks.event_id != "")].groupby(["event_id", "station_id"]).time.min().to_dict()
    rows = []
    for _, pk in sample.iterrows():
        m = _measure(reader, index, pk, c, p_first.get((pk.event_id, pk.station_id)) if pk.event_id else None)
        if m:
            rows.append({"station_id": pk.station_id, "phase": pk.phase, "time": pk.time, **m})
    m = pd.DataFrame(rows, columns=["station_id", "phase", "time", "component", "snr_at_pick", "snr_at_onset", "offset_s"])
    details = {"sampled_picks": int(len(sample)), "measured_picks": int(len(m))}
    checks = []
    clear = m[m.snr_at_onset >= c["onset_min_snr"]]
    per_phase = {ph: {"n": int(len(g)), "median_offset_s": round(float(g.offset_s.median()), 3),
                      "mad_offset_s": round(float((g.offset_s - g.offset_s.median()).abs().median()), 3),
                      "share_beyond_0p5_s": round(float((g.offset_s.abs() > 0.5).mean()), 3)} for ph, g in clear.groupby("phase")}
    if len(clear) < 10:
        checks.append(_skip("pick_onset_offset", "time", "s", exp_off, len(clear), f"{len(clear)} sampled picks with a clear onset"))
    else:
        # S onsets in P coda are not measured reliably by AIC (identical S picks can score differently), so only P flags
        worst = ("P", per_phase["P"]) if per_phase.get("P", {}).get("n", 0) >= 10 else max(per_phase.items(), key=lambda kv: kv[1]["n"])
        med = worst[1]["median_offset_s"]
        flag = worst[0] == "P" and abs(med) > lim["P"]
        checks.append(Check("pick_onset_offset", "time", med, "s", exp_off, len(clear), flag,
                            (f"Sampled {worst[0]} picks lie {abs(med):.2f} s {'after' if med > 0 else 'before'} the AIC onset of the "
                             f"{BAND_HZ[0]:g}–{BAND_HZ[1]:g} Hz record (median of {worst[1]['n']}).") if flag else None,
                            {"by_phase": per_phase, "phase_reported": worst[0]}))
    snr = m.snr_at_pick.dropna()
    if len(snr) < 10:
        checks.append(_skip("pick_snr", "reality", "share", exp_snr, len(snr), f"{len(snr)} sampled picks with a readable record"))
    else:
        low = float((snr < c["pick_snr_low"]).mean())
        flag = False  # correct catalogs often keep many weak picks; reported only
        by = {ph: round(float((g.snr_at_pick < c["pick_snr_low"]).mean()), 3) for ph, g in m.dropna(subset=["snr_at_pick"]).groupby("phase")}
        checks.append(Check("pick_snr", "reality", low, "share", exp_snr, len(snr), flag,
                            f"{low:.0%} of {len(snr)} sampled picks have less than {c['pick_snr_low']:g}× more amplitude after the pick than before it." if flag else None,
                            {"by_phase": by, "median_snr": round(float(snr.median()), 2)}))
    details["per_station"] = (m.groupby("station_id").agg(n=("offset_s", "size"), median_offset_s=("offset_s", "median"),
                                                          median_snr=("snr_at_pick", "median")).round(3).reset_index().to_dict("records"))
    return checks, {"measurements": m, **details}


def _pick_windows(picks: pd.DataFrame, c: dict) -> list[tuple[float, str]]:
    b = np.floor(picks.time / 60.0) * 60.0
    counts = b.value_counts().sort_index()
    dense = []
    for t, n in counts.sort_values(ascending=False, kind="stable").items():
        if len(dense) >= c["pick_figure_windows_dense"]:
            break
        if all(abs(t - u) >= 3600 for u, _ in dense):
            dense.append((float(t), "dense"))
    sparse_pool = counts[(counts >= 2) & (counts <= 4)]
    sparse = [(float(t), "sparse") for t in _even(sparse_pool.index, c["pick_figure_windows_sparse"])] if len(sparse_pool) else []
    return dense + sparse


def pick_figures(d: Data, index: pd.DataFrame, measured: pd.DataFrame, c: dict, output_dir: Path) -> tuple[list[str], dict]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    c = {**PICK_WAVEFORM_DEFAULTS, **c}
    reader = Reader(index)
    picks = d.all_picks[d.all_picks.station_id.isin(set(index.station_id))]
    names, summary = [], {"windows": [], "stacks": []}
    for k, (b0, kind) in enumerate(_pick_windows(picks, c)):
        inwin = picks[(picks.time >= b0) & (picks.time < b0 + 60)]
        first = inwin.groupby("station_id").time.min().sort_values()
        stas = list(first.index[:c["pick_figure_stations"]])
        t0 = float(first.iloc[0]) - 10.0
        t1 = max(t0 + 50.0, float(inwin.time.max()) + 10.0)
        t1 = min(t1, t0 + 90.0)
        allp = picks[(picks.time >= t0) & (picks.time <= t1) & picks.station_id.isin(stas)]
        fig, ax = plt.subplots(len(stas), 1, figsize=(12, 1.25 * len(stas) + 1), sharex=True, squeeze=False)
        for r, sta in enumerate(stas):
            a = ax[r, 0]
            ch = station_channels(index, sta)
            for j, comp in enumerate([x for x in ("Z", "3") if x in ch][:1] + [x for x in HORIZONTAL if x in ch][:1]):
                w = reader.window(ch[comp], t0, t1)
                if w is None:
                    continue
                y = bandpass(w[1], w[2])
                scale = np.percentile(np.abs(y), 99.5) or 1.0
                a.plot(w[0] - t0, np.clip(y / scale, -1.2, 1.2) - 2.6 * j, lw=0.5, c="k" if j == 0 else "tab:blue")
                a.text(0, -2.6 * j + 0.6, comp, fontsize=7)
            for _, pk in allp[allp.station_id == sta].iterrows():
                a.axvline(pk.time - t0, c="tab:red" if pk.phase == "P" else "tab:blue", lw=1.0, ls="-" if pk.event_id else ":")
                if np.isfinite(pk.probability):
                    a.text(pk.time - t0, 0.9, f"{pk.phase} {pk.probability:.2f}", fontsize=6, color="tab:red" if pk.phase == "P" else "tab:blue")
            a.set_yticks([])
            a.set_ylabel(sta, fontsize=7)
        ax[-1, 0].set_xlabel(f"s after {pd.Timestamp(t0, unit='s', tz='UTC'):%Y-%m-%d %H:%M:%S} UTC")
        fig.suptitle(f"Picks window {k + 1} ({kind}): {BAND_HZ[0]:g}–{BAND_HZ[1]:g} Hz, clipped at the 99.5th percentile; black vertical, blue horizontal; "
                     "red P, blue S; solid associated, dotted unassociated", fontsize=9)
        fig.tight_layout()
        name = f"picks_window_{k + 1}.png"
        fig.savefig(output_dir / name, dpi=110)
        plt.close(fig)
        names.append(name)
        summary["windows"].append({"figure": name, "kind": kind, "start_utc": f"{pd.Timestamp(t0, unit='s', tz='UTC'):%Y-%m-%dT%H:%M:%S}Z",
                                   "stations": stas, "picks": int(len(allp)), "p": int((allp.phase == "P").sum()),
                                   "s": int((allp.phase == "S").sum()), "unassociated": int((allp.event_id == "").sum())})
    p = picks[picks.phase == "P"]
    top = p.station_id.value_counts().head(c["stack_stations"]).index
    if len(top):
        fig, ax = plt.subplots(1, len(top), figsize=(3.2 * len(top), 7), squeeze=False)
        for j, sta in enumerate(top):
            a = ax[0, j]
            sel = _even_df(p[p.station_id == sta].sort_values("time"), c["stack_picks"])
            ch = station_channels(index, sta)
            comp = "Z" if "Z" in ch else next(iter(ch), None)
            n = 0
            for _, pk in sel.iterrows():
                w = reader.window(ch[comp], pk.time - 6.0, pk.time + 6.0) if comp else None
                if w is None or not np.isfinite(w[1]).all():
                    continue
                y = bandpass(w[1], w[2])
                keep = (w[0] >= pk.time - 4.0) & (w[0] <= pk.time + 4.0)
                yy = y[keep]
                a.plot(w[0][keep] - pk.time, yy / (np.abs(yy).max() or 1) * 0.6 - n, lw=0.4, c="k")
                n += 1
            a.axvline(0, c="tab:red", lw=0.8)
            a.set(title=f"{sta} ({n} P picks)", xlabel="s from pick", yticks=[])
            ms = measured[(measured.station_id == sta) & (measured.phase == "P")] if len(measured) else measured
            summary["stacks"].append({"station": sta, "picks_shown": n,
                                      "median_offset_from_aic_s": round(float(ms.offset_s.median()), 3) if len(ms) else None})
        fig.suptitle(f"P picks aligned on the pick time ({comp}, {BAND_HZ[0]:g}–{BAND_HZ[1]:g} Hz, each trace normalised): "
                     "onsets should line up at 0", fontsize=9)
        fig.tight_layout()
        fig.savefig(output_dir / "picks_station_stacks.png", dpi=110)
        plt.close(fig)
        names.append("picks_station_stacks.png")
    return names, summary
