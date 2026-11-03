"""Runtime environment discovery for Agent runs."""

from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import subprocess
from typing import Any, Mapping

import yaml


class EnvironmentConfigError(ValueError):
    """Raised when an execution environment configuration is invalid."""


_ENVIRONMENT_FIELDS = {"mode", "python", "network_policy", "package_installation"}
# run_local: packages may be installed only into a virtual environment the Agent creates in its
# run directory; pip refuses to install into the shared environment (PIP_REQUIRE_VIRTUALENV).
PACKAGE_POLICIES = {"allowed", "blocked", "run_local"}


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


def load_environment_config(path: str | Path) -> dict[str, str]:
    """Load the non-secret execution environment configuration."""
    source = Path(path)
    try:
        value = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise EnvironmentConfigError(f"cannot load environment config {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise EnvironmentConfigError("environment config must be a YAML mapping")
    unknown = sorted(set(value) - _ENVIRONMENT_FIELDS)
    if unknown:
        raise EnvironmentConfigError(f"unknown environment config fields: {', '.join(unknown)}")
    for field in ("mode", "python"):
        if field in value and (not isinstance(value[field], str) or not value[field]):
            raise EnvironmentConfigError(f"environment config.{field} must be a non-empty string")
    if "network_policy" in value and value["network_policy"] not in {"allowed", "blocked"}:
        raise EnvironmentConfigError("environment config.network_policy must be allowed or blocked")
    if "package_installation" in value and value["package_installation"] not in PACKAGE_POLICIES:
        raise EnvironmentConfigError(
            f"environment config.package_installation must be one of {', '.join(sorted(PACKAGE_POLICIES))}")
    return {str(key): str(item) for key, item in value.items()}


def environment_fingerprint(prefix: str | Path | None) -> dict[str, Any] | None:
    """Names of the installed packages of a conda prefix (conda-meta records and site-packages entries).

    Comparing the fingerprint before and after a run shows whether the run changed the shared
    environment (an install, upgrade or removal changes a name, since names carry versions)."""
    if not prefix:
        return None
    root = Path(prefix)
    names: list[str] = []
    meta = root / "conda-meta"
    if meta.is_dir():
        names += [f"conda-meta/{p.name}" for p in meta.glob("*.json")]
    for site in sorted(root.glob("lib/python*/site-packages")):
        names += [f"{site.relative_to(root)}/{p.name}" for p in site.iterdir()]
    if not names:
        return None
    names.sort()
    import hashlib
    return {"prefix": str(root), "entries": names,
            "sha256": hashlib.sha256("\n".join(names).encode()).hexdigest()}


def compare_fingerprints(before: Mapping[str, Any] | None, after: Mapping[str, Any] | None) -> dict[str, Any]:
    """Record of what changed in the shared environment during a run (entries only, no contents)."""
    if not before or not after:
        return {"checked": False}
    b, a = set(before["entries"]), set(after["entries"])
    return {"checked": True, "prefix": before["prefix"], "changed": before["sha256"] != after["sha256"],
            "added": sorted(a - b), "removed": sorted(b - a)}


def write_environment_config_snapshot(run_dir: str | Path, config: Mapping[str, Any]) -> Path:
    """Write the selected non-secret environment configuration under run control."""
    target = Path(run_dir) / "control" / "environment_config.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump(dict(config), sort_keys=False), encoding="utf-8")
    return target


def probe_runtime(executable: str | None = None, *, network_policy: str = "allowed",
                  package_installation: str = "allowed",
                  environment: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Collect non-sensitive runtime facts before an Agent starts."""
    env = dict(os.environ)
    if environment:
        env.update(environment)
    python = _python_info(executable or env.get("PYTHON"))
    conda_prefix = None
    conda_name = None
    executable_path = Path(python["executable"]).resolve()
    candidate = executable_path.parent.parent
    if candidate.parent.name == "envs":
        # The selected interpreter is authoritative. The launcher may itself
        # run from base while selecting a different environment's Python.
        conda_prefix = str(candidate)
        conda_name = candidate.name
    else:
        conda_prefix = env.get("CONDA_PREFIX")
        conda_name = env.get("CONDA_DEFAULT_ENV")
    return {
        "operating_system": _os_release(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "python": python,
        "conda_environment": conda_name,
        "conda_prefix": conda_prefix,
        "network_policy": network_policy,
        "package_installation": package_installation,
    }
