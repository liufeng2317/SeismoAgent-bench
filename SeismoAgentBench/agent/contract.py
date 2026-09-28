"""Minimal, serializable contract for launching an agent entrypoint."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Sequence

from SeismoAgentBench.workflow import run_task
from SeismoAgentBench.reporting import write_evaluation_report


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


def run_agent(task_path: str | Path, manifest_path: str | Path, agent: AgentSpec,
              run_root: str | Path, run_id: str, *, timeout: float = 600,
              reference_manifest: str | Path | None = None) -> dict[str, Any]:
    """Run one declared agent through the standard task workflow."""
    result = run_task(task_path, manifest_path, agent.command, run_root, run_id,
                      timeout=timeout, reference_manifest=reference_manifest)
    run = Path(run_root).resolve() / run_id
    (run / "agent_command.json").write_text(json.dumps(agent.record(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["agent"] = agent.record()
    run_result = json.loads((run / "run_result.json").read_text(encoding="utf-8"))
    run_result["agent"] = agent.record()
    (run / "run_result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_evaluation_report(run, run_result, agent.record())
    return result
