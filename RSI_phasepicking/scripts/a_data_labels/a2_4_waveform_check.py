"""a2: check the first-batch waveforms against the reference picks.

Per event: stations with data, channel families, sampling rates, gaps, and the
share of manual picks whose station has data covering the pick time. Plots a
distance-ordered record section (vertical channel; HH, else EH, else HN;
zero-phase band-pass) with manual (solid) and automatic (dashed) P/S picks for
--n-plots events spread over the batch.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from obspy import UTCDateTime, read

from a1_2_candidate_regions import dist_km
from paths import DATA, RES_A

FAMILY_ORDER = ["HH", "EH", "HN"]


def vertical(stream, station):
    net, sta = station.split(".")
    for fam in FAMILY_ORDER:
        sel = stream.select(network=net, station=sta, channel=f"{fam}Z")
        if len(sel):
            locs = sorted({tr.stats.location for tr in sel})
            return sel.select(location=locs[0]).merge(fill_value=0)[0]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", default="socal_r2")
    ap.add_argument("--n-plots", type=int, default=3)
    ap.add_argument("--freqmin", type=float, default=1.0)
    ap.add_argument("--freqmax", type=float, default=20.0)
    args = ap.parse_args()
    batch = RES_A / "a1_first_batch"
    out = RES_A / "a2_labels" / "waveform_check"
    out.mkdir(parents=True, exist_ok=True)
    stations = pd.read_csv(batch / "stations.csv").set_index("station")
    picks = pd.read_csv(RES_A / "a2_labels" / "reference_picks_first_batch.csv")
    wdir = DATA / "waveforms" / "raw" / args.name

    rows = []
    for eid, g in picks.groupby("event_id"):
        path = wdir / f"{eid}.mseed"
        if not path.exists():
            rows.append(dict(event_id=eid, file=False))
            continue
        st = read(str(path))
        have = {f"{tr.stats.network}.{tr.stats.station}" for tr in st}
        gaps = st.get_gaps()
        covered = []
        for p in g[g["mode"] == "manual"].itertuples():
            net, sta = p.station.split(".")
            t = UTCDateTime(p.time)
            covered.append(any(tr.stats.starttime <= t <= tr.stats.endtime
                               for tr in st.select(network=net, station=sta)))
        rows.append(dict(
            event_id=eid, file=True, magnitude=g.magnitude.iloc[0], stations_with_data=len(have),
            stations_missing=",".join(sorted(set(stations.index) - have)),
            families=",".join(sorted({tr.stats.channel[:2] for tr in st})),
            sampling_rates=",".join(str(r) for r in sorted({tr.stats.sampling_rate for tr in st})),
            traces=len(st), gaps=len(gaps), manual_picks=len(covered),
            manual_picks_with_data=float(np.mean(covered)) if covered else np.nan))
    cov = pd.DataFrame(rows)
    cov.to_csv(out / "coverage.csv", index=False)

    done = cov[cov.file].sort_values("event_id")
    idx = np.linspace(0, len(done) - 1, min(args.n_plots, len(done))).round().astype(int)
    for eid in done.event_id.iloc[idx]:
        g = picks[picks.event_id == eid]
        o = g.iloc[0]
        t0 = UTCDateTime(o.origin_time)
        st = read(str(wdir / f"{eid}.mseed"))
        st.detrend("demean")
        st.filter("bandpass", freqmin=args.freqmin, freqmax=args.freqmax, zerophase=True)
        sta_d = {s: dist_km(o.origin_lat, o.origin_lon, r.lat, r.lon) for s, r in stations.iterrows()}
        fig, ax = plt.subplots(figsize=(11, 9))
        for s, d in sorted(sta_d.items(), key=lambda x: x[1]):
            tr = vertical(st, s)
            if tr is None:
                continue
            t = tr.times() + (tr.stats.starttime - t0)
            y = tr.data / (np.abs(tr.data).max() or 1) * 2.0
            ax.plot(t, d + y, color="0.3", lw=0.4)
            ax.text(-4, d, f"{s} {tr.stats.channel}", fontsize=6, ha="right", va="center")
            for p in g[g.station == s].itertuples():
                tp = UTCDateTime(p.time) - t0
                ax.plot([tp, tp], [d - 2.5, d + 2.5], color="tab:blue" if p.phase == "P" else "tab:red",
                        lw=1.2, ls="-" if p.mode == "manual" else "--")
        ax.set_xlim(-5, 60)
        ax.set_xlabel("Time after catalog origin (s)")
        ax.set_ylabel("Epicentral distance (km)")
        ax.set_title(f"Event {eid}, M{o.magnitude} {o.magnitude_type}, {o.origin_time[:19]}; "
                     f"P blue, S red; solid manual, dashed automatic; {args.freqmin}-{args.freqmax} Hz")
        fig.tight_layout()
        fig.savefig(out / f"record_section_{eid}.png", dpi=130)
        plt.close(fig)

    print(cov.drop(columns=["stations_missing"]).describe().round(3).to_string())
    print("events without file:", int((~cov.file).sum()))


if __name__ == "__main__":
    main()
