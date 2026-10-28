"""End-to-end run: inputs -> windows -> pair correlations -> dt.cc.

Inputs (CSV, header row):
- events:   event_id, origin_time_utc, latitude, longitude, depth_km
- arrivals: event_id, station_id (NET.STA), phase (P|S), time_utc[, source]
  The arrival only positions the windows (pick or prediction); it does not
  enter dt (see correlate.py).
- pairs (optional): event_id_1, event_id_2. Default: every event with its
  ``pairs.max_neighbors`` nearest events within ``pairs.max_distance_km``
  (hypocentral distance), each unordered pair once.

Outputs in the run directory:
- dt.cc            hypoDD (getdata.f) and GrowClust xcordata format:
                   ``# id1 id2 0.0`` then ``STA DT WEIGHT PHASE`` lines,
                   DT = tt(id1) - tt(id2), accepted measurements only
- event_ids.csv    integer id written to dt.cc <-> input event_id
- measurements.csv one row per pair/station/phase attempted (all statuses,
                   or accepted only with ``write_rejected: false``)
- run_result.json  counts by status, timing, configuration
"""
from __future__ import annotations

import copy
import csv
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .correlate import measure_pairs
from .windows import choose_channels, extract_channel, index_waveforms

DEFAULT_CONFIG = {
    "channels": {"families": ["HH", "EH", "BH", "HN", "EN"], "P": ["Z"], "S": ["N", "E", "1", "2"]},
    "filter": {"freqmin": 2.0, "freqmax": 15.0, "corners": 4},
    "window": {"P": {"before_s": 0.2, "after_s": 0.6}, "S": {"before_s": 0.3, "after_s": 1.0}},
    "max_lag_s": {"P": 0.3, "S": 0.4},
    "pad_s": 30.0,            # neighbouring data read around each file (filter start-up, boundaries)
    "edge_guard_s": 3.0,      # a window must sit this far from a trace end or gap
    "taper_s": 2.0,
    # Defaults from a real-data pick check: at SNR >= 3
    # and CC >= 0.7, 6 % of P measurements differ from PhaseNet pick
    # differences by > 0.1 s (12 % at SNR >= 2, CC >= 0.6).
    "snr": {"noise_s": 2.0, "min": 3.0},
    "accept": {"min_cc": 0.7, "ambiguity_ratio": 0.9, "ambiguity_guard_s": 0.1},
    "pairs": {"max_distance_km": 3.0, "max_neighbors": 30},
    "phases": ["P", "S"],
    "weight": "cc",           # "cc" or "cc2"
    "write_rejected": True,
}


def merge_config(user: Optional[dict]) -> dict:
    cfg = copy.deepcopy(DEFAULT_CONFIG)

    def deep(a, b):
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(a.get(k), dict):
                deep(a[k], v)
            else:
                a[k] = v
    deep(cfg, user or {})
    return cfg


def _epoch(text: str) -> float:
    """UTC epoch of an ISO 8601 time; accepts a space separator, a trailing Z
    or +00:00 and more than six fractional digits (pandas writes nanoseconds)."""
    import re
    from obspy import UTCDateTime
    t = text.strip().replace(" ", "T")
    if t.endswith("+00:00"):
        t = t[:-6]
    elif re.search(r"[+-]\d\d:\d\d$", t):
        raise ValueError(f"only UTC times are accepted: {text!r}")
    t = re.sub(r"(\.\d{6})\d+", r"\1", t.rstrip("Z"))
    return float(UTCDateTime(t + "Z"))


def read_events(path) -> Tuple[List[str], np.ndarray, np.ndarray]:
    ids, origin, xyz = [], [], []
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            ids.append(r["event_id"].strip())
            origin.append(_epoch(r["origin_time_utc"]))
            xyz.append((float(r["latitude"]), float(r["longitude"]), float(r["depth_km"])))
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate event_id in events table")
    return ids, np.array(origin), np.array(xyz)


def read_arrivals(path, row_of: Dict[str, int], phases) -> Dict[Tuple[str, str], List[Tuple[int, float]]]:
    out: Dict[Tuple[str, str], List[Tuple[int, float]]] = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            ph = r["phase"].strip().upper()[:1]
            ev = r["event_id"].strip()
            if ph not in phases or ev not in row_of:
                continue
            out.setdefault((r["station_id"].strip(), ph), []).append((row_of[ev], _epoch(r["time_utc"])))
    # one arrival per event/station/phase (first wins)
    for key, lst in out.items():
        seen, uniq = set(), []
        for row, t in lst:
            if row not in seen:
                seen.add(row)
                uniq.append((row, t))
        out[key] = uniq
    return out


def neighbour_pairs(xyz: np.ndarray, max_km: float, k: int) -> np.ndarray:
    from scipy.spatial import cKDTree
    lat0 = np.radians(np.nanmean(xyz[:, 0]))
    pts = np.c_[xyz[:, 1] * 111.195 * np.cos(lat0), xyz[:, 0] * 111.195, xyz[:, 2]]
    tree = cKDTree(pts)
    d, j = tree.query(pts, k=min(k + 1, len(pts)), distance_upper_bound=max_km)
    pairs = set()
    for i in range(len(pts)):
        for dd, jj in zip(np.atleast_1d(d[i]), np.atleast_1d(j[i])):
            if jj != i and jj < len(pts) and np.isfinite(dd):
                pairs.add((min(i, jj), max(i, jj)))
    return np.array(sorted(pairs), dtype=np.int64).reshape(-1, 2)


def read_pairs(path, row_of) -> np.ndarray:
    pairs = set()
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            a, b = row_of.get(r["event_id_1"].strip()), row_of.get(r["event_id_2"].strip())
            if a is not None and b is not None and a != b:
                pairs.add((min(a, b), max(a, b)))
    return np.array(sorted(pairs), dtype=np.int64).reshape(-1, 2)


