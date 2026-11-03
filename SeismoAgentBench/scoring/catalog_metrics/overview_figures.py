"""Summary figures of the S0 / S1 results for the paper outline (docs/research/02_Paper_Outline.md §4.1).

For each case: the strongest reference catalog, the official catalog, the S0 ``min`` run, the S1 ``tools`` run and
the human-in-loop final, all cut to the case's scoring mask exactly as the scorer does.

- ``<case>_space.png``: map and depth profile (distance along the principal axis of the final's epicentres)
  per catalog, same extents in every panel;
- ``<case>_detection.png``: time–magnitude per catalog; cumulative number of events; cumulative
  frequency–magnitude distribution with Mc (maximum curvature + 0.2, as the scorer); depth distribution;
- ``criteria_heatmap.png``: every trusted-catalog criterion as value / threshold for the five catalogs of each
  case (the final sets the thresholds; ✓ pass, ✗ fail, – not applicable).

Usage: python -m SeismoAgentBench.scoring.catalog_metrics.overview_figures [--out docs/research/assets/results_overview]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from .case import headline, load_case  # noqa: E402
from .dimensions import mc_max_curvature  # noqa: E402
from .metrics import ceilings  # noqa: E402
from .tables import Population, in_mask, read_candidate_catalog  # noqa: E402
from .trust import CRITERIA, trust_verdict  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
TASKS = ROOT / "workflows" / "tasks"
CASES = {  # case: (title, strongest reference, official catalog)
    "2011_prague_oklahoma": ("Prague 2011", "cochran", "comcat"),
    "2020_magna_utah": ("Magna 2020", "pang", "uuss"),
    "2017_maple_creek_yellowstone": ("Maple Creek 2017", "shelly", "comcat"),
    "2018_kilauea_hawaii": ("Kīlauea 2018", "shelly", "comcat"),
    "2019_ridgecrest_california": ("Ridgecrest 2019", "shelly", "official_earthquake"),
    "2016_kaikoura_new_zealand": ("Kaikōura 2016", "chamberlain", "geonet"),
}
REF_LABEL = {"cochran": "Cochran", "comcat": "ComCat", "pang": "Pang", "uuss": "UUSS", "shelly": "Shelly",
             "official_earthquake": "SCSN", "chamberlain": "Chamberlain", "geonet": "GeoNet"}
# categorical slots 1–5 of the validated default palette, fixed per catalog role (never cycled)
COLORS = {"strongest": "#2a78d6", "official": "#eb6834", "min": "#1baf7a", "tools": "#eda100", "final": "#e87ba4"}
ROLE_TITLE = {"strongest": "strongest reference", "official": "official catalog", "min": "S0 min", "tools": "S1 tools",
              "final": "human-in-loop final"}
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
plt.rcParams.update({"font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.titlesize": 8.5, "axes.titlecolor": INK, "figure.facecolor": "#fcfcfb",
                     "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb", "axes.spines.top": False,
                     "axes.spines.right": False})


def _latest_run(case: str, variant: str) -> Path | None:
    runs = sorted(p for p in (TASKS / case / "runs" / variant).glob("*/*/2*") if (p / "evaluation/metrics.json").is_file()
                  and not (p / "EXCLUDED.md").exists())
    return runs[-1] if runs else None


def catalogs(case: str) -> dict:
    """role -> (label, events cut to the mask, metrics headline or None)."""
    c = load_case(TASKS / case)
    _, strongest, official = CASES[case]
    out = {"strongest": (REF_LABEL[strongest], c.refs[strongest].events, None),
           "official": (REF_LABEL[official], c.refs[official].events, None)}
    for role, variant in (("min", "min"), ("tools", "tools")):
        run = _latest_run(case, variant)
        if run is None or not (run / "work/catalog.csv").is_file():
            out[role] = (ROLE_TITLE[role] + " (not completed)", None, None)
            continue
        ev, _ = read_candidate_catalog(run / "work/catalog.csv")
        ev = ev[in_mask(ev, c.mask, depth_known=True)].reset_index(drop=True)
        out[role] = (ROLE_TITLE[role], ev, json.loads((run / "evaluation/metrics.json").read_text()))
    out["final"] = (ROLE_TITLE["final"], c.expert["final"].events, None)
    return {"case": c, "catalogs": out}


def _profile_axis(final: pd.DataFrame, centre) -> tuple[np.ndarray, float, float]:
    lon0, lat0 = centre
    k = 111.195 * np.cos(np.radians(lat0))
    xy = np.c_[(final.longitude - lon0) * k, (final.latitude - lat0) * 111.195]
    xy = xy[np.isfinite(xy).all(axis=1)]
    w, v = np.linalg.eigh(np.cov(xy.T))
    return v[:, np.argmax(w)], lon0, lat0


def space_figure(case: str, data: dict, out: Path) -> None:
    c, cats = data["case"], data["catalogs"]
    roles = [r for r in COLORS if cats[r][1] is not None and cats[r][1].latitude.notna().any()]
    if case == "2017_maple_creek_yellowstone":  # Shelly is time-only: no locations
        roles = [r for r in roles if r != "strongest"]
    axis, lon0, lat0 = _profile_axis(cats["final"][1], c.center)
    k = 111.195 * np.cos(np.radians(lat0))
    la, lo, dz = c.mask["latitude"], c.mask["longitude"], c.mask["depth_bsl_km"]
    corners = np.array([[(x - lon0) * k, (y - lat0) * 111.195] for x in lo for y in la]) @ axis
    fig, axes = plt.subplots(2, len(roles), figsize=(2.6 * len(roles), 5.2), gridspec_kw={"height_ratios": [1.25, 1]},
                             squeeze=False)
    for j, role in enumerate(roles):
        label, ev, _ = cats[role]
        e = ev.dropna(subset=["latitude", "longitude"])
        size = 0.6 if len(e) > 5000 else 1.5 if len(e) > 1000 else 3
        a = axes[0, j]
        a.scatter(e.longitude, e.latitude, s=size, c=COLORS[role], lw=0, alpha=0.6, rasterized=True)
        a.set_xlim(lo)
        a.set_ylim(la)
        a.set_aspect(1 / np.cos(np.radians(lat0)))
        a.set_title(f"{label}\n{len(ev):,} events", color=INK)
        a.tick_params(labelsize=6.5)
        a.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3))
        a.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4))
        if j:
            a.set_yticklabels([])
        b = axes[1, j]
        d = e.dropna(subset=["depth_km"])
        s = np.c_[(d.longitude - lon0) * k, (d.latitude - lat0) * 111.195] @ axis
        b.scatter(s, d.depth_km, s=size, c=COLORS[role], lw=0, alpha=0.6, rasterized=True)
        b.set_xlim(corners.min(), corners.max())
        b.set_ylim(dz[1], dz[0])
        b.grid(color=GRID, lw=0.5)
        b.tick_params(labelsize=6.5)
        b.set_xlabel("distance along strike (km)", fontsize=7)
        if j == 0:
            b.set_ylabel("depth below sea level (km)", fontsize=7)
        else:
            b.set_yticklabels([])
    fig.suptitle(f"{CASES[case][0]}: epicentres and depth profile (scoring mask)", color=INK, fontsize=9.5, x=0.01,
                 ha="left")
    fig.tight_layout()
    fig.savefig(out / f"{case}_space.png", dpi=170)
    plt.close(fig)


def _mc(m: np.ndarray) -> float | None:
    m = m[np.isfinite(m)]
    return mc_max_curvature(m) if len(m) >= 50 else None


def detection_figure(case: str, data: dict, out: Path) -> None:
    c, cats = data["case"], data["catalogs"]
    roles = [r for r in COLORS if cats[r][1] is not None]
    t0 = c.mask["start"]
    fig = plt.figure(figsize=(11, 6.4))
    gs = fig.add_gridspec(len(roles), 3, width_ratios=[1.6, 1, 1], hspace=0.12, wspace=0.32)
    mags = np.concatenate([cats[r][1].magnitude.dropna().to_numpy() for r in roles])
    mlim = (np.floor(np.nanpercentile(mags, 0.5) * 2) / 2, np.ceil(np.nanmax(mags) * 2) / 2)
    days = (c.mask["end"] - t0) / 86400
    for i, role in enumerate(roles):
        label, ev, _ = cats[role]
        a = fig.add_subplot(gs[i, 0])
        a.scatter((ev.time - t0) / 86400, ev.magnitude, s=1.2, c=COLORS[role], lw=0, alpha=0.7, rasterized=True)
        a.set_xlim(0, days)
        a.set_ylim(mlim)
        a.grid(color=GRID, lw=0.5)
        a.text(0.005, 0.95, f"{label} ({len(ev):,})", transform=a.transAxes, va="top", fontsize=7, color=INK)
        a.tick_params(labelsize=6.5)
        if i < len(roles) - 1:
            a.set_xticklabels([])
        else:
            a.set_xlabel("days since window start", fontsize=7)
        if i == len(roles) // 2:
            a.set_ylabel("magnitude", fontsize=7)
    right = gs[:, 1:].subgridspec(3, 1, hspace=0.45)
    cum, fmd, dep = (fig.add_subplot(right[k]) for k in range(3))
    for role in roles:
        label, ev, _ = cats[role]
        t = np.sort((ev.time.to_numpy() - t0) / 86400)
        cum.plot(t, np.arange(1, len(t) + 1), color=COLORS[role], lw=1.6, label=label)
        m = ev.magnitude.dropna().to_numpy()
        if len(m):
            edges = np.arange(mlim[0], mlim[1] + 0.1, 0.1)
            n = np.array([(m >= x).sum() for x in edges])
            mc = _mc(m)
            fmd.semilogy(edges[n > 0], n[n > 0], color=COLORS[role], lw=1.6,
                         label=f"{label}: Mc {mc:.1f}" if mc is not None else label)
            if mc is not None:
                fmd.plot([mc], [max(1, (m >= mc).sum())], marker="o", ms=4.5, color=COLORS[role], mec="#fcfcfb", mew=1)
        z = ev.depth_km.dropna().to_numpy()
        if len(z) > 20:
            bins = np.arange(c.mask["depth_bsl_km"][0], c.mask["depth_bsl_km"][1] + 0.5, 0.5)
            h, _ = np.histogram(z, bins=bins, density=True)
            dep.step(bins[:-1], h, where="post", color=COLORS[role], lw=1.4)
    cum.set_title("cumulative number of events", loc="left")
    cum.set_xlabel("days", fontsize=7)
    cum.set_xlim(0, days)
    fmd.set_title("frequency–magnitude (cumulative); dot = Mc", loc="left")
    fmd.set_xlabel("magnitude", fontsize=7)
    dep.set_title("depth distribution (density)", loc="left")
    dep.set_xlabel("depth below sea level (km)", fontsize=7)
    for a in (cum, fmd, dep):
        a.grid(color=GRID, lw=0.5)
        a.tick_params(labelsize=6.5)
    cum.legend(fontsize=6.5, frameon=False, loc="upper left")
    fmd.legend(fontsize=6.2, frameon=False, loc="upper right")
    fig.suptitle(f"{CASES[case][0]}: detection, magnitudes and depths (scoring mask)", color=INK, fontsize=9.5, x=0.01,
                 ha="left")
    fig.savefig(out / f"{case}_detection.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


CRITERION_LABEL = {"inside_region": "inside station coverage", "false_events": "false events (audit)",
                   "time_bias": "time bias", "time_spread": "time spread", "after_large_events": "after large events",
                   "horizontal_shift": "horizontal shift", "depth_bias": "depth bias",
                   "horizontal_scatter": "horizontal scatter", "off_structure": "off structure",
                   "depth_pileup": "depth pile-up", "magnitude_offset": "magnitude offset",
                   "magnitude_spread": "magnitude spread", "magnitude_scale": "magnitude scale",
                   "large_events_present": "large events found"}
ORDER = [c[2] for c in CRITERIA if c[2] != "false_events"] + ["large_events_present"]  # no blind audit yet


def _verdicts(data: dict) -> dict:
    """role -> {criterion: (ratio to threshold or None, verdict, value)}."""
    c, cats = data["case"], data["catalogs"]
    base = json.loads((c.task_dir / "evaluation/human_in_loop/metrics_baseline.json").read_text())
    final = base["rows"]["expert_final"]["headline"]
    ceil = ceilings(c.refs)
    heads = {"final": final}
    for role in ("strongest", "official"):
        key = CASES[c.task_dir.name][{"strongest": 1, "official": 2}[role]]
        heads[role] = headline(base["rows"][key], c, ceil) if "headline" not in base["rows"][key] else base["rows"][key]["headline"]
    for role in ("min", "tools"):
        m = cats[role][2]
        heads[role] = (m or {}).get("headline")
    out = {}
    for role, h in heads.items():
        if not h:
            out[role] = None
            continue
        v = trust_verdict(h, final, True)
        row = {}
        for dim in v["dimensions"].values():
            for name, chk in dim["checks"].items():
                val, thr, op = chk.get("value"), chk.get("threshold"), chk.get("op")
                if name == "large_events_present":
                    row[name] = (0.5 if chk["verdict"] == "pass" else 2.0, chk["verdict"], None)
                elif val is None or thr in (None, 0):
                    row[name] = (None, chk["verdict"], val)
                elif op == ">=":
                    row[name] = (thr / val if val else 9.9, chk["verdict"], val)
                else:
                    row[name] = (abs(val) / thr, chk["verdict"], val)
        out[role] = row
    return out


def heatmap_figure(all_data: dict, out: Path) -> None:
    cmap = LinearSegmentedColormap.from_list("pass_fail", ["#1c5cab", "#86b6ef", "#f0efec", "#f19b8b", "#b8312f"])
    fig, axes = plt.subplots(2, 3, figsize=(12, 9.5), gridspec_kw={"wspace": 0.06, "hspace": 0.28})
    roles = list(COLORS)
    for k, (ax, (case, data)) in enumerate(zip(axes.ravel(), all_data.items())):
        v = _verdicts(data)
        grid = np.full((len(ORDER), len(roles)), np.nan)
        for j, role in enumerate(roles):
            for i, name in enumerate(ORDER):
                cell = (v.get(role) or {}).get(name)
                if cell and cell[0] is not None:
                    grid[i, j] = np.log2(max(min(cell[0], 8.0), 1 / 8))
        ax.imshow(np.ma.masked_invalid(grid), cmap=cmap, vmin=-3, vmax=3, aspect="auto")
        ax.set_facecolor("#ecebe7")
        for j, role in enumerate(roles):
            for i, name in enumerate(ORDER):
                cell = (v.get(role) or {}).get(name)
                if v.get(role) is None:
                    txt = "" if i else "not\ncompleted"
                elif not cell or cell[1] in (None, "insufficient") or cell[0] is None:
                    txt = "–"
                else:
                    mark = "✓" if cell[1] == "pass" else "✗" if cell[1] == "fail" else "?"
                    val = cell[2]
                    txt = mark if val is None else f"{mark} {val:.2g}" if abs(val) < 100 else f"{mark} {val:.0f}"
                ax.text(j, i, txt, ha="center", va="center", fontsize=6.3,
                        color="#ffffff" if np.isfinite(grid[i, j]) and abs(grid[i, j]) > 1.6 else INK)
        labels = []
        for r in roles:
            lab = data["catalogs"][r][0]
            labels.append(lab.replace(" (not completed)", "").replace("human-in-loop final", "HIL final"))
        ax.set_xticks(range(len(roles)), labels, rotation=30, ha="right", fontsize=7)
        ax.set_yticks(range(len(ORDER)), [CRITERION_LABEL[n] for n in ORDER] if k % 3 == 0 else [], fontsize=7)
        ax.set_title(CASES[case][0], loc="left", fontsize=9)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xticks(np.arange(-0.5, len(roles)), minor=True)
        ax.set_yticks(np.arange(-0.5, len(ORDER)), minor=True)
        ax.grid(which="minor", color="#fcfcfb", lw=2)
        ax.tick_params(which="minor", length=0)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(-3, 3))
    cb = fig.colorbar(sm, ax=axes, shrink=0.5, pad=0.02, ticks=[-3, -2, -1, 0, 1, 2, 3])
    cb.ax.set_yticklabels(["≤ 1/8", "1/4", "1/2", "1 (threshold)", "2", "4", "≥ 8"], fontsize=7)
    cb.set_label("value / threshold (blue passes, red fails)", fontsize=7.5)
    fig.suptitle("Trusted-catalog criteria: value relative to the threshold set by the human-in-loop final "
                 "(✓ pass, ✗ fail, – not applicable, no value or too few pairs; the blind audit of false events is not done yet)", x=0.01, ha="left", fontsize=9.5, color=INK)
    fig.savefig(out / "criteria_heatmap.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "docs/research/assets/results_overview")
    ap.add_argument("--cases", nargs="*", default=list(CASES))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    all_data = {}
    for case in a.cases:
        data = catalogs(case)
        all_data[case] = data
        space_figure(case, data, a.out)
        detection_figure(case, data, a.out)
        print("figures:", case, flush=True)
    heatmap_figure(all_data, a.out)
    print("figures: criteria_heatmap")


if __name__ == "__main__":
    main()
