#!/usr/bin/env python3
"""Reference local magnitude (ML) following the IASPEI standard, with every unit stated.

Standard (IASPEI 2011/2013; NMSOP-2 IS 3.3 eq. 1, DS 3.1 eq. 2):

    ML = log10(A) + 1.11 log10(R) + 0.00189 R - 2.09

    A  maximum trace amplitude in **nanometres**, measured on a horizontal component whose response
       replicates a Wood-Anderson seismograph **with static magnification 1** (IS 3.3 Table 1:
       zeros 0, 0; poles -5.49779 +/- 5.60886i rad/s; normalised to 1 at 4 Hz with A0 = 1.0028).
       The amplitude is one half of the largest peak-to-adjacent-trough deflection ("half
       peak-to-peak"); each horizontal component is a separate datum (no vector sum).
    R  hypocentral distance in km (typically < 1000 km).

The same relation written for amplitudes read on a classical Wood-Anderson record (static
magnification 2080, trace amplitude in **millimetres**) is Hutton & Boore (1987), expanded:

    ML = log10(A_mm) + 1.11 log10(R/100) + 0.00189 (R - 100) + 3.0
       = log10(A_mm) + 1.11 log10(R) + 0.00189 R + 0.591

The two forms agree because A_mm = 2080 * A_nm * 1e-6, i.e. log10(A_mm) = log10(A_nm) - 2.682.
Mixing them (an amplitude in mm with the -2.09 constant, or nm with +0.591) shifts every
magnitude by 2.68 units. Pre-1990 calibrations assumed magnification 2800 (log10(2800/2080) =
0.129); see DS 3.1 Comment 1.1.

Regional calibration functions (-logA0) from standard compilations are in ``calibrations.json``; see
``minus_log_a0`` and README §5.

Use ``python ml_reference.py selftest`` to check the formulas and the instrument response, and
``python ml_reference.py recompute ...`` to recompute ML for a sample of catalog events from the
waveforms and compare with the catalog's magnitudes.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

# IASPEI standard Wood-Anderson displacement response (IS 3.3 Table 1), static magnification 1.
WA_IASPEI = {"zeros": [0j, 0j], "poles": [-5.49779 - 5.60886j, -5.49779 + 5.60886j], "gain": 1.0028, "sensitivity": 1.0}
WA_MAGNIFICATION = 2080.0  # experimentally determined static magnification (Uhrhammer & Collins, 1990)
NM_TO_MM_ON_WA = WA_MAGNIFICATION * 1e-6  # A_mm (classical WA record) = A_nm * 2080 * 1e-6


def ml_iaspei(amplitude_nm, hypocentral_km):
    """IASPEI standard ML from the WA amplitude in nm (static magnification 1) and R in km."""
    a, r = np.asarray(amplitude_nm, float), np.asarray(hypocentral_km, float)
    return np.log10(a) + 1.11 * np.log10(r) + 0.00189 * r - 2.09


def ml_hutton_boore_mm(amplitude_mm, hypocentral_km):
    """Hutton & Boore (1987) ML from a classical WA record amplitude in mm (magnification 2080) and R in km."""
    a, r = np.asarray(amplitude_mm, float), np.asarray(hypocentral_km, float)
    return np.log10(a) + 1.11 * np.log10(r / 100.0) + 0.00189 * (r - 100.0) + 3.0


CALIBRATIONS = Path(__file__).resolve().parent / "calibrations.json"


def calibrations() -> dict:
    """Library of -logA0 calibration functions (calibrations.json), keyed by entry id."""
    return {e["id"]: e for e in json.loads(CALIBRATIONS.read_text(encoding="utf-8"))["entries"]}


def minus_log_a0(entry_id: str, R=None, D=None, T=None, ML=None, component: str | None = None) -> float:
    """-logA0 of a library entry. R hypocentral km, D epicentral km, T period s (if the entry uses it),
    ML a first estimate (magnitude-dependent branches), component "horizontal"/"vertical" where an entry has both.
    The amplitude to add, log10(A), must be in the unit and on the instrument the entry states."""
    lib = calibrations()
    e = lib[entry_id]
    if "table" in e or "table_ref" in e:
        pts = np.array((e.get("table") or lib[e["table_ref"]]["table"])["points"], float)
        return float(np.interp(D if D is not None else R, pts[:, 0], pts[:, 1]))
    env = {"log": math.log10, "R": R, "D": D if D is not None else R, "T": T, "ML": ML}
    exprs = e["expressions"]
    if component:
        exprs = [x for x in exprs if x.get("component", component) == component] or exprs
    if len(exprs) > 1 and "ML" in exprs[0]["valid"]:
        exprs = [x for x in exprs if eval(x["valid"], {}, env)]
    elif len(exprs) > 1 and any(v in exprs[0]["valid"] for v in ("R", "D")):
        inside = [x for x in exprs if eval(x["valid"], {}, env)]
        exprs = inside or exprs
    return float(eval(exprs[0]["expr"], {}, env))


def wa_response(freq_hz):
    """Complex WA displacement response (static magnification 1) at the given frequencies."""
    s = 2j * np.pi * np.asarray(freq_hz, float)
    h = WA_IASPEI["gain"] * np.prod([s - z for z in WA_IASPEI["zeros"]], axis=0) / np.prod([s - p for p in WA_IASPEI["poles"]], axis=0)
    return h


def half_peak_to_peak(x: np.ndarray) -> float:
    """Largest half deflection between a peak and the adjacent trough (one zero crossing apart)."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return float("nan")
    d = np.diff(x)
    turn = np.where(np.sign(d[1:]) != np.sign(d[:-1]))[0] + 1  # local extrema
    ext = np.r_[0, turn, len(x) - 1]
    vals = x[ext]
    if len(vals) < 2:
        return float(np.max(np.abs(x)))
    return float(np.max(np.abs(np.diff(vals))) / 2.0)


