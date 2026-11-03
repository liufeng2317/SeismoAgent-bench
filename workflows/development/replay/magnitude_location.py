#!/usr/bin/env python3
"""Does a location error compress local magnitudes? Offline test.

For a sample of events matched to the case's magnitude reference (spread evenly over the reference magnitude),
the Wood-Anderson amplitudes are measured once from the waveforms (as ``magnitude_scale.py`` ``default``) and
standard ML is computed twice: with the hypocentral distances of the run's own locations, and with those of the
human-in-loop final locations of the same events. The slope and median offset of (ML − reference) against the
reference are reported for both, next to the run's catalog magnitudes. Usage: magnitude_location.py CASE RUN.
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
import replay_lib  # noqa: E402,F401  (sets sys.path)
from replay_lib import ROOT, Run  # noqa: E402
from magnitude_scale import amplitudes, slope  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.case import load_case  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.matching import correspond  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.tables import Population, read_candidate_catalog  # noqa: E402
from catalog_checker.magnitude_recompute import _inventory, standard_ml  # noqa: E402
from catalog_checker.waveforms import file_index  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("run")
    ap.add_argument("--events", type=int, default=300)
    a = ap.parse_args()
    run = Run(a.case, a.run)
    case = load_case(ROOT / "workflows/tasks" / a.case)
    ref, final = case.refs[case.primary["magnitude"]], case.expert["final"]
    events, _ = read_candidate_catalog(run.catalog)
    cand = Population(key="candidate", events=events, depth_known=True)
    pr, pf = correspond(cand, ref)["pairs"], correspond(cand, final)["pairs"]
    m = pd.DataFrame({"event_id": cand.events.event_id.to_numpy()[pr.a], "ref": ref.events.magnitude.to_numpy()[pr.b],
                      "agent": cand.events.magnitude.to_numpy()[pr.a]}).dropna(subset=["ref"])
    fin = pd.DataFrame({"event_id": cand.events.event_id.to_numpy()[pf.a],
                        "f_lat": final.events.latitude.to_numpy()[pf.b], "f_lon": final.events.longitude.to_numpy()[pf.b],
                        "f_depth": final.events.depth_km.to_numpy()[pf.b]})
    m = m.merge(fin, on="event_id").sort_values("ref")
    m = m.iloc[np.unique(np.linspace(0, len(m) - 1, min(a.events, len(m))).round().astype(int))]
    d = run.data()
    ev = d.events[d.events.event_id.isin(m.event_id)]
    amps = amplitudes(run, ev, d.picks, file_index(run.waveforms), _inventory(run.stations))
    amps = amps[np.isfinite(amps["default"]) & (amps["default"] > 0)]
    st = d.stations.set_index("station_id")
    x = amps.merge(m[["event_id", "f_lat", "f_lon", "f_depth"]], on="event_id")
    s = st.loc[x.station_id]
    epi = np.hypot((x.f_lat.to_numpy() - s.latitude.to_numpy()) * 111.195,
                   (x.f_lon.to_numpy() - s.longitude.to_numpy()) * 111.195 * np.cos(np.radians(x.f_lat.to_numpy())))
    x["r_final"] = np.hypot(epi, x.f_depth.to_numpy() + s.elevation_m.to_numpy() / 1000.0)
    out = {"case": a.case, "run": a.run, "events": int(len(m)), "records": int(len(x)),
           "median_hypocentral_change_km": round(float(np.median(x.r - x.r_final)), 3),
           "agent_catalog": dict(zip(("slope", "median_offset"), slope(m.agent.to_numpy(), m.ref.to_numpy())))}
    for label, col in (("run_locations", "r"), ("final_locations", "r_final")):
        x["ml"] = standard_ml(x["default"], x[col])
        ml = m.event_id.map(x.groupby("event_id").ml.median()).to_numpy()
        out[label] = dict(zip(("slope", "median_offset"), slope(ml, m.ref.to_numpy())))
    path = HERE / "outputs/magnitude_location" / f"{a.case}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
