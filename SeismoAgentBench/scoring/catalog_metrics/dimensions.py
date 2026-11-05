"""Time, space and strength by magnitude class (docs/framework/02_Catalog_Metrics.md §5, §5.1).

Magnitude classes use the case's magnitude authority (its operational
catalog; Prague: Cochran). A candidate event enters class M>=T after its
median magnitude offset from the authority is removed, so precision and F1
measure detection; the calibration itself is scored under ``strength``.
"""

from __future__ import annotations

import numpy as np

from .matching import correspond
from .tables import Population, local_xyz

CLASSES = (2.0, 3.0, 4.0, 5.0)
LIST_EVENTS_UP_TO = 20       # list every reference event of a class this small (and of every M4+ class)
LIST_FROM_MAGNITUDE = 4.0
BIAS_MIN_PAIRS = 5
SLOPE_MIN_PAIRS = 30  # a magnitude-scale slope from fewer pairs is not judged (docs/research/progress/records/07_scoring_questions.md)
MC_BIN = 0.1
MC_CORRECTION = 0.2          # maximum curvature + 0.2 (Woessner & Wiemer 2005)
B_MIN_EVENTS = 50
AFTER_LARGE_S = 3600.0
DAY_S = 86400.0


def _num(value, digits: int = 4):
    if value is None:
        return None
    value = float(value)
    return round(value, digits) if np.isfinite(value) else None


def _describe(values: np.ndarray, signed: bool = True) -> dict:
    """Mean, median, standard deviation and 90th percentile of |value| (n alongside)."""
    v = values[np.isfinite(values)]
    if not len(v):
        return {"n": 0}
    out = {"n": int(len(v)), "mean": _num(v.mean()), "median": _num(np.median(v)),
           "std": _num(v.std(ddof=1)) if len(v) > 1 else None}
    out["abs_p90" if signed else "p90"] = _num(np.percentile(np.abs(v), 90))
    return out


def _pair_errors(cand: Population, ref: Population, pairs, center) -> dict:
    """Per matched pair: signed dt, epicentral distance, signed dz, signed dmag."""
    ea, eb = cand.events.iloc[pairs.a], ref.events.iloc[pairs.b]
    xa, xb = local_xyz(ea, center), local_xyz(eb, center)
    return {"dt_s": ea.time.to_numpy() - eb.time.to_numpy(),
            "epi_km": np.hypot(*(xa[:, :2] - xb[:, :2]).T),
            "dz_km": xa[:, 2] - xb[:, 2],
            "dmag": ea.magnitude.to_numpy() - eb.magnitude.to_numpy()}


def magnitude_bias(cand: Population, authority: Population, pairs) -> float | None:
    dm = cand.events.magnitude.to_numpy()[pairs.a] - authority.events.magnitude.to_numpy()[pairs.b]
    dm = dm[np.isfinite(dm)]
    return float(np.median(dm)) if len(dm) >= BIAS_MIN_PAIRS else None


def magnitude_classes(cand: Population, authority: Population, center, pairs=None, supported=None) -> dict:
    """Recall, precision, F1 and matched-pair error distributions for M>=2, 3, 4, 5.

    A candidate event counts as real when it matches an authority event or,
    given ``supported`` (union support, §5 L1), any other reference: an
    operational catalog can be incomplete even at M 2 (Kilauea, 4-5 May 2018).
    """
    if pairs is None:
        pairs = correspond(cand, authority)["pairs"]
    bias = magnitude_bias(cand, authority, pairs)
    m_ref = authority.events.magnitude.to_numpy()
    m_cand = cand.events.magnitude.to_numpy()
    aligned = m_cand - (bias or 0.0)
    matched_cand = np.zeros(len(m_cand), dtype=bool)
    matched_cand[pairs.a] = True
    real = matched_cand | (supported if supported is not None else False)
    pair_of_ref = np.full(len(m_ref), -1)
    pair_of_ref[pairs.b] = np.arange(len(pairs))
    errors = _pair_errors(cand, authority, pairs, center)
    out = {"authority": authority.key, "magnitude_bias": _num(bias), "bias_removed": bias is not None,
           "candidate_without_magnitude": int(np.isnan(m_cand).sum()), "classes": {}}
    for t in CLASSES:
        ref_in = np.flatnonzero(m_ref >= t - 1e-9)
        if not len(ref_in):
            continue
        hit = pair_of_ref[ref_in] >= 0
        recall = hit.mean()
        cand_in = np.isfinite(aligned) & (aligned >= t - 1e-9)
        raw_in = np.isfinite(m_cand) & (m_cand >= t - 1e-9)
        precision = real[cand_in].mean() if cand_in.any() else None
        f1 = (2 * precision * recall / (precision + recall)
              if precision is not None and precision + recall > 0 else None)
        sel = pair_of_ref[ref_in][hit]
        entry = {"reference_events": int(len(ref_in)), "matched": int(hit.sum()), "recall": _num(recall),
                 "candidate_events": int(cand_in.sum()), "precision": _num(precision), "f1": _num(f1),
                 "precision_unaligned": _num(real[raw_in].mean()) if raw_in.any() else None,
                 "precision_authority_only": _num(matched_cand[cand_in].mean()) if cand_in.any() else None,
                 "dt_s": _describe(errors["dt_s"][sel]), "epi_km": _describe(errors["epi_km"][sel], signed=False),
                 "dz_km": _describe(errors["dz_km"][sel]), "dmag": _describe(errors["dmag"][sel])}
        if cand.depth_known is False or authority.depth_known is False:
            entry["dz_km"]["datum_known"] = False
        if len(ref_in) <= LIST_EVENTS_UP_TO or t >= LIST_FROM_MAGNITUDE:
            entry["events"] = _event_list(authority, ref_in, pair_of_ref, errors, cand, pairs)
        out["classes"][f"M{t:g}"] = entry
    return out


