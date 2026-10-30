"""Figures of the association and location stages, each with the numbers it shows."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .checks import Data


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _utc(t: float) -> str:
    return f"{pd.Timestamp(t, unit='s', tz='UTC'):%Y-%m-%dT%H:%M:%S}Z"


def representative_events(d: Data, n_each: int = 2) -> list[tuple[str, str]]:
    """Most picks, fewest picks (≥ 3) and the busiest hour; ties broken by time."""
    counts = d.all_picks[d.all_picks.event_id != ""].groupby("event_id").size()
    ev = d.events.set_index("event_id").join(counts.rename("n"), how="inner").sort_values("time")
    if ev.empty:
        return []
    chosen: list[tuple[str, str]] = []
    for eid in ev.sort_values(["n", "time"], ascending=[False, True]).index[:n_each]:
        chosen.append((eid, "most picks"))
    for eid in ev[ev.n >= 3].sort_values(["n", "time"]).index[:n_each]:
        if eid not in dict(chosen):
            chosen.append((eid, "fewest picks"))
    hour = np.floor(d.all_picks.time / 3600)
    busy = hour.value_counts().idxmax() * 3600
    for eid in ev[(ev.time >= busy) & (ev.time < busy + 3600)].index[:n_each]:
        if eid not in dict(chosen):
            chosen.append((eid, "busiest hour"))
    return chosen


def association_figures(d: Data, output_dir: Path) -> tuple[list[str], dict]:
    plt = _plt()
    names, summary = [], {}
    p = d.all_picks
    if p.empty:
        return names, summary
    hour = np.floor(p.time / 3600) * 3600
    g = pd.DataFrame({"hour": hour, "assoc": p.event_id != ""}).groupby("hour").assoc.agg(["size", "mean"])
    eh = (np.floor(d.events.time / 3600) * 3600).value_counts().reindex(g.index, fill_value=0)
    fig, ax = plt.subplots(3, 1, figsize=(12, 7), sharex=True)
    days = (g.index - g.index.min()) / 86400.0
    ax[0].plot(days, g["size"], lw=0.7)
    ax[0].set_ylabel("picks / hour")
    ax[1].plot(days, eh.to_numpy(), lw=0.7, c="tab:green")
    ax[1].set_ylabel("events / hour")
    ax[2].plot(days, g["mean"], lw=0.7, c="tab:purple")
    ax[2].set(ylabel="associated share", xlabel=f"days after {_utc(g.index.min())}", ylim=(0, 1))
    if d.events.magnitude.notna().any():
        for _, e in d.events.nlargest(3, "magnitude").iterrows():
            for a in ax:
                a.axvline((e.time - g.index.min()) / 86400.0, c="tab:red", lw=0.6, ls="--")
            ax[0].text((e.time - g.index.min()) / 86400.0, ax[0].get_ylim()[1] * 0.9, f"M{e.magnitude:.1f}", fontsize=7, color="tab:red")
    fig.suptitle("Picks, events and the associated share per hour (dashed: the three largest events)", fontsize=10)
    fig.tight_layout()
    fig.savefig(output_dir / "association_rates.png", dpi=110)
    plt.close(fig)
    names.append("association_rates.png")
    summary["rates"] = {"hours": int(len(g)), "median_picks_per_hour": float(g["size"].median()), "max_picks_per_hour": int(g["size"].max()),
                        "median_events_per_hour": float(np.median(eh)), "associated_share_quantiles": {q: round(float(g["mean"].quantile(q)), 3) for q in (0.1, 0.5, 0.9)}}

    chosen = representative_events(d)
    if chosen:
        fig, ax = plt.subplots(1, len(chosen), figsize=(3.2 * len(chosen), 5), squeeze=False)
        rows = []
        for j, (eid, why) in enumerate(chosen):
            a = ax[0, j]
            e = d.events.set_index("event_id").loc[eid]
            pk = d.all_picks[d.all_picks.event_id == eid].merge(d.stations[["station_id", "x", "y"]], on="station_id", how="left")
            located = np.isfinite(e.x) if "x" in e else False
            if located:
                pk["dist"] = np.hypot(pk.x - e.x, pk.y - e.y)
                xlabel = "epicentral distance (km)"
            else:
                order = pk.groupby("station_id").time.min().rank(method="first")
                pk["dist"] = pk.station_id.map(order)
                xlabel = "station rank by first arrival"
            t0 = e.time
            other = d.all_picks[(d.all_picks.event_id == "") & (d.all_picks.time >= pk.time.min() - 5) &
                                (d.all_picks.time <= pk.time.max() + 5) & d.all_picks.station_id.isin(pk.station_id)]
            other = other.assign(dist=other.station_id.map(pk.groupby("station_id").dist.first()))
            for ph, col in (("P", "tab:red"), ("S", "tab:blue")):
                s = pk[pk.phase == ph]
                a.scatter(s.dist, s.time - t0, s=14, c=col, label=ph)
            a.scatter(other.dist, other.time - t0, s=14, marker="x", c="gray", label="unassociated")
            a.set(xlabel=xlabel, ylabel="pick time − origin time (s)", title=f"{why}\n{_utc(t0)}", )
            a.title.set_fontsize(8)
            if j == 0:
                a.legend(fontsize=7)
            sp = pk[pk.phase == "P"].dropna(subset=["dist"])
            fit = np.polyfit(sp.dist, sp.time - t0, 1) if located and len(sp) >= 3 and sp.dist.nunique() > 1 else None
            rows.append({"event_id": eid, "why": why, "origin_utc": _utc(t0), "p": int((pk.phase == "P").sum()), "s": int((pk.phase == "S").sum()),
                         "unassociated_nearby": int(len(other)),
                         "p_apparent_velocity_km_s": round(1 / fit[0], 2) if fit is not None and fit[0] > 0 else None,
                         "p_residual_std_s": round(float(np.std(sp.time - t0 - np.polyval(fit, sp.dist))), 3) if fit is not None else None})
        fig.suptitle("Representative events: picks against distance; picks of one event should form P and S travel-time curves", fontsize=10)
        fig.tight_layout()
        fig.savefig(output_dir / "association_events.png", dpi=110)
        plt.close(fig)
        names.append("association_events.png")
        summary["events"] = rows
    return names, summary


def location_figures(d: Data, checks: list, ensemble: dict | None, output_dir: Path) -> tuple[list[str], dict]:
    plt = _plt()
    names, summary = [], {}
    e = d.events.dropna(subset=["x", "y", "depth_km"])
    if len(e) < 5:
        return names, summary
    fig, ax = plt.subplots(1, 3, figsize=(16, 5.5))
    lim = [np.percentile(e.x, [0.5, 99.5]), np.percentile(e.y, [0.5, 99.5]), np.percentile(e.depth_km, [0.5, 99.5])]
    ax[0].scatter(e.x, e.depth_km, s=0.6, c="k", alpha=0.4, rasterized=True)
    ax[0].set(xlim=lim[0], ylim=lim[2][::-1], xlabel="east (km)", ylabel="depth below sea level (km)", title="East–west section")
    ax[1].scatter(e.y, e.depth_km, s=0.6, c="k", alpha=0.4, rasterized=True)
    ax[1].set(xlim=lim[1], ylim=lim[2][::-1], xlabel="north (km)", ylabel="depth below sea level (km)", title="North–south section")
    res = next((c.details.get("per_station") for c in checks if c.id == "station_residual_azimuth" and c.details.get("per_station")), None)
    a = ax[2]
    a.scatter(e.x, e.y, s=0.4, c="lightgray", rasterized=True)
    if res:
        st = pd.DataFrame(res).T
        sc = a.scatter(st.x_km, st.y_km, c=st.median_residual_s, cmap="RdBu_r", vmin=-0.5, vmax=0.5, s=70, marker="^", edgecolor="k")
        fig.colorbar(sc, ax=a, label="median P residual (s)")
        for s, r in st.iterrows():
            a.annotate(s.split(".")[-1], (r.x_km, r.y_km), fontsize=6, xytext=(3, 3), textcoords="offset points")
    else:
        a.scatter(d.stations.x, d.stations.y, marker="^", c="k", s=30)
    a.set(xlabel="east (km)", ylabel="north (km)", title="Station P residuals about the travel-time fit", aspect="equal")
    fig.tight_layout()
    fig.savefig(output_dir / "location_sections.png", dpi=110)
    plt.close(fig)
    names.append("location_sections.png")
    summary["sections"] = {"depth_quantiles_km": {q: round(float(e.depth_km.quantile(q)), 2) for q in (0.05, 0.5, 0.95)},
                           "east_range_km": [round(float(v), 1) for v in lim[0]], "north_range_km": [round(float(v), 1) for v in lim[1]]}
    fig_data = (ensemble or {}).get("_figure")
    if fig_data:
        models = fig_data["models"]
        fig, ax = plt.subplots(1, 2, figsize=(13, 5))
        bins = np.linspace(min(np.min(fig_data["catalog_depth"]), *[np.min(m["depth"]) for m in models.values()]),
                           max(np.max(fig_data["catalog_depth"]), *[np.max(m["depth"]) for m in models.values()]), 40)
        ax[0].hist(fig_data["catalog_depth"], bins=bins, histtype="stepfilled", color="lightgray", label="catalog")
        for name, m in models.items():
            ax[0].hist(m["depth"], bins=bins, histtype="step", lw=1.2, label=name)
        ax[0].set(xlabel="depth below sea level (km)", ylabel="events", title="Depths of the sampled events: catalog and each generic model")
        ax[0].legend(fontsize=7)
        rows = []
        for name, m in models.items():
            dz = fig_data["catalog_depth"] - m["depth"]
            dt = fig_data["catalog_time"] - m["time"]
            ax[1].scatter(np.median(dt), np.median(dz), s=50, label=name)
            ax[1].errorbar(np.median(dt), np.median(dz), xerr=np.subtract(*np.percentile(dt, [75, 25])) / 2,
                           yerr=np.subtract(*np.percentile(dz, [75, 25])) / 2, fmt="none", c="gray", lw=0.8)
            rows.append({"model": name, "median_depth_catalog_minus_model_km": round(float(np.median(dz)), 3),
                         "median_origin_catalog_minus_model_s": round(float(np.median(dt)), 3)})
        ax[1].axhline(0, c="k", lw=0.6)
        ax[1].axvline(0, c="k", lw=0.6)
        ax[1].set(xlabel="catalog − model origin time (s, median ± half IQR)", ylabel="catalog − model depth (km)",
                  title="Where the catalog sits among the generic models")
        ax[1].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(output_dir / "location_model_ensemble.png", dpi=110)
        plt.close(fig)
        names.append("location_model_ensemble.png")
        summary["model_ensemble"] = rows
    return names, summary


def magnitude_figures(d: Data, output_dir: Path) -> tuple[list[str], dict]:
    plt = _plt()
    e = d.events.dropna(subset=["magnitude"])
    if len(e) < 10:
        return [], {}
    m = e.magnitude.to_numpy()
    bins = np.arange(np.floor(m.min() * 10) / 10, m.max() + 0.2, 0.1)
    counts, edges = np.histogram(m, bins)
    cum = counts[::-1].cumsum()[::-1]
    p = d.picks[np.isfinite(d.picks.hyp_km)]
    far = p.groupby("event_id").hyp_km.max()
    j = e.set_index("event_id").join(far.rename("r"), how="inner")
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    ax[0].semilogy(edges[:-1], np.maximum(cum, 0.8), "o", ms=3, label="cumulative")
    ax[0].semilogy(edges[:-1], np.maximum(counts, 0.8), "s", ms=3, mfc="none", label="per 0.1 bin")
    ax[0].set(xlabel="magnitude", ylabel="events", title="Frequency–magnitude distribution")
    ax[0].legend(fontsize=8)
    ax[1].scatter(j.r, j.magnitude, s=2, alpha=0.4, c="k", rasterized=True)
    rr = np.linspace(max(1.0, float(j.r.min()) if len(j) else 1.0), float(j.r.max()) if len(j) else 100.0, 100)
    for loga in (-2.3, -1.0, 0.5):
        ax[1].plot(rr, loga + 1.11 * np.log10(rr / 100) + 0.00189 * (rr - 100) + 3.0, lw=0.8, label=f"log A = {loga:g} mm")
    ax[1].set(xlabel="farthest detecting station, hypocentral (km)", ylabel="magnitude",
              title="Magnitude vs farthest detection (Hutton & Boore 1987)")
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "magnitude_distribution.png", dpi=110)
    plt.close(fig)
    peak = float(edges[np.argmax(counts)])
    return ["magnitude_distribution.png"], {"events_with_magnitude": int(len(e)), "magnitude_quantiles": {q: round(float(np.quantile(m, q)), 2) for q in (0.05, 0.5, 0.95)},
                                            "most_frequent_bin": round(peak, 1),
                                            "median_farthest_km": round(float(j.r.median()), 1) if len(j) else None}
