"""Render task instructions with optional structured run metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .validation import load_json, load_task, validate_manifest


def _cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def render_agent_prompt(task_path: str | Path, manifest_path: str | Path | None = None,
                        *, extra_instructions: str | None = None) -> str:
    """Render the task prompt and optional manifest/contract hints."""
    task_source = Path(task_path).resolve()
    task = load_task(task_source)
    manifest = None
    if manifest_path is not None:
        manifest = load_json(manifest_path)
        validate_manifest(manifest, task=task, check_paths=False)

    lines = [
        f"# Task: {task.get('title') or task['task_id']}",
        "",
        task["task_prompt"].strip(),
    ]
    if manifest is not None:
        lines.extend([
            "",
            "## Input data",
            "",
            "Input data for this run is available under `$BENCH_OUTPUT/input/` (the same directory exposed as `$BENCH_INPUT`).",
            "The `input/` directory and everything below it are read-only; do not modify or delete them.",
        ])
    if task.get("output_artifacts"):
        lines.extend([
            "",
            "## Structured output hints",
            "",
            "These are optional structured hints. The task prompt remains the primary output instruction.",
            "",
            "| ID | Path | Kind | Required |",
            "|---|---|---|---|",
        ])
        for artifact in task["output_artifacts"]:
            lines.append("| " + " | ".join([
                _cell(artifact["id"]), _cell(artifact["path"]), _cell(artifact["kind"]),
                "yes" if artifact["required"] else "no",
            ]) + " |")
    lines.extend([
        "",
        "## Output location",
        "",
        "- `$BENCH_OUTPUT` is the Agent work/output root; write all task results below it.",
        "- Declared input links are below `$BENCH_OUTPUT/input/` and are read-only.",
        "",
        "## Framework constraints",
        "",
        "- Do not modify task files, manifests or run-control files.",
        "- Keep all Agent-created files below `$BENCH_OUTPUT`.",
    ])
    if extra_instructions and extra_instructions.strip():
        lines.extend(["", "## Additional instructions", "", extra_instructions.strip()])
    return "\n".join(lines) + "\n"
