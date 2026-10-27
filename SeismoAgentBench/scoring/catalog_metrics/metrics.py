"""Metrics L1-L4 and L7 of docs/framework/03_EVALUATION_METRICS.md (§4-§5)."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

from .matching import CHANCE_SHIFT_S, SENSITIVITY_GATES, correspond, match
from .tables import Population, local_xyz

MAG_BIN = 0.5
M90_MIN_EVENTS = 10
PAIR_NEIGHBOURS = 10
PAIR_RADIUS_KM = 5.0
THICKNESS_NEIGHBOURS = 20


def _num(value: Any, digits: int = 4):
    if value is None:
        return None
    value = float(value)
    return round(value, digits) if np.isfinite(value) else None


def _median(values: np.ndarray):
    return _num(np.median(values)) if len(values) else None


def _p90(values: np.ndarray):
    return _num(np.percentile(values, 90)) if len(values) else None


def _mad(values: np.ndarray):
    return _num(np.median(np.abs(values - np.median(values)))) if len(values) else None


# ------------------------------------------------------------------ L1

def recall_by_magnitude(mags: np.ndarray, hit: np.ndarray) -> list[dict]:
    ok = np.isfinite(mags)
    if not ok.any():
        return []
    lo = np.floor(mags[ok].min() / MAG_BIN) * MAG_BIN
    bins = []
    for left in np.arange(lo, mags[ok].max() + MAG_BIN, MAG_BIN):
        sel = ok & (mags >= left - 1e-9) & (mags < left + MAG_BIN - 1e-9)
        if sel.any():
            bins.append({"magnitude_from": _num(left, 2), "events": int(sel.sum()),
                         "recall": _num(hit[sel].mean())})
    return bins


def m90(mags: np.ndarray, hit: np.ndarray) -> float | None:
    """Lowest reference magnitude M with recall(M_ref >= M) >= 0.9 (§5 L1)."""
    ok = np.isfinite(mags)
    if not ok.any():
        return None
    # Candidate thresholds are the reference's own magnitudes (to 0.1), so M90 is a magnitude it reports.
    for m in np.unique(np.round(mags[ok], 1)):
        sel = ok & (mags >= m - 0.05)
        if sel.sum() < M90_MIN_EVENTS:
            return None
        if hit[sel].mean() >= 0.9:
            return float(m)
    return None


def detection(ref: Population, result: Mapping[str, Any]) -> dict:
    pairs, n = result["pairs"], len(ref.events)
    out = {"matched": len(pairs), "reference_events": n, "recall": _num(len(pairs) / n) if n else None}
    if result["gates"][1] is None:
        out["chance"] = result["chance"]
        out["recall_net"] = _num((len(pairs) - result["chance"]) / n) if n else None
    hit = np.zeros(n, dtype=bool)
    hit[pairs.b] = True
    mags = ref.events.magnitude.to_numpy()
    out["recall_by_mag"] = recall_by_magnitude(mags, hit)
    out["M90"] = m90(mags, hit)
    return out


def effective_recall(entry: Mapping[str, Any]):
    """Chance-corrected recall for time-only pairing, raw recall otherwise."""
    return entry.get("recall_net", entry.get("recall"))


# ------------------------------------------------------------------ L2 / L4 / L7

def location(cand: Population, ref: Population, pairs) -> dict:
    d = pairs.distance_km[np.isfinite(pairs.distance_km)]
    out = {"pairs": int(len(d)), "epi_median_km": _median(d), "epi_p90_km": _p90(d),
           "dt_median_s": _median(pairs.dt_s)}
    if cand.depth_known and ref.depth_known:
        dz = cand.events.depth_km.to_numpy()[pairs.a] - ref.events.depth_km.to_numpy()[pairs.b]
        dz = dz[np.isfinite(dz)]
        out.update({"depth_pairs": int(len(dz)), "dz_median_km": _median(dz), "dz_mad_km": _mad(dz)})
    return out


def magnitude(cand: Population, ref: Population, pairs) -> dict:
    dm = cand.events.magnitude.to_numpy()[pairs.a] - ref.events.magnitude.to_numpy()[pairs.b]
    types = cand.events.magnitude_type.to_numpy()[pairs.a]
    ok = np.isfinite(dm)
    out = {"pairs": int(ok.sum()), "dmag_median": _median(dm[ok]), "dmag_mad": _mad(dm[ok]), "by_type": {}}
    for t in sorted(set(types[ok])):
        sel = ok & (types == t)
        out["by_type"][t or "unspecified"] = {"pairs": int(sel.sum()), "dmag_median": _median(dm[sel]),
                                               "dmag_mad": _mad(dm[sel])}
    return out


def uncertainty(cand: Population, ref: Population, pairs) -> dict | None:
    """Reported 1-sigma uncertainty against the actual difference (§5 L7)."""
    e = cand.events
    if not e.horizontal_uncertainty_km.notna().any():
        return None
    out = {}
    herr = e.horizontal_uncertainty_km.to_numpy()[pairs.a]
    ok = np.isfinite(herr) & np.isfinite(pairs.distance_km)
    out["horizontal"] = _coverage(herr[ok], pairs.distance_km[ok])
    if cand.depth_known and ref.depth_known and e.depth_uncertainty_km.notna().any():
        zerr = e.depth_uncertainty_km.to_numpy()[pairs.a]
        dz = np.abs(e.depth_km.to_numpy()[pairs.a] - ref.events.depth_km.to_numpy()[pairs.b])
        ok = np.isfinite(zerr) & np.isfinite(dz)
        out["depth"] = _coverage(zerr[ok], dz[ok])
    return out


def _coverage(reported: np.ndarray, error: np.ndarray) -> dict:
    out = {"pairs": int(len(error)), "coverage": _num((error <= reported).mean()) if len(error) else None}
    out["rank_corr"] = _num(spearmanr(reported, error)[0]) if len(error) >= 5 else None
    return out


# ------------------------------------------------------------------ L3

def pair_distance_error(cand: Population, ref: Population, pairs, center) -> dict:
    """|d_cand - d_ref| over each matched event's nearest matched neighbours (3-D, frame-free)."""
    xr = local_xyz(ref.events.iloc[pairs.b], center)
    xc = local_xyz(cand.events.iloc[pairs.a], center)
    ok = np.isfinite(xr).all(axis=1) & np.isfinite(xc).all(axis=1)
    xr, xc = xr[ok], xc[ok]
    if len(xr) < 2:
        return {"pairs": 0, "median_km": None, "p90_km": None}
    dist, idx = cKDTree(xr).query(xr, k=min(PAIR_NEIGHBOURS + 1, len(xr)), distance_upper_bound=PAIR_RADIUS_KM)
    i = np.repeat(np.arange(len(xr)), dist.shape[1] - 1)
    j, dref = idx[:, 1:].ravel(), dist[:, 1:].ravel()
    keep = np.isfinite(dref) & (i < j)
    i, j, dref = i[keep], j[keep], dref[keep]
    err = np.abs(np.linalg.norm(xc[i] - xc[j], axis=1) - dref)
    return {"pairs": int(len(err)), "median_km": _median(err), "p90_km": _p90(err)}


