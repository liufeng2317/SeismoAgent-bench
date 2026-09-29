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
