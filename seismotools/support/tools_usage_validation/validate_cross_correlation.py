#!/usr/bin/env python3
"""Validate the local cross-correlation tool (ccdt): kernels, synthetic known answers, Ridgecrest picks."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "seismotools" / "cross_correlation"
PY = sys.executable
sys.path.insert(0, str(TOOL / "runtime" / "python"))

from ccdt import cc_curves, pick_peak  # noqa: E402

RC = ROOT / "workflows" / "tasks" / "2019_ridgecrest_california" / "expert" / "export"
RC_WAVES = ROOT / "data" / "2019_ridgecrest_california" / "data" / "waveforms" / "data"


def check_kernels() -> dict:
    """cc_curves against a brute-force Pearson loop; parabolic peak on a cosine."""
    rng = np.random.default_rng(0)
    t, s = rng.normal(size=(5, 40)), rng.normal(size=(5, 40 + 2 * 7))
    fast = cc_curves(t, s)
    brute = np.array([[np.corrcoef(t[i], s[i, k:k + 40])[0, 1] for k in range(15)] for i in range(5)])
    true_frac = 0.3
    lags = np.arange(-10, 11)
    cc = np.cos(2 * np.pi * (lags - true_frac) / 40.0)[None, :]
    k, peak, frac, ok = pick_peak(cc)
    return {"max_abs_diff_vs_bruteforce": float(np.abs(fast - brute).max()),
            "parabola_frac": float(frac[0]), "parabola_true": true_frac,
            "status": "pass" if np.abs(fast - brute).max() < 1e-10 and abs(frac[0] - true_frac) < 0.01 and ok[0]
            else "fail"}


def check_synthetic(tmp: Path) -> dict:
    data, run1, run4 = tmp / "syn", tmp / "syn_run1", tmp / "syn_run4"
    subprocess.run([PY, "-I", str(TOOL / "examples/smoke/make_synthetic.py"), "--out", str(data)], check=True,
                   capture_output=True)
    for out, w in ((run1, 1), (run4, 4)):
        subprocess.run([PY, "-I", str(TOOL / "interface/run.py"), "--events", str(data / "events.csv"),
                        "--arrivals", str(data / "arrivals.csv"), "--waveforms", str(data / "waveforms"),
                        "--output-dir", str(out), "--workers", str(w), "--quiet"], check=True, capture_output=True)
    chk = subprocess.run([PY, "-I", str(TOOL / "examples/smoke/check_synthetic.py"), "--data", str(data),
                          "--run", str(run4)], capture_output=True, text=True)
    summary = json.loads(chk.stdout)
    summary["workers_1_vs_4_identical"] = (run1 / "dt.cc").read_bytes() == (run4 / "dt.cc").read_bytes()
    if not summary["workers_1_vs_4_identical"]:
        summary["status"] = "fail"
    return summary


def check_ridgecrest(tmp: Path, n_events: int = 80) -> dict:
    """CC dt of well-picked Ridgecrest events must agree with their pick differential times.

    PhaseNet picks carry their own errors (tens of ms, occasionally more), so
    the criteria are robust: |median(cc - pick)| < 10 ms, MAD < 30 ms, the
    geometric mean of the two Theil-Sen slopes (cc on pick, pick on cc;
    errors on either axis attenuate one of them) within 5 % of 1, and fewer
    than 10 % of measurements more than 0.1 s from the pick difference."""
    events = RC / "06_full_catalog" / "52_full_catalog" / "working_catalog.csv"
    if not events.is_file() or not RC_WAVES.is_dir():
        return {"status": "skipped", "reason": "Ridgecrest expert export or waveforms absent"}
    import pandas as pd
    ev = pd.read_csv(events, low_memory=False)
    ev["t"] = pd.to_datetime(ev.origin_time, utc=True, format="ISO8601")
    hour = ev[(ev.t >= "2019-07-05T10:00:00Z") & (ev.t < "2019-07-05T12:00:00Z")]
    assoc = pd.read_csv(RC / "01_baseline" / "04_locate_nonlinloc" / "full" / "picks.csv")
    picks = pd.read_csv(RC / "02_pick_phasenet" / "full" / "picks.csv", usecols=["pick_id", "station_id", "time_utc"])
    p = assoc[assoc.residual_s.abs() <= 0.2].merge(picks, on="pick_id")
    support = p.groupby("event_id").size()
    sel = hour[hour.event_id.isin(support[support >= 20].index)].nsmallest(n_events, "t")
    p = p[p.event_id.isin(sel.event_id)].drop_duplicates(["event_id", "station_id", "phase"])
    sel[["event_id", "origin_time", "latitude", "longitude", "depth_below_sea_level_km"]].rename(
        columns={"origin_time": "origin_time_utc", "depth_below_sea_level_km": "depth_km"}).to_csv(
        tmp / "rc_events.csv", index=False)
    p[["event_id", "station_id", "phase", "time_utc"]].to_csv(tmp / "rc_arrivals.csv", index=False)
    # the 2019-07-05 day files of the stations involved, linked into a small tree
    wav = tmp / "rc_waves"
    wav.mkdir()
    for st in p.station_id.unique():
        for f in (RC_WAVES / st).glob(f"{st}.*__20190705T000000Z__*.mseed"):
            (wav / f.name).symlink_to(f)
    out = tmp / "rc_run"
    proc = subprocess.run([PY, "-I", str(TOOL / "interface/run.py"), "--events", str(tmp / "rc_events.csv"),
                           "--arrivals", str(tmp / "rc_arrivals.csv"), "--waveforms", str(wav), "--output-dir",
                           str(out), "--workers", "8", "--quiet"], capture_output=True, text=True)
    if proc.returncode != 0:
        return {"status": "fail", "error": (proc.stderr or proc.stdout)[-2000:]}
    m = pd.read_csv(out / "measurements.csv")
    m = m[m.status == "accepted"]
    o = dict(zip(sel.event_id, pd.to_datetime(sel.origin_time, utc=True, format="ISO8601")))
    pk = {(r.event_id, r.station_id, r.phase): pd.Timestamp(r.time_utc) for r in p.itertuples()}
    diff, dpk = [], []
    for r in m.itertuples():
        a, b = (r.event_id_1, r.station_id, r.phase), (r.event_id_2, r.station_id, r.phase)
        if a in pk and b in pk:
            d = ((pk[a] - o[r.event_id_1]) - (pk[b] - o[r.event_id_2])).total_seconds()
            dpk.append(d)
            diff.append(r.dt_s - d)
    diff, dpk = np.array(diff), np.array(dpk)
    dcc = dpk + diff
    from scipy.stats import theilslopes
    slope = float(np.sqrt(theilslopes(dcc, dpk)[0] / theilslopes(dpk, dcc)[0])) if len(dpk) > 2 else float("nan")
    med, mad = float(np.median(diff)), float(np.median(np.abs(diff - np.median(diff))))
    outliers = float(np.mean(np.abs(diff) > 0.1)) if len(diff) else float("nan")
    res = {"events": int(len(sel)), "accepted": int(len(m)), "compared_with_picks": int(len(diff)),
           "median_cc_minus_pick_s": round(med, 4), "mad_s": round(mad, 4), "robust_slope": round(slope, 3),
           "fraction_beyond_0p1_s": round(outliers, 3),
           }
    res["status"] = "pass" if len(diff) >= 200 and abs(med) < 0.01 and mad < 0.03 and abs(slope - 1) < 0.05 \
        and outliers < 0.10 else "fail"
    return res


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ccdt_validate_") as d:
        tmp = Path(d)
        report = {"tool": "cross_correlation", "kernels": check_kernels(), "synthetic": check_synthetic(tmp),
                  "ridgecrest": check_ridgecrest(tmp)}
    report["status"] = "pass" if all(report[k]["status"] in ("pass", "skipped")
                                     for k in ("kernels", "synthetic", "ridgecrest")) else "fail"
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