def off_structure_fraction(pop: Population, structure: Iterable[Population], center, radius_km: float) -> dict:
    """Fraction of located events whose epicentre is farther than ``radius_km`` from every
    structure-reference epicentre (depth is scored separately, by L2)."""
    refs = [r for r in structure if r.key != pop.key]
    if not refs:
        return {"fraction": None, "events": 0, "radius_km": radius_km}
    tree = cKDTree(np.vstack([local_xyz(r.events[r.located], center)[:, :2] for r in refs]))
    xy = local_xyz(pop.events[pop.located], center)[:, :2]
    nearest = tree.query(xy)[0] if len(xy) else np.array([])
    return {"fraction": _num((nearest > radius_km).mean()) if len(xy) else None, "events": int(len(xy)),
            "radius_km": radius_km, "members": [r.key for r in refs]}


def local_thickness(pop: Population, center) -> float | None:
    """Median minor-axis standard deviation of each event's 20 nearest neighbours (km)."""
    xyz = local_xyz(pop.events, center)
    xyz = xyz[np.isfinite(xyz).all(axis=1)]
    if len(xyz) <= THICKNESS_NEIGHBOURS:
        return None
    _, idx = cKDTree(xyz).query(xyz, k=THICKNESS_NEIGHBOURS + 1)
    groups = xyz[idx]
    centred = groups - groups.mean(axis=1, keepdims=True)
    cov = np.einsum("nki,nkj->nij", centred, centred) / (THICKNESS_NEIGHBOURS + 1)
    minor = np.sqrt(np.clip(np.linalg.eigvalsh(cov)[:, 0], 0.0, None))
    return _num(np.median(minor))


