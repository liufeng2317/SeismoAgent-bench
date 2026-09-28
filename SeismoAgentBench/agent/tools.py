"""Metadata contracts for scientific-tool adapters.

This module records tool invocations but does not launch tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Any, Mapping


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_STATUSES = {"not_started", "completed", "failed", "timeout"}


class ToolRecordError(ValueError):
    """Raised when a tool or invocation record is invalid."""


@dataclass(frozen=True)
class ToolSpec:
    """Identity and declared inputs for one scientific tool."""

    name: str
    version: str
    executable: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    model_id: str | None = None
    auxiliary_files: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _IDENTIFIER.fullmatch(self.name):
            raise ToolRecordError("tool name must be a valid identifier")
        if not isinstance(self.version, str) or not self.version:
            raise ToolRecordError("tool version must be non-empty")
        if not isinstance(self.executable, str) or not self.executable:
            raise ToolRecordError("tool executable must be non-empty")
        if not isinstance(self.parameters, Mapping):
            raise ToolRecordError("tool parameters must be an object")
        try:
            json.dumps(dict(self.parameters))
        except (TypeError, ValueError) as exc:
            raise ToolRecordError(f"tool parameters must be JSON-serializable: {exc}") from exc
        if self.model_id is not None and (not isinstance(self.model_id, str) or not self.model_id):
            raise ToolRecordError("tool model_id must be non-empty when provided")
        if not all(isinstance(path, str) and path for path in self.auxiliary_files):
            raise ToolRecordError("tool auxiliary_files must contain non-empty strings")

    def record(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "executable": self.executable,
            "parameters": dict(self.parameters),
            "model_id": self.model_id,
            "auxiliary_files": list(self.auxiliary_files),
        }


@dataclass(frozen=True)
class ToolRunRecord:
    """Outcome metadata returned by an adapter after a tool attempt."""

    tool: ToolSpec
    status: str
    started_at: str | None = None
    finished_at: str | None = None
    exit_code: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None

    def __post_init__(self) -> None:
        if self.status not in _STATUSES:
            raise ToolRecordError(f"unsupported tool run status: {self.status}")
        if self.exit_code is not None and not isinstance(self.exit_code, int):
            raise ToolRecordError("tool exit_code must be an integer or null")
        for field_name in ("started_at", "finished_at", "stdout_path", "stderr_path"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value):
                raise ToolRecordError(f"tool {field_name} must be non-empty when provided")

    def record(self) -> dict[str, Any]:
        return {
            "tool": self.tool.record(),
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
        }
