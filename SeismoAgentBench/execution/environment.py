"""Runtime environment discovery for Agent runs."""

from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import subprocess
from typing import Any, Mapping


def _os_release() -> str:
    values: dict[str, str] = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value.strip().strip('"')
    except OSError:
        pass
    return values.get("PRETTY_NAME") or values.get("NAME") or platform.platform()


def _python_info(executable: str | None) -> dict[str, str]:
    selected = executable or os.environ.get("PYTHON") or "python"
    try:
        probe = subprocess.run(
            [selected, "-c", "import sys; print(sys.executable); print(sys.version.split()[0])"],
            check=True, capture_output=True, text=True, timeout=10,
        )
        lines = probe.stdout.splitlines()
        return {"executable": lines[0], "version": lines[1]}
    except (OSError, subprocess.SubprocessError, IndexError):
        return {"executable": selected, "version": "unknown"}


def probe_runtime(executable: str | None = None, *, network_policy: str = "allowed",
                  environment: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Collect non-sensitive runtime facts before an Agent starts."""
    env = dict(os.environ)
    if environment:
        env.update(environment)
    python = _python_info(executable or env.get("PYTHON"))
    conda_prefix = env.get("CONDA_PREFIX")
    conda_name = env.get("CONDA_DEFAULT_ENV")
    if not conda_prefix:
        executable_path = Path(python["executable"]).resolve()
        candidate = executable_path.parent.parent
        if candidate.parent.name == "envs":
            conda_prefix = str(candidate)
            conda_name = conda_name or candidate.name
    return {
        "operating_system": _os_release(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "python": python,
        "conda_environment": conda_name,
        "conda_prefix": conda_prefix,
        "network_policy": network_policy,
    }
