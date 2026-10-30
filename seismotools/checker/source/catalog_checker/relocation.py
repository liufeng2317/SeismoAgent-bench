"""Stage 5, relative relocation: compare the catalog before and after relocation, event by event.

Relative relocation should sharpen the relative positions without moving the catalog as a whole or
creating structure that is thinner than the data can resolve. Events are matched by ``event_id``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .checks import Check, _skip
from .io import local_km

RELOCATION_DEFAULTS = {
    "relocated_share_min": 0.5, "shift_max_km": 1.5, "displacement_large_km": 5.0, "displacement_large_share_max": 0.05,
    "thickness_neighbours": 20, "thickness_events": 3000, "thinning_ratio_max": 5.0,
}


def _xyz(e: pd.DataFrame, lat0: float, lon0: float) -> np.ndarray:
    x, y = local_km(e.latitude, e.longitude, lat0, lon0)
    return np.c_[x, y, e.depth_km.to_numpy(dtype=float)]


def local_thickness(xyz: np.ndarray, k: int, n: int) -> float:
    """Median over events of the smallest principal standard deviation of each event's k nearest neighbours."""
    if len(xyz) <= k:
        return np.nan
    idx = np.linspace(0, len(xyz) - 1, min(n, len(xyz))).round().astype(int)
    _, nn = cKDTree(xyz).query(xyz[idx], k=k + 1)
    out = []
    for row in nn:
        pts = xyz[row]
        ev = np.linalg.eigvalsh(np.cov((pts - pts.mean(axis=0)).T))
        out.append(np.sqrt(max(ev[0], 0.0)))
    return float(np.median(out))


def relocation_checks(before: pd.DataFrame, after: pd.DataFrame, lat0: float, lon0: float, c: dict) -> tuple[list[Check], dict]:
    c = {**RELOCATION_DEFAULTS, **c}
    b = before.dropna(subset=["latitude", "longitude", "depth_km"]).drop_duplicates("event_id").set_index("event_id")
    a = after.dropna(subset=["latitude", "longitude", "depth_km"]).drop_duplicates("event_id").set_index("event_id")
    common = b.index.intersection(a.index)
    exp_share = f"share ≥ {c['relocated_share_min']:.0%} of located events moved by relocation"
    if len(common) < 20:
        why = f"{len(common)} events in both catalogs (matched by event_id)"
        return [_skip(i, "space", u, e, len(common), why) for i, u, e in (
            ("relocated_share", "share", exp_share), ("relocation_shift", "km", ""), ("relocation_large_moves", "share", ""),
            ("relocation_thinning", "ratio", ""))], {}
    xb, xa = _xyz(b.loc[common], lat0, lon0), _xyz(a.loc[common], lat0, lon0)
    disp = xa - xb
    moved = np.linalg.norm(disp, axis=1) > 1e-3
    share = float(moved.sum() / len(b))
    checks = [Check("relocated_share", "space", share, "share", exp_share, len(b), share < c["relocated_share_min"],
                    f"Only {moved.sum():,} of {len(b):,} located events changed position in relocation." if share < c["relocated_share_min"] else None,
                    {"events_before": int(len(b)), "events_after": int(len(a)), "in_both": int(len(common)), "moved": int(moved.sum()),
                     "only_after": int(len(a.index.difference(b.index)))})]
    d = disp[moved] if moved.any() else disp
    med = np.median(d, axis=0)
    horiz = float(np.hypot(med[0], med[1]))
    flag = horiz > c["shift_max_km"] or abs(med[2]) > c["shift_max_km"]
    checks.append(Check("relocation_shift", "space", max(horiz, abs(float(med[2]))), "km",
                        f"median displacement of moved events ≤ {c['shift_max_km']} km horizontally and in depth", len(d), flag,
                        (f"Relocation moved the events by a median {med[0]:+.2f} km east, {med[1]:+.2f} km north and {med[2]:+.2f} km down.") if flag else None,
                        {"median_east_km": round(float(med[0]), 3), "median_north_km": round(float(med[1]), 3), "median_down_km": round(float(med[2]), 3)}))
    dist = np.linalg.norm(d, axis=1)
    large = float((dist > c["displacement_large_km"]).mean())
    flag = large > c["displacement_large_share_max"]
    checks.append(Check("relocation_large_moves", "space", large, "share",
                        f"share ≤ {c['displacement_large_share_max']:.0%} of moved events displaced by more than {c['displacement_large_km']} km", len(d), flag,
                        f"{large:.1%} of moved events moved by more than {c['displacement_large_km']} km." if flag else None,
                        {"displacement_km_quantiles": {q: round(float(np.quantile(dist, q)), 3) for q in (0.5, 0.9, 0.99)}}))
    tb = local_thickness(xb[moved], c["thickness_neighbours"], c["thickness_events"])
    ta = local_thickness(xa[moved], c["thickness_neighbours"], c["thickness_events"])
    ratio = tb / max(ta, 0.001) if np.isfinite(ta) and np.isfinite(tb) else np.nan  # 1 m floor: a fully collapsed cluster has zero thickness
    flag = bool(np.isfinite(ratio) and ratio > c["thinning_ratio_max"])
    checks.append(Check("relocation_thinning", "space", ratio, "ratio",
                        f"local thickness before ÷ after ≤ {c['thinning_ratio_max']} (smallest principal spread of {c['thickness_neighbours']} neighbours)",
                        int(moved.sum()), flag,
                        f"Relocation made the local structure {ratio:.1f}× thinner ({tb:.2f} km → {ta:.2f} km)." if flag else None,
                        {"thickness_before_km": round(tb, 3), "thickness_after_km": round(ta, 3)}))
    return checks, {"xyz_before": xb, "xyz_after": xa, "moved": moved}


