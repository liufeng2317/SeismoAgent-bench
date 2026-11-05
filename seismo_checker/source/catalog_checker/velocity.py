"""Generic 1-D velocity models for a region, from global models only (no case-specific information).

- ``crust1``: CRUST1.0 (Laske et al., 2013): the 1°×1° cell under each station and under the event
  centroid, water and ice removed, slowness-averaged over those columns (each column counted once).
- ``litho1``: LITHO1.0 (Pasyanos et al., 2014): the nearest node to each of the same points, the same way.

Columns are averaged (in slowness) against depth below their own solid surface, then placed at the
columns' mean surface elevation; columns under more than 0.2 km of water are offshore at this
resolution and are left out when any land column exists.
- ``ak135``, ``iasp91``, ``prem``: the crust and uppermost mantle of the global 1-D reference models
  (Kennett et al., 1995; Kennett & Engdahl, 1991; Dziewonski & Anderson, 1981; PREM's ocean layer
  replaced by its upper crust, isotropic values).

Every model is returned as step layers ``[(top_km_below_sea_level, vp_km_s, vs_km_s), ...]``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

MODELS_DIR = Path(__file__).resolve().parents[2] / "runtime/velocity_models"
GLOBAL_1D = {
    "ak135": [(0.0, 5.80, 3.46), (20.0, 6.50, 3.85), (35.0, 8.04, 4.48), (77.5, 8.045, 4.49)],
    "iasp91": [(0.0, 5.80, 3.36), (20.0, 6.50, 3.75), (35.0, 8.04, 4.47), (77.5, 8.045, 4.485)],
    "prem": [(0.0, 5.80, 3.20), (15.0, 6.80, 3.90), (24.4, 8.11, 4.49), (80.0, 8.08, 4.47)],
}
REL_DEPTHS = np.round(np.arange(0.0, 100.0 + 1e-9, 0.1), 3)  # km below the local solid surface
LAYER_MERGE_VP = 0.05
MIN_LAYER_KM = 0.5
MAX_WATER_KM = 0.2  # columns under deeper water are offshore at 1° and are left out when any land column exists


def _column(tops_bsl: np.ndarray, vp: np.ndarray, vs: np.ndarray, water_km: float) -> dict | None:
    """One model column as velocity against depth below its own solid surface."""
    ok = np.isfinite(tops_bsl) & np.isfinite(vp) & (vp > 0)
    tops, vp, vs = tops_bsl[ok], vp[ok], vs[ok]
    if not len(tops):
        return None
    order = np.argsort(tops, kind="stable")
    tops, vp, vs = tops[order], vp[order], vs[order]
    idx = np.clip(np.searchsorted(tops - tops[0], REL_DEPTHS, side="right") - 1, 0, len(tops) - 1)
    return {"surface_bsl": float(tops[0]), "water_km": water_km, "vp": vp[idx], "vs": np.maximum(vs[idx], 0.1)}


def _average(columns: list[dict]) -> list[tuple[float, float, float]]:
    land = [c for c in columns if c["water_km"] <= MAX_WATER_KM]
    use = land or columns
    vp = 1.0 / np.mean([1.0 / c["vp"] for c in use], axis=0)
    vs = 1.0 / np.mean([1.0 / c["vs"] for c in use], axis=0)
    datum = float(np.mean([c["surface_bsl"] for c in use]))  # mean solid surface, km below sea level
    rows = [(0.0, float(vp[0]), float(vs[0]))]
    for z, p, s in zip(REL_DEPTHS[1:], vp[1:], vs[1:]):
        if abs(p - rows[-1][1]) > LAYER_MERGE_VP and z - rows[-1][0] >= MIN_LAYER_KM:
            rows.append((float(z), float(p), float(s)))
    return [(round(z + datum, 2), round(p, 3), round(s, 3)) for z, p, s in rows]


def _crust1(lat: np.ndarray, lon: np.ndarray) -> tuple[list, int]:
    m = np.load(MODELS_DIR / "crust1.npz")
    cells = sorted({(int(np.clip(np.floor(89.999 - la), 0, 179)), int(np.clip(np.floor(lo + 180.0), 0, 359)))
                    for la, lo in zip(lat, lon)})
    columns = []
    for i, j in cells:
        top_elev = m["top_elev_km"][:, i, j].astype(float)
        thick = np.r_[-np.diff(top_elev), 1e9]
        keep = (np.arange(9) >= 2) & (thick > 0)  # drop water and ice and absent layers
        col = _column(-top_elev[keep], m["vp"][keep, i, j].astype(float), m["vs"][keep, i, j].astype(float),
                      water_km=float(max(thick[0], 0.0)))
        if col:
            columns.append(col)
    return _average(columns), len(columns)


def _litho1(lat: np.ndarray, lon: np.ndarray) -> tuple[list, int]:
    m = np.load(MODELS_DIR / "litho1.npz")
    nlat = np.radians(m["lat"].astype(float))
    nlon = np.radians(np.where(m["lon"] > 180, m["lon"] - 360, m["lon"]).astype(float))
    xyz = np.c_[np.cos(nlat) * np.cos(nlon), np.cos(nlat) * np.sin(nlon), np.sin(nlat)]
    plat, plon = np.radians(lat), np.radians(lon)
    pts = np.c_[np.cos(plat) * np.cos(plon), np.cos(plat) * np.sin(plon), np.sin(plat)]
    nodes = sorted({int(np.argmax(xyz @ p)) for p in pts})
    layers = list(m["layers"])
    keep = np.array([name != "WATER" for name in layers])
    w = layers.index("WATER")
    columns = []
    for k in nodes:
        tops = m["top_depth_km"][:, k].astype(float)
        nxt = tops[w + 1:][np.isfinite(tops[w + 1:])]
        water = float(nxt[0] - tops[w]) if len(nxt) and np.isfinite(tops[w]) else 0.0
        col = _column(tops[keep], m["vp"][keep, k].astype(float), m["vs"][keep, k].astype(float), water_km=max(water, 0.0))
        if col:
            columns.append(col)
    return _average(columns), len(columns)


def regional_models(lat: np.ndarray, lon: np.ndarray) -> dict[str, dict]:
    """All generic models for the points (stations and the event centroid): name -> {rows, source, columns}."""
    lat, lon = np.asarray(lat, dtype=float), np.asarray(lon, dtype=float)
    crust, nc = _crust1(lat, lon)
    litho, nl = _litho1(lat, lon)
    out = {"crust1": {"rows": crust, "source": "CRUST1.0, columns under stations and events", "columns": nc},
           "litho1": {"rows": litho, "source": "LITHO1.0, nodes nearest stations and events", "columns": nl}}
    for name, rows in GLOBAL_1D.items():
        out[name] = {"rows": rows, "source": f"{name} global 1-D (crust and uppermost mantle)", "columns": None}
    return out


def with_vpvs(rows: list, vpvs: float) -> list:
    """The same Vp layers with Vs = Vp / vpvs (a data-derived Vp/Vs)."""
    return [(z, p, round(p / vpvs, 3)) for z, p, _ in rows]
