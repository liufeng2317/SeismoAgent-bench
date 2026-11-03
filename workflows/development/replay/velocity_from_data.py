#!/usr/bin/env python3
"""Can a better velocity model be built from the Agent's own picks? Offline test of the standard practice.

No case gets a specific velocity model (decision 2026-11-03). Seismologists then build one from the data: a
minimum 1-D model searched jointly with station corrections, chosen by the travel-time misfit (VELEST). This
replays that on the representative pilot of each formal tools run (500 events, the subset and the generic
CRUST1.0 column of ``near_surface.py``): every velocity of the column is scaled by a factor; for each factor
the events are located with NonLinLoc EDT_OT_WT, then station corrections are iterated (median P and S residual
per station with at least 10 picks, minus the network median of each phase, so a shared offset is not absorbed;
accumulated over the iterations). Reference-free measures (median RMS) are recorded at every step; the
references are read only to score each step (time, depth and horizontal bias against the human-in-loop final).

Usage: velocity_from_data.py [case ...] [--workers 16]. Needs the outputs of near_surface.py.
Writes outputs/velocity_from_data/<case>.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import replay_lib  # noqa: E402
from replay_lib import Run, score  # noqa: E402
from near_surface import RUNS  # noqa: E402

LOCATE = replay_lib.ROOT / "seismotools/nonlinloc/interface/locate.py"
SCALES = (0.88, 0.94, 1.0, 1.06, 1.12)
ITERATIONS = 3          # station-correction rounds after the first location
MIN_PICKS = 10
OUT = HERE / "outputs/velocity_from_data"


def locate(src: Path, model: Path, delays: pd.DataFrame | None, out: Path, workers: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-I", str(LOCATE), "--arrivals", str(src / "arrivals.csv"), "--stations", str(src / "stations.csv"),
           "--velocity-model", str(model), "--config", str(src / "relocated_config.json"), "--output-dir", str(out / "run"),
           "--workers", str(workers), "--quiet", "--overwrite"]
    if delays is not None and len(delays):
        delays.to_csv(out / "delays.csv", index=False)
        cmd += ["--station-delays", str(out / "delays.csv")]
    subprocess.run(cmd, check=False, capture_output=True)
    ev = pd.read_csv(out / "run/events.csv")
    return ev[ev.status == "LOCATED"].copy(), pd.read_csv(out / "run/arrivals.csv")


def new_delays(arrivals: pd.DataFrame, damping: float = 1.0, cap_s: float | None = None) -> pd.DataFrame:
    g = arrivals.dropna(subset=["residual_s"]).groupby(["station_id", "phase"]).residual_s
    d = pd.DataFrame({"delay_s": g.median(), "n_picks": g.size()}).reset_index()
    d = d[d.n_picks >= MIN_PICKS]
    d["delay_s"] -= d.groupby("phase").delay_s.transform("median")  # station differences only, not a shared offset
    d["delay_s"] *= damping
    return d


def catalog(run: Run, sub_cat: Path, ev: pd.DataFrame, datum: float, path: Path) -> Path:
    loc = pd.DataFrame({"event_id": ev.event_id, "depth_bsl": ev.depth_km - datum, "latitude": ev.latitude,
                        "longitude": ev.longitude, "rms_s": ev.rms_s,
                        "t": (pd.to_datetime(ev.origin_time_utc, utc=True, format="ISO8601") - pd.Timestamp(0, tz="UTC")).dt.total_seconds()})
    raw = pd.read_csv(sub_cat, dtype=str, keep_default_na=False)
    replay_lib.apply_relocation(raw, loc, "drop").to_csv(path, index=False)
    return path


def run_case(case: str, workers: int, scales=SCALES, damping: float = 1.0, cap_s: float | None = None,
             tag: str = "") -> dict:
    run = Run(case, RUNS[case])
    ns = json.loads((HERE / "outputs/near_surface" / f"{case}.json").read_text())
    base_dir = HERE / "outputs/near_surface" / case
    src = base_dir / "generic_CRUST10" / "relocation"
    sub_cat = base_dir / "subset" / "catalog.csv"
    rows = np.loadtxt(base_dir / "generic_CRUST10" / "model.txt", ndmin=2)
    datum = float(json.loads((src / "relocated_config.json").read_text())["reference_elevation_km"])
    out = OUT / (case + (f"_{tag}" if tag else ""))
    steps = []
    for s in scales:
        model = out / f"scale_{s:.2f}" / "model.txt"
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_text("".join(f"{z:.3f} {vp * s:.3f} {vs * s:.3f}\n" for z, vp, vs in rows))
        delays = None
        for k in range(ITERATIONS + 1):
            step_dir = model.parent / f"iter_{k}"
            ev, arr = locate(src, model, delays, step_dir, workers)
            truth = score(run, catalog(run, sub_cat, ev, datum, step_dir / "catalog.csv"))["values"]
            rec = {"scale": s, "iteration": k, "located": int(len(ev)), "median_rms_s": round(float(ev.rms_s.median()), 4),
                   "mean_abs_delay_s": None if delays is None else round(float(delays.delay_s.abs().mean()), 3),
                   "dt_s": truth.get("time_bias_final_s"), "dz_km": truth.get("dz_final_km"), "shift_km": truth.get("shift_final_km")}
            steps.append(rec)
            print(case, rec, flush=True)
            d = new_delays(arr, damping)
            if delays is not None:
                d = d.merge(delays, on=["station_id", "phase"], how="outer", suffixes=("", "_old")).fillna(0.0)
                d["delay_s"] = d.delay_s + d.delay_s_old
                d["n_picks"] = d[["n_picks", "n_picks_old"]].max(axis=1).astype(int)
                d = d[["station_id", "phase", "delay_s", "n_picks"]]
            if cap_s is not None:
                d["delay_s"] = d.delay_s.clip(-cap_s, cap_s)
            delays = d
    res = {"case": case, "run": RUNS[case], "datum_km": datum, "events": ns["events"], "damping": damping, "cap_s": cap_s,
           "steps": steps}
    (OUT / f"{case}{'_' + tag if tag else ''}.json").write_text(json.dumps(res, indent=1, default=float))
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*", default=list(RUNS))
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--scales", type=float, nargs="*", default=list(SCALES))
    ap.add_argument("--damping", type=float, default=1.0, help="fraction of each round's new corrections applied")
    ap.add_argument("--cap-s", type=float, default=None, help="limit on the accumulated |delay|")
    ap.add_argument("--tag", default="", help="suffix of the output (variants)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for case in a.cases:
        run_case(case, a.workers, a.scales, a.damping, a.cap_s, a.tag)


if __name__ == "__main__":
    main()
