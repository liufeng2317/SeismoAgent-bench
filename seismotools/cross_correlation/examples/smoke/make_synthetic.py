#!/usr/bin/env python3
"""Synthetic known-answer dataset for the cross-correlation tool.

Homogeneous half-space (Vp 6.0, Vs 3.5 km/s, straight rays, stations at the
surface). Each station/phase radiates one fixed analytic wavelet (a sum of
2-12 Hz sinusoids under a Gaussian envelope), evaluated at the exact
(fractional-sample) arrival time, so every true differential time is known.

Stations (network XX):
- S01-S08  HH Z/N/E, 100 Hz
- S09      HH Z/1/2, 100 Hz (numbered horizontals)
- S10      HH Z/E only (no N)
- S11      HH Z/N/E, 200 Hz
- S12      HH Z/N/E, 100 Hz, polarity reversed for even-numbered events
40 events in a 2 km cluster at 5-7 km depth, origin times every ~26 s
from 23:50 to 00:10 UTC across midnight (two files per channel), three of
them within 2 s of midnight, and one deliberate overlap: ev025 starts 0.6 s
after ev024, so their phases share search windows (the ambiguity case). Arrivals: events 0-9 exact, 10-24 +-0.1 s random error, 25-39
"predicted" with +0.15 s bias.

Writes <out>/{waveforms/, events.csv, arrivals.csv, truth.json}.
"""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from obspy import Stream, Trace, UTCDateTime

VP, VS = 6.0, 3.5
LAT0, LON0 = 35.0, -117.0
MIDNIGHT = UTCDateTime("2019-07-05T00:00:00")
T0, T1 = MIDNIGHT - 600, MIDNIGHT + 600


def wavelet_factory(rng, width):
    f = rng.uniform(2.0, 12.0, 6)
    ph = rng.uniform(0, 2 * np.pi, 6)
    a = rng.uniform(0.5, 1.0, 6)

    def w(t):
        env = np.exp(-0.5 * ((t - 2.5 * width) / width) ** 2)
        return env * sum(ai * np.sin(2 * np.pi * fi * t + pi) for ai, fi, pi in zip(a, f, ph))
    return w


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    out = args.out
    (out / "waveforms").mkdir(parents=True, exist_ok=True)
    km_lat, km_lon = 111.195, 111.195 * math.cos(math.radians(LAT0))
    # stations on a spiral 5-50 km
    stations = {}
    for k in range(12):
        r = 5 + 45 * k / 11
        az = 2.4 * k
        stations[f"S{k + 1:02d}"] = (LAT0 + r * math.cos(az) / km_lat, LON0 + r * math.sin(az) / km_lon)
    rates = {s: (200.0 if s == "S11" else 100.0) for s in stations}
    comps = {s: ("Z", "N", "E") for s in stations}
    comps["S09"] = ("Z", "1", "2")
    comps["S10"] = ("Z", "E")
    # events
    n_ev = 40
    ot = float(T0) + 40 + 26.0 * np.arange(n_ev) + rng.uniform(-3, 3, n_ev)
    near = int(np.argmin(np.abs(ot - float(MIDNIGHT))))
    ot[near - 1:near + 2] = [float(MIDNIGHT) - 1.7, float(MIDNIGHT) - 0.4, float(MIDNIGHT) + 0.9]
    ot[25] = ot[24] + 0.6
    ev = [{"id": f"ev{i:03d}", "ot": float(ot[i]),
           "lat": LAT0 + rng.uniform(-1, 1) / km_lat, "lon": LON0 + rng.uniform(-1, 1) / km_lon,
           "dep": rng.uniform(5, 7), "amp": float(10 ** rng.uniform(0, 1))} for i in range(n_ev)]
    wav = {(s, ph): wavelet_factory(rng, 0.15 if ph == "P" else 0.3) for s in stations for ph in "PS"}
    hang = {s: rng.uniform(0, np.pi) for s in stations}           # S polarization angle
    tt = {}
    for i, e in enumerate(ev):
        for s, (la, lo) in stations.items():
            d = math.hypot((la - e["lat"]) * km_lat, (lo - e["lon"]) * km_lon)
            r = math.hypot(d, e["dep"])
            tt[(i, s, "P")], tt[(i, s, "S")] = r / VP, r / VS
    # waveforms: two files per channel split at midnight
    noise = 0.02
    for s in stations:
        sr = rates[s]
        n = int(round((T1 - T0) * sr))
        t = np.arange(n) / sr + float(T0)
        tr_data = {c: rng.normal(0, noise, n) for c in comps[s]}
        for i, e in enumerate(ev):
            sign = -1.0 if (s == "S12" and i % 2 == 0) else 1.0
            for ph in "PS":
                ta = e["ot"] + tt[(i, s, ph)]
                # wavelet onset 2.5 widths before its envelope peak: arrival = onset
                lo, hi = np.searchsorted(t, ta - 0.5), np.searchsorted(t, ta + 3.0)
                g = sign * e["amp"] * wav[(s, ph)](t[lo:hi] - ta)
                if ph == "P":
                    tr_data["Z"][lo:hi] += g
                else:
                    hz = [c for c in comps[s] if c != "Z"]
                    proj = {"N": math.cos(hang[s]), "1": math.cos(hang[s]),
                            "E": math.sin(hang[s]), "2": math.sin(hang[s])}
                    for c in hz:
                        tr_data[c][lo:hi] += g * proj[c]
        for c, x in tr_data.items():
            tr = Trace(x.astype(np.float32), header={"network": "XX", "station": s, "location": "",
                                                     "channel": "HH" + c, "sampling_rate": sr,
                                                     "starttime": T0})
            for name, a, b in (("d1", T0, MIDNIGHT - 1.0 / sr), ("d2", MIDNIGHT, T1)):
                piece = tr.slice(a, b, nearest_sample=False)
                Stream([piece]).write(str(out / "waveforms" / f"XX.{s}..HH{c}__{name}.mseed"), format="MSEED",
                                      encoding="FLOAT32")
    with (out / "events.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["event_id", "origin_time_utc", "latitude", "longitude", "depth_km"])
        for e in ev:
            w.writerow([e["id"], UTCDateTime(e["ot"]).isoformat() + "Z", f"{e['lat']:.6f}", f"{e['lon']:.6f}",
                        f"{e['dep']:.4f}"])
    with (out / "arrivals.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["event_id", "station_id", "phase", "time_utc", "source"])
        for i, e in enumerate(ev):
            for s in stations:
                for ph in "PS":
                    t_true = e["ot"] + tt[(i, s, ph)]
                    if i < 10:
                        err, src = 0.0, "pick"
                    elif i < 25:
                        err, src = rng.uniform(-0.1, 0.1), "pick"
                    else:
                        err, src = 0.15 + rng.uniform(-0.05, 0.05), "predicted"
                    w.writerow([e["id"], f"XX.{s}", ph, UTCDateTime(t_true + err).isoformat() + "Z", src])
    truth = {"events": {e["id"]: {"origin": e["ot"], "amp": e["amp"]} for e in ev},
             "tt": {f"{ev[i]['id']}|XX.{s}|{ph}": v for (i, s, ph), v in tt.items()},
             "rates": {f"XX.{s}": r for s, r in rates.items()},
             "reversed": {"station": "XX.S12", "events": [ev[i]["id"] for i in range(0, n_ev, 2)]},
             "near_midnight": [ev[i]["id"] for i in range(n_ev) if abs(ev[i]["ot"] - float(MIDNIGHT)) < 2],
             "overlap": [ev[24]["id"], ev[25]["id"]]}
    (out / "truth.json").write_text(json.dumps(truth, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
