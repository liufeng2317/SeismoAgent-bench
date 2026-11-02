#!/usr/bin/env python3
"""Why do recomputed local magnitudes come out compressed (negative slope against the reference)? Offline test.

For a sample of events matched to the case's magnitude reference (spread evenly over the reference magnitude),
standard ML (IASPEI, Wood-Anderson, half peak-to-peak, median of horizontal channels) is recomputed from the
waveforms with one processing choice changed at a time:

- ``default``: the checker's recompute (window 1 s before the first pick to S + max(3 s, 0.5 (S − origin)) + 2 s;
  pre-filter 0.05–0.1 Hz to 0.4–0.45 fs);
- ``highpass1``: as default plus a 1 Hz high-pass on the Wood-Anderson record;
- ``snr3``: as default, keeping only records whose amplitude is ≥ 3× the same measure in the 10 s before the window;
- ``long``: window to S + max(30 s, 4 (S − P));
- ``near100``: as default, stations within 100 km only.

For each variant: the median offset and the slope of (ML − reference) against the reference, as the scorer computes
it (``dimensions.strength``); the human-in-loop final's own slope on the same events is the baseline, since errors
in the reference alone make the slope negative. Usage: magnitude_scale.py CASE RUN [--events 300].
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
from SeismoAgentBench.scoring.catalog_metrics.case import load_case  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.matching import correspond  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.tables import Population, read_candidate_catalog  # noqa: E402
from catalog_checker.magnitude_recompute import WA_IASPEI, _inventory, half_peak_to_peak, standard_ml  # noqa: E402
from catalog_checker.waveforms import file_index  # noqa: E402

VARIANTS = ("default", "highpass1", "snr3", "long", "near100")


def amplitudes(run: Run, ev: pd.DataFrame, picks: pd.DataFrame, index: pd.DataFrame, inv) -> pd.DataFrame:
    from obspy import UTCDateTime, read
    rows = []
    for eid, sp in picks[picks.event_id.isin(ev.event_id)].groupby("event_id"):
        e = ev.set_index("event_id").loc[eid]
        for sta, g in sp.groupby("station_id"):
            tp = g[g.phase == "P"].time.min()
            ts = g[g.phase == "S"].time.min()
            first = tp if np.isfinite(tp) else ts
            last = ts if np.isfinite(ts) else tp + 0.7 * (tp - e.time)
            t0, t1 = first - 1.0, last + max(3.0, 0.5 * (last - e.time)) + 2.0
            t1_long = last + max(30.0, 4.0 * ((ts - tp) if np.isfinite(tp) and np.isfinite(ts) else (last - e.time)))
            r = float(g.hyp_km.iloc[0])
            files = index[(index.station_id == sta) & index.component.isin(list("NE12")) & (index.file_start < t1_long) & (index.file_end > t0 - 12)]
            for seed, f in files.groupby("seed_id"):
                try:
                    st = read(str(f.file.iloc[0]), starttime=UTCDateTime(t0 - 40), endtime=UTCDateTime(t1_long + 30))
                    st.merge(fill_value=0)
                    tr = st[0]
                    tr.detrend("demean"); tr.detrend("linear")
                    fs = tr.stats.sampling_rate
                    tr.remove_response(inventory=inv, output="DISP", pre_filt=(0.05, 0.1, 0.4 * fs, 0.45 * fs), water_level=60)
                    tr.simulate(paz_simulate=WA_IASPEI, simulate_sensitivity=False)
                    hp = tr.copy().filter("highpass", freq=1.0, corners=4, zerophase=True)
                    def amp(trace, a, b):
                        return half_peak_to_peak(trace.slice(UTCDateTime(a), UTCDateTime(b)).data * 1e9)
                    rows.append({"event_id": eid, "station_id": sta, "seed": seed, "r": r,
                                 "default": amp(tr, t0, t1), "highpass1": amp(hp, t0, t1), "long": amp(tr, t0, t1_long),
                                 "noise": amp(tr, t0 - 10.0, t0)})
                except Exception:
                    continue
    return pd.DataFrame(rows)


def slope(m: np.ndarray, ref: np.ndarray) -> tuple[float | None, float | None]:
    ok = np.isfinite(m) & np.isfinite(ref)
    if ok.sum() < 20:
        return None, None
    dm = m[ok] - ref[ok]
    return round(float(np.polyfit(ref[ok], dm, 1)[0]), 3), round(float(np.median(dm)), 3)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("run")
    ap.add_argument("--events", type=int, default=300)
    a = ap.parse_args()
    run = Run(a.case, a.run)
    case = load_case(ROOT / "workflows/tasks" / a.case)
    ref = case.refs[case.primary["magnitude"]]
    events, _ = read_candidate_catalog(run.catalog)
    cand = Population(key="candidate", events=events, depth_known=True)
    pairs = correspond(cand, ref)["pairs"]
    m = pd.DataFrame({"event_id": cand.events.event_id.to_numpy()[pairs.a], "ref": ref.events.magnitude.to_numpy()[pairs.b],
                      "agent": cand.events.magnitude.to_numpy()[pairs.a]}).dropna(subset=["ref"])
    final = case.expert.get("final")
    fpairs = correspond(final, ref)["pairs"]
    fslope = slope(final.events.magnitude.to_numpy()[fpairs.a], ref.events.magnitude.to_numpy()[fpairs.b])
    m = m.sort_values("ref")
    m = m.iloc[np.unique(np.linspace(0, len(m) - 1, min(a.events, len(m))).round().astype(int))]
    d = run.data()
    ev = d.events[d.events.event_id.isin(m.event_id)]
    amps = amplitudes(run, ev, d.picks, file_index(run.waveforms), _inventory(run.stations))
    out = {"case": a.case, "run": a.run, "events": int(len(m)), "records": int(len(amps)),
           "final_vs_reference": {"slope": fslope[0], "median_offset": fslope[1]},
           "agent_catalog_vs_reference": dict(zip(("slope", "median_offset"), slope(m.agent.to_numpy(), m.ref.to_numpy())))}
    for v in VARIANTS:
        col = {"snr3": "default", "near100": "default"}.get(v, v)
        x = amps[np.isfinite(amps[col]) & (amps[col] > 0)].copy()
        if v == "snr3":
            x = x[x[col] >= 3 * x.noise]
        if v == "near100":
            x = x[x.r <= 100]
        x["ml"] = standard_ml(x[col], x.r)
        ml = x.groupby("event_id").ml.median()
        s, med = slope(m.event_id.map(ml).to_numpy(), m.ref.to_numpy())
        out[v] = {"slope": s, "median_offset": med, "events_with_ml": int(ml.reindex(m.event_id).notna().sum())}
    path = HERE / "outputs/magnitude_scale" / f"{a.case}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