def wa_trace_nm(trace, inventory, pre_filt=None):
    """Ground displacement filtered by the IASPEI WA response (static magnification 1), in nm.

    counts --(remove instrument response)--> displacement in m --(WA, magnification 1)--> m --> nm
    """
    tr = trace.copy()
    tr.detrend("demean")
    tr.detrend("linear")
    fs = tr.stats.sampling_rate
    pre = pre_filt or (0.05, 0.1, 0.4 * fs, 0.45 * fs)
    tr.remove_response(inventory=inventory, output="DISP", pre_filt=pre, water_level=60)  # metres
    tr.simulate(paz_simulate=WA_IASPEI, simulate_sensitivity=False)  # still metres, WA-shaped
    tr.data = tr.data * 1e9  # nanometres
    return tr


# --------------------------------------------------------------------------- self test

def selftest() -> int:
    ok = True

    def check(name, value, target, tol):
        nonlocal ok
        good = abs(value - target) <= tol
        ok &= good
        print(f"{'ok  ' if good else 'FAIL'} {name}: {value:.4f} (expected {target:.4f} ± {tol})")

    # 1 mm on a classical WA record at 100 km is ML 3.0 (Richter's definition); in nm that is 1 / (2080e-6) nm.
    check("Hutton & Boore, 1 mm at 100 km", float(ml_hutton_boore_mm(1.0, 100.0)), 3.0, 1e-9)
    check("IASPEI, same amplitude in nm", float(ml_iaspei(1.0 / NM_TO_MM_ON_WA, 100.0)), 3.0, 0.002)
    check("Hutton & Boore 10 mm at 17 km", float(ml_hutton_boore_mm(10.0, 17.0)), 3.0, 0.03)
    # The classic mistake: the WA record amplitude in mm used with the nm constant
    check("mm with the -2.09 constant (should be 2.68 too low)", float(ml_iaspei(1.0, 100.0)), 3.0 - 2.682, 0.002)
    # WA response: magnification 1 at high frequency, 1 at 4 Hz by normalisation, falls off below ~1.25 Hz
    check("|WA| at 4 Hz", float(abs(wa_response(4.0))), 1.0, 0.005)
    check("|WA| at 20 Hz", float(abs(wa_response(20.0))), 1.0, 0.01)
    check("|WA| at 0.5 Hz", float(abs(wa_response(0.5))), 0.145, 0.02)
    # every library entry meets Richter's definition in its own units (3.0 at 100 km for mm, 0.318 for nm, 2.0 at 17 km for 10 mm at 17 km)
    for eid, e in calibrations().items():
        a = e.get("anchor")
        if a:
            v = minus_log_a0(eid, R=a.get("R"), D=a.get("D"), T=a.get("T", 1.0), ML=3.0)
            check(f"anchor {eid}", v, a["value"], a.get("tolerance", 0.1))
    # half peak-to-peak of a sine of amplitude 3 is 3
    t = np.linspace(0, 2, 2001)
    check("half peak-to-peak of 3 sin", half_peak_to_peak(3 * np.sin(2 * np.pi * 2 * t)), 3.0, 0.01)
    print("PASS" if ok else "FAILED")
    return 0 if ok else 1


# --------------------------------------------------------------------------- recompute

def _seconds(values):
    import pandas as pd
    text = pd.Series(values).astype(str).str.strip().str.replace(r"(\.\d{6})\d+", r"\1", regex=True)
    return ((pd.to_datetime(text, utc=True, format="ISO8601", errors="coerce") - pd.Timestamp(0, tz="UTC")).dt.total_seconds()).to_numpy()