def _event_list(authority, ref_in, pair_of_ref, errors, cand, pairs) -> list:
    rows = []
    e = authority.events
    for j in ref_in[np.argsort(-e.magnitude.to_numpy()[ref_in])]:
        k = pair_of_ref[j]
        row = {"reference_event_id": str(e.event_id.iloc[j]),
               "origin_time_utc": str(np.datetime64(int(round(e.time.iloc[j] * 1e6)), "us")) + "Z",
               "reference_magnitude": _num(e.magnitude.iloc[j], 2), "matched": bool(k >= 0)}
        if k >= 0:
            row.update({"candidate_event_id": str(cand.events.event_id.iloc[pairs.a[k]]),
                        "candidate_magnitude": _num(cand.events.magnitude.iloc[pairs.a[k]], 2),
                        "dt_s": _num(errors["dt_s"][k], 3), "epi_km": _num(errors["epi_km"][k], 3),
                        "dz_km": _num(errors["dz_km"][k], 3), "dmag": _num(errors["dmag"][k], 3)})
        rows.append(row)
    return rows


# ------------------------------------------------------------------ strength

def mc_max_curvature(m: np.ndarray) -> float | None:
    m = m[np.isfinite(m)]
    if len(m) < B_MIN_EVENTS:
        return None
    bins = np.round(np.floor(m / MC_BIN) * MC_BIN, 1)
    values, counts = np.unique(bins, return_counts=True)
    return float(values[counts.argmax()] + MC_CORRECTION)


def b_value(m: np.ndarray, mc: float | None) -> dict:
    """Aki-Utsu maximum-likelihood b above Mc, with Shi & Bolt (1982) uncertainty."""
    if mc is None:
        return {"b": None, "n": 0}
    m = m[np.isfinite(m) & (m >= mc - MC_BIN / 2)]
    if len(m) < B_MIN_EVENTS:
        return {"b": None, "n": int(len(m))}
    b = np.log10(np.e) / (m.mean() - (mc - MC_BIN / 2))
    sigma = 2.3 * b * b * np.sqrt(((m - m.mean()) ** 2).sum() / (len(m) * (len(m) - 1)))
    return {"b": _num(b, 3), "b_sigma": _num(sigma, 3), "n": int(len(m))}


def strength(cand: Population, authority: Population, pairs) -> dict:
    """Magnitude calibration against the authority and the magnitude-frequency distribution."""
    m_c = cand.events.magnitude.to_numpy()
    m_a = authority.events.magnitude.to_numpy()
    dm = m_c[pairs.a] - m_a[pairs.b]
    ok = np.isfinite(dm)
    out = {"authority": authority.key, "pairs": int(ok.sum()), "dmag": _describe(dm[ok])}
    if ok.sum() >= BIAS_MIN_PAIRS:
        out["dmag"]["mad"] = _num(np.median(np.abs(dm[ok] - np.median(dm[ok]))))
    if ok.sum() >= SLOPE_MIN_PAIRS:
        # Slope of dmag against the authority magnitude: < 0 means compression or saturation of large events.
        slope, intercept = np.polyfit(m_a[pairs.b][ok], dm[ok], 1)
        out["dmag_slope_per_unit"] = _num(slope)
    mc_c, mc_a = mc_max_curvature(m_c), mc_max_curvature(m_a)
    out["candidate"] = {"mc": _num(mc_c, 2), **b_value(m_c, mc_c)}
    out["authority_mfd"] = {"mc": _num(mc_a, 2), **b_value(m_a, mc_a)}
    if out["candidate"]["b"] is not None and out["authority_mfd"]["b"] is not None:
        out["b_difference"] = _num(out["candidate"]["b"] - out["authority_mfd"]["b"], 3)
    return out


# ------------------------------------------------------------------ time

def time_profile(cand: Population, detection_ref: Population, authority: Population, pairs, mask: dict) -> dict:
    """Origin-time errors, daily recall and recall right after large events."""
    t_ref = detection_ref.events.time.to_numpy()
    hit = np.zeros(len(t_ref), dtype=bool)
    hit[pairs.b] = True
    dt = cand.events.time.to_numpy()[pairs.a] - t_ref[pairs.b]
    out = {"reference": detection_ref.key, "dt_s": _describe(dt)}
    day = np.floor((t_ref - mask["start"]) / DAY_S).astype(int)
    out["recall_by_day"] = [{"day": int(d), "events": int((day == d).sum()), "recall": _num(hit[day == d].mean())}
                            for d in np.unique(day)]
    m_a = authority.events.magnitude.to_numpy()
    for threshold in (4.0, 3.0):
        large = authority.events.time.to_numpy()[np.isfinite(m_a) & (m_a >= threshold)]
        if len(large):
            break
    if len(large):
        k = np.searchsorted(large, t_ref, side="right") - 1
        after = (k >= 0) & (t_ref - large[np.clip(k, 0, None)] <= AFTER_LARGE_S)
        out["after_large"] = {"threshold": threshold, "large_events": int(len(large)), "window_s": AFTER_LARGE_S,
                              "events_after": int(after.sum()),
                              "recall_after": _num(hit[after].mean()) if after.any() else None,
                              "recall_other": _num(hit[~after].mean()) if (~after).any() else None}
    return out