# ------------------------------------------------------------------ assembly

def versus(cand: Population, ref: Population, center) -> dict:
    """All per-reference metrics for the roles ``ref`` carries."""
    result = correspond(cand, ref)
    pairs = result["pairs"]
    out = {"gates": result["gates"], "roles": "".join(sorted(ref.roles))}
    if "D" in ref.roles:
        out["detection"] = detection(ref, result)
    located_pair = result["gates"][1] is not None
    if located_pair and "L" in ref.roles:
        out["location"] = location(cand, ref, pairs)
        unc = uncertainty(cand, ref, pairs)
        if unc is not None:
            out["uncertainty"] = unc
    if "M" in ref.roles:
        out["magnitude"] = magnitude(cand, ref, pairs)
    if located_pair and "S" in ref.roles:
        out["pair_distance_error"] = pair_distance_error(cand, ref, pairs, center)
    if located_pair and not ref.gates and ref.roles & {"D", "L"}:
        out["sensitivity"] = {}
        for gates in SENSITIVITY_GATES:
            p = correspond(cand, ref, gates)["pairs"]
            entry = {"matched": len(p)}
            if "D" in ref.roles:
                entry["recall"] = _num(len(p) / len(ref.events)) if len(ref.events) else None
            if "L" in ref.roles:
                entry["epi_median_km"] = _median(p.distance_km)
            out["sensitivity"][f"{gates[0]:g}s_{gates[1]:g}km"] = entry
    return out


def union_support(cand: Population, union: Iterable[Population]) -> dict:
    """Fraction of candidate events matched to at least one population of U (§5 L1).

    Located members match under their primary gates. Time-only members match
    on |dt| alone; their chance coincidences are removed in aggregate: the
    events that only a 60-s shifted time-only member would support, among
    those no located member supports, are subtracted (``fraction``);
    ``fraction_raw`` keeps them.
    """
    n = len(cand.events)
    located = np.zeros(n, dtype=bool)
    timed = np.zeros(n, dtype=bool)
    shifted = np.zeros(n, dtype=bool)
    members = []
    for pop in union:
        if pop.key == cand.key:
            continue
        result = correspond(cand, pop)
        if result["gates"][1] is None:
            timed[result["pairs"].a] = True
            dt_max = result["gates"][0]
            shifted[match(cand, pop, dt_max, None, shift_b_s=CHANCE_SHIFT_S).a] = True
        else:
            located[result["pairs"].a] = True
        members.append(pop.key)
    supported = located | timed
    chance = int((shifted & ~located).sum())
    return {"fraction": _num((supported.sum() - chance) / n) if n else None,
            "fraction_raw": _num(supported.mean()) if n else None, "supported": int(supported.sum()),
            "chance": chance, "events": n, "members": members, "unsupported_index": np.flatnonzero(~supported)}


def ceilings(refs: Mapping[str, Population]) -> dict:
    """Reference-to-reference recall: ceiling(R) = max over other D references (§4)."""
    detecting = {k: r for k, r in refs.items() if "D" in r.roles}
    out = {}
    for key, ref in detecting.items():
        recalls = {}
        for other_key, other in detecting.items():
            if other_key != key:
                recalls[other_key] = effective_recall(detection(ref, correspond(other, ref)))
        best = max(recalls, key=lambda k: -1 if recalls[k] is None else recalls[k]) if recalls else None
        out[key] = {"value": recalls.get(best), "by": best, "recalls": recalls}
    return out


def score_population(cand: Population, refs: Mapping[str, Population], *, expert: Population | None,
                     center, off_structure_km: float) -> dict:
    """Metrics of one catalog against every reference (and the expert)."""
    out = {"events": int(len(cand.events)), "located": int(cand.located.sum()), "versus": {}}
    for key, ref in refs.items():
        if key != cand.key:
            out["versus"][key] = versus(cand, ref, center)
    if expert is not None and expert.key != cand.key:
        out["versus"][expert.key] = versus(cand, expert, center)
    union = [r for r in refs.values() if "D" in r.roles] + ([expert] if expert is not None else [])
    out["union_support"] = union_support(cand, union)
    structure = [r for r in refs.values() if "S" in r.roles]
    out["off_structure"] = off_structure_fraction(cand, structure, center, off_structure_km)
    out["local_thickness_km"] = local_thickness(cand, center)
    out["magnitude_coverage"] = _num(cand.events.magnitude.notna().mean()) if len(cand.events) else None
    return out
