"""Validation of agent output artifacts against a task contract."""

from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any, Mapping

from .catalog import CatalogValidationError, validate_catalog


class ArtifactValidationError(ValueError):
    """Raised when declared output artifacts are not valid."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _validate_declared_schema(item: Mapping[str, Any], path: Path) -> None:
    """Run a small schema validator declared by the task contract.

    The framework owns only generic interchange schemas. Scientific schemas
    are registered by task-specific scorers and are not inferred here.
    """
    schema = item.get("schema")
    if schema is None:
        return
    name = schema["name"]
    version = schema["version"]
    if name == "json-object" and version == 1:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("expected a JSON object")
    elif name == "csv-columns" and version == 1:
        with path.open(newline="", encoding="utf-8") as handle:
            fields = set(csv.DictReader(handle).fieldnames or ())
        required = set(schema.get("required_columns", []))
        missing = sorted(required - fields)
        if missing:
            raise ValueError(f"missing CSV columns: {', '.join(missing)}")
    else:
        raise ValueError(f"unsupported artifact schema: {name}@{version}")


def validate_artifacts(task: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    """Validate declared artifact paths and return a read-only inventory.

    This checks filesystem placement and basic JSON readability only. It does
    not assess scientific quality and does not modify output files.
    """
    root = Path(output_dir).resolve()
    errors: list[str] = []
    inventory: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in task.get("output_artifacts", []):
        artifact_id = item["id"]
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"artifact {artifact_id!r} has an unsafe relative path")
            continue
        if str(relative) in seen:
            errors.append(f"duplicate artifact path {relative}")
            continue
        seen.add(str(relative))
        path = root / relative
        try:
            inside = path.resolve().is_relative_to(root)
        except FileNotFoundError:
            inside = path.parent.resolve().is_relative_to(root)
        if not inside:
            errors.append(f"artifact {artifact_id!r} resolves outside output directory")
            continue
        if not path.exists():
            if item["required"]:
                errors.append(f"required artifact is missing: {relative}")
            continue
        if path.is_symlink() or not path.is_file():
            errors.append(f"artifact is not a regular file: {relative}")
            continue
        record = {"id": artifact_id, "path": str(relative), "kind": item["kind"], "bytes": path.stat().st_size}
        if item.get("schema") is not None:
            record["schema"] = item["schema"]
        if item["kind"].lower() == "json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                errors.append(f"artifact {artifact_id!r} is not valid JSON: {exc}")
                continue
        if item["kind"].lower() == "catalog":
            try:
                validate_catalog(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, UnicodeError, json.JSONDecodeError, CatalogValidationError) as exc:
                errors.append(f"artifact {artifact_id!r} is not a valid catalog: {exc}")
                continue
        try:
            _validate_declared_schema(item, path)
        except (OSError, UnicodeError, json.JSONDecodeError, csv.Error, ValueError) as exc:
            errors.append(f"artifact {artifact_id!r} does not satisfy declared schema: {exc}")
            continue
        inventory.append(record)
    if errors:
        raise ArtifactValidationError(errors)
    return {"validated": True, "artifacts": inventory}
