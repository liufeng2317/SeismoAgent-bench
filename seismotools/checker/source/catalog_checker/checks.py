"""Reference-free checks of a catalog against its own picks and the station geometry.

Every check measures one property, compares it with a case-agnostic expected
range and, when it falls outside, states the symptom: what was measured and
by how much it is out of range. No check names a cause or a repair.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .io import local_km

DEFAULTS: dict[str, Any] = {
    "outside_network_factor": 1.25, "outside_network_share_max": 0.10,
    "isolated_nn_factor": 5.0, "isolated_floor_km": 2.0, "isolated_share_max": 0.10,
    "duplicate_dt_s": 1.5, "duplicate_km": 3.0, "duplicate_share_max": 0.02,
    "min_p_picks": 4, "few_picks_share_max": 0.20,
    "wadati_min_pairs": 4, "wadati_vpvs": [1.4, 2.2], "wadati_min_events": 20, "wadati_offset_max_s": 0.3,
    "wadati_spread_max_s": 0.5,
    "tt_near_quantile": 0.6, "tt_min_picks": 200, "tt_intercept_max_s": 0.3,
    "station_residual_max_s": 0.5, "station_min_picks": 20, "azimuth_amplitude_max_s": 0.25,
    "depth_value_share_max": 0.05, "depth_edge_share_max": 0.05,
    "sp_depth_min_events": 20, "sp_depth_offset_max_km": 1.5,
    "magnitude_median_range": [-1.0, 5.0], "magnitude_very_low": -2.0, "magnitude_very_low_share_max": 0.05,
    "b_value_range": [0.6, 1.6], "b_min_events": 100,
    "detection_amplitude_range": [-2.3, 0.5], "detection_min_events": 50,
    "event_fit_min_picks": 5, "event_outlier_s": 1.0, "event_outlier_pick_share": 0.2, "event_fit_share_max": 0.1,
    "layer_bin_km": 0.1, "layer_neighbour_km": 1.0, "layer_excess_factor": 3.0, "layer_excess_share_max": 0.05,
    "rate_after_largest_n": 3, "rate_after_largest_window_s": 3600.0, "rate_after_largest_min_ratio": 0.5,
}


@dataclass
class Check:
    id: str
    dimension: str
    measured: float | None
    unit: str
    expected: str
    n: int
    flag: bool
    symptom: str | None = None
    details: dict = field(default_factory=dict)
    kind: str = "product"  # product: judged, flags; input: describes the input data, notes; report_only: measured, never judged

    def record(self) -> dict:
        value = None if self.measured is None or not np.isfinite(self.measured) else round(float(self.measured), 4)
        report_only = self.kind == "report_only"
        return {"id": self.id, "dimension": self.dimension, "kind": self.kind, "measured": value, "unit": self.unit,
                "expected": None if report_only else self.expected, "n": int(self.n),
                "flag": bool(self.flag) and self.kind == "product", "out_of_range": None if report_only else bool(self.flag),
                "symptom": None if report_only else self.symptom, "scope": scope(self.id), "details": self.details}


def _skip(id_: str, dimension: str, unit: str, expected: str, n: int, why: str) -> Check:
    return Check(id_, dimension, None, unit, expected, n, False, None, {"not_evaluated": why})


class Data:
    """Events, picks and stations in a local km frame centred on the station network."""

    def __init__(self, events: pd.DataFrame | None, picks: pd.DataFrame, stations: pd.DataFrame,
                 waveforms: pd.DataFrame | None = None):
        if events is None:
            events = pd.DataFrame(columns=["event_id", "time", "latitude", "longitude", "depth_km", "magnitude"])
        self.events = events.reset_index(drop=True)
        self.stations = stations
        self.waveforms = waveforms
        self.all_picks = picks  # every pick, associated or not
        self.lat0 = float(stations.latitude.median())
        self.lon0 = float(stations.longitude.median())
        self.events["x"], self.events["y"] = local_km(events.latitude, events.longitude, self.lat0, self.lon0)
        self.stations["x"], self.stations["y"] = local_km(stations.latitude, stations.longitude, self.lat0, self.lon0)
        events = self.events
        p = picks[picks.event_id != ""].merge(events[["event_id", "time", "x", "y", "depth_km"]], on="event_id",
                                              suffixes=("", "_origin"))
        p = p.merge(stations[["station_id", "x", "y", "elevation_m"]], on="station_id", suffixes=("", "_sta"))
        p["epi_km"] = np.hypot(p.x - p.x_sta, p.y - p.y_sta)
        p["dz_km"] = p.depth_km + p.elevation_m / 1000.0  # source depth below the station
        p["hyp_km"] = np.hypot(p.epi_km, p.dz_km)
        p["tt"] = p.time - p.time_origin
        self.picks = p
        self.unmatched_stations = sorted(set(picks.station_id) - set(stations.station_id))


# ------------------------------------------------------------------ event reality

def outside_network(d: Data, c: dict) -> Check:
    e = d.events.dropna(subset=["x", "y"])
    expected = f"share ≤ {c['outside_network_share_max']:.0%} beyond {c['outside_network_factor']}× the network radius"
    if not len(e) or len(d.stations) < 3:
        return _skip("events_outside_network", "reality", "share", expected, len(e), "too few events or stations")
    cx, cy = d.stations.x.mean(), d.stations.y.mean()
    radius = float(np.hypot(d.stations.x - cx, d.stations.y - cy).max())
    share = float((np.hypot(e.x - cx, e.y - cy) > c["outside_network_factor"] * radius).mean())
    flag = share > c["outside_network_share_max"]
    return Check("events_outside_network", "reality", share, "share", expected, len(e), flag,
                 f"{share:.1%} of located events lie farther than {c['outside_network_factor']}× the network radius ({radius:.0f} km) from the network centre." if flag else None,
                 {"network_radius_km": round(radius, 2)})


def isolated_events(d: Data, c: dict) -> Check:
    e = d.events.dropna(subset=["x", "y"])
    expected = f"share ≤ {c['isolated_share_max']:.0%} with no neighbour within max({c['isolated_floor_km']} km, {c['isolated_nn_factor']}× the median neighbour distance)"
    if len(e) < 20:
        return _skip("isolated_events", "reality", "share", expected, len(e), "fewer than 20 located events")
    nn = cKDTree(np.c_[e.x, e.y]).query(np.c_[e.x, e.y], k=2)[0][:, 1]
    limit = max(c["isolated_floor_km"], c["isolated_nn_factor"] * float(np.median(nn)))
    share = float((nn > limit).mean())
    flag = share > c["isolated_share_max"]
    return Check("isolated_events", "reality", share, "share", expected, len(e), flag,
                 f"{share:.1%} of located events have no other event within {limit:.1f} km." if flag else None,
                 {"median_neighbour_km": round(float(np.median(nn)), 3), "limit_km": round(limit, 3)})


def duplicate_events(d: Data, c: dict) -> Check:
    located = d.events.dropna(subset=["x", "y"])
    time_only = len(located) < 0.5 * len(d.events)
    e = (d.events.assign(x=0.0, y=0.0) if time_only else located).sort_values("time")
    expected = f"share ≤ {c['duplicate_share_max']:.0%} within {c['duplicate_dt_s']} s and {c['duplicate_km']} km of another event"
    if len(e) < 2:
        return _skip("duplicate_events", "reality", "share", expected, len(e), "fewer than 2 events")
    t, x, y = e.time.to_numpy(), e.x.to_numpy(), e.y.to_numpy()
    dup = np.zeros(len(e), dtype=bool)
    hi = np.searchsorted(t, t + c["duplicate_dt_s"], side="right")
    for i in range(len(e)):
        for j in range(i + 1, hi[i]):
            if np.hypot(x[i] - x[j], y[i] - y[j]) <= c["duplicate_km"]:
                dup[i] = dup[j] = True
    share = float(dup.mean())
    flag = share > c["duplicate_share_max"]
    where = "" if time_only else f" and {c['duplicate_km']} km"
    return Check("duplicate_events", "reality", share, "share", expected, len(e), flag,
                 f"{share:.1%} of events have another event within {c['duplicate_dt_s']} s{where}." if flag else None,
                 {"time_only": time_only, **_pick_overlap(d, c)})


def _pick_overlap(d: Data, c: dict) -> dict:
    from .diagnostics import duplicate_pick_overlap
    return duplicate_pick_overlap(d, c)


def few_picks(d: Data, c: dict) -> Check:
    n_p = d.picks[d.picks.phase == "P"].groupby("event_id").size().reindex(d.events.event_id, fill_value=0)
    expected = (f"share ≤ {c['few_picks_share_max']:.0%} of events with fewer than {c['min_p_picks']} P picks "
                "(a measure of how well events are constrained, not of whether they are located correctly)")
    if not len(n_p):
        return _skip("events_with_few_picks", "reality", "share", expected, 0, "no events")
    share = float((n_p < c["min_p_picks"]).mean())
    flag = share > c["few_picks_share_max"]
    return Check("events_with_few_picks", "reality", share, "share", expected, len(n_p), flag,
                 f"{share:.1%} of events have fewer than {c['min_p_picks']} associated P picks at known stations." if flag else None,
                 {"median_p_picks": float(np.median(n_p))})


# ------------------------------------------------------------------ time

def _wadati(d: Data, c: dict) -> pd.DataFrame:
    p = d.picks
    pp = p[p.phase == "P"].groupby(["event_id", "station_id"]).time.min()
    ss = p[p.phase == "S"].groupby(["event_id", "station_id"]).time.min()
    pairs = pd.concat({"tp": pp, "ts": ss}, axis=1).dropna().reset_index()
    pairs = pairs.merge(d.events[["event_id", "time"]], on="event_id")
    rows = []
    lo, hi = c["wadati_vpvs"]
    for event_id, g in pairs.groupby("event_id"):
        if len(g) < c["wadati_min_pairs"]:
            continue
        x = (g.tp - g.time).to_numpy()
        yv = (g.ts - g.tp).to_numpy()
        if np.ptp(x) <= 0:
            continue
        a, b = np.polyfit(x, yv, 1)
        if not lo - 1 <= a <= hi - 1:
            continue
        rows.append({"event_id": event_id, "vpvs": 1 + a, "offset_s": -b / a, "pairs": len(g)})
    return pd.DataFrame(rows, columns=["event_id", "vpvs", "offset_s", "pairs"])


def wadati_origin(d: Data, c: dict) -> tuple[Check, Check, pd.DataFrame]:
    w = _wadati(d, c)
    exp1 = f"|median| ≤ {c['wadati_offset_max_s']} s over ≥ {c['wadati_min_events']} events"
    exp2 = f"MAD ≤ {c['wadati_spread_max_s']} s"
    if len(w) < c["wadati_min_events"]:
        why = f"{len(w)} events with ≥ {c['wadati_min_pairs']} P–S pairs and a plausible Vp/Vs"
        return (_skip("wadati_origin_offset", "time", "s", exp1, len(w), why),
                _skip("wadati_origin_spread", "time", "s", exp2, len(w), why), w)
    med = float(np.median(w.offset_s))
    mad = float(np.median(np.abs(w.offset_s - med)))
    vpvs = round(float(np.median(w.vpvs)), 3)
    f1 = abs(med) > c["wadati_offset_max_s"]
    f2 = mad > c["wadati_spread_max_s"]
    when = "after" if med > 0 else "before"
    return (Check("wadati_origin_offset", "time", med, "s", exp1, len(w), f1,
                  f"Origin times from Wadati fits of the catalog's own P and S picks fall {abs(med):.2f} s {when} the catalog origin times (median of {len(w):,} events)." if f1 else None,
                  {"median_vpvs": vpvs}),
            Check("wadati_origin_spread", "time", mad, "s", exp2, len(w), f2,
                  f"Event-to-event spread (MAD) of the Wadati origin-time difference is {mad:.2f} s." if f2 else None), w)


def travel_time_fit(d: Data, c: dict) -> tuple[Check, dict | None]:
    p = d.picks[(d.picks.phase == "P") & np.isfinite(d.picks.hyp_km)]
    expected = f"|intercept| ≤ {c['tt_intercept_max_s']} s for P travel time against hypocentral distance (nearest {c['tt_near_quantile']:.0%} of picks)"
    if len(p) < c["tt_min_picks"]:
        return _skip("travel_time_intercept", "time", "s", expected, len(p), "too few P picks at known stations"), None
    near = p[p.hyp_km <= p.hyp_km.quantile(c["tt_near_quantile"])]
    bins = np.quantile(near.hyp_km, np.linspace(0, 1, 21))
    idx = np.clip(np.digitize(near.hyp_km, bins[1:-1]), 0, 19)
    med = near.groupby(idx).agg(d=("hyp_km", "median"), t=("tt", "median"), n=("tt", "size"))
    slope, intercept = np.polyfit(med.d, med.t, 1, w=np.sqrt(med.n))
    flag = abs(intercept) > c["tt_intercept_max_s"]
    fit = {"slowness_s_per_km": slope, "intercept_s": intercept}
    return (Check("travel_time_intercept", "time", float(intercept), "s", expected, len(near), flag,
                  f"P travel times against hypocentral distance extrapolate to {intercept:+.2f} s at zero distance (apparent velocity {1 / slope:.2f} km/s)." if flag and slope > 0 else
                  (f"P travel times against hypocentral distance extrapolate to {intercept:+.2f} s at zero distance." if flag else None),
                  {"apparent_velocity_km_s": round(1 / slope, 3) if slope > 0 else None}), fit)


def rate_after_largest(d: Data, c: dict) -> Check:
    e = d.events.dropna(subset=["magnitude"])
    expected = f"event rate in the hour after each of the {c['rate_after_largest_n']} largest events ≥ {c['rate_after_largest_min_ratio']}× the median hourly rate"
    t = d.events.time.to_numpy()
    if len(e) < 50 or np.ptp(t) < 86400:
        return _skip("rate_after_largest", "time", "ratio", expected, len(e), "fewer than 50 events with magnitude or less than a day")
    hours = np.floor((t - t.min()) / 3600)
    median_rate = float(np.median(np.bincount(hours.astype(int))))
    ratios = []
    for _, ev in e.nlargest(c["rate_after_largest_n"], "magnitude").iterrows():
        n = int(((t > ev.time) & (t <= ev.time + c["rate_after_largest_window_s"])).sum())
        ratios.append(n / median_rate if median_rate > 0 else np.nan)
    worst = float(np.nanmin(ratios))
    flag = worst < c["rate_after_largest_min_ratio"]
    return Check("rate_after_largest", "time", worst, "ratio", expected, len(ratios), flag,
                 f"In the hour after one of the largest events the catalog has {worst:.2f}× its median hourly event count." if flag else None,
                 {"median_hourly_events": median_rate, "ratios": [round(r, 3) for r in ratios]})


# ------------------------------------------------------------------ space

def depth_pileup(d: Data, c: dict) -> list[Check]:
    z = d.events.depth_km.dropna().to_numpy()
    exp1 = f"share ≤ {c['depth_value_share_max']:.0%} at any single depth value (0.01 km)"
    exp2 = f"share ≤ {c['depth_edge_share_max']:.0%} at the shallowest or deepest depth value"
    if len(z) < 20:
        return [_skip("depth_single_value", "space", "share", exp1, len(z), "fewer than 20 depths"),
                _skip("depth_at_edges", "space", "share", exp2, len(z), "fewer than 20 depths")]
    values, counts = np.unique(np.round(z, 2), return_counts=True)
    top = float(counts.max() / len(z))
    at = float(values[counts.argmax()])
    edge = float(max((np.round(z, 2) == values[0]).mean(), (np.round(z, 2) == values[-1]).mean()))
    f1, f2 = top > c["depth_value_share_max"], edge > c["depth_edge_share_max"]
    return [Check("depth_single_value", "space", top, "share", exp1, len(z), f1,
                  f"{top:.1%} of events sit at the same depth, {at:.2f} km." if f1 else None, {"depth_km": at}),
            Check("depth_at_edges", "space", edge, "share", exp2, len(z), f2,
                  f"{edge:.1%} of events sit at the shallowest ({values[0]:.2f} km) or deepest ({values[-1]:.2f} km) depth of the catalog." if f2 else None)]


def sp_depth(d: Data, c: dict, w: pd.DataFrame) -> Check:
    """Depth from S−P times, independent of the catalog's origin times and of any velocity model.

    S−P grows linearly with hypocentral distance, D = K·(S−P). K is fitted on
    stations far from each event (D ≈ epicentral distance); near stations then
    give the depth that their S−P implies, compared with the catalog depth.
    """
    expected = f"|median S−P depth − catalog depth| ≤ {c['sp_depth_offset_max_km']} km over ≥ {c['sp_depth_min_events']} events"
    p = d.picks
    pp = p[p.phase == "P"].groupby(["event_id", "station_id"]).agg(tp=("time", "min"), epi=("epi_km", "first"),
                                                                    dz=("dz_km", "first"))
    ss = p[p.phase == "S"].groupby(["event_id", "station_id"]).time.min().rename("ts")
    pairs = pp.join(ss, how="inner").reset_index()
    pairs = pairs[np.isfinite(pairs.epi) & np.isfinite(pairs.dz) & (pairs.dz > 0)]
    pairs["sp"] = pairs.ts - pairs.tp
    pairs = pairs[pairs.sp > 0]
    far = pairs[pairs.epi > 3 * pairs.dz]
    if len(far) < 50:
        return _skip("sp_depth_offset", "space", "km", expected, len(far), "too few distant P–S pairs to scale S−P")
    k = float(np.median(far.epi / far.sp))
    near = pairs[pairs.epi < pairs.dz].copy()
    hyp = k * near.sp
    near = near[hyp > near.epi]
    near["z_sp"] = np.sqrt((k * near.sp) ** 2 - near.epi ** 2)
    per_event = near.groupby("event_id").apply(lambda g: float(np.median(g.z_sp - g.dz)))
    if len(per_event) < c["sp_depth_min_events"]:
        return _skip("sp_depth_offset", "space", "km", expected, len(per_event), "too few events with a station closer than their depth")
    med = float(np.median(per_event))
    flag = abs(med) > c["sp_depth_offset_max_km"]
    word = "deeper" if med > 0 else "shallower"
    # Below the limit the sign of the difference is not reliable (velocity structure alone moves it by
    # about a kilometre either way), so only its size is reported.
    return Check("sp_depth_offset", "space", med if flag else abs(med), "km", expected, len(per_event), flag,
                 f"Depths implied by S−P times at stations closer than the source depth are {abs(med):.2f} km {word} than the catalog depths (median of {len(per_event):,} events)." if flag else None,
                 {"sp_scale_km_per_s": round(k, 3),
                  **({} if flag else {"direction": "not reported below the limit: velocity structure alone can move the value by about a kilometre either way"})})


def station_residuals(d: Data, c: dict, fit: dict | None) -> list[Check]:
    exp1 = f"no station with |median P residual| > {c['station_residual_max_s']} s about the travel-time fit"
    exp2 = f"azimuthal amplitude of station residuals ≤ {c['azimuth_amplitude_max_s']} s"
    if fit is None:
        return [_skip("station_residual_outliers", "space", "stations", exp1, 0, "no travel-time fit"),
                _skip("station_residual_azimuth", "space", "s", exp2, 0, "no travel-time fit")]
    p = d.picks[(d.picks.phase == "P") & np.isfinite(d.picks.hyp_km)].copy()
    p = p[p.hyp_km <= p.hyp_km.quantile(c["tt_near_quantile"])]
    p["res"] = p.tt - (fit["intercept_s"] + fit["slowness_s_per_km"] * p.hyp_km)
    st = p.groupby("station_id").agg(res=("res", "median"), n=("res", "size"), x=("x_sta", "first"), y=("y_sta", "first"))
    st = st[st.n >= c["station_min_picks"]]
    if len(st) < 4:
        return [_skip("station_residual_outliers", "space", "stations", exp1, len(st), "fewer than 4 stations with enough picks"),
                _skip("station_residual_azimuth", "space", "s", exp2, len(st), "fewer than 4 stations with enough picks")]
    bad = st[np.abs(st.res) > c["station_residual_max_s"]]
    ex, ey = float(d.events.x.median()), float(d.events.y.median())
    az = np.arctan2(st.x - ex, st.y - ey)
    design = np.c_[np.ones(len(st)), np.cos(az), np.sin(az)]
    coef, *_ = np.linalg.lstsq(design, st.res.to_numpy(), rcond=None)
    amp = float(np.hypot(coef[1], coef[2]))
    toward = float(np.degrees(np.arctan2(coef[2], coef[1])) % 360)
    f1, f2 = len(bad) > 0, amp > c["azimuth_amplitude_max_s"]
    return [Check("station_residual_outliers", "space", float(len(bad)), "stations", exp1, len(st), f1,
                  f"{len(bad)} of {len(st)} stations have median P residuals beyond ±{c['station_residual_max_s']} s ({', '.join(f'{s} {r:+.2f} s' for s, r in bad.res.items())})." if f1 else None),
            Check("station_residual_azimuth", "space", amp, "s", exp2, len(st), f2,
                  f"Station P residuals vary with azimuth from the event cluster with an amplitude of {amp:.2f} s (largest towards {toward:.0f}° from north)." if f2 else None,
                  {"azimuth_deg_of_largest_residual": round(toward, 1),
                   "per_station": {s: {"median_residual_s": round(float(r.res), 3), "n": int(r.n), "x_km": round(float(r.x), 2), "y_km": round(float(r.y), 2)}
                                   for s, r in st.iterrows()}})]


def azimuthal_gap(d: Data, c: dict) -> Check:
    """Largest azimuthal gap of each located event's picked stations (reported)."""
    expected = "reported: median gap and share of events with a gap > 180°"
    p = d.picks.dropna(subset=["x"])
    if p.empty:
        return _skip("azimuthal_gap", "space", "deg", expected, 0, "no located events with picks at known stations")
    az = np.degrees(np.arctan2(p.x_sta - p.x, p.y_sta - p.y)) % 360
    gaps = []
    for _, a in pd.Series(az.to_numpy(), index=p.event_id.to_numpy()).groupby(level=0):
        s = np.unique(np.round(a.to_numpy(), 3))
        gaps.append(360.0 if len(s) < 2 else float(np.max(np.diff(np.r_[s, s[0] + 360]))))
    g = np.array(gaps)
    return Check("azimuthal_gap", "space", float(np.median(g)), "deg", expected, len(g), False, None,
                 {"share_gap_over_180": round(float((g > 180).mean()), 3), "quantiles_deg": {q: round(float(np.quantile(g, q)), 1) for q in (0.1, 0.5, 0.9)}})


