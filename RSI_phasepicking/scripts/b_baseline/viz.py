"""Figures of the baseline pipeline: one standard figure per part, one style.

Colours: P blue, S red, analyst reference black, rejected or unassigned grey.
Times are seconds after the event-window trigger unless a panel says otherwise.
Waveforms are causally filtered (no energy drawn ahead of onsets).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

P_COLOR, S_COLOR, REF_COLOR, GREY = "#2563eb", "#dc2626", "#111827", "#9ca3af"
METHOD_COLORS = {"B0": "#d97706", "B1": "#7c3aed", "B8": "#111827", "agent": "#059669"}
METHOD_LABELS = {"B0": "B0 STA/LTA + AIC", "B1": "B1 PhaseNet (SCEDC)", "B8": "B8 analyst picks"}
FAMILY_STYLE = {"HH": ("^", "#2563eb"), "EHZ+HN": ("s", "#d97706"), "HN": ("D", "#7c3aed"),
                "Z only": ("v", GREY), "none": ("x", GREY)}


def style():
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "grid.color": "#e5e7eb",
                         "grid.linewidth": 0.6, "legend.frameon": False, "figure.dpi": 110,
                         "savefig.dpi": 150, "savefig.bbox": "tight"})


def _phase_color(ph):
    return P_COLOR if ph == "P" else S_COLOR


def _trace(tr, t_ref, freqmin=1.0, freqmax=20.0):
    """Causal filtering only: a zero-phase filter draws energy ahead of onsets,
    which would mislead anyone (or any agent) timing an onset from the plot."""
    tr = tr.copy().detrend("demean").taper(0.02)
    tr.filter("bandpass", freqmin=freqmin, freqmax=freqmax, zerophase=False)
    t = tr.times() + (tr.stats.starttime - t_ref)
    y = tr.data / (np.abs(tr.data).max() or 1.0)
    return t, y


def fig_window(event_id, chosen, window, origin_time, path):
    """Part 1: stations triggering on the vertical, and the window they define."""
    style()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True, height_ratios=[3, 1])
    trig = window["trigger"]
    first = {s: (min(t) - trig if t else np.inf) for s, t in window["onsets"].items()}
    order = sorted(chosen, key=lambda s: first.get(s, np.inf))
    for i, sid in enumerate(order):
        t, y = _trace(chosen[sid]["Z"], trig, window["cfg"]["freqmin"], window["cfg"]["freqmax"])
        a1.plot(t, i + 0.45 * y, color="#4b5563", lw=0.35)
        for t_on in window["onsets"].get(sid, []):
            a1.plot([t_on - trig] * 2, [i - 0.45, i + 0.45], color=P_COLOR, lw=1)
    a1.set_yticks(range(len(order)))
    a1.set_yticklabels(order, fontsize=6)
    a1.set_ylim(-1, len(order))
    a1.set_title(f"Event {event_id} — part 1: event window from the network trigger "
                 f"(blue ticks: STA/LTA onsets on the verticals)")
    t = window["grid"] + (window["grid_t0"] - trig)
    a2.step(t, window["count"], where="post", color="#111827", lw=1)
    a2.axhline(window["cfg"]["min_stations"], color=GREY, ls="--", lw=0.8)
    for a in (a1, a2):
        a.axvspan(window["start"] - trig, window["end"] - trig, color="#dbeafe", alpha=0.5, lw=0)
        a.axvline(0, color=P_COLOR, lw=1.2)
        if origin_time is not None:
            a.axvline(origin_time - trig, color=REF_COLOR, ls=":", lw=1)
    a2.set_ylabel("stations\ntriggered")
    a2.set_xlabel("Time after network trigger (s)   [shaded: event window; dotted: catalog origin, for checking only]")
    a2.set_xlim(window["start"] - trig - 20, window["end"] - trig + 10)
    fig.savefig(path)
    plt.close(fig)


def fig_channels(stations, channels, events, region, path):
    """Part 2: which channels each station contributes over the whole batch."""
    style()
    fig, ax = plt.subplots(figsize=(7.5, 6))
    ax.scatter(events.origin_lon, events.origin_lat, s=14, c="#d1d5db", edgecolor="#6b7280", lw=0.4,
               label="batch events (catalog)", zorder=1)
    with_data = channels[channels.family != "none"]
    fam = with_data.groupby("station").family.agg(lambda x: x.mode().iloc[0])
    missing = channels[channels.family == "none"].groupby("station").size()
    n_ev = channels.event_id.nunique()
    for f, (m, col) in FAMILY_STYLE.items():
        sub = stations[stations.station.map(fam) == f]
        if len(sub):
            ax.scatter(sub.lon, sub.lat, marker=m, s=46, color=col, edgecolor="white", lw=0.6,
                       label=f"{f} ({len(sub)})", zorder=3)
    for r in stations.itertuples():
        miss = int(missing.get(r.station, 0))
        txt = r.code + (f" (no data in {miss}/{n_ev})" if miss else "")
        ax.annotate(txt, (r.lon, r.lat), xytext=(3, 3), textcoords="offset points", fontsize=6,
                    color="#b91c1c" if miss else "#374151")
    lat, lon = region["latitude"], region["longitude"]
    ax.add_patch(plt.Rectangle((lon[0], lat[0]), lon[1] - lon[0], lat[1] - lat[0], fill=False, ec=GREY, ls="--"))
    ax.set_aspect(1 / np.cos(np.radians(np.mean(lat))))
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title(f"Part 2: channels used per station over {n_ev} events\n(HH: broadband 3C; EHZ+HN: "
                 "short-period vertical with accelerometer horizontals; dashed: association region)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8)
    fig.savefig(path)
    plt.close(fig)


def fig_picks(event_id, chosen, window, picks, ref, dist, path, title_method="B0"):
    """Part 3: picks on a distance-ordered record section, with the analyst reference."""
    style()
    trig = window["trigger"]
    order = sorted(chosen, key=lambda s: dist.get(s, 1e9))
    fig, ax = plt.subplots(figsize=(9, 0.28 * len(order) + 1.5))
    for i, sid in enumerate(order):
        t, y = _trace(chosen[sid]["Z"], trig)
        ax.plot(t, i + 0.42 * y, color="#4b5563", lw=0.35)
        if chosen[sid]["N"] is not None:
            t, y = _trace(chosen[sid]["N"], trig)
            ax.plot(t, i + 0.42 * y, color="#9ca3af", lw=0.3, alpha=0.7)
        for r in ref[(ref.station == sid) & (ref["mode"] == "manual")].itertuples():
            tt = _t(r.time) - trig
            ax.plot([tt, tt], [i - 0.48, i + 0.48], color=REF_COLOR, lw=0.9, ls=(0, (2, 1)))
        for r in picks[picks.station == sid].itertuples():
            tt = _t(r.time_utc) - trig
            ax.plot([tt, tt], [i - 0.4, i + 0.4], color=_phase_color(r.phase), lw=1.6)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"{s} {dist.get(s, np.nan):.0f} km" for s in order], fontsize=6)
    ax.set_ylim(-1, len(order))
    ax.set_xlim(-5, 45)
    ax.set_xlabel("Time after network trigger (s)   [dark: vertical; light: horizontal]")
    ax.set_title(f"Event {event_id} — part 3: {title_method} picks (P blue, S red) "
                 f"and analyst picks (black dashed)")
    fig.savefig(path)
    plt.close(fig)


def fig_association(event_id, picks_ev, origin_time, dist, path):
    """Part 4: picks against distance, assigned or not, with the predicted arrival."""
    style()
    fig, ax = plt.subplots(figsize=(7, 5))
    for r in picks_ev.itertuples():
        d = dist.get(r.station, np.nan)
        tt = _t(r.time_utc) - origin_time
        if r.assignment_status == "assigned":
            ax.scatter(d, tt, s=22, color=_phase_color(r.phase), zorder=3)
            if np.isfinite(r.residual_s):
                ax.plot([d, d], [tt, tt - r.residual_s], color=_phase_color(r.phase), lw=0.8, alpha=0.6)
        else:
            ax.scatter(d, tt, s=22, marker="x", color=GREY, zorder=2)
    ax.scatter([], [], s=22, color=P_COLOR, label="P assigned")
    ax.scatter([], [], s=22, color=S_COLOR, label="S assigned")
    ax.scatter([], [], s=22, marker="x", color=GREY, label="unassigned")
    ax.set_xlabel("Epicentral distance from the catalog location (km)")
    ax.set_ylabel("Time after catalog origin (s)")
    ax.set_title(f"Event {event_id} — part 4: association (PyOcto); vertical bars: residual to the predicted time")
    ax.legend(fontsize=8)
    fig.savefig(path)
    plt.close(fig)


def fig_location(loc, path, label="B0"):
    """Part 5: located epicentres and depths against the catalog."""
    style()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5), width_ratios=[1.3, 1])
    ok = loc[loc.status == "LOCATED"]
    for r in ok.itertuples():
        a1.plot([r.cat_lon, r.longitude], [r.cat_lat, r.latitude], color=GREY, lw=0.8)
    a1.scatter(loc.cat_lon, loc.cat_lat, s=26, facecolor="none", edgecolor=REF_COLOR, lw=0.8, label="catalog")
    a1.scatter(ok.longitude, ok.latitude, s=16, color=P_COLOR, label=f"{label} (HypoInverse, HK model)")
    a1.set_aspect(1 / np.cos(np.radians(ok.latitude.mean() if len(ok) else 34.2)))
    a1.set_xlabel("Longitude (°)")
    a1.set_ylabel("Latitude (°)")
    a1.legend(fontsize=8)
    a1.set_title(f"Part 5: epicentres ({len(ok)}/{len(loc)} located); grey lines join each pair")
    lim = [0, max(20, np.nanmax(np.r_[ok.depth_km, ok.cat_depth]) + 2)] if len(ok) else [0, 20]
    a2.plot(lim, lim, color=GREY, lw=0.8, ls="--")
    a2.scatter(ok.cat_depth, ok.depth_km, s=18, color=P_COLOR)
    a2.set_xlim(lim)
    a2.set_ylim(lim)
    a2.set_xlabel("Catalog depth (km)")
    a2.set_ylabel(f"{label} depth (km below sea level)")
    med = np.nanmedian(ok.epi_shift_km) if len(ok) else np.nan
    a2.set_title(f"Depths; median epicentre shift {med:.2f} km")
    fig.savefig(path)
    plt.close(fig)


def fig_overview(events, picks, path, label="B0"):
    """The whole run on one line: how many events and picks survive each part."""
    style()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3), width_ratios=[1, 1.6])
    names = list(events)
    a1.barh(names[::-1], list(events.values())[::-1], color="#93c5fd")
    for i, v in enumerate(list(events.values())[::-1]):
        a1.text(v, i, f" {v}", va="center", fontsize=8)
    a1.set_title("Events")
    a1.set_xlim(0, max(events.values()) * 1.15)
    stages = list(picks["P"])
    y = np.arange(len(stages))
    a2.barh(y + 0.2, [picks["P"][k] for k in stages[::-1]], height=0.4, color=P_COLOR, alpha=0.8, label="P")
    a2.barh(y - 0.2, [picks["S"][k] for k in stages[::-1]], height=0.4, color=S_COLOR, alpha=0.8, label="S")
    for i, k in enumerate(stages[::-1]):
        a2.text(picks["P"][k], i + 0.2, f" {picks['P'][k]}", va="center", fontsize=8)
        a2.text(picks["S"][k], i - 0.2, f" {picks['S'][k]}", va="center", fontsize=8)
    a2.set_yticks(y)
    a2.set_yticklabels(stages[::-1])
    a2.set_title("Picks")
    a2.legend(loc="lower right", fontsize=8)
    a2.set_xlim(0, max(max(picks["P"].values()), max(picks["S"].values())) * 1.15)
    for a in (a1, a2):
        a.grid(axis="y", visible=False)
    fig.suptitle(f"{label} pipeline overview: what survives each part", y=1.03)
    fig.savefig(path)
    plt.close(fig)


def _mc(m):
    return METHOD_COLORS.get(m, "#374151")


def fig_residuals(scored, tol, path):
    """Scoring: how far each method's nearest pick lies from the analyst's pick."""
    style()
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, ph, lim in zip(axes, ("P", "S"), (1.5, 3.0)):
        bins = np.linspace(-lim, lim, 61)
        for m, sc in scored.items():
            r = sc[(sc.phase == ph)].residual_s.dropna()
            ax.hist(r, bins=bins, histtype="step", lw=1.6, color=_mc(m),
                    label=f"{METHOD_LABELS.get(m, m)} (n={len(r)})")
        ax.axvspan(-tol[ph], tol[ph], color="#f3f4f6", zorder=0)
        ax.axvline(0, color=REF_COLOR, lw=0.8)
        ax.set_title(f"{ph}: nearest pick − analyst pick (shaded: matched, ±{tol[ph]} s)")
        ax.set_xlabel("Time difference (s)")
        ax.legend(fontsize=7, loc="upper left")
    axes[0].set_ylabel("Analyst picks")
    fig.savefig(path)
    plt.close(fig)


def fig_scorecard(card, path):
    """Scoring: the headline numbers per method and phase, with 95% event-bootstrap intervals."""
    style()
    metrics = [("recall", "Recall"), ("precision", "Precision"), ("within_01", "Within 0.1 s"),
               ("mae_s", "MAE (s)")]
    methods = list(dict.fromkeys(card.method))
    fig, axes = plt.subplots(2, 4, figsize=(11, 5), sharex=True)
    for i, ph in enumerate(("P", "S")):
        for j, (k, name) in enumerate(metrics):
            ax = axes[i, j]
            sub = card[card.phase == ph].set_index("method").reindex(methods)
            v = sub[k].values
            lo = v - sub[f"{k}_lo"].values
            hi = sub[f"{k}_hi"].values - v
            ax.bar(range(len(methods)), v, color=[_mc(m) for m in methods], yerr=[lo, hi], capsize=3,
                   error_kw=dict(lw=0.8))
            for x, y in enumerate(v):
                ax.text(x, y, f"{y:.2f}" if k != "mae_s" else f"{y:.3f}", ha="center", va="bottom", fontsize=7)
            ax.set_xticks(range(len(methods)))
            ax.set_xticklabels(methods)
            if k != "mae_s":
                ax.set_ylim(0, 1.08)
            if i == 0:
                ax.set_title(name)
            if j == 0:
                ax.set_ylabel(ph)
            ax.grid(axis="x", visible=False)
    fig.suptitle("Pick scorecard against the analyst's manual picks (error bars: 95% event bootstrap)", y=1.0)
    fig.savefig(path)
    plt.close(fig)


def fig_strata(strata, path):
    """Scoring: where each method is strong or weak (share within 0.1 s, and recall)."""
    style()
    methods = list(dict.fromkeys(strata.method))
    kinds = [("weight", "Analyst weight code"), ("family", "Channel of the analyst pick")]
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), gridspec_kw=dict(hspace=0.55))
    for i, ph in enumerate(("P", "S")):
        for j, (kind, xlabel) in enumerate(kinds):
            ax = axes[i, j]
            sub = strata[(strata.phase == ph) & (strata.kind == kind)]
            cats = list(dict.fromkeys(sub.stratum))
            w = 0.8 / max(len(methods), 1)
            for k, m in enumerate(methods):
                sm = sub[sub.method == m].set_index("stratum").reindex(cats)
                x = np.arange(len(cats)) + (k - (len(methods) - 1) / 2) * w
                ax.bar(x, sm.within_01, width=w, color=_mc(m), label=METHOD_LABELS.get(m, m))
                ax.scatter(x, sm.recall, color="white", edgecolor=_mc(m), zorder=3, s=18)
            n = sub.drop_duplicates("stratum").set_index("stratum").reindex(cats).n_ref
            ax.set_xticks(range(len(cats)))
            ax.set_xticklabels([f"{c}\n(n={int(v)})" for c, v in zip(cats, n)], fontsize=8)
            ax.set_ylim(0, 1.05)
            ax.set_title(f"{ph} by {xlabel.lower()}")
            ax.grid(axis="x", visible=False)
    axes[0, 0].set_ylabel("Share within 0.1 s (bars)\nrecall (dots)")
    axes[1, 0].set_ylabel("Share within 0.1 s (bars)\nrecall (dots)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=_mc(m)) for m in methods]
    fig.legend(handles, [METHOD_LABELS.get(m, m) for m in methods], loc="upper center", ncol=len(methods),
               bbox_to_anchor=(0.5, 0.97), fontsize=8)
    fig.suptitle("Pick quality by stratum (weight code 0–1 impulsive, 2–3 emergent; EH short-period, "
                 "HN accelerometer)", y=1.02)
    fig.savefig(path)
    plt.close(fig)


def fig_location_shift(shifts, path):
    """Scoring: how far each method's locations lie from the analyst-pick locations (B8)."""
    style()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
    for m, d in shifts.items():
        x = np.sort(d.epi_km.values)
        a1.step(x, np.arange(1, len(x) + 1) / len(x), where="post", color=_mc(m), lw=1.6,
                label=f"{METHOD_LABELS.get(m, m)}: median {np.median(x):.2f} km")
        a2.hist(d.depth_km, bins=np.arange(-6, 6.5, 0.5), histtype="step", lw=1.6, color=_mc(m),
                label=f"{m}: median {np.median(d.depth_km):+.2f} km")
    a1.set_xlabel("Epicentre shift from the analyst-pick location (km)")
    a1.set_ylabel("Share of events")
    a1.legend(fontsize=7, loc="lower right")
    a1.set_title("Epicentres relative to B8 (same locator and model)")
    a2.axvline(0, color=REF_COLOR, lw=0.8)
    a2.set_xlabel("Depth − B8 depth (km)")
    a2.set_ylabel("Events")
    a2.legend(fontsize=7)
    a2.set_title("Depths relative to B8")
    fig.savefig(path)
    plt.close(fig)


def _t(x):
    from obspy import UTCDateTime
    return UTCDateTime(str(x))
