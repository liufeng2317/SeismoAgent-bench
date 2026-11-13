"""Baseline pipeline shared by all pickers and, later, by the agent harness.

Parts (docs/design.md 5.1): 1 event window, 2 channels, 3 picks (pickers.py),
4 association (PyOcto), 5 location (HypoInverse). Every part works on plain
tables, so any picker -- classic, DL or agent -- can replace part 3 while the
other parts stay identical.
"""
import json
import subprocess
import sys

import numpy as np
import pandas as pd
from obspy import UTCDateTime, read
from obspy.signal.trigger import recursive_sta_lta, trigger_onset

from paths import DATA, HK_MODEL, RES_A, SEISMOTOOLS

# Part 1: network trigger defining the event window (design 5.1).
WINDOW_DEFAULTS = dict(freqmin=2.0, freqmax=15.0, sta_s=0.5, lta_s=10.0, thr_on=4.0, thr_off=1.5,
                       min_stations=5, coincidence_s=10.0, before_s=60.0, after_s=180.0,
                       skip_start_s=30.0, skip_end_s=5.0,  # taper and LTA warm-up give false triggers
                       peak_fraction=0.5)
# Part 4 and 5: shared by every picker.
REGION_R2 = dict(latitude=[33.6, 34.9], longitude=[-118.3, -116.7], depth_km=[0.0, 30.0])
ASSOCIATION_DEFAULTS = dict(region=REGION_R2, reference_elevation_km=0.0, velocity_layering="step",
                            associator=dict(n_picks=8, n_p_picks=4, n_s_picks=0, n_p_and_s_picks=0,
                                            pick_match_tolerance=1.5))  # no S required: B0 has few S
LOCATION_DEFAULTS = dict(model_type="CRE", reference_elevation_km=0.0, trial_depth_km=8.0)


# ---------------------------------------------------------------- data

def load_batch(name="a1_first_batch"):
    """Stations, events and reference picks of a selected batch (results of part a)."""
    batch = RES_A / name
    stations = pd.read_csv(batch / "stations.csv")
    events = pd.read_csv(batch / "events.csv")
    ref = pd.read_csv(RES_A / "a2_labels" / "reference_picks_first_batch.csv")
    origins = (ref.groupby("event_id")[["origin_time", "origin_lat", "origin_lon", "origin_depth_km",
                                        "magnitude"]].first())
    events = events.merge(origins, left_on="event_id", right_index=True, how="left")
    return stations, events, ref


def read_event(event_id, name="socal_r2"):
    return read(str(DATA / "waveforms" / "raw" / name / f"{event_id}.mseed"))


def station_table(stations):
    """Station list in the locator/associator contract."""
    return pd.DataFrame(dict(station_id=stations.station, latitude=stations.lat,
                             longitude=stations.lon, elevation_m=stations.elevation_m))


def distance_km(lat0, lon0, lat, lon):
    r = 6371.0
    p0, p = np.radians(lat0), np.radians(lat)
    a = np.sin((p - p0) / 2) ** 2 + np.cos(p0) * np.cos(p) * np.sin(np.radians(lon - lon0) / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


# ---------------------------------------------------------------- part 2: channels

def select_channels(st, stations, ref):
    """One three-component set per station (design 5.1).

    HH three components if present; otherwise short-period EHZ with the
    accelerometer HNN/HNE (where analysts pick S); otherwise HN; otherwise a
    vertical channel alone. With two location codes, the one carrying manual
    picks is used. Gaps (at most a few seconds here) are linearly interpolated.
    """
    chosen, rows = {}, []
    for sid in stations.station:
        net, sta = sid.split(".")
        sub = st.select(network=net, station=sta)
        if not len(sub):
            rows.append(dict(station=sid, family="none", location="", gaps=0))
            continue
        locs = sorted({tr.stats.location for tr in sub})
        ref_locs = ref[(ref.station == sid) & (ref["mode"] == "manual")].location.fillna("").astype(str)
        loc = next((l for l in locs if l in set(ref_locs)), locs[0])
        sub = sub.select(location=loc)
        gaps = len(sub.get_gaps())
        sub = sub.copy().merge(method=1, fill_value="interpolate")
        get = {tr.stats.channel: tr for tr in sub}
        if all(f"HH{c}" in get for c in "ZNE"):
            fam, z, n, e = "HH", get["HHZ"], get["HHN"], get["HHE"]
        elif "EHZ" in get and "HNN" in get and "HNE" in get:
            fam, z, n, e = "EHZ+HN", get["EHZ"], get["HNN"], get["HNE"]
        elif all(f"HN{c}" in get for c in "ZNE"):
            fam, z, n, e = "HN", get["HNZ"], get["HNN"], get["HNE"]
        else:
            zc = next((c for c in ("HHZ", "EHZ", "HNZ") if c in get), None)
            fam, z, n, e = ("Z only", get[zc], None, None) if zc else ("none", None, None, None)
        if z is not None:
            chosen[sid] = dict(Z=z, N=n, E=e, family=fam)
        rows.append(dict(station=sid, family=fam, location=loc or "--", gaps=gaps,
                         channels="/".join(t.stats.channel for t in (z, n, e) if t is not None)))
    return chosen, pd.DataFrame(rows)


# ---------------------------------------------------------------- part 1: event window

def event_window(chosen, cfg=None):
    """Network STA/LTA trigger on the vertical channels.

    Counts, on a 0.5 s grid, the stations with an onset in the last
    coincidence_s; the event is the burst around the peak of that count. The
    trigger is the earliest onset where the burst first reaches
    max(min_stations, peak_fraction x peak). Returns the trigger, the window [trigger - before_s,
    trigger + after_s], and the per-station trigger onsets and the count curve
    for plotting.
    """
    cfg = {**WINDOW_DEFAULTS, **(cfg or {})}
    onsets = {}
    t0 = min(c["Z"].stats.starttime for c in chosen.values())
    t1 = max(c["Z"].stats.endtime for c in chosen.values())
    for sid, c in chosen.items():
        tr = c["Z"].copy().detrend("demean").taper(0.02)
        tr.filter("bandpass", freqmin=cfg["freqmin"], freqmax=cfg["freqmax"], zerophase=True)
        fs = tr.stats.sampling_rate
        cft = recursive_sta_lta(tr.data, int(cfg["sta_s"] * fs), int(cfg["lta_s"] * fs))
        cft[: int(cfg["skip_start_s"] * fs)] = 0  # tapered start, LTA not yet stable
        cft[len(cft) - int(cfg["skip_end_s"] * fs):] = 0
        on = trigger_onset(cft, cfg["thr_on"], cfg["thr_off"])
        onsets[sid] = [tr.stats.starttime + i / fs for i, _ in on]
    grid = np.arange(0.0, t1 - t0, 0.5)
    count = np.zeros_like(grid)
    for times in onsets.values():
        hit = np.zeros_like(grid, bool)
        for t in times:
            hit |= (grid >= t - t0) & (grid < t - t0 + cfg["coincidence_s"])
        count += hit
    # The event is the largest burst of coincident triggers; scattered noise
    # triggers at a few stations can reach min_stations but not half the peak.
    peak = int(np.argmax(count))
    need = max(cfg["min_stations"], cfg["peak_fraction"] * count[peak])
    if count[peak] < cfg["min_stations"]:
        return None
    i = peak
    while i > 0 and count[i - 1] >= need:
        i -= 1
    # earliest onset among the stations counted at the start of that burst
    t_first = t0 + grid[i]
    early = [t for times in onsets.values() for t in times if t_first - cfg["coincidence_s"] <= t <= t_first]
    trig = min(early) if early else t_first
    return dict(trigger=trig, start=trig - cfg["before_s"], end=trig + cfg["after_s"],
                onsets=onsets, grid_t0=t0, grid=grid, count=count, cfg=cfg)


# ---------------------------------------------------------------- parts 4 and 5: upstream tools

def _run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"{cmd[1]} failed:\n{res.stdout[-2000:]}\n{res.stderr[-2000:]}")


