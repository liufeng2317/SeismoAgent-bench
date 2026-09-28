"""Explicit registry for versioned task specifications."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .validation import ValidationError, load_json, validate_task


class TaskRegistryError(ValueError):
    """Raised when task registration or lookup is invalid."""


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    version: str
    path: Path


class TaskRegistry:
    """In-memory registry backed by explicitly registered JSON task files."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], TaskRecord] = {}

    @classmethod
    def from_directory(cls, directory: str | Path) -> "TaskRegistry":
        """Register files named ``task.json`` below a directory."""
        root = Path(directory)
        if not root.is_dir():
            raise TaskRegistryError(f"task directory does not exist: {root}")
        registry = cls()
        for path in sorted(root.rglob("task.json")):
            if path.is_file() and not path.is_symlink():
                registry.register(path)
        return registry

    def register(self, path: str | Path) -> TaskRecord:
        source = Path(path)
        if not source.is_file() or source.is_symlink():
            raise TaskRegistryError(f"task path is not a regular file: {source}")
        try:
            task = validate_task(load_json(source))
        except ValidationError as exc:
            raise TaskRegistryError(f"invalid task {source}: {exc}") from exc
        key = (task["task_id"], task["version"])
        if key in self._records:
            raise TaskRegistryError(f"task is already registered: {key[0]}@{key[1]}")
        record = TaskRecord(key[0], key[1], source.resolve())
        self._records[key] = record
        return record

    def load(self, task_id: str, version: str | None = None) -> dict[str, Any]:
        """Load one registered task, requiring an explicit version if ambiguous."""
        matches = [record for (identifier, _), record in self._records.items() if identifier == task_id]
        if version is not None:
            matches = [record for record in matches if record.version == version]
        if not matches:
            label = f"{task_id}@{version}" if version is not None else task_id
            raise TaskRegistryError(f"task is not registered: {label}")
        if len(matches) > 1:
            versions = ", ".join(sorted(record.version for record in matches))
            raise TaskRegistryError(f"task version is ambiguous for {task_id}: {versions}")
        return validate_task(load_json(matches[0].path))

    def records(self) -> tuple[TaskRecord, ...]:
        """Return registered records in stable identifier/version order."""
        return tuple(self._records[key] for key in sorted(self._records))
