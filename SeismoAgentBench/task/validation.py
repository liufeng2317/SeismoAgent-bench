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


def validate_output_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the required output-artifact contract for one task."""
    errors: list[str] = []
    contract = _object(value, "output_contract", errors)
    if contract is None:
        raise ValidationError(errors)
    _unknown(contract, {"schema_version", "artifacts"}, "output_contract", errors)
    _required(contract, {"schema_version", "artifacts"}, "output_contract", errors)
    if contract.get("schema_version") != 1:
        errors.append("output_contract.schema_version must be 1")
    artifacts = contract.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("output_contract.artifacts must be a non-empty list")
        artifacts = []
    output_ids: set[str] = set()
    for index, raw in enumerate(artifacts):
        label = f"output_contract.artifacts[{index}]"
        item = _object(raw, label, errors)
        if item is None:
            continue
        _unknown(item, {"id", "path", "kind", "required", "schema"}, label, errors)
        _required(item, {"id", "path", "kind", "required"}, label, errors)
        artifact_id = item.get("id")
        if not isinstance(artifact_id, str) or not _ID.fullmatch(artifact_id):
            errors.append(f"{label}.id has an invalid identifier")
        elif artifact_id in output_ids:
            errors.append(f"duplicate output artifact id {artifact_id!r}")
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
        schema = item.get("schema")
        if schema is not None:
            if not isinstance(schema, dict):
                errors.append(f"{label}.schema must be an object")
            else:
                _unknown(schema, {"name", "version", "required_columns"}, f"{label}.schema", errors)
                _required(schema, {"name", "version"}, f"{label}.schema", errors)
                if not isinstance(schema.get("name"), str) or not schema.get("name"):
                    errors.append(f"{label}.schema.name must be a non-empty string")
                if not isinstance(schema.get("version"), int) or schema.get("version") < 1:
                    errors.append(f"{label}.schema.version must be a positive integer")
                if "required_columns" in schema and (
                        not isinstance(schema["required_columns"], list)
                        or any(not isinstance(column, str) or not column for column in schema["required_columns"])):
                    errors.append(f"{label}.schema.required_columns must be a list of non-empty strings")
    if errors:
        raise ValidationError(errors)
    return dict(value)


def load_task(path: str | Path) -> dict[str, Any]:
    """Load a task and resolve its external output contract, when declared."""
    source = Path(path)
    task = load_json(source)
    legacy_fields = sorted({"task_prompt", "input_types", "output_artifacts", "scorer"} & set(task))
    if legacy_fields:
        raise ValidationError([
            "task uses removed fields: " + ", ".join(legacy_fields)
            + "; use task_prompt_file, input_requirements and evaluation.scorers"
        ])
    prompt_ref = task.get("task_prompt_file")
    if prompt_ref is not None:
        if (not isinstance(prompt_ref, str) or not prompt_ref
                or Path(prompt_ref).is_absolute()
                or "\x00" in prompt_ref
                or any(part == ".." for part in Path(prompt_ref).parts)):
            raise ValidationError(["task.task_prompt_file must be a relative non-traversing path"])
        prompt_path = source.parent / prompt_ref
        try:
            prompt = prompt_path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as exc:
            raise ValidationError([f"cannot read task.task_prompt_file {prompt_path}: {exc}"]) from exc
        if not prompt:
            raise ValidationError(["task.task_prompt_file must not be empty"])
        task = dict(task)
        task["task_prompt"] = prompt
    contract_ref = task.get("output_contract")
    if contract_ref is not None:
        if (not isinstance(contract_ref, str) or not contract_ref
                or Path(contract_ref).is_absolute()
                or "\x00" in contract_ref
                or any(part == ".." for part in Path(contract_ref).parts)):
            raise ValidationError(["task.output_contract must be a relative non-traversing path"])
        contract_path = source.parent / contract_ref
        contract = load_json(contract_path)
        validate_output_contract(contract)
        task = dict(task)
        task["output_artifacts"] = contract["artifacts"]
    return validate_task(task)


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
    entry_allowed = {"id", "path", "path_type", "data_type", "format", "read_only", "bytes", "network", "station",
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
        path_type = entry.get("path_type", "file")
        if path_type not in {"file", "directory"}:
            errors.append(f"{label}.path_type must be file or directory")
        elif check_paths:
            target = Path(path)
            valid = target.is_dir() if path_type == "directory" else target.is_file()
            if not valid or target.is_symlink():
                expected = "directory" if path_type == "directory" else "regular file"
                errors.append(f"{label}.path is not an existing {expected}: {path}")
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
        required_types = {
            item.get("data_type")
            for item in task.get("input_requirements", [])
            if isinstance(item, Mapping) and item.get("required") is True
        }
        required_types.discard(None)
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
    allowed = {"task_id", "version", "title", "summary", "task_prompt_file",
               "output_contract", "category", "software", "required_system_packages",
               "taxonomy", "input_requirements", "reference_requirements", "evaluation",
               # These fields are materialized by load_task for downstream code.
               "task_prompt", "output_artifacts"}
    _unknown(task, allowed, "task", errors)
    _required(task, {"task_id", "version", "task_prompt_file", "input_requirements",
                     "output_contract", "evaluation"}, "task", errors)
    contract_ref = task.get("output_contract")
    if (not isinstance(contract_ref, str) or not contract_ref
            or Path(contract_ref).is_absolute()
            or "\x00" in contract_ref
            or any(part == ".." for part in Path(contract_ref).parts)):
        errors.append("task.output_contract must be a relative non-traversing path")
    if not isinstance(task.get("task_id"), str) or not _ID.fullmatch(task.get("task_id", "")):
        errors.append("task.task_id has an invalid identifier")
    if not isinstance(task.get("version"), str) or not task.get("version"):
        errors.append("task.version must be a non-empty string")
    for field in ("title", "summary"):
        if field in task and (not isinstance(task[field], str) or not task[field]):
            errors.append(f"task.{field} must be a non-empty string when provided")
    prompt_ref = task.get("task_prompt_file")
    if (not isinstance(prompt_ref, str) or not prompt_ref
            or Path(prompt_ref).is_absolute()
            or "\x00" in prompt_ref
            or any(part == ".." for part in Path(prompt_ref).parts)):
        errors.append("task.task_prompt_file must be a relative non-traversing path")

    input_requirements = task.get("input_requirements")
    if not isinstance(input_requirements, list) or not input_requirements:
        errors.append("task.input_requirements must be a non-empty list")
        input_requirements = []
    seen_input_requirements: set[str] = set()
    for index, raw in enumerate(input_requirements):
        label = f"task.input_requirements[{index}]"
        item = _object(raw, label, errors)
        if item is None:
            continue
        _unknown(item, {"id", "data_type", "format", "required"}, label, errors)
        _required(item, {"id", "data_type", "required"}, label, errors)
        identifier = item.get("id")
        if not isinstance(identifier, str) or not _ID.fullmatch(identifier):
            errors.append(f"{label}.id has an invalid identifier")
        elif identifier in seen_input_requirements:
            errors.append(f"duplicate input_requirements id {identifier!r}")
        else:
            seen_input_requirements.add(identifier)
        if item.get("data_type") not in _INPUT_TYPES:
            errors.append(f"{label}.data_type is not supported")
        if not isinstance(item.get("required"), bool):
            errors.append(f"{label}.required must be boolean")
        if "format" in item and (not isinstance(item["format"], str) or not item["format"].strip()):
            errors.append(f"{label}.format must be a non-empty string")

    category = task.get("category")
    if category is not None and (not isinstance(category, str) or not category.strip()):
        errors.append("task.category must be a non-empty string when provided")
    for field in ("software", "required_system_packages"):
        values = task.get(field)
        if values is not None:
            if (not isinstance(values, list)
                    or any(not isinstance(item, str) or not item.strip() for item in values)):
                errors.append(f"task.{field} must be a list of non-empty strings")
            elif len(set(values)) != len(values):
                errors.append(f"task.{field} must not contain duplicates")

    taxonomy = task.get("taxonomy")
    if taxonomy is not None:
        if not isinstance(taxonomy, dict):
            errors.append("task.taxonomy must be an object")
        else:
            for key, item in taxonomy.items():
                valid_scalar = isinstance(item, str) and bool(item.strip())
                valid_list = (isinstance(item, list) and bool(item)
                              and all(isinstance(entry, str) and entry.strip() for entry in item))
                if not isinstance(key, str) or not key.strip() or not (valid_scalar or valid_list):
                    errors.append("task.taxonomy values must be non-empty strings or string lists")

    for field in ("reference_requirements",):
        requirements = task.get(field)
        if requirements is None:
            continue
        if not isinstance(requirements, list) or not requirements:
            errors.append(f"task.{field} must be a non-empty list when provided")
            continue
        seen_requirements: set[str] = set()
        for index, raw in enumerate(requirements):
            label = f"task.{field}[{index}]"
            item = _object(raw, label, errors)
            if item is None:
                continue
            allowed_fields = {"id", "data_type", "format", "required", "role"}
            _unknown(item, allowed_fields, label, errors)
            _required(item, {"id", "required"}, label, errors)
            identifier = item.get("id")
            if not isinstance(identifier, str) or not _ID.fullmatch(identifier):
                errors.append(f"{label}.id has an invalid identifier")
            elif identifier in seen_requirements:
                errors.append(f"duplicate {field} id {identifier!r}")
            else:
                seen_requirements.add(identifier)
            if "data_type" in item and item["data_type"] not in _INPUT_TYPES:
                errors.append(f"{label}.data_type is not supported")
            for string_field in ("format", "role"):
                if string_field in item and (
                        not isinstance(item[string_field], str) or not item[string_field].strip()):
                    errors.append(f"{label}.{string_field} must be a non-empty string")
            if not isinstance(item.get("required"), bool):
                errors.append(f"{label}.required must be boolean")

    evaluation = task.get("evaluation")
    evaluation_obj = _object(evaluation, "task.evaluation", errors)
    if evaluation_obj is not None:
        _unknown(evaluation_obj, {"scorers"}, "task.evaluation", errors)
        scorers = evaluation_obj.get("scorers")
        if not isinstance(scorers, list) or not scorers:
            errors.append("task.evaluation.scorers must be a non-empty list")
        else:
            for index, raw in enumerate(scorers):
                label = f"task.evaluation.scorers[{index}]"
                scorer_item = _object(raw, label, errors)
                if scorer_item is None:
                    continue
                _unknown(scorer_item, {"name", "version"}, label, errors)
                _required(scorer_item, {"name", "version"}, label, errors)
                if not isinstance(scorer_item.get("name"), str) or not scorer_item["name"].strip():
                    errors.append(f"{label}.name must be a non-empty string")
                if not isinstance(scorer_item.get("version"), str) or not scorer_item["version"].strip():
                    errors.append(f"{label}.version must be a non-empty string")
    has_artifacts = "output_artifacts" in task
    outputs = task.get("output_artifacts")
    output_ids: set[str] = set()
    if has_artifacts and (not isinstance(outputs, list) or not outputs):
        errors.append("task.output_artifacts must be a non-empty list")
    elif has_artifacts:
        for index, raw in enumerate(outputs):
            label = f"task.output_artifacts[{index}]"
            item = _object(raw, label, errors)
            if item is None:
                continue
            _unknown(item, {"id", "path", "kind", "required", "schema"}, label, errors)
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
            schema = item.get("schema")
            if schema is not None:
                if not isinstance(schema, dict):
                    errors.append(f"{label}.schema must be an object")
                else:
                    _required(schema, {"name", "version"}, f"{label}.schema", errors)
                    if not isinstance(schema.get("name"), str) or not schema.get("name"):
                        errors.append(f"{label}.schema.name must be a non-empty string")
                    if not isinstance(schema.get("version"), int) or schema.get("version") < 1:
                        errors.append(f"{label}.schema.version must be a positive integer")
    if errors:
        raise ValidationError(errors)
    return dict(value)
