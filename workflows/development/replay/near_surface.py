#!/usr/bin/env python3
"""Can the near surface be constrained without a regional model? An offline test on the formal tools runs' picks.

The Agent gets no specific velocity model (decision 2026-11-03), so it starts from a generic one. For each case:
the generic CRUST1.0 column with Vs from the data's own Wadati Vp/Vs, placed with its top at the mean station
elevation, and the same model under a slow near-surface layer (thickness 1, 2, 3 km; Vp 2.5, 3.5, 4.5 km/s).
Each candidate relocates the same pilot batch (the representative part of pilot.py events) with NonLinLoc
EDT_OT_WT. Reference-free measures, which an Agent can compute, are recorded for every candidate:
Wadati origin offset, travel-time intercept, signed S−P depth offset, mean station residual, median RMS,
share at the shallowest depth. The references are read only to score each candidate (time and depth bias
against the human-in-loop final), so that one can ask which measure, if any, picks the best candidate.

Usage: near_surface.py [case ...] [--workers 12]. Writes outputs/near_surface/<case>.json and a summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import replay_lib  # noqa: E402
from replay_lib import Run, relocate, score, write_subset  # noqa: E402
from catalog_checker.checks import DEFAULTS, Data, travel_time_fit, wadati_origin, depth_pileup, station_residuals  # noqa: E402
from catalog_checker.io import read_catalog, read_picks, read_stations  # noqa: E402
from catalog_checker.pilot import select_events  # noqa: E402
from catalog_checker.velocity import regional_models  # noqa: E402

RUNS = {"2011_prague_oklahoma": "tools/claude/glm-5.3/20261028T043719Z",
        "2018_kilauea_hawaii": "tools/claude/glm-5.3/20261029T084718Z",
        "2020_magna_utah": "tools/claude/glm-5.3/20261028T135931Z",
        "2017_maple_creek_yellowstone": "tools/claude/glm-5.3/20261028T220746Z",
        "2019_ridgecrest_california": "tools/claude/glm-5.3/20261029T203757Z",
        "2016_kaikoura_new_zealand": "tools/claude/glm-5.3/20261029T183933Z"}
OUT = HERE / "outputs/near_surface"


def candidates(d: Data, vpvs: float) -> tuple[dict[str, list], float]:
    """Models as (depth below the datum, vp, vs) rows; the datum is the mean station elevation (km)."""
    datum = float(d.stations.elevation_m.mean()) / 1000.0
    ev = d.events.dropna(subset=["latitude"])
    crust = regional_models(np.r_[d.stations.latitude, ev.latitude.median()], np.r_[d.stations.longitude, ev.longitude.median()])["crust1"]["rows"]
    base = [(max(z + datum, 0.0), vp, vp / vpvs) for z, vp, _ in crust]  # tops below the datum
    base[0] = (0.0, base[0][1], base[0][2])
    base = sorted({r[0]: r for r in base}.values())
    out = {"generic (CRUST1.0)": base}
    for h in (1.0, 2.0, 3.0):
        for vp in (2.5, 3.5, 4.5):
            rows = [(0.0, vp, vp / vpvs)] + [r for r in base if r[0] >= h]
            if rows[1][0] > h:  # the base velocity at depth h continues below the slow layer
                below = [r for r in base if r[0] < h][-1]
                rows.insert(1, (h, below[1], below[2]))
            out[f"slow top {h:g} km, Vp {vp:g}"] = rows
    return out, datum


def signed_sp_depth(d: Data) -> float | None:
    """The checker's S−P depth offset with its sign (the report hides the sign below the limit)."""
    p = d.picks
    pp = p[p.phase == "P"].groupby(["event_id", "station_id"]).agg(tp=("time", "min"), epi=("epi_km", "first"), dz=("dz_km", "first"))
    ss = p[p.phase == "S"].groupby(["event_id", "station_id"]).time.min().rename("ts")
    pairs = pp.join(ss, how="inner").reset_index()
    pairs = pairs[np.isfinite(pairs.epi) & np.isfinite(pairs.dz) & (pairs.dz > 0)]
    pairs["sp"] = pairs.ts - pairs.tp
    pairs = pairs[pairs.sp > 0]
    far = pairs[pairs.epi > 3 * pairs.dz]
    if len(far) < 50:
        return None
    k = float(np.median(far.epi / far.sp))
    near = pairs[pairs.epi < pairs.dz].copy()
    near = near[k * near.sp > near.epi]
    near["z_sp"] = np.sqrt((k * near.sp) ** 2 - near.epi ** 2)
    per = near.groupby("event_id").apply(lambda g: float(np.median(g.z_sp - g.dz)))
    return round(float(np.median(per)), 3) if len(per) >= 10 else None


