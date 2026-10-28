"""Location diagnostics figure for one scored catalog (shift, scatter, depth, where the misfits are)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

from .matching import correspond  # noqa: E402
from .metrics import DEPTH_BAND_KM, densest_band  # noqa: E402
from .tables import Population, local_xyz  # noqa: E402

# Okabe-Ito, fixed order: candidate, expert final, expert blind, reference.
CANDIDATE, FINAL, BLIND, REFERENCE = "#0072B2", "#E69F00", "#009E73", "0.55"
# Offset classes on the map: sequential single hue (light -> dark blue), then vermillion for > 5 km.
OFFSET_EDGES = [0, 0.5, 1, 2, 5, 15]
OFFSET_COLORS = ["#c6dbef", "#6baed6", "#2171b5", "#08306b", "#D55E00"]


def _offsets(cand: Population, ref: Population, center):
    pairs = correspond(cand, ref)["pairs"]
    xa = local_xyz(cand.events.iloc[pairs.a], center)
    xb = local_xyz(ref.events.iloc[pairs.b], center)
    return xa, xb


def _cdf(ax, values, color, label, style="-"):
    v = np.sort(values)
    if len(v):
        ax.plot(v, np.arange(1, len(v) + 1) / len(v), color=color, lw=1.6, ls=style, label=label)


def location_figure(path: Path, cand: Population, ref: Population, structure: list, expert: dict, center,
                    *, title: str, off_structure_km: float) -> None:
    xa, xb = _offsets(cand, ref, center)
    offset = xa[:, :2] - xb[:, :2]
    epi = np.hypot(*offset.T) if len(offset) else np.array([])
    shift = np.median(offset, axis=0) if len(offset) else np.zeros(2)
    plt.rcParams.update({"font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titlesize": 8, "axes.titlelocation": "left"})
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 6.4))
    (a, b), (c, d) = axes

    # (a) offset vectors: the common shift (arrow) versus the scatter about it
    lim = 8.0
    a.scatter(np.clip(offset[:, 0], -lim, lim), np.clip(offset[:, 1], -lim, lim), s=3, lw=0,
              color=CANDIDATE, alpha=0.35, rasterized=True)
    for r in (2, 5):
        a.add_patch(plt.Circle((0, 0), r, fill=False, color="0.6", lw=0.6, ls="--"))
        a.text(r * 0.71, r * 0.71, f"{r} km", fontsize=6.5, color="0.4")
    a.annotate("", xy=shift, xytext=(0, 0), arrowprops={"arrowstyle": "-|>", "color": "#D55E00", "lw": 1.8})
    a.axhline(0, color="0.85", lw=0.6)
    a.axvline(0, color="0.85", lw=0.6)
    a.set(xlim=(-lim, lim), ylim=(-lim, lim), aspect="equal", xlabel="east offset (km)", ylabel="north offset (km)")
    scatter = np.median(np.hypot(*(offset - shift).T)) if len(offset) else np.nan
    a.set_title(f"(a) offset from {ref.key}, {len(offset):,} matched\n"
                f"shift {np.hypot(*shift):.2f} km (arrow) · scatter {scatter:.2f} km")
    a.text(0.02, 0.02, f"beyond ±{lim:g} km: drawn at the edge", transform=a.transAxes, fontsize=6, color="0.4")

    # (b) CDF of epicentral offset with the expert yardsticks
    _cdf(b, epi, CANDIDATE, f"this catalog (median {np.median(epi):.2f} km)" if len(epi) else "this catalog")
    for key, color, style in (("final", FINAL, "-"), ("blind", BLIND, "--")):
        if key in expert:
            xe, xr = _offsets(expert[key], ref, center)
            e = np.hypot(*(xe[:, :2] - xr[:, :2]).T)
            _cdf(b, e, color, f"human-in-loop {key} (median {np.median(e):.2f} km)", style)
    b.set(xscale="log", xlim=(0.03, 15), ylim=(0, 1), xlabel=f"epicentral offset from {ref.key} (km)",
          ylabel="cumulative fraction of matched events")
    b.grid(color="0.92", lw=0.6)
    b.legend(frameon=False, fontsize=6.5, loc="upper left")
    b.set_title("(b) offset distribution")

    # (c) depth distributions (population level, no matching)
    zc = cand.events.depth_km.dropna().to_numpy()
    zr = ref.events.depth_km.dropna().to_numpy()
    if len(zc) or len(zr):
        top = np.nanpercentile(np.concatenate([zc, zr]), [0.5, 99.5]) if len(zc) + len(zr) else (0, 20)
        bins = np.linspace(np.floor(top[0]) - 1, np.ceil(top[1]) + 1, 60)
        c.hist(zr, bins=bins, orientation="horizontal", density=True, color=REFERENCE, alpha=0.5, label=ref.key)
        c.hist(zc, bins=bins, orientation="horizontal", density=True, histtype="step", color=CANDIDATE, lw=1.4,
               label="this catalog" + ("" if cand.depth_known else " (datum unknown)"))
        for z, color, who in ((zc, CANDIDATE, "this catalog"), (zr, REFERENCE, ref.key)):
            if len(z):
                top_km, share = densest_band(z)
                if who == "this catalog":
                    c.axhspan(top_km, top_km + DEPTH_BAND_KM, color="#D55E00", alpha=0.12, lw=0)
                c.text(0.98, 0.04 if who == "this catalog" else 0.11,
                       f"densest 1 km, {who}: {share:.0%} ({top_km:.1f}-{top_km + DEPTH_BAND_KM:.1f} km)",
                       transform=c.transAxes, ha="right", fontsize=6.5,
                       color="#D55E00" if who == "this catalog" else "0.35")
        c.invert_yaxis()
        c.set(xlabel="density", ylabel="depth below sea level (km)")
        c.legend(frameon=False, fontsize=6.5, loc="center right")
    c.set_title("(c) depth distribution")

    # (d) where the misfits are: matched events by offset class, off-structure events marked
    rxy = np.vstack([local_xyz(r.events[r.located], center)[:, :2] for r in structure]) if structure else None
    d.scatter(*local_xyz(ref.events[ref.located], center)[:, :2].T, s=1, color="0.85", lw=0, rasterized=True,
              label=f"{ref.key} epicentres")
    cmap = ListedColormap(OFFSET_COLORS)
    norm = BoundaryNorm(OFFSET_EDGES, cmap.N)
    order = np.argsort(epi)
    sc = d.scatter(xb[order, 0], xb[order, 1], c=np.clip(epi[order], 0, 14.9), cmap=cmap, norm=norm, s=3, lw=0,
                   rasterized=True)
    if rxy is not None:
        own = local_xyz(cand.events[cand.located], center)[:, :2]
        far = cKDTree(rxy).query(own)[0] > off_structure_km
        d.scatter(*own[far].T, s=5, marker="x", lw=0.5, color="#CC79A7",
                  label=f"> {off_structure_km:g} km from structure ({far.mean():.1%})")
    span = np.percentile(np.abs(local_xyz(ref.events[ref.located], center)[:, :2]), 99) * 1.3
    d.set(xlim=(-span, span), ylim=(-span, span), aspect="equal", xlabel="km east", ylabel="km north")
    d.legend(frameon=False, fontsize=6.5, loc="lower left", markerscale=3)
    cb = fig.colorbar(sc, ax=d, shrink=0.8, ticks=OFFSET_EDGES)
    cb.set_label("offset (km), at the reference position", fontsize=6.5)
    d.set_title("(d) matched events by offset; off-structure events")

    fig.suptitle(title, x=0.01, ha="left", fontsize=8.5)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)