def _measure_task(task):
    station, phase, wins, pairs, origin, min_cc, min_snr, ratio, guard = task
    rows_with = set()
    for w in wins:
        rows_with.update(int(r) for r, v in zip(w["rows"], w["valid"]) if v)
    sel = np.array([(a in rows_with) and (b in rows_with) for a, b in pairs], dtype=bool) if len(pairs) else \
        np.zeros(0, dtype=bool)
    p = pairs[sel]
    if not len(p):
        return station, phase, None
    res = []
    for lo in range(0, len(p), 20000):
        chunk = p[lo:lo + 20000]
        r = measure_pairs(wins, chunk[:, 0], chunk[:, 1], origin, min_cc, min_snr, ratio, guard)
        r["a"], r["b"] = chunk[:, 0], chunk[:, 1]
        res.append(r)
    merged = {k: np.concatenate([r[k] for r in res]) for k in res[0]}
    return station, phase, merged


def run(events_csv, arrivals_csv, waveforms, output_dir, config=None, pairs_csv=None,
        workers: int = 1, log=print) -> dict:
    t_start = time.time()
    cfg = merge_config(config)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    ids, origin, xyz = read_events(events_csv)
    row_of = {e: i for i, e in enumerate(ids)}
    arrivals = read_arrivals(arrivals_csv, row_of, set(cfg["phases"]))
    pairs = read_pairs(pairs_csv, row_of) if pairs_csv else \
        neighbour_pairs(xyz, cfg["pairs"]["max_distance_km"], cfg["pairs"]["max_neighbors"])
    log(f"{len(ids)} events, {len(pairs)} pairs, {sum(len(v) for v in arrivals.values())} arrivals")
    stations = sorted({st for st, _ in arrivals})
    codes = {}
    for st in stations:
        codes.setdefault(st.split(".")[-1], []).append(st)
    clash = {c: v for c, v in codes.items() if len(v) > 1}
    if clash:
        raise ValueError(f"station codes repeat across networks (dt.cc carries the code only): {clash}")
    index = index_waveforms(waveforms, workers=workers)
    tasks, groups = [], {}
    for (station, phase), arr in sorted(arrivals.items()):
        for tid in choose_channels(index, station, phase, cfg):
            groups.setdefault((station, phase), []).append(len(tasks))
            tasks.append((tid, index[tid], arr, phase, cfg))
    t_windows = time.time()
    with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
        windows = list(pool.map(extract_channel, tasks, chunksize=1))
    log(f"windows: {len(windows)} channels in {time.time() - t_windows:.0f} s")
    wcount = {}
    for w in windows:
        for r in w["reason"]:
            wcount[r] = wcount.get(r, 0) + 1
    acc = cfg["accept"]
    mtasks = [(st, ph, [windows[i] for i in idx], pairs, origin, float(acc["min_cc"]), float(cfg["snr"]["min"]),
               float(acc["ambiguity_ratio"]), float(acc["ambiguity_guard_s"])) for (st, ph), idx in sorted(groups.items())]
    t_cc = time.time()
    with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(_measure_task, mtasks, chunksize=1))
    log(f"correlation: {len(results)} station-phases in {time.time() - t_cc:.0f} s")
    # outputs
    cusp = {i: i + 1 for i in range(len(ids))}
    with (out / "event_ids.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["cusp_id", "event_id"])
        for i, e in enumerate(ids):
            w.writerow([cusp[i], e])
    status_count: Dict[str, int] = {}
    by_pair: Dict[Tuple[int, int], List[Tuple[str, float, float, str]]] = {}
    weight = (lambda c: c * c) if cfg["weight"] == "cc2" else (lambda c: c)
    with (out / "measurements.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["event_id_1", "event_id_2", "station_id", "phase", "dt_s", "cc", "lag_s",
                    "n_components", "snr_1", "snr_2", "status"])
        for station, phase, r in results:
            if r is None:
                continue
            for i in range(len(r["a"])):
                st_ = r["status"][i]
                status_count[st_] = status_count.get(st_, 0) + 1
                if st_ != "accepted" and not cfg["write_rejected"]:
                    continue
                a, b = int(r["a"][i]), int(r["b"][i])
                w.writerow([ids[a], ids[b], station, phase, f"{r['dt'][i]:.5f}", f"{r['cc'][i]:.4f}",
                            f"{r['lag_s'][i]:.5f}", int(r["n_components"][i]),
                            f"{r['snr_a'][i]:.2f}", f"{r['snr_b'][i]:.2f}", st_])
                if st_ == "accepted":
                    by_pair.setdefault((a, b), []).append((station.split(".")[-1], float(r["dt"][i]),
                                                           weight(float(r["cc"][i])), phase))
    n_lines = 0
    with (out / "dt.cc").open("w") as fh:
        for (a, b) in sorted(by_pair):
            fh.write(f"# {cusp[a]:9d} {cusp[b]:9d} 0.0\n")
            for sta, dt, wt, ph in by_pair[(a, b)]:
                fh.write(f"{sta:<7s} {dt:10.5f} {wt:6.4f} {ph}\n")
                n_lines += 1
    result = {"status": "success", "events": len(ids), "pairs_considered": int(len(pairs)),
              "pairs_with_dt": len(by_pair), "dt_lines": n_lines, "measurement_status": status_count,
              "window_status": wcount, "channels": len(windows),
              "timing_s": {"total": round(time.time() - t_start, 1),
                           "windows": round(t_cc - t_windows, 1), "correlation": round(time.time() - t_cc, 1)}}
    (out / "run_result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
