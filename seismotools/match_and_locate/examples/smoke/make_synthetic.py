#!/usr/bin/env python3
"""Write raw synthetic inputs for the two-step interface, with known answers.

Eight stations (elevations 1.2-1.8 km) surround a template source at 35.0N,
117.0W, 6.5 km below sea level, in a three-layer model whose datum is 1.5 km
above sea level. Five events share one waveform signature per channel and
phase: the template, two smaller co-located repeats and two events offset by
0.5-0.75 km horizontally and 0.5 km in depth. Arrivals use exact
first-arrival times for the true geometry (station elevation included), are
placed with sub-sample precision in raw 100 Hz MiniSEED, and noise is added.

Outputs (all inputs of interface/prepare.py, plus truth.json):
waveforms/*.mseed, stations.csv, templates.csv, picks.csv (template picks at
three stations), velocity_model.csv, prepare_config.json, truth.json.
Depths in templates.csv and truth.json are km below sea level.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from obspy import Trace, UTCDateTime

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "runtime" / "python" / "MatchLocatepy"))
from matchlocate_runner.native import KM_PER_DEG  # noqa: E402
from matchlocate_runner.traveltime import LayeredModel, epicentral_km, first_arrival  # noqa: E402

DAY = UTCDateTime(2020, 1, 1)
LENGTH_S = 1200.0
RAW_SR = 100.0
DATUM_KM = 1.5                      # model datum elevation above sea level
MODEL_ROWS = [(0.0, 4.8), (4.0, 6.0), (15.0, 6.6)]
MODEL = LayeredModel(tuple(r[0] for r in MODEL_ROWS), tuple(r[1] for r in MODEL_ROWS),
                     tuple(r[1] / 1.73 for r in MODEL_ROWS))
CENTER = (35.0, -117.0, 6.5)        # depth km below sea level
TEMPLATE_MAG = 2.0
# (origin offset s, north km, east km, down km, amplitude ratio)
EVENTS = [(120.0, 0.0, 0.0, 0.0, 1.0), (330.0, 0.0, 0.0, 0.0, 0.3), (560.0, 0.5, -0.5, 0.5, 0.5),
          (790.0, 0.0, 0.0, 0.0, 0.08), (1000.0, -0.75, 0.25, -0.5, 0.2)]
PREPARE_CONFIG = {
    "processing": {"sampling_rate": 50.0, "freqmin": 2.0, "freqmax": 10.0},
    "segments": {"windows": [{"segment_id": "W20200101", "start": "2020-01-01T00:00:00Z",
                              "end": "2020-01-01T00:20:00Z"}]},
    "channels": {"families": ["HH"], "P": ["Z"], "S": ["N", "E"]},
    "window": {"length_s": 2.0, "before_s": 0.2, "after_s": 1.8},
    "selection": {"max_distance_km": 60.0, "min_snr": 3.0, "noise_s": 5.0, "min_rows": 12},
    "marks": {"source": "picks_then_model"},
    "depth": {"input_reference": "sea_level", "model_datum_elevation_km": DATUM_KM},
    "run": {
        "search": {"units": "km", "half_width_km": 1.0, "step_km": 0.25, "half_depth_km": 1.0, "step_depth_km": 0.25},
        "window": {"length_s": 2.0, "before_s": 0.2, "after_s": 1.8},
        "detection": {"cc_threshold": 0.0, "mad_threshold": 9.0, "min_separation_s": 4.0},
        "merge": {"engine": "python", "cc_threshold": 0.2, "mad_threshold": 9.0, "min_separation_s": 4.0},
        "min_channels": 12,
    },
}


def signature(seed: int):
    """Continuous-time decaying wave packet: a sum of seeded Gabor atoms."""
    rng = np.random.default_rng(seed)
    atoms = [(rng.uniform(3.0, 8.0), rng.uniform(0, 2 * np.pi), rng.uniform(0.0, 0.8), rng.uniform(0.5, 1.0))
             for _ in range(6)]

    def wave(t):
        out = np.zeros_like(t)
        for f, ph, delay, amp in atoms:
            tt = t - delay
            out += amp * np.where(tt >= 0, np.exp(-tt / 0.35) * (1 - np.exp(-tt / 0.03)), 0.0) * np.cos(2 * np.pi * f * tt + ph)
        return out / sum(a[3] for a in atoms)
    return wave


def offset_position(dn, de, dz):
    lat0, lon0, z0 = CENTER
    return lat0 + dn / KM_PER_DEG, lon0 + de / (KM_PER_DEG * math.cos(math.radians(lat0))), z0 + dz


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.output_dir
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"{root} must be new or empty")
    (root / "waveforms").mkdir(parents=True)
    rng = np.random.default_rng(20200101)
    t_axis = np.arange(int(LENGTH_S * RAW_SR)) / RAW_SR
    stations, picks = [], []
    for k, dist in enumerate([6, 9, 12, 15, 18, 21, 24, 27]):
        az = math.radians(45.0 * k + 10.0)
        lat, lon, _ = offset_position(dist * math.cos(az), dist * math.sin(az), 0.0)
        stations.append((f"S{k + 1:02d}", lat, lon, 1200.0 + 85.0 * k))
    for s_index, (sta, slat, slon, elev) in enumerate(stations):
        zr = DATUM_KM - elev / 1000.0
        arrivals = []
        for n, (origin, dn, de, dz, amp) in enumerate(EVENTS):
            elat, elon, edp = offset_position(dn, de, dz)
            dist = epicentral_km(slat, slon, elat, elon)
            tp = first_arrival(MODEL, "P", dist, edp + DATUM_KM, zr).travel_time_s
            ts = first_arrival(MODEL, "S", dist, edp + DATUM_KM, zr).travel_time_s
            arrivals.append((origin, amp, tp, ts))
            if n == 0 and s_index < 3:
                picks += [("T0", f"SY.{sta}", "P", DAY + origin + tp), ("T0", f"SY.{sta}", "S", DAY + origin + ts)]
        for c_index, comp in enumerate("ZNE"):
            p_wave = signature(1000 + 10 * s_index + c_index)
            s_wave = signature(5000 + 10 * s_index + c_index)
            p_amp, s_amp = (0.4, 0.3) if comp == "Z" else (0.15, 1.0)
            data = rng.normal(0.0, 0.02, t_axis.size)
            for origin, amp, tp, ts in arrivals:
                data += amp * p_amp * p_wave(t_axis - (origin + tp))
                data += amp * s_amp * s_wave(t_axis - (origin + ts))
            raw = Trace((data * 1e4).astype(np.int32), header={
                "network": "SY", "station": sta, "location": "00", "channel": f"HH{comp}",
                "sampling_rate": RAW_SR, "starttime": DAY})
            raw.write(str(root / "waveforms" / f"SY.{sta}.00.HH{comp}.mseed"), format="MSEED")

    with (root / "stations.csv").open("w", newline="") as h:
        w = csv.writer(h, lineterminator="\n")
        w.writerow(["station_id", "latitude", "longitude", "elevation_m"])
        w.writerows([(f"SY.{s}", la, lo, el) for s, la, lo, el in stations])
    with (root / "templates.csv").open("w", newline="") as h:
        w = csv.writer(h, lineterminator="\n")
        w.writerow(["event_id", "origin_time_utc", "latitude", "longitude", "depth_km", "magnitude"])
        w.writerow(["T0", str(DAY + EVENTS[0][0]), *CENTER, TEMPLATE_MAG])
    with (root / "picks.csv").open("w", newline="") as h:
        w = csv.writer(h, lineterminator="\n")
        w.writerow(["event_id", "station_id", "phase", "time_utc"])
        w.writerows([(e, s, p, str(t)) for e, s, p, t in picks])
    with (root / "velocity_model.csv").open("w", newline="") as h:
        w = csv.writer(h, lineterminator="\n")
        w.writerow(["top_of_layer_km", "vp_km_s", "vs_km_s"])
        w.writerows([(top, vp, vp / 1.73) for top, vp in MODEL_ROWS])
    (root / "prepare_config.json").write_text(json.dumps(PREPARE_CONFIG, indent=2) + "\n")
    truth = []
    for origin, dn, de, dz, amp in EVENTS:
        lat, lon, depth = offset_position(dn, de, dz)
        truth.append({"origin_time_utc": str(DAY + origin), "time_s": origin, "latitude": lat, "longitude": lon,
                      "depth_km": depth, "magnitude": TEMPLATE_MAG + math.log10(amp), "offset_km": [dn, de, dz],
                      # S peak ~4x the noise RMS: the native peak-amplitude ratio reads high
                      "low_snr": amp < 0.1})
    (root / "truth.json").write_text(json.dumps(truth, indent=2) + "\n")
    print(json.dumps({"inputs": str(root), "stations": len(stations), "events": len(truth), "picks": len(picks)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