# ------------------------------------------------------------------ strength

def magnitude_range(d: Data, c: dict) -> Check:
    m = d.events.magnitude.dropna().to_numpy()
    lo, hi = c["magnitude_median_range"]
    expected = f"median magnitude in [{lo}, {hi}] and ≤ {c['magnitude_very_low_share_max']:.0%} below {c['magnitude_very_low']}"
    if not len(m):
        return _skip("magnitude_range", "strength", "magnitude", expected, 0, "no magnitudes")
    med = float(np.median(m))
    low = float((m < c["magnitude_very_low"]).mean())
    flag = not lo <= med <= hi or low > c["magnitude_very_low_share_max"]
    return Check("magnitude_range", "strength", med, "magnitude", expected, len(m), flag,
                 f"Median magnitude is {med:.2f} (range {m.min():.2f} to {m.max():.2f}); {low:.1%} of events are below {c['magnitude_very_low']}." if flag else None,
                 {"min": round(float(m.min()), 2), "max": round(float(m.max()), 2), "share_below": round(low, 4)})


def b_value(d: Data, c: dict) -> Check:
    m = d.events.magnitude.dropna().to_numpy()
    lo, hi = c["b_value_range"]
    expected = f"b in [{lo}, {hi}] above the maximum-curvature completeness + 0.2"
    if len(m) < c["b_min_events"]:
        return _skip("b_value", "strength", "b", expected, len(m), f"fewer than {c['b_min_events']} magnitudes")
    bins = np.round(m, 1)
    values, counts = np.unique(bins, return_counts=True)
    mc = float(values[counts.argmax()]) + 0.2
    above = m[m >= mc - 0.05]
    if len(above) < 50 or above.mean() - (mc - 0.05) <= 0:
        return _skip("b_value", "strength", "b", expected, len(above), "fewer than 50 events above completeness")
    b = float(np.log10(np.e) / (above.mean() - (mc - 0.05)))
    flag = not lo <= b <= hi
    return Check("b_value", "strength", b, "b", expected, len(above), flag,
                 f"The Gutenberg–Richter b-value above Mc {mc:.1f} is {b:.2f}." if flag else None, {"mc": round(mc, 2)})


