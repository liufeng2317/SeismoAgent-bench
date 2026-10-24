#!/usr/bin/env python3
"""Check a run on the synthetic dataset against the known differential times.

Checks (all must pass):
1. every accepted dt has the right sign convention: |dt - (tt1 - tt2)| small;
   p95 error <= 0.2 sample and max <= 1 sample, per sampling rate;
2. pairs across the polarity reversal at XX.S12 are never accepted;
3. the arrival errors (+-0.1 s picks, +0.15 s predictions) do not bias dt:
   median error per arrival class within 0.05 sample;
4. coverage: >= 90 % of same-polarity measurements between non-overlapping
   events are accepted, and the overlapping pair's shared windows never give
   a wrong dt (rejected as ambiguous or measured correctly);
5. near-midnight events, the 1/2-component station (S on 2 components), the
   E-only station (S on 1 component) and the 200 Hz station all contribute;
6. dt.cc lines equal the accepted measurements.
Prints a JSON summary; exit status 1 on failure.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--run", type=Path, required=True)
    args = ap.parse_args()
    truth = json.loads((args.data / "truth.json").read_text())
    rev_sta, rev = truth["reversed"]["station"], set(truth["reversed"]["events"])
    cls = {e: ("exact" if int(e[2:]) < 10 else "pick_err" if int(e[2:]) < 25 else "predicted")
           for e in truth["events"]}
    rows = list(csv.DictReader((args.run / "measurements.csv").open()))
    fails, err_by_rate, err_by_cls = [], {}, {}
    accepted = same_pol = same_pol_acc = cross_acc = 0
    contrib = {"midnight": 0, "S09_2comp": 0, "S10_1comp": 0, "S11_200Hz": 0}
    mid = set(truth["near_midnight"])
    ovl = set(truth["overlap"])
    ambiguous = 0
    for r in rows:
        a, b, st, ph = r["event_id_1"], r["event_id_2"], r["station_id"], r["phase"]
        cross = st == rev_sta and ((a in rev) != (b in rev))
        if not cross and not ({a, b} & ovl):
            same_pol += 1
        ambiguous += r["status"] == "ambiguous"
        if r["status"] != "accepted":
            continue
        accepted += 1
        if cross:
            cross_acc += 1
            continue
        same_pol_acc += not ({a, b} & ovl)
        true = truth["tt"][f"{a}|{st}|{ph}"] - truth["tt"][f"{b}|{st}|{ph}"]
        delta = 1.0 / truth["rates"][st]
        e = (float(r["dt_s"]) - true) / delta
        err_by_rate.setdefault(truth["rates"][st], []).append(e)
        for c in {cls[a], cls[b]}:
            err_by_cls.setdefault(c, []).append(e)
        if a in mid or b in mid:
            contrib["midnight"] += 1
        if st == "XX.S09" and ph == "S" and int(r["n_components"]) == 2:
            contrib["S09_2comp"] += 1
        if st == "XX.S10" and ph == "S" and int(r["n_components"]) == 1:
            contrib["S10_1comp"] += 1
        if st == "XX.S11":
            contrib["S11_200Hz"] += 1
    summary = {"measurements": len(rows), "accepted": accepted, "cross_polarity_accepted": cross_acc,
               "ambiguous_rejected": ambiguous,
               "coverage_same_polarity": round(same_pol_acc / max(same_pol, 1), 4), "contributions": contrib,
               "error_samples": {}, "median_error_by_arrival_class": {}}
    for rate, e in sorted(err_by_rate.items()):
        e = np.abs(np.array(e))
        summary["error_samples"][f"{rate:g} Hz"] = {"n": int(e.size), "median": round(float(np.median(e)), 4),
                                                   "p95": round(float(np.percentile(e, 95)), 4),
                                                   "max": round(float(e.max()), 4)}
        if np.percentile(e, 95) > 0.2 or e.max() > 1.0:
            fails.append(f"dt error at {rate:g} Hz: p95 {np.percentile(e, 95):.3f}, max {e.max():.3f} samples")
    for c, e in sorted(err_by_cls.items()):
        med = float(np.median(e))
        summary["median_error_by_arrival_class"][c] = round(med, 4)
        if abs(med) > 0.05:
            fails.append(f"arrival class {c} biases dt by {med:.3f} samples")
    if cross_acc:
        fails.append(f"{cross_acc} polarity-reversed pairs accepted")
    if summary["coverage_same_polarity"] < 0.9:
        fails.append(f"coverage {summary['coverage_same_polarity']:.3f} < 0.9")
    for k, v in contrib.items():
        if v == 0:
            fails.append(f"no accepted measurement for {k}")
    n_lines = sum(1 for line in (args.run / "dt.cc").open() if not line.startswith("#"))
    if n_lines != accepted:
        fails.append(f"dt.cc has {n_lines} lines, accepted {accepted}")
    summary["status"] = "pass" if not fails else "fail"
    summary["failures"] = fails
    print(json.dumps(summary, indent=1))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
