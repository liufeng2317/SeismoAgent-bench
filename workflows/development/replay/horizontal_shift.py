#!/usr/bin/env python3
"""Where does the horizontal shift of the Agent's locations come from? A step-by-step swap on the pilot batch.

In three cases (Kaikoura, Magna, Maple) every generic or slow-top 1-D model left a common horizontal shift of
1.1-2.9 km against the human-in-loop final (near_surface.py). This replays the same pilot batch of each formal
tools run (outputs/near_surface/<case>/subset, 300 events) and replaces one component at a time, all located with
NonLinLoc EDT_OT_WT as in near_surface.py:

  generic          the Agent's picks, generic CRUST1.0 column (near_surface.py's candidate, reused)
  expert_model     the Agent's picks, the final's 1-D model and datum (hil_relocation/cases/<case>.yaml)
  expert_delays    + the final's NonLinLoc station delays, where the final's round has them
  hil_picks        the final's own picks of the same events (matched by the scorer), same model and delays:
                   reproduces the final if the setup is right, so expert_delays - hil_picks is the picks' share
  hil_picks_agent_stations  the same, restricted to the stations the Agent picked: the station set's share

For each step: the common shift (median east/north offset of matched pairs, the scorer's definition) against the
final and against the primary location reference, the depth bias and the pair count. The final's own shift against
the primary reference is printed with them (its frame). Analysis only; references are read to score each step.

Usage: horizontal_shift.py [case ...] [--workers 16]. Writes outputs/horizontal_shift/<case>.json.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import replay_lib  # noqa: E402
from replay_lib import ROOT, Run, _model_rows, _velocity_rows, LOCATE  # noqa: E402
from near_surface import RUNS  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.case import load_case  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.matching import correspond  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.metrics import location  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.tables import Population  # noqa: E402

OUT = HERE / "outputs/horizontal_shift"
NS = HERE / "outputs/near_surface"
HIL = ROOT / "workflows/development/hil_relocation/cases"
# NonLinLoc station delays of the round the final's picked events were located in
DELAYS = {"2011_prague_oklahoma": "expert/export/r5/04_locate_nonlinloc/full/station_delays.csv",
          "2016_kaikoura_new_zealand": "expert/export/r6/04_locate_nonlinloc/full/station_delays.csv",
          "2017_maple_creek_yellowstone": "expert/export/r9/04_locate_nonlinloc/full/station_delays.csv"}


def ts(s):
    return pd.to_datetime(s, utc=True, format="ISO8601")


def locate(arr: pd.DataFrame, st: pd.DataFrame, rows, ref_elev: float, region: dict, out: Path, workers: int,
           delays: Path | None = None) -> pd.DataFrame:
    """NonLinLoc EDT_OT_WT as replay_lib.relocate's expert usage; returns event_id, latitude, longitude, depth_bsl, t."""
    out.mkdir(parents=True, exist_ok=True)
    done = out / "located.csv"
    if done.is_file():
        return pd.read_csv(done)
    arr.to_csv(out / "arrivals.csv", index=False)
    st.to_csv(out / "stations.csv", index=False)
    cfg = {"reference_elevation_km": ref_elev, "velocity_layering": "step", "grid_depth_km": [-3.0, 35.0],
           "region": {**region, "depth_km": [0, 20]}, "location_method": "EDT_OT_WT", "pick_error_s": {"P": 0.1, "S": 0.2}}
    (out / "model.txt").write_text("".join(f"{z:.3f} {vp:.3f} {vs:.3f}\n" for z, vp, vs in _model_rows(rows, ref_elev)))
    (out / "config.json").write_text(json.dumps(cfg))
    cmd = [sys.executable, "-I", str(LOCATE), "--arrivals", str(out / "arrivals.csv"), "--stations", str(out / "stations.csv"),
           "--velocity-model", str(out / "model.txt"), "--config", str(out / "config.json"), "--output-dir", str(out / "nll"),
           "--workers", str(workers), "--quiet", "--overwrite"]
    if delays is not None:  # only the stations of this step (locate.py rejects delays of absent stations)
        d = pd.read_csv(delays)
        d[d.station_id.isin(set(st.station_id))].to_csv(out / "delays.csv", index=False)
        cmd += ["--station-delays", str(out / "delays.csv")]
    subprocess.run(cmd, check=False, capture_output=True)
    ev = pd.read_csv(out / "nll/events.csv")
    ev = ev[ev.status == "LOCATED"]
    loc = pd.DataFrame({"event_id": ev.event_id, "latitude": ev.latitude, "longitude": ev.longitude,
                        "depth_bsl": ev.depth_km - ref_elev, "t": (ts(ev.origin_time_utc) - pd.Timestamp(0, tz="UTC")).dt.total_seconds()})
    loc.to_csv(done, index=False)
    return loc


def population(loc: pd.DataFrame) -> Population:
    e = pd.DataFrame({"event_id": loc.event_id, "time": loc.t, "latitude": loc.latitude, "longitude": loc.longitude,
                      "depth_km": loc.depth_bsl, "magnitude": np.nan}).reset_index(drop=True)
    return Population(key="c", events=e, depth_known=True)


