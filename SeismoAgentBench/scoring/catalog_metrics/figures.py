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


def _strike_axes(xy: np.ndarray) -> tuple[np.ndarray, float]:
    """Unit vector of the principal horizontal axis (strike) of the epicentres, and its azimuth."""
    if len(xy) < 3:
        return np.array([0.0, 1.0]), 0.0
    w, v = np.linalg.eigh(np.cov((xy - np.median(xy, axis=0)).T))
    s = v[:, np.argmax(w)]
    if s[1] < 0:
        s = -s
    return s, float(np.degrees(np.arctan2(s[0], s[1])) % 180)


def spatial_figure(path: Path, cand: Population, ref: Population, final: Population | None, center, *, title: str) -> None:
    """The run, the human-in-loop final and the primary reference side by side, on the same extent and colour scale.

    Rows: map view, depth section along strike, depth section across strike (strike = principal axis of the
    final's epicentres, or of the reference's when there is no final). Bottom row: depth distributions,
    epicentral offset and origin-time difference against the final (with the reference as yardstick).
    """
    from matplotlib.colors import LogNorm

    pops = [(f"reference: {ref.key}", ref), ("human-in-loop final", final), ("this run", cand)]
    pops = [(name, p) for name, p in pops if p is not None]
    anchor = final if final is not None else ref
    axy = local_xyz(anchor.events[anchor.located], center)
    rxy = local_xyz(ref.events[ref.located], center)
    base = np.vstack([axy, rxy])
    origin = np.median(axy[:, :2], axis=0)
    strike, strike_az = _strike_axes(axy[:, :2])
    normal = np.array([strike[1], -strike[0]])
    along = (base[:, :2] - origin) @ strike
    across = (base[:, :2] - origin) @ normal
    pad = 1.15
    lim_x = np.percentile(base[:, 0], [0.5, 99.5]); lim_y = np.percentile(base[:, 1], [0.5, 99.5])
    half = max(np.ptp(lim_x), np.ptp(lim_y)) * pad / 2
    cx, cy = np.mean(lim_x), np.mean(lim_y)
    ext_map = (cx - half, cx + half, cy - half, cy + half)
    lim_a = np.percentile(along, [0.5, 99.5]) * pad
    lim_c = np.percentile(across, [0.5, 99.5]) * pad
    zs = base[:, 2][np.isfinite(base[:, 2])]
    lim_z = (np.floor(np.percentile(zs, 0.5)) - 1, np.ceil(np.percentile(zs, 99.5)) + 1) if len(zs) else (-1, 20)
    cell = max(2 * half / 90, 0.25)  # finer cells only resolve rounding of the coordinates

    plt.rcParams.update({"font.size": 7, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titlesize": 7.5, "axes.titlelocation": "left"})
    fig = plt.figure(figsize=(7.1, 10.2))
    gs = fig.add_gridspec(4, len(pops), height_ratios=[1.25, 0.8, 0.8, 1.0], hspace=0.45, wspace=0.28)
    norm = LogNorm(1, None)
    vmax = 1
    hist = []
    for j, (name, p) in enumerate(pops):
        xyz = local_xyz(p.events[p.located], center)
        al = (xyz[:, :2] - origin) @ strike
        ac = (xyz[:, :2] - origin) @ normal
        h_map = np.histogram2d(xyz[:, 0], xyz[:, 1], bins=[np.arange(ext_map[0], ext_map[1] + cell, cell),
                                                            np.arange(ext_map[2], ext_map[3] + cell, cell)])
        zok = np.isfinite(xyz[:, 2])
        h_al = np.histogram2d(al[zok], xyz[zok, 2], bins=[np.arange(lim_a[0], lim_a[1] + cell, cell),
                                                          np.arange(lim_z[0], lim_z[1] + cell, cell)])
        h_ac = np.histogram2d(ac[zok], xyz[zok, 2], bins=[np.arange(lim_c[0], lim_c[1] + cell, cell),
                                                          np.arange(lim_z[0], lim_z[1] + cell, cell)])
        outside = int((~((xyz[:, 0] >= ext_map[0]) & (xyz[:, 0] <= ext_map[1]) & (xyz[:, 1] >= ext_map[2]) & (xyz[:, 1] <= ext_map[3]))).sum())
        hist.append((name, p, h_map, h_al, h_ac, outside, len(xyz)))
        vmax = max(vmax, h_map[0].max(), h_al[0].max(), h_ac[0].max())
    norm = LogNorm(1, vmax)
    cmap = plt.get_cmap("Blues").copy()
    cmap.set_under("white")
    letters = iter("abcdefghijklmnopqrstuvwxyz")
    for j, (name, p, h_map, h_al, h_ac, outside, n) in enumerate(hist):
        for i, (h, xl, yl) in enumerate(((h_map, "east (km)", "north (km)"),
                                         (h_al, f"along strike, N{strike_az:.0f}°E (km)", "depth bsl (km)"),
                                         (h_ac, f"across strike, N{(strike_az + 90) % 360:.0f}°E (km)", "depth bsl (km)"))):
            ax = fig.add_subplot(gs[i, j])
            counts, xe, ye = h
            im = ax.pcolormesh(xe, ye, np.where(counts > 0, counts, np.nan).T, cmap=cmap, norm=norm, rasterized=True)
            if i == 0:
                ax.set_aspect("equal")
                ax.set_title(f"({next(letters)}) {name}\nn = {n:,}" + (f", {outside:,} outside view" if outside else ""))
                if strike is not None:
                    ax.plot([origin[0] - strike[0] * half, origin[0] + strike[0] * half],
                            [origin[1] - strike[1] * half, origin[1] + strike[1] * half], color="0.5", lw=0.5, ls="--")
            else:
                ax.invert_yaxis()
                ax.set_title(f"({next(letters)})")
                if not p.depth_known:
                    ax.text(0.5, 0.5, "depth datum unknown", transform=ax.transAxes, ha="center", fontsize=6.5, color="#D55E00")
            ax.set_xlabel(xl)
            if j == 0:
                ax.set_ylabel(yl)
    cax = fig.add_axes([0.92, 0.55, 0.012, 0.3])
    fig.colorbar(im, cax=cax).set_label(f"events per {cell:.2g} × {cell:.2g} km cell", fontsize=6.5)

    # bottom row: depth distributions, offsets and origin-time differences against the final
    ax = fig.add_subplot(gs[3, 0])
    colors = {"this run": CANDIDATE, "human-in-loop final": FINAL}
    bins = np.linspace(lim_z[0], lim_z[1], 50)
    for name, p, *_ in hist:
        z = p.events.depth_km.dropna().to_numpy()
        if len(z) and p.depth_known:
            ax.hist(z, bins=bins, orientation="horizontal", density=True, histtype="step", lw=1.3,
                    color=colors.get(name, REFERENCE), label=name.replace("reference: ", ""))
    ax.invert_yaxis()
    ax.set(xlabel="density", ylabel="depth bsl (km)")
    ax.legend(frameon=False, fontsize=6)
    ax.set_title(f"({next(letters)}) depth distributions")
    ax_off = fig.add_subplot(gs[3, 1]) if len(pops) > 1 else None
    ax_dt = fig.add_subplot(gs[3, 2]) if len(pops) > 2 else None
    if final is not None and ax_off is not None:
        diffs = []
        for name, p, color in (("this run", cand, CANDIDATE), (f"{ref.key}", ref, REFERENCE)):
            pairs = correspond(p, final)["pairs"]
            if not len(pairs):
                continue
            xa = local_xyz(p.events.iloc[pairs.a], center)
            xb = local_xyz(final.events.iloc[pairs.b], center)
            epi = np.hypot(*(xa[:, :2] - xb[:, :2]).T)
            _cdf(ax_off, epi, color, f"{name}: {np.median(epi):.2f} km ({len(epi):,})")
            if ax_dt is not None:
                diffs.append((name, color, p.events.time.to_numpy()[pairs.a] - final.events.time.to_numpy()[pairs.b]))
        if ax_dt is not None and diffs:
            span = float(np.clip(np.ceil(max(np.percentile(np.abs(d), 99) for _, _, d in diffs)), 2, 10))
            for name, color, dt in diffs:
                ax_dt.hist(np.clip(dt, -span, span), bins=np.linspace(-span, span, 61), density=True, histtype="step", lw=1.3,
                           color=color, label=f"{name}: {np.median(dt):+.2f} s")
        ax_off.set(xscale="log", xlim=(0.03, 20), ylim=(0, 1), xlabel="epicentral offset from the final (km)",
                   ylabel="cumulative fraction")
        ax_off.grid(color="0.92", lw=0.6)
        ax_off.legend(frameon=False, fontsize=5.8, loc="upper left", bbox_to_anchor=(0, -0.28), title="median (matched)",
                      title_fontsize=5.8)
        ax_off.set_title(f"({next(letters)}) offset from the final")
        if ax_dt is not None:
            ax_dt.axvline(0, color="0.7", lw=0.6)
            ax_dt.set(xlabel=f"origin time − final (s, clipped at ±{span:g})", ylabel="density")
            ax_dt.legend(frameon=False, fontsize=5.8, loc="upper left", bbox_to_anchor=(0, -0.28), title="median", title_fontsize=5.8)
            ax_dt.set_title(f"({next(letters)}) origin time against the final")
    fig.suptitle(title, x=0.01, ha="left", fontsize=8)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
