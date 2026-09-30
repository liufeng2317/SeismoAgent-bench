"""Resolve external Agent authentication references without reading secrets."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any, Mapping


class AuthConfigError(ValueError):
    """Raised when an Agent authentication declaration is incomplete."""


_MODES = {"external_profile", "env_file", "codex_home"}


def resolve_auth(config: Mapping[str, Any] | None) -> dict[str, str | None]:
    """Return external authentication references declared by a profile.

    This function deliberately does not open an env file or login directory.
    The caller decides when to load/inject those values, while provenance can
    record only the mode and sanitized source path.
    """
    auth = (config or {}).get("auth", {})
    if not isinstance(auth, Mapping):
        raise AuthConfigError("Agent config auth must be a mapping")
    mode = auth.get("mode", "external_profile")
    if not isinstance(mode, str) or mode not in _MODES:
        raise AuthConfigError(f"unsupported authentication mode: {mode!r}")
    result: dict[str, str | None] = {"mode": mode, "env_file": None, "codex_home": None}
    if mode == "env_file":
        source = auth.get("env_file")
        if not isinstance(source, str) or not source:
            raise AuthConfigError("auth.env_file is required for env_file mode")
        result["env_file"] = str(Path(source).expanduser())
    elif mode == "codex_home":
        source = auth.get("codex_home")
        if not isinstance(source, str) or not source:
            raise AuthConfigError("auth.codex_home is required for codex_home mode")
        result["codex_home"] = str(Path(source).expanduser())
    return result


def prepare_codex_runtime_home(runtime_root: str | Path, source_home: str | Path) -> Path:
    """Copy one private ``auth.json`` into a per-run temporary Codex home."""
    source = Path(source_home).expanduser()
    if source.is_symlink() or not source.is_dir():
        raise AuthConfigError(f"Codex auth source must be a real directory: {source}")
    if source.stat().st_mode & 0o077:
        raise AuthConfigError(f"Codex auth source must not be group/other accessible: {source}")
    source_auth = source / "auth.json"
    if source_auth.is_symlink() or not source_auth.is_file():
        raise AuthConfigError(f"Codex auth file not found: {source_auth}")
    if source_auth.stat().st_mode & 0o077:
        raise AuthConfigError(f"Codex auth file must not be group/other accessible: {source_auth}")
    target_home = Path(runtime_root) / "codex_home"
    target_home.mkdir(mode=0o700, exist_ok=False)
    target_home.chmod(0o700)
    target_auth = target_home / "auth.json"
    try:
        shutil.copy2(source_auth, target_auth)
        target_auth.chmod(0o600)
    except BaseException:
        shutil.rmtree(target_home, ignore_errors=True)
        raise
    return target_home
