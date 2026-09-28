"""Basic event-level scientific metrics for matched earthquake catalogs."""

from __future__ import annotations

from datetime import datetime
from statistics import mean, median
from typing import Any, Mapping

from .catalog import CatalogValidationError, validate_catalog
from .reference import MatchingPolicy, ReferenceError, match_events


class ScientificScoreError(ValueError):
    """Raised when scientific catalog metrics cannot be computed."""


def _average(values: list[float]) -> float | None:
    return mean(values) if values else None


def _percentile_summary(values: list[float]) -> dict[str, float | None]:
    return {"mean": _average(values), "median": median(values) if values else None}


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ScientificScoreError("catalog event times must include a timezone")
    return parsed


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def score_catalogs(candidate: Mapping[str, Any], reference: Mapping[str, Any], *,
                   reference_id: str, reference_version: str,
                   policy: MatchingPolicy | None = None) -> dict[str, Any]:
    """Compute basic event-level metrics from deterministic event matches.

    This is a first scientific scorer. It does not assign a single quality
    rank, compare magnitude distributions or aggregate across tasks.
    """
    try:
        candidate = validate_catalog(candidate)
        reference = validate_catalog(reference)
        matched = match_events(candidate, reference, policy)
    except (CatalogValidationError, ReferenceError) as exc:
        raise ScientificScoreError(str(exc)) from exc
    candidate_events = {event["event_id"]: event for event in candidate["events"]}
    reference_events = {event["event_id"]: event for event in reference["events"]}
    horizontal = [item["horizontal_distance_km"] for item in matched["matches"]]
    depth = [item["depth_difference_km"] for item in matched["matches"]]
    time_differences = [item["time_difference_s"] for item in matched["matches"]]
    matched_count = len(matched["matches"])
    candidate_count = len(candidate_events)
    reference_count = len(reference_events)
    precision = _rate(matched_count, candidate_count)
    recall = _rate(matched_count, reference_count)
    f1 = (2 * precision * recall / (precision + recall)
          if precision is not None and recall is not None and precision + recall else None)
    return {
        "schema_version": 1,
        "status": "scored",
        "scorer": {"name": "catalog-basic", "version": "1"},
        "reference": {"id": reference_id, "version": reference_version},
        "matching": matched,
        "metrics": {
            "candidate_events": candidate_count,
            "reference_events": reference_count,
            "matched_events": matched_count,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "origin_time_error_s": _percentile_summary(time_differences),
            "horizontal_error_km": _percentile_summary(horizontal),
            "depth_error_km": _percentile_summary(depth),
        },
        "matches": matched["matches"],
    }
