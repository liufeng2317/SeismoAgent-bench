"""Trusted-catalog verdict (docs/framework/02_Catalog_Metrics.md §7a, v2).

Does a run's catalog reach the standard of a trusted catalog? Judged on four
dimensions, each read against the human-in-loop final of the same case:

- ``reality``: the events are real (inside the region, few false events);
- ``time``, ``space``, ``strength``: each split into *accuracy* (a systematic
  offset from the final) and *stability* (spread and consistency).

Completeness (how many of the final's events the run recovers) is reported
next to the verdict, not judged: an incomplete catalog of accurate events
(an operational catalog, say) can still be trusted.

Thresholds are absolute, relaxed to the final's own value plus a margin
where the final itself would fail them. A criterion whose metric the final
lacks does not apply, except those measured against the final itself. A
metric the run lacks fails the criterion; the audit-based false rate is
``pending`` until the blind review is labelled.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

DIMENSIONS = ("reality", "time", "space", "strength")
COMPLETENESS = ("recall_norm", "recall_tight", "recall_final", "event_ratio_final")
LARGE_CLASSES = ("recall_M4", "recall_M5")


def _after_large_ratio(h: Mapping[str, Any]):
    after, other = h.get("recall_after_large"), h.get("recall_other")
    return after / other if after is not None and other else None


# (dimension, aspect, name, value getter, comparison, threshold from the final's value, needs the final's value)
Criterion = tuple[str, str, str, Callable, str, Callable[[float], float], bool]


def _key(name: str) -> Callable:
    return lambda h: h.get(name)


CRITERIA: list[Criterion] = [
    # events beyond the station coverage (hull + 10 km): poorly constrained, almost never sequence events;
    # the share outside the scoring mask also counts real regional events and is reported only (docs/research/progress/checker_validation/07_scoring_questions.md).
    # Where real seismicity lies beyond the network (the final has a share), the share also depends on how
    # many events inside were detected, so the margin scales with the final's share.
    ("reality", "accuracy", "inside_region", _key("out_of_coverage_fraction"), "<=", lambda f: max(0.05, 1.5 * f), True),
    ("reality", "accuracy", "false_events", _key("audited_false_rate"), "<=", lambda f: 0.02, False),
    ("time", "accuracy", "time_bias", _key("time_bias_final_s"), "abs<=", lambda f: 0.3, False),
    ("time", "stability", "time_spread", _key("time_mad_final_s"), "<=", lambda f: 0.3, False),
    ("time", "stability", "after_large_events", _after_large_ratio, ">=", lambda f: 0.8 * f, True),
    ("space", "accuracy", "horizontal_shift", _key("shift_final_km"), "<=", lambda f: 1.0, False),
    ("space", "accuracy", "depth_bias", _key("dz_final_km"), "abs<=", lambda f: 1.0, False),
    ("space", "stability", "horizontal_scatter", _key("scatter_final_km"), "<=",
     lambda f: max(1.0, f), True),  # threshold from the final's own scatter about the primary reference
    ("space", "stability", "off_structure", _key("off_structure_fraction"), "<=", lambda f: max(0.05, 3 * f), True),
    ("space", "stability", "depth_pileup", _key("depth_mode_share"), "<=", lambda f: max(0.05, f + 0.02), True),
    ("strength", "accuracy", "magnitude_offset", _key("dmag_median"), "abs<=", lambda f: abs(f) + 0.2, True),
    ("strength", "stability", "magnitude_spread", _key("dmag_std"), "<=", lambda f: max(0.3, f + 0.1), True),
    ("strength", "stability", "magnitude_scale", _key("dmag_slope_per_unit"), "abs<=",
     lambda f: max(0.2, abs(f) + 0.1), True),
]
# Headline key each criterion reads (after_large_events is the ratio recall_after_large / recall_other).
CRITERION_METRIC = {
    "inside_region": "out_of_coverage_fraction", "false_events": "audited_false_rate",
    "time_bias": "time_bias_final_s", "time_spread": "time_mad_final_s", "after_large_events": "after_large",
    "horizontal_shift": "shift_final_km", "depth_bias": "dz_final_km", "horizontal_scatter": "scatter_final_km",
    "off_structure": "off_structure_fraction", "depth_pileup": "depth_mode_share",
    "magnitude_offset": "dmag_median", "magnitude_spread": "dmag_std", "magnitude_scale": "dmag_slope_per_unit",
    "large_events_present": "recall_M4",
}
# The final's value that sets a threshold, where it is not the same headline key.
FINAL_SOURCE = {"horizontal_scatter": "scatter_median_km"}


def _passes(value: float, op: str, threshold: float) -> bool:
    if op == ">=":
        return value >= threshold - 1e-9
    if op == "<=":
        return value <= threshold + 1e-9
    return abs(value) <= threshold + 1e-9


def _final_value(name: str, getter: Callable, final: Mapping[str, Any]):
    if name in FINAL_SOURCE:
        return final.get(FINAL_SOURCE[name])
    return getter(final)


def trust_verdict(headline: Mapping[str, Any], final: Mapping[str, Any] | None, completed: bool) -> dict:
    """Per-dimension verdicts and the overall ``trusted`` flag, with completeness alongside.

    A dimension passes when all its applicable criteria pass; it is pending when
    only the audit is open. ``trusted`` is True when all four dimensions pass,
    False when any fails, None while only pending criteria remain.
    """
    completeness = {k: headline.get(k) for k in COMPLETENESS}
    if not completed:
        return {"trusted": False, "failed": ["completed"], "pending": [], "dimensions": {},
                "completeness": completeness}
    if final is None:
        return {"trusted": None, "failed": [], "pending": ["baseline"], "dimensions": {},
                "completeness": completeness, "note": "score the baseline (metrics_baseline.json) first"}
    dims = {d: {"verdict": "pass", "checks": {}} for d in DIMENSIONS}
    failed, pending = [], []
    for dim, aspect, name, getter, op, rule, needs_final in CRITERIA:
        reference = _final_value(name, getter, final)
        if needs_final and reference is None:
            continue  # the final has no value: the criterion does not apply to this case
        threshold = round(rule(reference if reference is not None else 0.0), 4)
        value = getter(headline)
        if value is None and name == "magnitude_scale" and (headline.get("dmag_pairs") or 0) >= 5:
            verdict = "insufficient"  # magnitudes exist but too few pairs for a slope (SLOPE_MIN_PAIRS)
        elif value is None:
            verdict = "pending" if name == "false_events" else "fail"
        else:
            verdict = "pass" if _passes(value, op, threshold) else "fail"
        dims[dim]["checks"][name] = {"aspect": aspect, "value": None if value is None else round(value, 4),
                                     "op": op, "threshold": threshold,
                                     "final": None if reference is None else round(reference, 4),
                                     "verdict": verdict}
        if verdict == "fail":
            failed.append(name)
        elif verdict == "pending":
            pending.append(name)
    large = {k: headline.get(k) for k in LARGE_CLASSES if final.get(k) is not None}
    if large:
        ok = all(v is not None and v >= 1.0 - 1e-9 for v in large.values())
        dims["strength"]["checks"]["large_events_present"] = {"aspect": "accuracy", "value": large,
                                                              "op": "all ==", "threshold": 1.0,
                                                              "verdict": "pass" if ok else "fail"}
        if not ok:
            failed.append("large_events_present")
    for d in dims.values():
        verdicts = {c["verdict"] for c in d["checks"].values()}
        d["verdict"] = "fail" if "fail" in verdicts else "pending" if "pending" in verdicts else "pass"
    trusted = False if failed else (None if pending else True)
    return {"trusted": trusted, "failed": failed, "pending": pending, "dimensions": dims,
            "completeness": completeness}