def associate(picks, stations, out, cfg=None, workers=4):
    """PyOcto on all picks of the batch; returns picks with event_index, status and residual."""
    cfg = json.loads(json.dumps({**ASSOCIATION_DEFAULTS, **(cfg or {})}))
    out.mkdir(parents=True, exist_ok=True)
    p = picks.reset_index(drop=True).copy()
    p["pick_id"] = [f"p{i:06d}" for i in range(len(p))]
    p[["pick_id", "station", "phase", "time_utc"]].rename(columns={"station": "station_id"}) \
        .to_csv(out / "picks_in.csv", index=False)
    station_table(stations).to_csv(out / "stations.csv", index=False)
    (out / "config_in.json").write_text(json.dumps(cfg, indent=1))
    _run([sys.executable, str(SEISMOTOOLS / "pyocto" / "interface" / "run.py"),
          "--picks", str(out / "picks_in.csv"), "--stations", str(out / "stations.csv"),
          "--velocity-model", str(HK_MODEL), "--config", str(out / "config_in.json"),
          "--output-dir", str(out / "pyocto"), "--workers", str(workers), "--overwrite", "--quiet"])
    asg = pd.read_csv(out / "pyocto" / "assignments.csv")
    ev = pd.read_csv(out / "pyocto" / "events.csv")
    p = p.merge(asg[["pick_id", "event_index", "assignment_status", "residual_s"]], on="pick_id", how="left")
    return p, ev


def locate(arrivals, stations, out, cfg=None):
    """HypoInverse with the SCSN Hadley-Kanamori model; arrivals need event_id."""
    cfg = {**LOCATION_DEFAULTS, **(cfg or {})}
    out.mkdir(parents=True, exist_ok=True)
    a = arrivals.reset_index(drop=True).copy()
    if "pick_id" not in a:
        a["pick_id"] = [f"a{i:06d}" for i in range(len(a))]
    cols = ["event_id", "pick_id", "station", "phase", "time_utc"] + (["uncertainty_s"] if "uncertainty_s" in a else [])
    a[cols].rename(columns={"station": "station_id"}).to_csv(out / "arrivals_in.csv", index=False)
    station_table(stations).to_csv(out / "stations.csv", index=False)
    (out / "config_in.json").write_text(json.dumps(cfg, indent=1))
    _run([sys.executable, str(SEISMOTOOLS / "hypoinverse" / "interface" / "run.py"),
          "--arrivals", str(out / "arrivals_in.csv"), "--stations", str(out / "stations.csv"),
          "--velocity-model", str(HK_MODEL), "--config", str(out / "config_in.json"),
          "--output-dir", str(out / "hypoinverse"), "--overwrite", "--quiet"])
    ev = pd.read_csv(out / "hypoinverse" / "events.csv")
    arr = pd.read_csv(out / "hypoinverse" / "arrivals.csv")
    return ev, arr


def utc(x):
    return UTCDateTime(str(x))

