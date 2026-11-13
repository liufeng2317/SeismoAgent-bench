"""Pickers for part 3 of the pipeline. All share one contract:

    picks = picker(chosen, window, cfg) -> DataFrame[station, phase, time_utc, score, method]

where `chosen` comes from pipeline.select_channels and `window` from
pipeline.event_window. B0 is classical (no trained model); B1 is PhaseNet with
the SCEDC weights. The agent will plug in through the same contract.
"""
import numpy as np
import pandas as pd
from obspy import Stream
from obspy.signal.trigger import recursive_sta_lta, trigger_onset

from paths import SEISBENCH_ROOT

# B0: P by STA/LTA + AIC on the vertical, S by STA/LTA + AIC on the horizontals
# (design 5.1). ObsPy's AR-AIC ar_pick was dropped: on this machine repeated calls
# on identical input returned S = 0 in about 8% of calls (memory-dependent).
CLASSIC_DEFAULTS = dict(
    freqmin=1.0, freqmax=20.0,                      # zero-phase band-pass before picking
    sta_s=0.3, lta_s=5.0, thr_on=4.0, thr_off=1.5,  # P detection on the vertical
    aic_before_s=1.0, aic_after_s=0.5,              # AIC search around the P trigger
    snr_min=3.0, snr_noise_s=2.0, snr_signal_s=1.0,  # RMS ratio after/before the pick
    s_after_p_s=1.0, s_window_s=30.0,                # S searched in [P + this, P + s_window_s]
    s_sta_s=0.5, s_lta_s=3.0,                        # STA/LTA on the horizontal amplitude
    s_aic_before_s=1.5, s_aic_after_s=0.5,           # AIC search around the S trigger
)


def aic_onset(x, edge=0.1):
    """Index of the AIC minimum, or None when it sits within `edge` (fraction of
    the window) of either end: refinement failed and the trigger is kept."""
    a = aic(x)
    k = int(np.argmin(a))
    m = max(2, int(edge * len(x)))
    return None if (k < m or k > len(x) - m) else k


def aic(x):
    """Maeda (1985) AIC; the onset is at the minimum."""
    n = len(x)
    out = np.full(n, np.inf)
    for k in range(2, n - 2):
        v1, v2 = np.var(x[:k]), np.var(x[k:])
        if v1 > 0 and v2 > 0:
            out[k] = k * np.log(v1) + (n - k - 1) * np.log(v2)
    return out


def _prep(tr, cfg, window):
    """Causal band-pass for detection. A zero-phase filter rings ahead of strong
    impulsive onsets and made STA/LTA trigger ~1 s early on M4 events."""
    tr = tr.copy().trim(window["start"] - 5, window["end"])
    tr.detrend("demean").taper(0.02)
    tr.filter("bandpass", freqmin=cfg["freqmin"], freqmax=cfg["freqmax"], zerophase=False)
    return tr


def _prep_onset(tr, cfg, window):
    """Causal high-pass only, for timing the onset: a zero-phase filter spreads
    energy ahead of an impulsive onset (up to ~1/freqmin s) and pulls AIC early."""
    tr = tr.copy().trim(window["start"] - 5, window["end"])
    tr.detrend("demean").taper(0.02)
    tr.filter("highpass", freq=cfg["freqmin"], corners=2, zerophase=False)
    return tr


def _snr(data, i, fs, cfg):
    noise = data[max(0, i - int(cfg["snr_noise_s"] * fs)): i]
    sig = data[i: i + int(cfg["snr_signal_s"] * fs)]
    if len(noise) < 10 or len(sig) < 10:
        return 0.0
    return float(np.sqrt(np.mean(sig ** 2)) / (np.sqrt(np.mean(noise ** 2)) + 1e-20))


def classic_p(tr, window, cfg, onset_tr=None):
    """Largest STA/LTA trigger in the window (on tr, causal band-pass), refined
    by AIC on onset_tr (causal high-pass; defaults to tr). Returns (time, snr) or None."""
    on_data = (onset_tr if onset_tr is not None else tr).data
    fs = tr.stats.sampling_rate
    cft = recursive_sta_lta(tr.data, int(cfg["sta_s"] * fs), int(cfg["lta_s"] * fs))
    cft[: int(cfg["lta_s"] * fs)] = 0
    lo = max(0, int((window["start"] - tr.stats.starttime) * fs))
    on = [(a, b) for a, b in trigger_onset(cft, cfg["thr_on"], cfg["thr_off"]) if a >= lo]
    if not on:
        return None
    a, b = max(on, key=lambda ab: cft[ab[0]: ab[1] + 1].max())
    i0, i1 = max(0, a - int(cfg["aic_before_s"] * fs)), min(len(tr.data), a + int(cfg["aic_after_s"] * fs))
    k = aic_onset(on_data[i0:i1])
    k = a if k is None else i0 + k
    return tr.stats.starttime + k / fs, _snr(tr.data, k, fs, cfg)


