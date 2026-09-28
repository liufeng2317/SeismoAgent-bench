"""Reference catalog manifests and deterministic event matching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

from .catalog import CatalogValidationError, validate_catalog


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class ReferenceError(ValueError):
    """Raised when a reference manifest or match request is invalid."""


@dataclass(frozen=True)
class ReferenceSpec:
    reference_id: str
    version: str
    role: str
    path: Path
    description: str | None = None
    source_identity: str | None = None

    @classmethod
    def from_manifest(cls, path: str | Path) -> "ReferenceSpec":
        source = Path(path)
        try:
            value = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ReferenceError(f"cannot load reference manifest {source}: {exc}") from exc
        if not isinstance(value, dict):
            raise ReferenceError("reference manifest must be an object")
        allowed = {"schema_version", "reference_id", "version", "role", "path", "description", "source_identity"}
        errors = [f"reference manifest has unknown field {key!r}" for key in sorted(set(value) - allowed)]
        if value.get("schema_version") != 1:
            errors.append("reference manifest.schema_version must be 1")
        for field in ("reference_id", "version", "role", "path"):
            if field not in value:
                errors.append(f"reference manifest is missing required field {field!r}")
        if not isinstance(value.get("reference_id"), str) or not _ID.fullmatch(value.get("reference_id", "")):
            errors.append("reference manifest.reference_id has an invalid identifier")
        for field in ("version", "role"):
            if not isinstance(value.get(field), str) or not value.get(field):
                errors.append(f"reference manifest.{field} must be a non-empty string")
        reference_path = value.get("path")
        if not isinstance(reference_path, str) or not reference_path or "\x00" in reference_path:
            errors.append("reference manifest.path must be a non-empty path")
        if errors:
            raise ReferenceError("; ".join(errors))
        reference_file = Path(reference_path)
        if not reference_file.is_absolute():
            reference_file = source.parent / reference_file
        return cls(value["reference_id"], value["version"], value["role"], reference_file,
                   value.get("description"), value.get("source_identity"))

    def load_catalog(self) -> dict[str, Any]:
        if not self.path.is_file() or self.path.is_symlink():
            raise ReferenceError(f"reference catalog is not a regular file: {self.path}")
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return validate_catalog(value)
        except (OSError, UnicodeError, json.JSONDecodeError, CatalogValidationError) as exc:
            raise ReferenceError(f"invalid reference catalog {self.path}: {exc}") from exc

    def record(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "version": self.version,
            "role": self.role,
            "path": str(self.path),
            "description": self.description,
            "source_identity": self.source_identity,
        }


@dataclass(frozen=True)
class MatchingPolicy:
    time_tolerance_s: float = 5.0
    horizontal_tolerance_km: float = 10.0
    depth_tolerance_km: float | None = None

    def __post_init__(self) -> None:
        if self.time_tolerance_s <= 0 or self.horizontal_tolerance_km <= 0:
            raise ReferenceError("matching tolerances must be positive")
        if self.depth_tolerance_km is not None and self.depth_tolerance_km <= 0:
            raise ReferenceError("depth tolerance must be positive when provided")

    def record(self) -> dict[str, float]:
        record: dict[str, float] = {
            "time_tolerance_s": self.time_tolerance_s,
            "horizontal_tolerance_km": self.horizontal_tolerance_km,
        }
        if self.depth_tolerance_km is not None:
            record["depth_tolerance_km"] = self.depth_tolerance_km
        return record


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ReferenceError("event times must include a timezone")
    return parsed


def _horizontal_distance_km(first: Mapping[str, Any], second: Mapping[str, Any]) -> float:
    radius_km = 6371.0
    lat1, lat2 = math.radians(first["latitude"]), math.radians(second["latitude"])
    dlat = lat2 - lat1
    dlon = math.radians(second["longitude"] - first["longitude"])
    haversine = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius_km * math.asin(math.sqrt(haversine))


def match_events(candidate: Mapping[str, Any], reference: Mapping[str, Any],
                 policy: MatchingPolicy | None = None) -> dict[str, Any]:
    """Return deterministic one-to-one event matches without assigning scores."""
    policy = policy or MatchingPolicy()
    try:
        candidate = validate_catalog(candidate)
        reference = validate_catalog(reference)
    except CatalogValidationError as exc:
        raise ReferenceError(f"cannot match invalid catalog: {exc}") from exc
    available = {event["event_id"]: event for event in reference["events"]}
    matches: list[dict[str, Any]] = []
    unmatched_candidates: list[str] = []
    for event in sorted(candidate["events"], key=lambda item: item["event_id"]):
        candidates: list[tuple[tuple[float, float, str], dict[str, Any]]] = []
        event_time = _timestamp(event["origin_time"])
        for reference_id, target in available.items():
            time_delta = abs((event_time - _timestamp(target["origin_time"])).total_seconds())
            horizontal = _horizontal_distance_km(event, target)
            depth_delta = abs(event["depth_km"] - target["depth_km"])
            if time_delta > policy.time_tolerance_s or horizontal > policy.horizontal_tolerance_km:
                continue
            if policy.depth_tolerance_km is not None and depth_delta > policy.depth_tolerance_km:
                continue
            candidates.append(((time_delta, horizontal, reference_id), {
                "candidate_event_id": event["event_id"],
                "reference_event_id": reference_id,
                "time_difference_s": time_delta,
                "horizontal_distance_km": horizontal,
                "depth_difference_km": depth_delta,
            }))
        if not candidates:
            unmatched_candidates.append(event["event_id"])
            continue
        _, match = min(candidates, key=lambda item: item[0])
        matches.append(match)
        del available[match["reference_event_id"]]
    return {
        "policy": policy.record(),
        "matches": matches,
        "unmatched_candidate_event_ids": unmatched_candidates,
        "unmatched_reference_event_ids": sorted(available),
    }
