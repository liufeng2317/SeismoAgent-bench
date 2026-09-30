"""Agent runtime configuration loading and safe run snapshots."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

import yaml


class AgentConfigError(ValueError):
    """Raised when an Agent configuration is invalid or unsafe to record."""


_TOP_LEVEL = {
    "harness", "model", "provider", "base_url", "api_key", "config",
    "executable", "version_command", "auth",
}
_SECRET = re.compile(r"(api[_-]?key|token|password|secret|credential)", re.I)


def _redact(value: Any, *, key: str = "") -> Any:
    if _SECRET.search(key):
        if value not in (None, "", False):
            raise AgentConfigError(f"secret-bearing field must be null or empty: {key}")
        return None
    if isinstance(value, Mapping):
        return {str(k): _redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def load_agent_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML Agent config and return a safe, serializable snapshot."""
    source = Path(path)
    try:
        value = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise AgentConfigError(f"cannot load Agent config {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise AgentConfigError("Agent config must be a YAML mapping")
    unknown = sorted(set(value) - _TOP_LEVEL)
    if unknown:
        raise AgentConfigError(f"unknown Agent config fields: {', '.join(unknown)}")
    if not isinstance(value.get("harness"), str) or not value["harness"]:
        raise AgentConfigError("Agent config harness must be a non-empty string")
    if "executable" in value and (
        not isinstance(value["executable"], str) or not value["executable"]
    ):
        raise AgentConfigError("Agent config executable must be a non-empty string")
    version_command = value.get("version_command", ["--version"])
    if (not isinstance(version_command, list) or not version_command or
            any(not isinstance(item, str) or not item for item in version_command)):
        raise AgentConfigError("Agent config version_command must be a non-empty string list")
    auth = value.get("auth", {})
    if not isinstance(auth, dict):
        raise AgentConfigError("Agent config auth must be a mapping")
    if "mode" in auth and (not isinstance(auth["mode"], str) or not auth["mode"]):
        raise AgentConfigError("Agent config auth.mode must be a non-empty string")
    config = value.get("config", {})
    if not isinstance(config, dict):
        raise AgentConfigError("Agent config.config must be a mapping")
    return _redact(dict(value))


def write_agent_config_snapshot(run_dir: str | Path, config: Mapping[str, Any]) -> Path:
    """Write a validated, non-secret config snapshot under run control."""
    target = Path(run_dir) / "control" / "agent_config.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    safe = _redact(dict(config))
    target.write_text(yaml.safe_dump(safe, sort_keys=False), encoding="utf-8")
    return target
