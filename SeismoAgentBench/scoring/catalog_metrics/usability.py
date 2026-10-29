"""Usability: is a run's catalog usable for science? (docs/framework/03_EVALUATION_METRICS.md §7a, v2).

A pass/fail summary over the headline, read against the human-in-loop
final of the same case. Each criterion has an absolute threshold, relaxed to
the final's own value plus a margin where the final itself would fail it
(e.g. a frame offset at Kaikoura, a magnitude-scale offset at Prague), so
the final always passes. A criterion whose metric the final lacks does not
apply; one the final has but the run lacks fails. The audit-based false
rate is ``pending`` until the blind review is labelled.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

LARGE_CLASSES = ("recall_M4", "recall_M5")


def _at_least(ratio: float) -> Callable:
    return lambda final: ratio * final


def _criteria() -> list[tuple[str, str, str, Callable[[float], float]]]:
    """(name, headline key, comparison, threshold from the final's value)."""
    return [
        ("detection", "recall_norm", ">=", _at_least(0.9)),
        ("detection_tight", "recall_tight", ">=", _at_least(0.9)),
        ("completeness_vs_final", "recall_final", ">=", lambda final: 0.5),
        ("inside_region", "out_of_mask_fraction", "<=", lambda final: max(0.10, final + 0.05)),
        ("false_events", "audited_false_rate", "<=", lambda final: 0.02),
        ("location_shift", "shift_km", "<=", lambda final: max(1.0, final + 0.5)),
        ("origin_time", "dt_median_s", "<=", lambda final: max(0.3, final + 0.2)),
        ("depth_vs_final", "dz_final_km", "abs<=", lambda final: 1.0),
        ("depth_pileup", "depth_mode_share", "<=", lambda final: max(0.05, final + 0.02)),
        ("structure", "off_structure_fraction", "<=", lambda final: max(0.05, 3 * final)),
        ("magnitude_offset", "dmag_median", "abs<=", lambda final: abs(final) + 0.2),
    ]


# Criteria whose threshold does not depend on the final apply even where the final row has no value
# (the final is not compared with itself; the audit is a per-run review).
FINAL_FREE = {"completeness_vs_final", "depth_vs_final", "false_events"}


def _passes(value: float, op: str, threshold: float) -> bool:
    if op == ">=":
        return value >= threshold - 1e-9
    if op == "<=":
        return value <= threshold + 1e-9
    return abs(value) <= threshold + 1e-9


def usability(headline: Mapping[str, Any], final: Mapping[str, Any] | None, completed: bool) -> dict:
    """Per-criterion values, thresholds and verdicts, and the overall ``usable`` flag.

    ``usable`` is True when every applicable criterion passes, False when any
    fails, and None while only pending criteria (the audit) remain open.
    """
    if not completed:
        return {"usable": False, "failed": ["completed"], "pending": [], "checks": {}}
    if final is None:
        return {"usable": None, "failed": [], "pending": ["baseline"], "checks": {},
                "note": "score the baseline (metrics_baseline.json) first"}
    checks, failed, pending = {}, [], []
    for name, key, op, rule in _criteria():
        reference = final.get(key)
        if reference is None and name not in FINAL_FREE:
            continue  # the final has no value: the criterion does not apply to this case
        threshold = round(rule(reference if reference is not None else 0.0), 4)
        value = headline.get(key)
        if value is None:
            verdict = "pending" if key == "audited_false_rate" else "fail"
        else:
            verdict = "pass" if _passes(value, op, threshold) else "fail"
        checks[name] = {"metric": key, "value": value, "op": op, "threshold": threshold, "final": reference,
                        "verdict": verdict}
        (failed if verdict == "fail" else pending if verdict == "pending" else []).append(name)
    large = {k: headline.get(k) for k in LARGE_CLASSES if final.get(k) is not None}
    if large:
        ok = all(v is not None and v >= 1.0 - 1e-9 for v in large.values())
        checks["large_events_present"] = {"metric": "+".join(large), "value": large, "op": "all ==",
                                          "threshold": 1.0, "verdict": "pass" if ok else "fail"}
        if not ok:
            failed.append("large_events_present")
    usable = False if failed else (None if pending else True)
    return {"usable": usable, "failed": failed, "pending": pending, "checks": checks}