def classic_s(n, e, tp, cfg, onset=None):
    """Largest STA/LTA peak of the horizontal amplitude after P (n, e causal
    band-pass), refined by AIC on the larger horizontal of onset = (n, e) causal
    high-passed (defaults to n, e). Returns (time, snr) or None."""
    fs = n.stats.sampling_rate
    t0 = max(n.stats.starttime, e.stats.starttime)
    k = min(len(n.data) - int((t0 - n.stats.starttime) * fs), len(e.data) - int((t0 - e.stats.starttime) * fs))
    hn = n.data[int((t0 - n.stats.starttime) * fs):][:k]
    he = e.data[int((t0 - e.stats.starttime) * fs):][:k]
    amp = np.sqrt(hn ** 2 + he ** 2)
    cft = recursive_sta_lta(amp, int(cfg["s_sta_s"] * fs), int(cfg["s_lta_s"] * fs))
    lo = int((tp + cfg["s_after_p_s"] - t0) * fs)
    hi = min(len(cft), int((tp + cfg["s_window_s"] - t0) * fs))
    if hi - lo < fs:
        return None
    j = lo + int(np.argmax(cft[lo:hi]))
    if cft[j] < cfg["thr_on"] * 0.5:  # S rides on the P coda: half the P threshold
        return None
    on = onset if onset is not None else (n, e)
    cn = on[0].data[int((t0 - on[0].stats.starttime) * fs):][:k]
    ce = on[1].data[int((t0 - on[1].stats.starttime) * fs):][:k]
    comp = cn if np.abs(hn[j - lo:j]).max(initial=0) >= np.abs(he[j - lo:j]).max(initial=0) else ce
    i0, i1 = max(lo, j - int(cfg["s_aic_before_s"] * fs)), min(len(comp), j + int(cfg["s_aic_after_s"] * fs))
    if i1 - i0 < 10:
        return None
    m = aic_onset(comp[i0:i1])
    m = j if m is None else i0 + m
    return t0 + m / fs, _snr(comp, m, fs, cfg)


def pick_classic(chosen, window, cfg=None):
    cfg = {**CLASSIC_DEFAULTS, **(cfg or {})}
    rows = []
    for sid, c in chosen.items():
        z = _prep(c["Z"], cfg, window)
        p = classic_p(z, window, cfg, onset_tr=_prep_onset(c["Z"], cfg, window))
        if p is None or p[1] < cfg["snr_min"]:
            continue
        tp, snr_p = p
        rows.append(dict(station=sid, phase="P", time_utc=str(tp), score=snr_p, method="B0"))
        if c["N"] is None or c["E"] is None:
            continue
        s = classic_s(_prep(c["N"], cfg, window), _prep(c["E"], cfg, window), tp, cfg,
                      onset=(_prep_onset(c["N"], cfg, window), _prep_onset(c["E"], cfg, window)))
        if s is not None and s[1] >= cfg["snr_min"] * 0.67:  # a looser ratio on the P coda
            rows.append(dict(station=sid, phase="S", time_utc=str(s[0]), score=s[1], method="B0"))
    return pd.DataFrame(rows, columns=["station", "phase", "time_utc", "score", "method"])


# B1: PhaseNet, SCEDC weights, thresholds shipped with them (design 5.1).
_PHASENET = {}


def phasenet_model(name="scedc", version="2"):
    key = (name, version)
    if key not in _PHASENET:
        import seisbench
        import seisbench.models as sbm
        seisbench.cache_root = SEISBENCH_ROOT.resolve()
        _PHASENET[key] = sbm.PhaseNet.from_pretrained(name, version_str=version, update=False)
    return _PHASENET[key]


def pick_phasenet(chosen, window, cfg=None):
    cfg = dict(weights="scedc", version="2", **(cfg or {}))
    model = phasenet_model(cfg["weights"], cfg["version"])
    rows = []
    for sid, c in chosen.items():
        net, sta = sid.split(".")
        st = Stream()
        for comp in "ZNE":
            tr = c[comp] if c[comp] is not None else c["Z"]  # single-component: repeat Z (P only)
            tr = tr.copy().trim(window["start"], window["end"])
            tr.stats.network, tr.stats.station, tr.stats.location = net, sta, ""
            tr.stats.channel = f"XX{comp}"
            st += tr
        out = model.classify(st)
        for p in getattr(out, "picks", out):
            if c["N"] is None and p.phase == "S":
                continue
            rows.append(dict(station=sid, phase=p.phase, time_utc=str(p.peak_time), score=float(p.peak_value),
                             method="B1"))
    return pd.DataFrame(rows, columns=["station", "phase", "time_utc", "score", "method"])


PICKERS = {"B0": pick_classic, "B1": pick_phasenet}
