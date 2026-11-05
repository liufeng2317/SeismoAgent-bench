"""Small helpers for writing canonical task packages in unit tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_task_package(path: Path, task: dict[str, Any], prompt: str) -> None:
    """Write a task JSON plus its prompt and output contract sidecars."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(task)
    artifacts = payload.pop("output_artifacts", None)
    payload["task_prompt_file"] = "task_prompt.md"
    payload["output_contract"] = "output_contract.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    (path.parent / "task_prompt.md").write_text(prompt + "\n", encoding="utf-8")
    (path.parent / "output_contract.json").write_text(
        json.dumps({"schema_version": 1, "artifacts": artifacts or []}),
        encoding="utf-8",
    )


def write_input_manifest(path: Path, manifest: dict[str, Any]) -> None:
    """Write an input manifest whose entries exist: each declared file or folder is created beside the manifest.

    The runner refuses a manifest entry that does not exist, so a fixed path such as /tmp/metadata.json would
    make the tests depend on the machine they run on.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    for entry in manifest.get("entries", []):
        target = path.parent / "inputs" / Path(entry["path"]).name
        if entry.get("type") == "folder":
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text("{}", encoding="utf-8")
        entries.append({**entry, "path": str(target)})
    path.write_text(json.dumps({**manifest, "entries": entries}), encoding="utf-8")
