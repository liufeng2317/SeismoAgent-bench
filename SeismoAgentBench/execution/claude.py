"""Auditable command construction for host-direct Claude Code CLI runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ClaudeCommandError(ValueError):
    """Raised when a Claude Code command declaration is incomplete or unsafe."""


@dataclass(frozen=True)
class ClaudeCommandSpec:
    """Configuration for one non-interactive Claude Code CLI invocation.

    This class only constructs argv. It deliberately does not load
    credentials, settings, or execute the command. The process working
    directory is set by the runner; ``working_dir`` is recorded for
    provenance.

    By default the prompt goes to the process's standard input, not argv:
    on argv it is visible to every ``ps``/``pgrep`` in the session, and an
    Agent that kills processes by a pattern from its own prompt (a tool
    name, say) kills itself (Kaikoura tools, 2026-10-29).
    """

    claude_bin: str
    model: str | None
    working_dir: str
    prompt: str
    max_turns: int | None = None
    bypass_permissions: bool = True
    extra_args: tuple[str, ...] = ()
    prompt_via_stdin: bool = True

    def __post_init__(self) -> None:
        if not self.claude_bin:
            raise ClaudeCommandError("claude_bin must be non-empty")
        if self.model is not None and not self.model:
            raise ClaudeCommandError("model must be non-empty when provided")
        if not self.working_dir or not Path(self.working_dir).is_absolute():
            raise ClaudeCommandError("working_dir must be an absolute path")
        if not self.prompt:
            raise ClaudeCommandError("prompt must be non-empty")
        if self.max_turns is not None and (isinstance(self.max_turns, bool)
                                           or not isinstance(self.max_turns, int)
                                           or self.max_turns < 1):
            raise ClaudeCommandError("max_turns must be a positive integer when provided")
        if not all(isinstance(item, str) and item for item in self.extra_args):
            raise ClaudeCommandError("extra_args must contain non-empty strings")

    def argv(self) -> list[str]:
        """Return the exact argv for headless ``claude`` in host-direct mode."""
        command = [self.claude_bin, "--print", "--verbose", "--output-format", "stream-json"]
        if self.model is not None:
            command.extend(["--model", self.model])
        if self.max_turns is not None:
            command.extend(["--max-turns", str(self.max_turns)])
        if self.bypass_permissions:
            command.append("--dangerously-skip-permissions")
        command.extend(self.extra_args)
        if not self.prompt_via_stdin:
            command.append(self.prompt)
        return command

    def stdin_text(self) -> str | None:
        """The text to write to the process's standard input (the prompt), if any."""
        return self.prompt if self.prompt_via_stdin else None

    def record(self) -> dict[str, object]:
        """Return a JSON-safe command record without credentials."""
        return {
            "executable": self.claude_bin,
            "argv": self.argv(),
            "prompt_via": "stdin" if self.prompt_via_stdin else "argv",
            "model": self.model,
            "working_dir": self.working_dir,
            "max_turns": self.max_turns,
            "host_direct": True,
            "credentials_included": False,
        }
