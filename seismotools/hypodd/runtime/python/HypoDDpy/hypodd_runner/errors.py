"""Typed exceptions for the hypodd_runner public API."""
from __future__ import annotations

from typing import Iterable, Optional


class HypoddRunnerError(RuntimeError):
    """Base class for user-facing hypodd_runner runtime errors."""


class ConfigContractError(HypoddRunnerError):
    """Raised when API/config parameters violate the package contract."""


class NativeOutputError(HypoddRunnerError):
    """Raised when the native ph2dt/HypoDD run did not produce valid outputs."""


class InsufficientDTimeError(NativeOutputError):
    """Raised when HypoDD cannot relocate because no dtimes are available.

    This is a scientific/data-window failure, not a phase-file syntax error. It
    usually means the selected window is too sparse or pair-link constraints are
    too strict for the current data.
    """


def _indent_block(text: object, *, prefix: str = "  ") -> str:
    """Return ``text`` as an indented multi-line block."""
    lines = str(text).rstrip().splitlines() or [""]
    return "\n".join(f"{prefix}{line}" for line in lines)


def compact_items(items: Iterable[object], *, limit: int = 12) -> str:
    """Return a compact comma-separated preview of diagnostic items.

    Parameters
    ----------
    items
        Values to preview in an error or warning message.
    limit
        Maximum number of values shown before an omitted-count suffix is added.
    """
    values = [str(item) for item in items]
    shown = values[:limit]
    suffix = "" if len(values) <= limit else f", ... (+{len(values) - limit})"
    return ", ".join(shown) + suffix


def format_contract_error(
    *,
    title: str,
    real_error: object,
    location: Optional[str] = None,
    context: Optional[str] = None,
    expected: Optional[str] = None,
    minimal_example: Optional[str] = None,
    recommendation: Optional[str] = None,
    avoid: Optional[str] = None,
) -> str:
    """Format a user-facing package contract error without hiding the cause.

    Parameters
    ----------
    title
        Short heading for the error.
    real_error
        Original exception or message that identifies the real failure.
    location
        Optional file/function/path context.
    context
        Optional extra state that helps interpret the failure.
    expected
        Expected API or file-format contract.
    minimal_example
        Small valid example to guide repair.
    recommendation
        Suggested next repair step.
    avoid
        Explicit anti-pattern to discourage misleading fixes.

    The format is intentionally stable for agent debugging:
    real evidence first, then the contract, then the recommended repair
    direction. Callers should still raise from the original exception when one
    exists so Python traceback chaining preserves the true source error.
    """
    parts = [str(title).rstrip(), "", "Real error:", _indent_block(real_error)]
    if location:
        parts.extend(["", "Location:", _indent_block(location)])
    if context:
        parts.extend(["", "Context:", _indent_block(context)])
    if expected:
        parts.extend(["", "Expected contract:", _indent_block(expected)])
    if minimal_example:
        parts.extend(["", "Minimal valid example:", _indent_block(minimal_example)])
    if recommendation:
        parts.extend(["", "Recommended fix:", _indent_block(recommendation)])
    if avoid:
        parts.extend(["", "Do not:", _indent_block(avoid)])
    return "\n".join(parts).rstrip()


class NativeProgramError(HypoddRunnerError):
    """Raised when a native ph2dt/HypoDD process fails."""

    def __init__(
        self,
        *,
        program: str,
        command,
        cwd: str,
        returncode,
        log_path: str,
        log_tail: str = "",
    ) -> None:
        """Create an exception with command, working directory, and log evidence.

        Parameters
        ----------
        program
            Human-readable program/stage name, such as ``"ph2dt grid 0-0"``.
        command
            Command argv passed to :mod:`subprocess`.
        cwd
            Working directory used for native execution.
        returncode
            Native process return code, or ``"not-started"`` when the executable
            could not be launched.
        log_path
            File receiving combined stdout/stderr.
        log_tail
            Tail of the native log for compact traceback evidence.
        """
        self.program = program
        self.command = list(command)
        self.cwd = cwd
        self.returncode = returncode
        self.log_path = log_path
        self.log_tail = log_tail
        command_text = " ".join(str(x) for x in self.command)
        message = (
            f"Native program failed: {program}\n"
            f"command: {command_text}\n"
            f"cwd: {cwd}\n"
            f"returncode: {returncode}\n"
            f"log_path: {log_path}"
        )
        if log_tail:
            message += f"\n--- log tail ---\n{log_tail}"
        super().__init__(message)
