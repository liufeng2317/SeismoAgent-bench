"""Pure validation for task specifications and input manifests."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Mapping


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_SCOPE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_INPUT_TYPES = {"waveform", "station_metadata", "catalog", "metadata", "other"}


class ValidationError(ValueError):
    """Raised when a task or manifest violates its input contract."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON object without modifying the source file."""
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError([f"cannot load JSON {source}: {exc}"]) from exc
    if not isinstance(value, dict):
        raise ValidationError([f"top level of {source} must be an object"])
    return value


def _object(value: Any, label: str, errors: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return None
    return value


def _unknown(value: Mapping[str, Any], allowed: set[str], label: str, errors: list[str]) -> None:
    for key in sorted(set(value) - allowed):
        errors.append(f"{label} has unknown field {key!r}")


def _required(value: Mapping[str, Any], fields: set[str], label: str, errors: list[str]) -> None:
    for field in sorted(fields - set(value)):
        errors.append(f"{label} is missing required field {field!r}")


def _time(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{label} must be an ISO-8601 string")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} is not a valid ISO-8601 timestamp")


def validate_manifest(value: Mapping[str, Any], *, task: Mapping[str, Any] | None = None,
                      check_paths: bool = False) -> dict[str, Any]:
    """Validate and return an input manifest.

    Validation is read-only. ``check_paths`` performs optional existence and
    regular-file checks; it is disabled for portable task-definition checks.
    """
    errors: list[str] = []
    manifest = _object(value, "manifest", errors)
    if manifest is None:
        raise ValidationError(errors)
    allowed = {"schema_version", "case_id", "description", "entries"}
    _unknown(manifest, allowed, "manifest", errors)
    _required(manifest, {"schema_version", "case_id", "entries"}, "manifest", errors)
    if manifest.get("schema_version") != 1:
        errors.append("manifest.schema_version must be 1")
    scope_id = manifest.get("case_id")
    if not isinstance(scope_id, str) or not _SCOPE_ID.fullmatch(scope_id):
        errors.append("manifest.case_id has an invalid identifier")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("manifest.entries must be a non-empty list")
        entries = []
    seen: set[str] = set()
    data_types: set[str] = set()
    entry_allowed = {"id", "path", "data_type", "format", "read_only", "bytes", "network", "station",
                     "location", "channel", "start_time", "end_time", "sha256", "notes"}
    for index, raw in enumerate(entries):
        label = f"manifest.entries[{index}]"
        entry = _object(raw, label, errors)
        if entry is None:
            continue
        _unknown(entry, entry_allowed, label, errors)
        _required(entry, {"id", "path", "data_type", "format", "read_only"}, label, errors)
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not _ID.fullmatch(entry_id):
            errors.append(f"{label}.id has an invalid identifier")
        elif entry_id in seen:
            errors.append(f"duplicate manifest entry id {entry_id!r}")
        else:
            seen.add(entry_id)
        path = entry.get("path")
        if not isinstance(path, str) or not path.startswith("/") or "\x00" in path:
            errors.append(f"{label}.path must be an absolute path")
        elif check_paths and (not Path(path).is_file() or Path(path).is_symlink()):
            errors.append(f"{label}.path is not an existing regular file: {path}")
        data_type = entry.get("data_type")
        if data_type not in _INPUT_TYPES:
            errors.append(f"{label}.data_type is not supported")
        else:
            data_types.add(data_type)
        if not isinstance(entry.get("format"), str) or not entry.get("format"):
            errors.append(f"{label}.format must be a non-empty string")
        if entry.get("read_only") is not True:
            errors.append(f"{label}.read_only must be true")
        if "bytes" in entry and (not isinstance(entry["bytes"], int) or entry["bytes"] < 0):
            errors.append(f"{label}.bytes must be a non-negative integer")
        if "sha256" in entry and (not isinstance(entry["sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", entry["sha256"])):
            errors.append(f"{label}.sha256 must contain 64 hexadecimal characters")
        for field in ("start_time", "end_time"):
            if field in entry:
                _time(entry[field], f"{label}.{field}", errors)
    if task is not None and isinstance(task, Mapping):
        required_types = set(task.get("input_types", []))
        missing = sorted(required_types - data_types)
        if missing:
            errors.append(f"manifest is missing required input types: {', '.join(missing)}")
    if errors:
        raise ValidationError(errors)
    return dict(value)


def validate_task(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a task specification without accessing data or running tools."""
    errors: list[str] = []
    task = _object(value, "task", errors)
    if task is None:
        raise ValidationError(errors)
    allowed = {"task_id", "version", "title", "summary", "task_prompt",
               "input_types", "output_artifacts", "scorer"}
    _unknown(task, allowed, "task", errors)
    _required(task, {"task_id", "version", "task_prompt", "input_types",
                     "output_artifacts", "scorer"}, "task", errors)
    if not isinstance(task.get("task_id"), str) or not _ID.fullmatch(task.get("task_id", "")):
        errors.append("task.task_id has an invalid identifier")
    if not isinstance(task.get("version"), str) or not task.get("version"):
        errors.append("task.version must be a non-empty string")
    for field in ("title", "summary"):
        if field in task and (not isinstance(task[field], str) or not task[field]):
            errors.append(f"task.{field} must be a non-empty string when provided")
    if not isinstance(task.get("task_prompt"), str) or not task.get("task_prompt"):
        errors.append("task.task_prompt must be a non-empty string")
    input_types = task.get("input_types")
    if not isinstance(input_types, list) or not input_types or any(kind not in _INPUT_TYPES for kind in input_types):
        errors.append("task.input_types must be a non-empty list of supported input types")
    elif len(set(input_types)) != len(input_types):
        errors.append("task.input_types must not contain duplicates")
    outputs = task.get("output_artifacts")
    output_ids: set[str] = set()
    if not isinstance(outputs, list) or not outputs:
        errors.append("task.output_artifacts must be a non-empty list")
    else:
        for index, raw in enumerate(outputs):
            label = f"task.output_artifacts[{index}]"
            item = _object(raw, label, errors)
            if item is None:
                continue
            _unknown(item, {"id", "path", "kind", "required"}, label, errors)
            _required(item, {"id", "path", "kind", "required"}, label, errors)
            artifact_id = item.get("id")
            if not isinstance(artifact_id, str) or not _ID.fullmatch(artifact_id):
                errors.append(f"{label}.id has an invalid identifier")
            elif artifact_id in output_ids:
                errors.append(f"duplicate task output artifact id {artifact_id!r}")
            else:
                output_ids.add(artifact_id)
            artifact_path = item.get("path")
            unsafe_path = (
                not isinstance(artifact_path, str)
                or not artifact_path
                or Path(artifact_path).is_absolute()
                or "\x00" in artifact_path
                or any(part == ".." for part in Path(artifact_path).parts)
            )
            if unsafe_path:
                errors.append(f"{label}.path must be a relative non-traversing path")
            if not isinstance(item.get("kind"), str) or not item.get("kind"):
                errors.append(f"{label}.kind must be a non-empty string")
            if not isinstance(item.get("required"), bool):
                errors.append(f"{label}.required must be boolean")
    scorer = _object(task.get("scorer"), "task.scorer", errors)
    if scorer is not None:
        _unknown(scorer, {"name", "version"}, "task.scorer", errors)
        _required(scorer, {"name", "version"}, "task.scorer", errors)
        if not isinstance(scorer.get("name"), str) or not scorer.get("name"):
            errors.append("task.scorer.name must be a non-empty string")
        if not isinstance(scorer.get("version"), str) or not scorer.get("version"):
            errors.append("task.scorer.version must be a non-empty string")
    if errors:
        raise ValidationError(errors)
    return dict(value)
