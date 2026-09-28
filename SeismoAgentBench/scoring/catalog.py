"""Validation of the versioned, generic earthquake catalog format."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Mapping


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_EVENT_FIELDS = {
    "event_id", "origin_time", "latitude", "longitude", "depth_km", "magnitude",
    "magnitude_type", "horizontal_uncertainty_km", "depth_uncertainty_km",
    "origin_time_uncertainty_s", "location_method", "picks",
}
_PICK_FIELDS = {"pick_id", "station_id", "phase", "arrival_time", "probability"}


class CatalogValidationError(ValueError):
    """Raised when a catalog does not satisfy the output contract."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _time(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{label} must be an ISO-8601 string")
        return
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} is not a valid ISO-8601 timestamp")
        return
    if parsed.tzinfo is None:
        errors.append(f"{label} must include a timezone")


def _number(value: Any, label: str, errors: list[str], *, minimum: float | None = None,
            maximum: float | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{label} must be numeric")
        return
    if minimum is not None and value < minimum:
        errors.append(f"{label} must be >= {minimum}")
    if maximum is not None and value > maximum:
        errors.append(f"{label} must be <= {maximum}")


def _unknown(value: Mapping[str, Any], allowed: set[str], label: str, errors: list[str]) -> None:
    for key in sorted(set(value) - allowed):
        errors.append(f"{label} has unknown field {key!r}")


def validate_catalog(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a catalog without modifying it or applying science rules."""
    errors: list[str] = []
    if not isinstance(value, dict):
        raise CatalogValidationError(["catalog must be an object"])
    _unknown(value, {"schema_version", "catalog_id", "description", "events"}, "catalog", errors)
    if value.get("schema_version") != 1:
        errors.append("catalog.schema_version must be 1")
    if not isinstance(value.get("catalog_id"), str) or not _ID.fullmatch(value.get("catalog_id", "")):
        errors.append("catalog.catalog_id has an invalid identifier")
    events = value.get("events")
    if not isinstance(events, list):
        errors.append("catalog.events must be a list")
        events = []
    seen_events: set[str] = set()
    for index, event in enumerate(events):
        label = f"catalog.events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown(event, _EVENT_FIELDS, label, errors)
        for field in ("event_id", "origin_time", "latitude", "longitude", "depth_km"):
            if field not in event:
                errors.append(f"{label} is missing required field {field!r}")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not _ID.fullmatch(event_id):
            errors.append(f"{label}.event_id has an invalid identifier")
        elif event_id in seen_events:
            errors.append(f"duplicate catalog event id {event_id!r}")
        else:
            seen_events.add(event_id)
        _time(event.get("origin_time"), f"{label}.origin_time", errors)
        _number(event.get("latitude"), f"{label}.latitude", errors, minimum=-90, maximum=90)
        _number(event.get("longitude"), f"{label}.longitude", errors, minimum=-180, maximum=180)
        _number(event.get("depth_km"), f"{label}.depth_km", errors, minimum=0)
        for field in ("magnitude", "magnitude_type", "horizontal_uncertainty_km",
                      "depth_uncertainty_km", "origin_time_uncertainty_s", "location_method"):
            if field not in event:
                continue
            if field in {"magnitude_type", "location_method"}:
                if not isinstance(event[field], str):
                    errors.append(f"{label}.{field} must be a string")
            else:
                _number(event[field], f"{label}.{field}", errors,
                        minimum=0 if field != "magnitude" else None)
        picks = event.get("picks", [])
        if not isinstance(picks, list):
            errors.append(f"{label}.picks must be a list")
            continue
        seen_picks: set[str] = set()
        for pick_index, pick in enumerate(picks):
            pick_label = f"{label}.picks[{pick_index}]"
            if not isinstance(pick, dict):
                errors.append(f"{pick_label} must be an object")
                continue
            _unknown(pick, _PICK_FIELDS, pick_label, errors)
            for field in ("pick_id", "station_id", "phase", "arrival_time"):
                if field not in pick:
                    errors.append(f"{pick_label} is missing required field {field!r}")
            pick_id = pick.get("pick_id")
            if not isinstance(pick_id, str) or not _ID.fullmatch(pick_id):
                errors.append(f"{pick_label}.pick_id has an invalid identifier")
            elif pick_id in seen_picks:
                errors.append(f"duplicate pick id {pick_id!r} in {label}")
            else:
                seen_picks.add(pick_id)
            if not isinstance(pick.get("station_id"), str) or not pick.get("station_id"):
                errors.append(f"{pick_label}.station_id must be a non-empty string")
            if pick.get("phase") not in {"P", "S"}:
                errors.append(f"{pick_label}.phase must be P or S")
            _time(pick.get("arrival_time"), f"{pick_label}.arrival_time", errors)
            if "probability" in pick:
                _number(pick["probability"], f"{pick_label}.probability", errors, minimum=0, maximum=1)
    if errors:
        raise CatalogValidationError(errors)
    return dict(value)
