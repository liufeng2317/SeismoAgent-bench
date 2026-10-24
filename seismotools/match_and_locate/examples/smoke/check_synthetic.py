#!/usr/bin/env python3
"""Score a synthetic smoke run against truth.json (depths km below sea level).

Pass requires every injected event detected once (|dt| <= 2 samples at 50 Hz),
offset events located within 0.3 km horizontally and in depth, relative
magnitudes within 0.15 (0.3 for the low-SNR event: MatchLocate2's magnitude is
the median peak-amplitude ratio, and the peak of signal plus noise biases it
high when the signal is a few times the noise), a CC = 1 self-detection and no
extra detections.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from obspy import UTCDateTime

KM_PER_DEG = 6371.0 * math.pi / 180.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-dir", type=Path, required=True, help="folder with truth.json")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    truth = json.loads((args.inputs_dir / "truth.json").read_text())
    with (args.run_dir / "detections.csv").open() as handle:
        found = list(csv.DictReader(handle))
    rows, used, ok = [], set(), True
    for event in truth:
        t0 = UTCDateTime(event["origin_time_utc"])
        best = min(range(len(found)), key=lambda i: abs(UTCDateTime(found[i]["origin_time_utc"]) - t0), default=None)
        if best is None or abs(UTCDateTime(found[best]["origin_time_utc"]) - t0) > 0.1:
            rows.append({"truth_time_s": event["time_s"], "detected": False})
            ok = False
            continue
        used.add(best)
        d = found[best]
        dlat = (float(d["latitude"]) - event["latitude"]) * KM_PER_DEG
        dlon = (float(d["longitude"]) - event["longitude"]) * KM_PER_DEG * math.cos(math.radians(event["latitude"]))
        row = {"truth_time_s": event["time_s"], "detected": True,
               "dt_s": round(UTCDateTime(d["origin_time_utc"]) - t0, 3),
               "horizontal_error_km": round(math.hypot(dlat, dlon), 3),
               "depth_error_km": round(float(d["depth_km"]) - event["depth_km"], 3),
               "magnitude_error": round(float(d["magnitude"]) - event["magnitude"], 3),
               "cc": float(d["cc"]), "nmad": float(d["nmad"]), "low_snr": bool(event.get("low_snr"))}
        row["pass"] = (abs(row["dt_s"]) <= 0.04 + 1e-9 and row["horizontal_error_km"] <= 0.3
                       and abs(row["depth_error_km"]) <= 0.3
                       and abs(row["magnitude_error"]) <= (0.3 if event.get("low_snr") else 0.15))
        ok &= row["pass"]
        rows.append(row)
    extras = [found[i]["origin_time_utc"] for i in range(len(found)) if i not in used]
    self_detection = any(float(f["cc"]) == 1.0 for f in found)
    ok &= not extras and self_detection
    report = {"status": "pass" if ok else "fail", "events": rows, "extra_detections": extras,
              "self_detection_cc_1": self_detection}
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