def shift(pop: Population, ref: Population, center) -> dict:
    pr = correspond(pop, ref)["pairs"]
    loc = location(pop, ref, pr, center)
    a, b = pop.events.iloc[pr.a], ref.events.iloc[pr.b]
    dz = a.depth_km.to_numpy() - b.depth_km.to_numpy()
    return {"pairs": loc.get("pairs", 0), "east_km": loc.get("shift_east_km"), "north_km": loc.get("shift_north_km"),
            "shift_km": loc.get("shift_km"), "scatter_km": loc.get("scatter_median_km"),
            "dz_km": round(float(np.nanmedian(dz)), 3) if len(dz) else None}


def run_case(case: str, workers: int) -> dict:
    task = ROOT / "workflows/tasks" / case
    c = load_case(task)
    final = c.expert["final"]
    prim_key = c.primary["location"]
    prim = c.refs[prim_key]
    run = Run(case, RUNS[case])
    hil = yaml.safe_load((HIL / f"{case}.yaml").read_text())
    datum = float(hil["datum_km"])
    rows = _velocity_rows(run, None, {"model": hil["model"]["key"], "layering": hil["model"].get("layering", "step"),
                                      "datum_km": datum})
    base = NS / case
    sub = pd.read_csv(base / "subset/catalog.csv")
    ids = set(sub.event_id)
    lat, lon = np.nanpercentile(sub.latitude.astype(float), [0.1, 99.9]), np.nanpercentile(sub.longitude.astype(float), [0.1, 99.9])
    region = {"latitude": [float(lat[0] - 0.18), float(lat[1] + 0.18)], "longitude": [float(lon[0] - 0.18), float(lon[1] + 0.18)]}
    a_arr = pd.read_csv(base / "generic_CRUST10/relocation/arrivals.csv")
    a_st = pd.read_csv(base / "generic_CRUST10/relocation/stations.csv")
    out = OUT / case
    steps = {}
    g = pd.read_csv(base / "generic_CRUST10/relocation/relocated_events.csv")
    steps["generic"] = g[["event_id", "latitude", "longitude", "depth_bsl", "t"]]
    steps["expert_model"] = locate(a_arr, a_st, rows, datum, region, out / "expert_model", workers)
    delays = None
    if case in DELAYS:
        d = pd.read_csv(task / DELAYS[case])
        d["station_id"] = d.instrument_id.str.split(".").str[:2].str.join(".")
        delays = out / "expert_delays.csv"
        out.mkdir(parents=True, exist_ok=True)
        d[["station_id", "phase", "delay_s", "n_picks"]].drop_duplicates(["station_id", "phase"]).to_csv(delays, index=False)
        steps["expert_delays"] = locate(a_arr, a_st, rows, datum, region, out / "expert_delays", workers, delays)
    # the final's own picks of the matched events (hil_relocation inputs: located picks, |residual| <= 0.5 s)
    last = steps.get("expert_delays", steps["expert_model"])
    pr = correspond(population(last), final)["pairs"]
    fid = final.events.event_id.to_numpy()[pr.b] if "event_id" in final.events else None
    hin = task / "expert/export" / hil["new_round"] / "68_cc_relocation"
    h_arr = pd.read_csv(hin / "arrivals.csv")
    h_arr = h_arr[h_arr.source.eq("pick") & h_arr.event_id.isin(set(fid if fid is not None else []))]
    h_st = pd.read_csv(hin / "stations.csv")
    res_extra = {"hil_events_with_picks": int(h_arr.event_id.nunique()), "matched_pairs": int(len(pr)),
                 "agent_stations": int(a_arr.station_id.nunique()), "hil_stations": int(h_st.station_id.nunique()),
                 "shared_stations": int(len(set(a_arr.station_id) & set(h_st.station_id)))}
    if len(h_arr):
        cols = ["event_id", "station_id", "phase", "time_utc"]
        h = h_arr[cols].assign(pick_id=np.arange(len(h_arr)).astype(str))
        steps["hil_picks"] = locate(h, h_st, rows, datum, region, out / "hil_picks", workers, delays)
        hs = h[h.station_id.isin(set(a_arr.station_id))]
        steps["hil_picks_agent_stations"] = locate(hs, h_st[h_st.station_id.isin(set(hs.station_id))], rows, datum, region,
                                                   out / "hil_picks_agent_stations", workers, delays)
    res = {"case": case, "run": RUNS[case], "model": hil["model"]["key"], "datum_km": datum, "primary": prim_key,
           "delays": DELAYS.get(case), **res_extra, "final_vs_primary": shift(final, prim, c.center), "steps": {}}
    for name, loc in steps.items():
        p = population(loc)
        res["steps"][name] = {"located": int(len(loc)), "vs_final": shift(p, final, c.center),
                              "vs_primary": shift(p, prim, c.center)}
        print(case, name, res["steps"][name], flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{case}.json").write_text(json.dumps(res, indent=1, default=float))
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*", default=list(RUNS))
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    for case in a.cases:
        run_case(case, a.workers)


if __name__ == "__main__":
    main()
