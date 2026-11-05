#!/usr/bin/env python3
"""Do the locator's own residuals and uncertainties tell which events and stations are bad? An offline test.

Suggestion to test (2026-11-05): absolute locators (NonLinLoc, HypoInverse) return P and S residuals per pick and an
uncertainty per event; residuals per station could screen bad stations, and the uncertainty could indicate location
errors. On the pilot batch of each formal tools run (300 events, the Agent's own picks), located with NonLinLoc
EDT_OT_WT under two models (the generic CRUST1.0 column the Agent would start from, and the case's regional model):

- events: rank correlation of each diagnostic (sigma_h, sigma_z, RMS, azimuthal gap, number of phases) with the
  true error against the primary absolute-location reference (horizontal offset about the common shift, depth
  offset about the median), the area under the ROC curve for the bad events (horizontal error > max(2 km, 3 x the
  median)), and the effect of removing the 10 % most uncertain events against removing 10 % at random;
- stations: per station and phase, the median and the spread (MAD) of the residuals; stations whose spread is
  > max(0.2 s, 3 x the network median spread) are flagged, the batch is relocated without them, and the result is
  compared with removing the same number of random stations (3 draws).

The references are read only to score. Usage: locator_diagnostics.py [case ...] [--workers 8].
Writes outputs/locator_diagnostics/<case>.json.
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
import horizontal_shift as H  # noqa: E402
from near_surface import RUNS  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.case import load_case  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.matching import correspond  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.metrics import local_xyz  # noqa: E402

OUT = HERE / "outputs/locator_diagnostics"
NS, HS = HERE / "outputs/near_surface", HERE / "outputs/horizontal_shift"
DIAG = ["sigma_h_km", "sigma_depth_km", "rms_s", "gap_deg", "n_phases"]


def nll_events(d: Path) -> pd.DataFrame:
    ev = pd.read_csv(d / "nll/events.csv")
    ev = ev[ev.status == "LOCATED"].copy()
    ev["sigma_h_km"] = np.hypot(ev.sigma_x_km, ev.sigma_y_km)
    return ev


def pick_ref(pop, c):
    """The primary absolute-location reference, or, with fewer than 30 pairs, the located reference (L or S role)
    with the most pairs: the error about the common shift measures relative quality, which an S reference supports."""
    best = (c.primary["location"], len(correspond(pop, c.refs[c.primary["location"]])["pairs"]))
    if best[1] >= 30:
        return best[0]
    for k, r in c.refs.items():
        if r.events.latitude.notna().sum() > 100 and ("L" in r.roles or "S" in r.roles):
            n = len(correspond(pop, r)["pairs"])
            if n > best[1]:
                best = (k, n)
    return best[0]


def errors(ev: pd.DataFrame, loc: pd.DataFrame, c) -> pd.DataFrame:
    """Per event: horizontal error about the common shift and depth error about the median, against pick_ref."""
    pop = H.population(loc)
    ref = c.refs[pick_ref(pop, c)]
    pr = correspond(pop, ref)["pairs"]
    a, b = pop.events.iloc[pr.a], ref.events.iloc[pr.b]
    xa, xb = local_xyz(a, c.center), local_xyz(b, c.center)
    off = xa[:, :2] - xb[:, :2]
    off = off - np.median(off, axis=0)
    dz = a.depth_km.to_numpy() - b.depth_km.to_numpy()
    out = pd.DataFrame({"event_id": a.event_id.to_numpy(), "err_h_km": np.hypot(*off.T),
                        "err_z_km": np.abs(dz - np.nanmedian(dz))})
    return out.merge(ev[["event_id"] + DIAG], on="event_id")


def auc(score: np.ndarray, bad: np.ndarray) -> float | None:
    if bad.sum() == 0 or (~bad).sum() == 0:
        return None
    r = pd.Series(score).rank().to_numpy()
    return round(float((r[bad].sum() - bad.sum() * (bad.sum() + 1) / 2) / (bad.sum() * (~bad).sum())), 3)


def event_level(e: pd.DataFrame) -> dict:
    thr = max(2.0, 3 * float(e.err_h_km.median()))
    bad = (e.err_h_km > thr).to_numpy()
    out = {"pairs": int(len(e)), "bad_threshold_km": round(thr, 2), "bad": int(bad.sum()), "diagnostics": {}}
    for d in DIAG:
        x = e[d].to_numpy(dtype=float)
        sign = -1 if d == "n_phases" else 1  # fewer phases = worse
        out["diagnostics"][d] = {"spearman_err_h": round(float(pd.Series(sign * x).corr(e.err_h_km, method="spearman")), 3),
                                 "spearman_err_z": round(float(pd.Series(sign * x).corr(e.err_z_km, method="spearman")), 3),
                                 "auc_bad": auc(sign * x, bad)}
    keep = e.sigma_h_km <= e.sigma_h_km.quantile(0.9)
    rng = np.random.default_rng(0)
    rand = [e.sample(frac=0.9, random_state=int(rng.integers(1e9))) for _ in range(200)]
    out["drop_10pct_most_uncertain"] = {"median_err_h_km": round(float(e[keep].err_h_km.median()), 3),
                                        "bad_share": round(float((e[keep].err_h_km > thr).mean()), 4)}
    out["drop_10pct_random"] = {"median_err_h_km": round(float(np.mean([r.err_h_km.median() for r in rand])), 3),
                                "bad_share": round(float(np.mean([(r.err_h_km > thr).mean() for r in rand])), 4)}
    out["all"] = {"median_err_h_km": round(float(e.err_h_km.median()), 3), "bad_share": round(float(bad.mean()), 4)}
    return out


def station_stats(arr: pd.DataFrame) -> pd.DataFrame:
    a = arr.dropna(subset=["residual_s"])
    g = a.groupby(["station_id", "phase"]).residual_s
    s = pd.DataFrame({"n": g.size(), "median_s": g.median(),
                      "mad_s": g.apply(lambda x: float(np.median(np.abs(x - np.median(x)))))}).reset_index()
    return s[s.n >= 10]


def run_case(case: str, workers: int) -> dict:
    c = load_case(ROOT_TASKS / case)
    res = {"case": case}
    for model in ("generic", "regional"):
        if model == "regional":
            d = HS / case / "expert_model"
            arr_in, st_in = pd.read_csv(d / "arrivals.csv"), pd.read_csv(d / "stations.csv")
            cfg = json.loads((d / "config.json").read_text())
            rows = np.loadtxt(d / "model.txt", ndmin=2)
        else:  # the near-surface replay's generic column, relocated here to get NonLinLoc's uncertainties
            src = NS / case / "generic_CRUST10/relocation"
            arr_in, st_in = pd.read_csv(src / "arrivals.csv"), pd.read_csv(src / "stations.csv")
            cfg = json.loads((src / "relocated_config.json").read_text())
            rows = np.loadtxt(src / "relocated_model.txt", ndmin=2)
            d = OUT / case / "generic"
        ref_elev, region = float(cfg["reference_elevation_km"]), {k: cfg["region"][k] for k in ("latitude", "longitude")}
        # rows are written by H.locate's _model_rows from "below sea level" rows: invert (tops below the datum + datum)
        model_rows = [(float(z) - ref_elev, float(vp), float(vs)) for z, vp, vs in rows]
        if model == "generic":
            H.locate(arr_in, st_in, model_rows, ref_elev, region, d, workers)
        ev = nll_events(d)
        loc = pd.read_csv(d / "located.csv") if (d / "located.csv").is_file() else H.locate(arr_in, st_in, model_rows, ref_elev, region, d, workers)
        e = errors(ev, loc, c)
        refkey = pick_ref(H.population(loc), c)
        out = {"located": int(len(ev)), "reference": refkey, "events": event_level(e)}
        st = station_stats(pd.read_csv(d / "nll/arrivals.csv"))
        net = float(st.mad_s.median()) if len(st) else 0.0
        bad_st = sorted(set(st.station_id[st.mad_s > max(0.2, 3 * net)]))
        out["stations"] = {"network_median_mad_s": round(net, 3), "flagged": bad_st,
                           "per_station": st.round(3).to_dict(orient="records")}
        if bad_st:
            def score(sub: str, drop: list[str]) -> dict:
                dd = OUT / case / f"{model}_{sub}"
                lc = H.locate(arr_in[~arr_in.station_id.isin(drop)], st_in[~st_in.station_id.isin(drop)], model_rows, ref_elev,
                              region, dd, workers)
                s = H.shift(H.population(lc), c.refs[refkey], c.center)
                return {"dropped": drop, "located": int(len(lc)), "scatter_km": s["scatter_km"], "shift_km": s["shift_km"],
                        "dz_km": s["dz_km"], "pairs": s["pairs"]}
            base = H.shift(H.population(loc), c.refs[refkey], c.center)
            others = sorted(set(st.station_id) - set(bad_st))
            rng = np.random.default_rng(1)
            out["station_screening"] = {"all_stations": {"scatter_km": base["scatter_km"], "shift_km": base["shift_km"],
                                                         "dz_km": base["dz_km"], "pairs": base["pairs"]},
                                        "without_flagged": score("screened", bad_st),
                                        "without_random": [score(f"random{k}", list(rng.choice(others, len(bad_st), replace=False)))
                                                           for k in range(3) if len(others) >= len(bad_st)]}
        res[model] = out
        print(case, model, json.dumps({"events": out["events"]["diagnostics"]["sigma_h_km"], "flagged": bad_st}), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{case}.json").write_text(json.dumps(res, indent=1, default=float, ensure_ascii=False))
    return res


ROOT_TASKS = H.ROOT / "workflows/tasks"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*", default=list(RUNS))
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    for case in a.cases:
        run_case(case, a.workers)


if __name__ == "__main__":
    main()
