"""Non-invasive executable version probing for run provenance."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Sequence


def probe_executable_version(
    executable: str,
    version_command: Sequence[str] = ("--version",),
    *,
    timeout: float = 10.0,
) -> dict[str, object]:
    """Run an executable's version command without a shell.

    A probe is metadata collection, so an unavailable or non-conforming
    executable is reported in the returned record rather than aborting the
    benchmark run. No environment values or command output beyond the first
    line are persisted.
    """
    if not isinstance(executable, str) or not executable:
        raise ValueError("executable must be a non-empty string")
    command = list(version_command)
    if not command or any(not isinstance(item, str) or not item for item in command):
        raise ValueError("version_command must be a non-empty string sequence")
    if timeout <= 0:
        raise ValueError("version probe timeout must be positive")
    resolved = shutil.which(executable) or executable
    argv = [resolved, *command]
    record: dict[str, object] = {
        "command": argv,
        "executable": executable,
        "resolved_executable": str(Path(resolved).resolve()) if Path(resolved).exists() else resolved,
    }
    try:
        completed = subprocess.run(
            argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, errors="replace", timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        record["status"] = "unavailable"
        record["error"] = "timeout" if isinstance(exc, subprocess.TimeoutExpired) else type(exc).__name__
        return record
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    record["status"] = "ok" if completed.returncode == 0 and lines else "unavailable"
    record["returncode"] = completed.returncode
    if lines:
        record["version"] = lines[0][:500]
    return record


SEISMOTOOLS = Path(__file__).resolve().parents[2] / "seismotools"


def tools_snapshot(tools_dir: Path = SEISMOTOOLS, *, timeout: float = 10.0) -> dict[str, object]:
    """Identify the shared tool library an Agent could use: git commit and local changes.

    Tools are added over time (for example new associators and locators), so a
    run records which snapshot was visible. Metadata only: a missing git or a
    non-repository directory yields null fields instead of an error.
    """
    record: dict[str, object] = {"path": str(tools_dir), "commit": None, "dirty": None}
    try:
        head = subprocess.run(["git", "-C", str(tools_dir), "rev-parse", "HEAD"], stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, text=True, timeout=timeout, check=True)
        status = subprocess.run(["git", "-C", str(tools_dir), "status", "--porcelain", "--", "."],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=timeout,
                                check=True)
    except (OSError, subprocess.SubprocessError):
        return record
    record["commit"] = head.stdout.strip() or None
    record["dirty"] = bool(status.stdout.strip())
    return record