def read_dtcc(path: Path) -> dict:
    """Summary of a hypoDD dt.cc file: pairs, observations per pair, correlation coefficients."""
    pairs, obs, cc = 0, [], []
    n = 0
    with Path(path).open() as f:
        for line in f:
            if line.startswith("#"):
                if pairs:
                    obs.append(n)
                pairs, n = pairs + 1, 0
                continue
            parts = line.split()
            if len(parts) >= 3:
                n += 1
                try:
                    cc.append(float(parts[2]))
                except ValueError:
                    pass
    if pairs:
        obs.append(n)
    return {"pairs": pairs, "observations": int(sum(obs)), "median_observations_per_pair": float(np.median(obs)) if obs else None,
            "cc_quantiles": {q: round(float(np.quantile(cc, q)), 3) for q in (0.1, 0.5, 0.9)} if cc else None}


def relocation_figure(extra: dict, output_dir: Path) -> str | None:
    if not extra:
        return None
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    xb, xa, moved = extra["xyz_before"], extra["xyz_after"], extra["moved"]
    fig, ax = plt.subplots(3, 3, figsize=(14, 13))
    lim = [np.percentile(np.r_[xb[:, i], xa[:, i]], [0.5, 99.5]) for i in range(3)]
    for r, (xyz, name) in enumerate(((xb, "before"), (xa, "after"))):
        for col, (i, j, lab) in enumerate(((0, 1, ("east (km)", "north (km)")), (0, 2, ("east (km)", "depth (km)")), (1, 2, ("north (km)", "depth (km)")))):
            a = ax[r, col]
            a.scatter(xyz[:, i], xyz[:, j], s=0.5, c="k", alpha=0.4, rasterized=True)
            a.set(xlim=lim[i], ylim=lim[j][::-1] if j == 2 else lim[j], xlabel=lab[0], ylabel=lab[1], title=f"{name}: {lab[1].split()[0]} vs {lab[0].split()[0]}")
            a.set_aspect("equal", adjustable="box")
    a = ax[2, 0]
    sel = np.where(moved)[0]
    sel = sel[np.linspace(0, len(sel) - 1, min(600, len(sel))).round().astype(int)] if len(sel) else sel
    a.quiver(xb[sel, 0], xb[sel, 1], xa[sel, 0] - xb[sel, 0], xa[sel, 1] - xb[sel, 1], angles="xy", scale_units="xy", scale=1, width=0.002)
    a.set(xlim=lim[0], ylim=lim[1], xlabel="east (km)", ylabel="north (km)", title="Displacement (sample, true scale)")
    a = ax[2, 1]
    dist = np.linalg.norm((xa - xb)[moved], axis=1)
    a.hist(np.clip(dist, 0, 10), bins=60)
    a.set(xlabel="displacement (km, clipped at 10)", ylabel="events", title="Displacement")
    a = ax[2, 2]
    a.hist(np.clip((xa - xb)[moved, 2], -5, 5), bins=60)
    a.set(xlabel="depth change (km, + deeper)", ylabel="events", title="Depth change")
    fig.tight_layout()
    fig.savefig(output_dir / "relocation_comparison.png", dpi=100)
    plt.close(fig)
    return "relocation_comparison.png"