def measures(cat: Path, picks: Path, run: Run, loc: pd.DataFrame) -> dict:
    d = Data(read_catalog(cat), read_picks(picks), read_stations(run.stations))
    c = dict(DEFAULTS)
    off, spread, w = wadati_origin(d, c)
    tt, fit = travel_time_fit(d, c)
    st = station_residuals(d, c, fit)
    per = (st[1].details or {}).get("per_station", {})
    pile = depth_pileup(d, c)
    return {"wadati_origin_offset_s": off.measured, "wadati_spread_s": spread.measured,
            "travel_time_intercept_s": tt.measured, "sp_depth_offset_km": signed_sp_depth(d),
            "mean_station_residual_s": round(float(np.mean([v["median_residual_s"] for v in per.values()])), 3) if per else None,
            "median_rms_s": round(float(loc.rms_s.median()), 3) if len(loc) else None,
            "share_at_edges": pile[1].measured, "located": int(len(loc))}


def run_case(case: str, workers: int) -> dict:
    run = Run(case, RUNS[case])
    d = run.data()
    w = wadati_origin(d, dict(DEFAULTS))[2]
    vpvs = float(np.median(w.vpvs)) if len(w) else 1.73
    ids = select_events(d.events, d.picks, {"events": 500})["representative"]
    base_dir = OUT / case
    sub_cat, sub_picks = write_subset(run, ids, base_dir / "subset")
    models, datum = candidates(d, vpvs)
    rows_out = {}
    for name, rows in models.items():
        key = name.replace(" ", "_").replace(",", "").replace("(", "").replace(")", "").replace(".", "")
        mdir = base_dir / key
        mdir.mkdir(parents=True, exist_ok=True)
        (mdir / "model.txt").write_text("".join(f"{z:.3f} {a:.3f} {b:.3f}\n" for z, a, b in rows))
        spec = {"type": "relocate", "model": "file", "path": str(mdir / "model.txt"), "file_reference_km": datum,
                "layering": "step", "datum_km": datum, "usage": "expert"}
        loc = relocate(run, spec, mdir / "relocation", ids, workers)
        raw = pd.read_csv(sub_cat, dtype=str, keep_default_na=False)
        new = replay_lib.apply_relocation(raw, loc, "drop")
        new.to_csv(mdir / "catalog.csv", index=False)
        m = measures(mdir / "catalog.csv", sub_picks, run, loc)
        s = score(run, mdir / "catalog.csv")["values"]
        rows_out[name] = {"agent_view": m, "truth": {"dt_s": s["time_bias_final_s"], "dz_km": s["dz_final_km"],
                                                     "shift_km": s["shift_final_km"]}}
        print(case, name, m, rows_out[name]["truth"], flush=True)
    res = {"case": case, "run": RUNS[case], "vpvs": round(vpvs, 3), "datum_km": round(datum, 3), "events": len(ids), "candidates": rows_out}
    (OUT / f"{case}.json").write_text(json.dumps(res, indent=1, default=float))
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*", default=list(RUNS))
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for case in a.cases:
        run_case(case, a.workers)


if __name__ == "__main__":
    main()
