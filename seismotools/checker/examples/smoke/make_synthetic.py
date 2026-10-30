#!/usr/bin/env python3
"""Synthetic inputs for the checker smoke test: a clean network, catalog, picks and records, and one
variant per injected error.

10 stations (ZNE, 50 Hz, two one-hour files per channel), 80 events in a 10 km cluster at 5–10 km
depth below sea level, homogeneous Vp 6.0 km/s and Vs 3.46 km/s. Records are Gaussian noise plus a
damped 8 Hz P pulse (mostly vertical) and 5 Hz S pulse (mostly horizontal). Magnitudes are set so the
Wood-Anderson amplitude at the farthest station is 10^-1.2 mm.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from obspy import Stream, Trace, UTCDateTime

LAT0, LON0, KM = 35.0, -97.0, 111.195
VP, VS, RATE = 6.0, 3.46, 50.0
START = UTCDateTime("2020-01-01T00:00:00Z")


def utc(t: float) -> str:
    return (START + t).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def pulse(n: int, rate: float, f: float, decay: float) -> np.ndarray:
    t = np.arange(n) / rate
    return np.sin(2 * np.pi * f * t) * np.exp(-t / decay)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    out = parser.parse_args().output_dir
    rng = np.random.default_rng(7)
    out.mkdir(parents=True, exist_ok=True)

    az = np.radians(np.arange(10) * 36.0 + 5.0)
    radius = np.r_[np.full(5, 8.0), np.full(5, 30.0)]
    sx, sy = radius * np.sin(az), radius * np.cos(az)
    stations = pd.DataFrame({"station_id": [f"XX.S{i:02d}" for i in range(10)], "latitude": LAT0 + sy / KM,
                             "longitude": LON0 + sx / (KM * np.cos(np.radians(LAT0))), "elevation_m": 300.0})
    stations.to_csv(out / "stations.csv", index=False)

    n_ev = 80
    t0 = np.sort(rng.uniform(60, 7140, n_ev))
    ex, ey, ez = rng.uniform(-5, 5, n_ev), rng.uniform(-5, 5, n_ev), rng.uniform(5, 10, n_ev)
    rmax = np.array([np.hypot(np.hypot(sx - x, sy - y).max(), z + 0.3) for x, y, z in zip(ex, ey, ez)])
    mag = -1.2 + 1.11 * np.log10(rmax / 100) + 0.00189 * (rmax - 100) + 3.0 + rng.normal(0, 0.1, n_ev)
    catalog = pd.DataFrame({"event_id": [f"ev{i:03d}" for i in range(n_ev)], "origin_time_utc": [utc(t) for t in t0],
                            "latitude": LAT0 + ey / KM, "longitude": LON0 + ex / (KM * np.cos(np.radians(LAT0))),
                            "depth_km": np.round(ez, 3), "magnitude": np.round(mag, 2), "status": "accepted"})
    catalog.to_csv(out / "catalog.csv", index=False)

    picks, n = [], int(7200 * RATE)
    data = {(s, c): rng.normal(0, 1.0, n) for s in stations.station_id for c in "ZNE"}
    for i in range(n_ev):
        for j, s in enumerate(stations.station_id):
            r = np.hypot(np.hypot(sx[j] - ex[i], sy[j] - ey[i]), ez[i] + 0.3)
            amp = 400.0 * 10 ** (mag[i] - 1.0) / r
            for ph, v, f, comp_amp in (("P", VP, 8.0, {"Z": 1.0, "N": 0.3, "E": 0.3}), ("S", VS, 5.0, {"Z": 0.3, "N": 1.0, "E": 1.0})):
                ta = t0[i] + r / v
                k = int(round(ta * RATE))
                w = pulse(int(2 * RATE), RATE, f, 0.4)
                for comp, a in comp_amp.items():
                    seg = data[(s, comp)][k:k + len(w)]
                    seg += (2.0 if ph == "S" else 1.0) * amp * a * w[:len(seg)]
                picks.append({"event_id": f"ev{i:03d}", "station_id": s, "phase": ph, "time": ta + rng.normal(0, 0.01)})
    picks = pd.DataFrame(picks).sort_values("time").reset_index(drop=True)
    picks.insert(0, "pick_id", [f"pk{i:05d}" for i in range(len(picks))])
    picks["time_utc"] = [utc(t) for t in picks.time]
    picks["probability"] = 0.9
    picks["status"] = "accepted"
    cols = ["pick_id", "event_id", "station_id", "phase", "time_utc", "probability", "status"]
    picks[cols].to_csv(out / "picks.csv", index=False)

    def write(folder: Path, transform=None, rate_of=None):
        for (s, comp), x in data.items():
            net, sta = s.split(".")
            y = transform(x) if transform else x
            r = (rate_of or {}).get((s, comp), RATE)
            if r != RATE:
                y = y[::int(RATE / r)]
            for h in range(2):
                m = int(3600 * r)
                tr = Trace(np.round(y[h * m:(h + 1) * m] * 100).astype(np.int32),
                           header={"network": net, "station": sta, "location": "", "channel": f"HH{comp}",
                                   "sampling_rate": r, "starttime": START + 3600 * h})
                d = folder / s
                d.mkdir(parents=True, exist_ok=True)
                name = f"{s}..HH{comp}__{(START + 3600 * h).strftime('%Y%m%dT%H%M%SZ')}__{(START + 3600 * (h + 1)).strftime('%Y%m%dT%H%M%SZ')}.mseed"
                Stream([tr]).write(str(d / name), format="MSEED", encoding="STEIM2")

    write(out / "waveforms")
    # variant: one station records its east channel at a lower rate
    write(out / "waveforms_mixed_rates", rate_of={("XX.S03", "E"): 25.0})
    # variant: "processed" records shifted 0.3 s late
    shift = int(0.3 * RATE)
    write(out / "processed_shifted", transform=lambda x: np.r_[np.zeros(shift), x[:-shift]])

    variants = out / "variants"
    variants.mkdir(exist_ok=True)
    p = picks.copy()
    p["time_utc"] = [utc(t - 2.5) for t in p.time]
    p[cols].to_csv(variants / "picks_early_2p5s.csv", index=False)
    dup = picks.sample(frac=0.1, random_state=1).copy()
    dup["pick_id"] = dup.pick_id + "d"
    dup["time_utc"] = [utc(t + 0.1) for t in dup.time]
    pd.concat([picks, dup])[cols].to_csv(variants / "picks_duplicated.csv", index=False)
    c = catalog.copy()
    c.loc[c.index % 5 < 2, "depth_km"] = 7.0
    c.to_csv(variants / "catalog_depth_layer.csv", index=False)
    c = catalog.copy()
    c["magnitude"] = c.magnitude - 3.0
    c.to_csv(variants / "catalog_magnitude_offset.csv", index=False)
    c = catalog.copy()
    c["depth_km"] = c.depth_km + rng.normal(0, 0.05, n_ev)
    c.to_csv(variants / "relocated_clean.csv", index=False)
    c = catalog.copy()
    c["depth_km"] = c.depth_km + 2.0
    c.to_csv(variants / "relocated_shifted.csv", index=False)
    c = catalog.copy()
    grp = np.arange(n_ev) % 4
    for g in range(4):  # collapse onto four points: structure far thinner than before
        c.loc[grp == g, ["latitude", "longitude", "depth_km"]] = c.loc[grp == g, ["latitude", "longitude", "depth_km"]].iloc[0].to_numpy()
    c["depth_km"] = c.depth_km + rng.normal(0, 0.002, n_ev)
    c.to_csv(variants / "relocated_collapsed.csv", index=False)
    (out / "truth.json").write_text(json.dumps({"events": n_ev, "picks": int(len(picks)), "stations": 10}, indent=1))
    print(f"synthetic inputs in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
