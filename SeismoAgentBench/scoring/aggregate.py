"""Task-level aggregation for one scientific catalog score."""

from __future__ import annotations

from typing import Any, Mapping


class AggregationError(ValueError):
    """Raised when a scientific score cannot be aggregated."""


def aggregate_catalog_score(score: Mapping[str, Any]) -> dict[str, Any]:
    """Create a transparent task summary without inventing a composite rank."""
    if score.get("status") != "scored":
        raise AggregationError("only scored scientific results can be aggregated")
    metrics = score.get("metrics")
    if not isinstance(metrics, Mapping):
        raise AggregationError("scientific score must contain a metrics object")
    required = {"candidate_events", "reference_events", "matched_events", "precision", "recall", "f1",
                "origin_time_error_s", "horizontal_error_km", "depth_error_km"}
    missing = sorted(required - set(metrics))
    if missing:
        raise AggregationError(f"scientific score is missing metrics: {', '.join(missing)}")
    return {
        "schema_version": 1,
        "status": "aggregated",
        "aggregator": {"name": "catalog-task-summary", "version": "1"},
        "source_scorer": score.get("scorer"),
        "reference": score.get("reference"),
        "metrics": {
            "detection": {
                "candidate_events": metrics["candidate_events"],
                "reference_events": metrics["reference_events"],
                "matched_events": metrics["matched_events"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
            },
            "location": {
                "origin_time_error_s": metrics["origin_time_error_s"],
                "horizontal_error_km": metrics["horizontal_error_km"],
            },
            "depth": metrics["depth_error_km"],
        },
        "source_metrics": dict(metrics),
        "matching": score.get("matching"),
        "matches": score.get("matches", []),
    }
