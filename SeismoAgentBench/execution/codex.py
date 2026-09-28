"""Auditable command construction for host-direct Codex CLI runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class CodexCommandError(ValueError):
    """Raised when a Codex command declaration is incomplete or unsafe."""


@dataclass(frozen=True)
class CodexCommandSpec:
    """Configuration for one non-interactive Codex CLI invocation.

    This class only constructs argv. It deliberately does not load
    credentials, proxy files, or execute the command.
    """

    codex_bin: str
    model: str
    working_dir: str
    prompt: str
    reasoning_effort: str = "medium"
    bypass_sandbox: bool = True
    ephemeral: bool = True
    extra_args: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.codex_bin:
            raise CodexCommandError("codex_bin must be non-empty")
        if not self.model:
            raise CodexCommandError("model must be non-empty")
        if not self.working_dir or not Path(self.working_dir).is_absolute():
            raise CodexCommandError("working_dir must be an absolute path")
        if not self.prompt:
            raise CodexCommandError("prompt must be non-empty")
        if self.reasoning_effort not in {"low", "medium", "high", "xhigh", "max"}:
            raise CodexCommandError("unsupported reasoning_effort")
        if not all(isinstance(item, str) and item for item in self.extra_args):
            raise CodexCommandError("extra_args must contain non-empty strings")

    def argv(self) -> list[str]:
        """Return the exact argv for ``codex exec`` in host-direct mode."""
        command = [self.codex_bin, "exec", "--json"]
        if self.ephemeral:
            command.append("--ephemeral")
        command.extend(["--skip-git-repo-check", "--model", self.model,
                        "-C", self.working_dir,
                        "-c", f'model_reasoning_effort="{self.reasoning_effort}"'])
        if self.bypass_sandbox:
            command.append("--dangerously-bypass-approvals-and-sandbox")
        command.extend(self.extra_args)
        command.append(self.prompt)
        return command

    def record(self) -> dict[str, object]:
        """Return a JSON-safe command record without credentials."""
        return {
            "executable": self.codex_bin,
            "argv": self.argv(),
            "model": self.model,
            "working_dir": self.working_dir,
            "reasoning_effort": self.reasoning_effort,
            "host_direct": True,
            "credentials_included": False,
        }
