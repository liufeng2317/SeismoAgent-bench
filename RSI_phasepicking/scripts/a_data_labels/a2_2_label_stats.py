"""a2: label statistics for the candidate regions.

Parses the SCEDC QuakeML of results/a_data_labels/a2_labels/region_events.csv and tabulates,
per pick: phase, evaluationMode (manual/automatic), onset, polarity, time
uncertainty and the matching Hypoinverse weight code, epicentral distance and
its rank within the event. Summaries: per region; per region x year; per
magnitude bin; by distance rank; manual P picks per event. Picks whose
automatic times may come from PhaseNet are flagged (SCSN hypoPN: M<3 from
2023-11-06, and the hypoPN test dates; see docs/design.md section 2).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py
import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from obspy import read_events

from paths import CATALOGS_RAW, RES_A

QUAKEML = CATALOGS_RAW / "scedc_quakeml"
WEIGHT_CODES = {0: 0.03, 1: 0.06, 2: 0.15, 3: 0.30}  # SCSN QuakeML uncertainty (s) per code
HYPOPN_START = pd.Timestamp("2023-11-06")
# Tepp et al. 2025 hypoPN tests. "2020-04-12/15" is read conservatively as the
# whole range; tests 5 (2023-11-08..17) and 6 (2024-01..02) are flagged for all
# magnitudes. All of 2020-01 is flagged separately below.
HYPOPN_TEST_DAYS = (["2020-04-06", "2020-04-07", "2020-04-12", "2020-04-13", "2020-04-14", "2020-04-15",
                     "2023-09-29"] + [f"2023-11-{d:02d}" for d in range(8, 18)])
HYPOPN_TEST_MONTHS = ["2020-01", "2024-01", "2024-02"]
MAG_BINS = [2.5, 3.0, 4.0, 10.0]
RANK_BINS = [0, 5, 10, 20, 1000]


def weight_code(unc):
    if unc is None or np.isnan(unc):
        return np.nan
    return min(WEIGHT_CODES, key=lambda k: abs(WEIGHT_CODES[k] - unc))


def parse_event(path):
    cat = read_events(str(path))
    ev = cat[0]
    org = ev.preferred_origin() or ev.origins[0]
    picks = {p.resource_id.id: p for p in ev.picks}
    rows = []
    for arr in org.arrivals:
        p = picks.get(arr.pick_id.id)
        if p is None:
            continue
        unc = p.time_errors.uncertainty if p.time_errors else None
        rows.append(dict(
            station=f"{p.waveform_id.network_code}.{p.waveform_id.station_code}",
            phase=(arr.phase or p.phase_hint or "")[:1].upper(),
            mode=p.evaluation_mode or "",
            onset=p.onset or "",
            polarity=p.polarity or "",
            uncertainty_s=unc,
            distance_km=arr.distance * 111.19 if arr.distance is not None else np.nan,
            time_weight=arr.time_weight,
        ))
    gap = org.quality.azimuthal_gap if org.quality else None
    info = dict(origin_status=org.evaluation_status or "", origin_mode=org.evaluation_mode or "", azimuthal_gap=gap)
    return rows, info


def share(s):
    return float((s == "manual").mean()) if len(s) else np.nan


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(RES_A / "a2_labels"))
    args = ap.parse_args()
    out = pd.io.common.Path(args.out)
    events = pd.read_csv(out / "region_events.csv", parse_dates=["time"])

    pick_rows, ev_rows = [], []
    for eid, g in events.groupby("event_id"):
        path = QUAKEML / f"{eid}.xml"
        if not path.exists():
            continue
        rows, info = parse_event(path)
        e = g.iloc[0]
        ev_rows.append(dict(event_id=eid, time=e.time, mag=e.mag, lat=e.lat, lon=e.lon,
                            regions=",".join(sorted(g.region)), **info))
        for r in rows:
            for region in g.region:
                pick_rows.append(dict(event_id=eid, region=region, time=e.time, mag=e.mag, **r))
    picks = pd.DataFrame(pick_rows)
    evs = pd.DataFrame(ev_rows)
    picks["weight_code"] = picks.uncertainty_s.apply(weight_code)
    picks["year"] = picks.time.dt.year
    picks["mag_bin"] = pd.cut(picks.mag, MAG_BINS, right=False)
    picks["rank"] = picks.groupby(["event_id", "region", "phase"]).distance_km.rank(method="first")
    picks["rank_bin"] = pd.cut(picks["rank"], RANK_BINS, labels=["1-5", "6-10", "11-20", ">20"])
    day = picks.time.dt.strftime("%Y-%m-%d")
    picks["phasenet_period"] = ((picks.time >= HYPOPN_START) & (picks.mag < 3)) | day.isin(HYPOPN_TEST_DAYS) \
        | picks.time.dt.strftime("%Y-%m").isin(HYPOPN_TEST_MONTHS)
    picks.to_csv(out / "picks.csv", index=False)
    evs.to_csv(out / "events.csv", index=False)

    P, S = picks[picks.phase == "P"], picks[picks.phase == "S"]
    per_ev = P[P["mode"] == "manual"].groupby(["region", "event_id"]).size()
    summ = []
    for reg, g in picks.groupby("region"):
        gp, gs = g[g.phase == "P"], g[g.phase == "S"]
        mp = gp[gp["mode"] == "manual"]
        n_ev = g.event_id.nunique()
        mpe = per_ev.loc[reg] if reg in per_ev.index.get_level_values(0) else pd.Series(dtype=float)
        summ.append(dict(
            region=reg, events=n_ev, picks_per_event=round(len(g) / n_ev, 1),
            P=len(gp), S=len(gs), S_per_P=round(len(gs) / max(len(gp), 1), 2),
            manual_share_P=round(share(gp["mode"]), 3), manual_share_S=round(share(gs["mode"]), 3),
            manual_share_P_outside_phasenet_period=round(share(gp[~gp.phasenet_period]["mode"]), 3),
            manual_P_impulsive_share=round(float((mp.onset == "impulsive").mean()), 3) if len(mp) else np.nan,
            manual_P_with_polarity=round(float(mp.polarity.isin(["positive", "negative"]).mean()), 3) if len(mp) else np.nan,
            manual_P_per_event_median=float(mpe.median()) if len(mpe) else 0.0,
            events_with_ge10_manual_P=int((mpe >= 10).sum()),
            median_azimuthal_gap=float(evs[evs.regions.str.contains(reg)].azimuthal_gap.median()),
        ))
    summ = pd.DataFrame(summ)
    summ.to_csv(out / "region_summary.csv", index=False)

    by_year = P.groupby(["region", "year"])["mode"].apply(share).unstack(0)
    by_mag = P.groupby(["region", "mag_bin"], observed=False)["mode"].apply(share).unstack(0)
    by_rank = P.groupby(["region", "rank_bin"], observed=False)["mode"].apply(share).unstack(0)
    wc = P[P["mode"] == "manual"].groupby(["region", "weight_code"]).size().unstack(1).fillna(0).astype(int)
    by_year.to_csv(out / "manual_share_P_by_year.csv")
    by_mag.to_csv(out / "manual_share_P_by_mag.csv")
    by_rank.to_csv(out / "manual_share_P_by_distance_rank.csv")
    wc.to_csv(out / "manual_P_weight_codes.csv")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    for ax, tab, title, xlabel in [(axes[0], by_year, "By year", "Year"),
                                   (axes[1], by_mag, "By magnitude", "Magnitude bin"),
                                   (axes[2], by_rank, "By distance rank in the event", "Station rank (nearest = 1)")]:
        for reg in tab.columns:
            ax.plot([str(x) for x in tab.index], tab[reg].values, marker="o", label=reg)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Share of P picks that are manual")
    axes[0].set_ylim(0, 1.02)
    axes[0].legend(fontsize=8)
    fig.suptitle("Manual share of P picks, SCEDC M≥2.5 events in candidate regions")
    fig.tight_layout()
    fig.savefig(out / "manual_share_P.png", dpi=150)

    fig, ax = plt.subplots(figsize=(7, 4))
    for reg in sorted(per_ev.index.get_level_values(0).unique()):
        v = per_ev.loc[reg].values
        ax.hist(v, bins=np.arange(0, max(v.max(), 10) + 2, 2), histtype="step", lw=1.5, label=f"{reg} (n={len(v)})")
    ax.set_xlabel("Manual P picks per event")
    ax.set_ylabel("Events")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "manual_P_per_event.png", dpi=150)

    print(summ.to_string(index=False))
    print("\nmanual P share by year\n", by_year.round(2).to_string())
    print("\nmanual P share by magnitude\n", by_mag.round(2).to_string())
    print("\nmanual P share by distance rank\n", by_rank.round(2).to_string())
    print("\nmanual P weight codes\n", wc.to_string())
    (out / "summary.json").write_text(json.dumps(dict(events_parsed=len(evs), picks=len(picks)), indent=1))


if __name__ == "__main__":
    main()