def event_travel_time_fit(d: Data, c: dict) -> Check:
    """Picks that do not fit their event's travel-time curve.

    The catalog's own median travel time against hypocentral distance (per phase, in distance bins of
    equal pick count) is the reference curve; each event's median residual is removed (origin-time
    error), and a pick is an outlier when its remaining residual exceeds ``event_outlier_s``. Picks
    from another event or with the wrong phase label are outliers; structure and depth errors move
    whole events and are mostly removed with the event's median.
    """
    expected = (f"share ≤ {c['event_fit_share_max']:.0%} of events with more than {c['event_outlier_pick_share']:.0%} of their picks "
                f"off the catalog's median travel-time curve by > {c['event_outlier_s']} s")
    p = d.picks[np.isfinite(d.picks.hyp_km) & np.isfinite(d.picks.tt)].copy()
    if len(p) < 200:
        return _skip("event_travel_time_fit", "reality", "share", expected, len(p), "fewer than 200 located picks")
    p["res"] = np.nan
    for ph, g in p.groupby("phase"):
        if len(g) < 50:
            continue
        edges = np.unique(np.quantile(g.hyp_km, np.linspace(0, 1, min(40, len(g) // 25) + 1)))
        mid = 0.5 * (edges[1:] + edges[:-1])
        med = [np.median(g.tt[(g.hyp_km >= lo) & (g.hyp_km <= hi)]) for lo, hi in zip(edges[:-1], edges[1:])]
        p.loc[g.index, "res"] = g.tt - np.interp(g.hyp_km, mid, med)
    p = p.dropna(subset=["res"])
    p["res"] -= p.groupby("event_id").res.transform("median")
    n = p.groupby("event_id").res.size()
    out = (p.res.abs() > c["event_outlier_s"]).groupby(p.event_id).mean()[n >= c["event_fit_min_picks"]]
    if len(out) < 20:
        return _skip("event_travel_time_fit", "reality", "share", expected, len(out), f"{len(out)} located events with ≥ {c['event_fit_min_picks']} picks")
    share = float((out > c["event_outlier_pick_share"]).mean())
    flag = False  # reported only (see REPORT_ONLY)
    return Check("event_travel_time_fit", "reality", share, "share", expected, len(out), flag,
                 (f"For {share:.0%} of {len(out):,} events more than {c['event_outlier_pick_share']:.0%} of the picks lie more than "
                  f"{c['event_outlier_s']} s off the catalog's travel-time curve.") if flag else None,
                 {"outlier_pick_share_overall": round(float((p.res.abs() > c["event_outlier_s"]).mean()), 4),
                  "worst_events": out.sort_values(ascending=False).head(10).round(3).to_dict()})


def depth_layers(d: Data, c: dict) -> Check:
    """Thin depth slices inside the depth range holding far more events than the depths around them."""
    expected = (f"share ≤ {c['layer_excess_share_max']:.0%} of events in excess of the neighbouring depths, counted in "
                f"{c['layer_bin_km']} km slices holding ≥ 10 events, > {c['layer_excess_factor']:g}× and > 4 Poisson σ above the median of slices within ±{c['layer_neighbour_km']} km. "
                "Slices also form at the interfaces of a correct layered velocity model, so the share alone does not rank two models")
    z = d.events.depth_km.dropna().to_numpy()
    if len(z) < 50:
        return _skip("depth_layers", "space", "share", expected, len(z), "fewer than 50 depths")
    w = c["layer_bin_km"]
    edges = np.arange(np.floor(z.min() / w) * w, z.max() + 2 * w, w)
    counts, _ = np.histogram(z, edges)
    k = int(round(c["layer_neighbour_km"] / w))
    excess, layers = 0.0, []
    for i, n in enumerate(counts):
        nb = np.r_[counts[max(i - k, 0):max(i - 1, 0)], counts[i + 2:i + k + 1]]
        if len(nb) < k // 2 or edges[i] < z.min() + 0.2 or edges[i + 1] > z.max() - 0.2:
            continue  # pile-ups at the shallowest and deepest depths are depth_at_edges
        ref = max(float(np.median(nb)), 1.0)
        # far above the neighbours and beyond Poisson scatter of the neighbour level
        if n >= 10 and n > c["layer_excess_factor"] * ref and n > ref + 4.0 * np.sqrt(ref) and n - ref >= 0.005 * len(z):
            excess += n - ref
            layers.append((round(float(edges[i]), 2), int(n), round(ref, 1)))
    share = excess / len(z)
    flag = share > c["layer_excess_share_max"]
    top = sorted(layers, key=lambda x: -(x[1] - x[2]))[:6]
    return Check("depth_layers", "space", share, "share", expected, len(z), flag,
                 (f"{share:.1%} of events are excess events in thin depth slices "
                  f"({', '.join(f'{a:.1f}–{a + w:.1f} km: {n} vs ~{r:g}' for a, n, r in top)}).") if flag else None,
                 {"slices": [{"top_km": a, "events": n, "neighbour_median": r} for a, n, r in layers]})


def magnitude_detection(d: Data, c: dict) -> Check:
    """Wood-Anderson amplitude implied at the farthest detecting station, from the catalog magnitude.

    log10 A = M − 1.11 log10(R/100) − 0.00189 (R − 100) − 3 (Hutton & Boore, 1987; A in mm, R hypocentral km).
    Small events are detected out to where their amplitude reaches the noise, so for the smaller half of
    the catalog this amplitude estimates the detection level, which a consistent magnitude scale keeps
    at noise-like values. A magnitude offset moves it by the same amount.
    """
    lo, hi = c["detection_amplitude_range"]
    expected = f"median log10 amplitude (mm) at the farthest detecting station, smaller half of events, in [{lo}, {hi}]"
    p = d.picks[np.isfinite(d.picks.hyp_km)]
    far = p.groupby("event_id").agg(r=("hyp_km", "max"), n=("hyp_km", "size"))
    e = d.events.dropna(subset=["magnitude"]).merge(far[far.n >= 3], left_on="event_id", right_index=True)
    if len(e) < c["detection_min_events"]:
        return _skip("magnitude_detection", "strength", "log10 mm", expected, len(e), f"{len(e)} events with a magnitude and ≥ 3 located picks")
    r = e.r.clip(lower=1.0)
    loga = e.magnitude - 1.11 * np.log10(r / 100.0) - 0.00189 * (r - 100.0) - 3.0
    small = loga[e.magnitude <= e.magnitude.median()]
    med = float(small.median())
    flag = not lo <= med <= hi
    return Check("magnitude_detection", "strength", med, "log10 mm", expected, len(small), flag,
                 (f"For the smaller half of events the magnitudes imply a Wood-Anderson amplitude of 10^{med:.1f} mm at the farthest "
                  f"detecting station ({'below' if med < lo else 'above'} the expected range).") if flag else None,
                 {"median_farthest_km_small_half": round(float(e.r[e.magnitude <= e.magnitude.median()].median()), 1),
                  "median_magnitude_small_half": round(float(e.magnitude[e.magnitude <= e.magnitude.median()].median()), 2)})


# Checks that measure correctly but did not separate correct from faulty catalogs in validation
# (docs/research/04_Checker_Design.md §10): reported, never flagged. The reasons are shown to the Agent,
# so they stay general and name no case.
REPORT_ONLY = {
    "events_outside_network": "real seismicity can lie outside the network, so the share alone does not show an error",
    "wadati_origin_offset": "velocity structure alone can offset this value by close to a second in correct catalogs",
    "travel_time_intercept": "velocity structure alone can give intercepts near a second in correct catalogs",
    "station_residual_outliers": "3-D structure alone can give correct catalogs large station residuals",
    "station_residual_azimuth": "3-D structure alone can give correct catalogs azimuth-dependent residuals",
    "model_ensemble_depth": "generic velocity models differ from each other by several km in depth, more than most catalog errors",
    "model_ensemble_time": "generic velocity models differ from each other by up to a second or more in origin time",
    "pick_snr": "correct catalogs often keep many weak picks",
    "event_travel_time_fit": "correct catalogs, especially on regional networks, show similar shares",
    "azimuthal_gap": "describes the station geometry around each event; no expected range",
    "b_value": "early in an aftershock sequence the catalog is incomplete and maximum-curvature completeness underestimates b in correct catalogs",
    "rate_after_largest": "the event rate after large events varies widely in correct catalogs",
    "depth_constraint": "describes how well depths can be constrained by the picks and the station geometry; not an error",
    "pile_against_setup": "locates the most common depth relative to the declared location set-up; evidence for attributing a pile-up",
    "station_delays": "station residuals also carry 3-D structure; the P/S ratio of a delay helps to tell a clock from a path",
    "station_time_steps": "residuals also change when seismicity moves; a step equal in P and S points to a clock or instrument change",
    "wadati_events": "event-by-event Vp/Vs scatters in correct catalogs; outlier S picks point to mispicks or wrong phase labels",
    "day_night_ratio": "real seismicity has no daily cycle, but detection and blasting do; the ratio alone does not show an error",
    "b_positive": "an estimate to read next to the standard b-value: a large difference points to incompleteness",
}
# Checks that describe the input data rather than the Agent's products: reported as input notes when out
# of range; they need no disposition, since the Agent cannot change its input.
INPUT_CHECKS = {"stations_with_data", "daily_station_count", "network_geometry", "channel_sample_rates", "data_gaps"}


# Checks of the distribution of the whole catalog. Each of the other checks measures a property of single
# picks, events or stations (a median or a share over them), which a pilot batch estimates as well as the
# full run; these depend on how many events there are and how they are spread, so a pilot batch does
# not show them. In replays of pilot batches against their full runs the item checks measured close to
# the full-run values (verdicts differed only for values near a limit); these changed verdict often.
POPULATION = {
    "depth_single_value": "a pile-up of events at one depth often forms only among the weaker events of the full catalog",
    "depth_at_edges": "a pile-up at the shallowest or deepest depth often forms only among the weaker events of the full catalog",
    "depth_layers": "thin depth slices need the event density of the full catalog to stand out",
    "isolated_events": "the distance to the nearest neighbour depends on how many events there are",
    "duplicate_events": "pairs close in time and space depend on how many events there are",
    "association_busy_hours": "busy hours are a property of the full time span",
    "b_value": "the magnitude distribution needs the full catalog",
    "rate_after_largest": "the event rate after large events needs the full time span",
    "relocation_thinning": "local thickness is measured among neighbours, which depend on how many events there are",
    "station_time_steps": "a step needs days of data on both sides",
    "day_night_ratio": "the daily cycle needs many days of events",
    "b_positive": "the magnitude distribution needs the full catalog",
}


def scope(check_id: str) -> str:
    """'population' for checks of the whole catalog's distribution, 'item' for checks a pilot batch estimates."""
    return "population" if check_id in POPULATION else "item"


def apply_report_only(checks: list[Check], pilot: bool = False) -> list[Check]:
    """Set each check's kind: report-only checks never flag, input checks become notes.

    On a pilot batch (``pilot``) the population checks are reported but not judged either."""
    for c in checks:
        if pilot and c.id in POPULATION and c.id not in REPORT_ONLY:
            c.kind = "report_only"
            c.details = {**c.details, "reported_only": "pilot batch: " + POPULATION[c.id] + "; judge it on the full run"}
            c.flag, c.symptom = False, None
        elif c.id in REPORT_ONLY:
            c.kind = "report_only"
            c.details = {**c.details, "reported_only": REPORT_ONLY[c.id]}
            c.flag, c.symptom = False, None
        elif c.id in INPUT_CHECKS:
            c.kind = "input"
    return checks


STAGES = ("data", "picks", "association", "location", "relocation", "magnitude", "all")


def run_checks(d: Data, config: dict | None = None, stage: str = "all") -> tuple[list[Check], dict]:
    """The checks of the picks, association, location and magnitude stages up to ``stage``.

    The data stage, the waveform checks of the picks stage, the model ensemble and the relocation
    stage need extra inputs and are run by the interface.
    """
    from .stages import association_checks, picks_checks
    c = {**DEFAULTS, **(config or {})}
    upto = STAGES.index(stage)
    extras: dict = {"config": c, "stage": stage}
    checks: list[Check] = []
    if upto >= STAGES.index("picks"):
        checks += picks_checks(d, c)
    if upto >= STAGES.index("association"):
        checks += association_checks(d, c) + [duplicate_events(d, c), few_picks(d, c), event_travel_time_fit(d, c)]
    if upto >= STAGES.index("location"):
        checks += [outside_network(d, c), isolated_events(d, c)]
        wad_offset, wad_spread, w = wadati_origin(d, c)
        tt_check, fit = travel_time_fit(d, c)
        checks += [wad_offset, wad_spread, tt_check]
        checks += [azimuthal_gap(d, c)] + depth_pileup(d, c) + [depth_layers(d, c), sp_depth(d, c, w)] + station_residuals(d, c, fit)
        extras.update({"wadati": w, "fit": fit})
        from .diagnostics import (_residuals, day_night, depth_constraint, pile_against_setup, station_delays,
                                  station_time_steps, wadati_events)
        dc, per_event = depth_constraint(d, c)
        res = _residuals(d) if len(d.picks) else pd.DataFrame()
        checks += [dc, station_delays(d, c, res), station_time_steps(d, c, res), wadati_events(d, c), day_night(d, c)]
        pile = pile_against_setup(d, c)
        checks += [pile] if pile is not None else []
        extras["depth_constraint"] = per_event
    if upto >= STAGES.index("magnitude"):
        from .diagnostics import b_positive
        checks += [magnitude_range(d, c), b_value(d, c), b_positive(d, c), magnitude_detection(d, c), rate_after_largest(d, c)]
    return checks, extras
