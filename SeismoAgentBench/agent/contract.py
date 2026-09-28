"""Minimal, serializable contract for launching an agent entrypoint."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Sequence


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class AgentError(ValueError):
    """Raised when an agent entrypoint declaration is invalid."""


@dataclass(frozen=True)
class AgentSpec:
    """Identity and command for one agent implementation."""

    name: str
    version: str
    command: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _IDENTIFIER.fullmatch(self.name):
            raise AgentError("agent name must be a valid identifier")
        if not isinstance(self.version, str) or not self.version:
            raise AgentError("agent version must be non-empty")
        if not self.command or not all(isinstance(item, str) and item for item in self.command):
            raise AgentError("agent command must be a non-empty sequence of strings")

    @classmethod
    def from_command(cls, name: str, version: str, command: Sequence[str]) -> "AgentSpec":
        return cls(name=name, version=version, command=tuple(command))

    def record(self) -> dict[str, Any]:
        return {"name": self.name, "version": self.version, "command": list(self.command)}


def run_agent(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility import; the implementation belongs to ``workflow``."""
    from SeismoAgentBench.workflow.run_agent import run_agent as _run_agent
    return _run_agent(*args, **kwargs)