def recompute(args) -> int:
    import pandas as pd
    from obspy import UTCDateTime, read, read_inventory

    cat = pd.read_csv(args.catalog, dtype=str, keep_default_na=False)
    cat = cat[cat.get("status", "") != "rejected"].copy()
    cat["t"] = _seconds(cat.origin_time_utc)
    for col in ("latitude", "longitude", "depth_km", "magnitude"):
        cat[col] = pd.to_numeric(cat[col], errors="coerce")
    picks = pd.read_csv(args.picks, dtype=str, keep_default_na=False)
    picks = picks[(picks.get("status", "") != "rejected") & (picks.event_id != "")].copy()
    picks["t"] = _seconds(picks.time_utc)
    picks["phase"] = picks.phase.str.upper().str[0]
    inv = None
    for f in sorted(Path(args.stations).rglob("*")) if Path(args.stations).is_dir() else [Path(args.stations)]:
        if f.suffix.lower() in (".xml", ".stationxml"):
            inv = read_inventory(str(f)) if inv is None else inv + read_inventory(str(f))
    files = {}
    for f in Path(args.waveforms).rglob("*.mseed"):
        seed = f.name.split("__")[0]
        files.setdefault(".".join(seed.split(".")[:2]), []).append(f)

    counts = picks.groupby("event_id").size()
    ev = cat[cat.event_id.isin(counts.index) & cat.magnitude.notna() & cat.depth_km.notna()].copy()
    ev["n"] = ev.event_id.map(counts)
    ev = ev.sort_values(["n", "t"], ascending=[False, True])
    idx = np.linspace(0, len(ev) - 1, min(args.events, len(ev))).round().astype(int) if len(ev) else []
    ev = ev.iloc[sorted(set(idx))]
    rows = []
    for _, e in ev.iterrows():
        ep = picks[picks.event_id == e.event_id]
        for sta, sp in ep.groupby("station_id"):
            if sta not in files:
                continue
            tp = sp[sp.phase == "P"].t.min()
            ts = sp[sp.phase == "S"].t.min()
            t0 = (tp if np.isfinite(tp) else ts) - 1.0
            tend = (ts if np.isfinite(ts) else tp + 1.7 * (tp - e.t)) + max(3.0, 0.5 * ((ts if np.isfinite(ts) else tp) - e.t)) + 2.0
            try:
                st = inv.select(network=sta.split(".")[0], station=sta.split(".")[1])
                sla, slo = st[0][0].latitude, st[0][0].longitude
                selev = st[0][0].elevation
            except Exception:
                continue
            epi = math.hypot((sla - e.latitude) * 111.195, (slo - e.longitude) * 111.195 * math.cos(math.radians(e.latitude)))
            r = math.hypot(epi, e.depth_km + selev / 1000.0)
            for f in files[sta]:
                ch = f.name.split("__")[0].split(".")[3]
                if ch[-1] not in "NE12":
                    continue
                try:
                    tr = read(str(f), starttime=UTCDateTime(t0 - 30), endtime=UTCDateTime(tend + 30))
                    tr.merge(fill_value=0)
                    if not len(tr):
                        continue
                    w = wa_trace_nm(tr[0], inv)
                    w.trim(UTCDateTime(t0), UTCDateTime(tend))
                    a = half_peak_to_peak(w.data)
                except Exception:
                    continue
                if np.isfinite(a) and a > 0:
                    rows.append({"event_id": e.event_id, "station_id": sta, "channel": ch, "R_km": round(r, 2),
                                 "A_nm": a, "ml_station": float(ml_iaspei(a, r)), "catalog_magnitude": e.magnitude})
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    sta = pd.DataFrame(rows)
    sta.to_csv(out / "station_ml.csv", index=False)
    if sta.empty:
        print("no amplitudes measured")
        return 1
    evm = sta.groupby("event_id").agg(ml_reference=("ml_station", "median"), n_amplitudes=("ml_station", "size"),
                                      catalog_magnitude=("catalog_magnitude", "first")).reset_index()
    evm["catalog_minus_reference"] = evm.catalog_magnitude - evm.ml_reference
    evm.to_csv(out / "event_ml.csv", index=False)
    d = evm.catalog_minus_reference
    summary = {"events": int(len(evm)), "amplitudes": int(len(sta)), "formula": "IASPEI standard ML (A in nm, WA magnification 1)",
               "median_catalog_minus_reference": round(float(d.median()), 3),
               "mad": round(float((d - d.median()).abs().median()), 3),
               "slope_catalog_vs_reference": round(float(np.polyfit(evm.ml_reference, evm.catalog_magnitude, 1)[0]), 3) if len(evm) > 2 else None}
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest", help="check formulas, unit conversion and the WA response")
    r = sub.add_parser("recompute", help="recompute IASPEI ML for a sample of catalog events and compare")
    r.add_argument("--catalog", required=True)
    r.add_argument("--picks", required=True)
    r.add_argument("--stations", required=True, help="StationXML file or directory")
    r.add_argument("--waveforms", required=True, help="folder of NET.STA.LOC.CHA__start__end.mseed files")
    r.add_argument("--events", type=int, default=50, help="events sampled evenly by number of picks")
    r.add_argument("--output-dir", required=True)
    a = p.parse_args(argv)
    return selftest() if a.cmd == "selftest" else recompute(a)


if __name__ == "__main__":
    raise SystemExit(main())
