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
        "# SeismoAgentBench Task",
        "",
        f"## Task: {task.get('title') or task['task_id']}",
        "",
        task["task_prompt"].strip(),
    ]
    if manifest is not None:
        lines.extend([
            "",
            "## Input data",
            "",
            "The following inputs are declared for this run. Use only these inputs and do not modify them.",
            "",
            "| ID | Semantic type | Format | Path | Path type | Time window |",
            "|---|---|---|---|---|---|",
        ])
        for entry in manifest["entries"]:
            window = ""
            if entry.get("start_time") or entry.get("end_time"):
                window = f"{entry.get('start_time', '')} to {entry.get('end_time', '')}"
            lines.append("| " + " | ".join([
                _cell(entry["id"]), _cell(entry["data_type"]), _cell(entry["format"]),
                _cell(entry["path"]), _cell(entry.get("path_type", "file")), _cell(window),
            ]) + " |")
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
    lines.extend(["", "## Runtime paths", "", "- Task specification: `$BENCH_TASK_SPEC`"])
    if manifest is not None:
        lines.append("- Optional input manifest: `$BENCH_INPUT_MANIFEST`")
    if task.get("output_contract"):
        lines.append("- Optional output contract: `$BENCH_OUTPUT_CONTRACT`")
    lines.extend([
        "- Working directory: `$BENCH_WORK`",
        "- Agent work and output root: `$BENCH_OUTPUT`",
        "",
        "## Framework constraints",
        "",
        "- Do not modify task files, manifests or run-control files.",
        "- Keep all Agent-created files below `$BENCH_OUTPUT`.",
    ])
    if extra_instructions and extra_instructions.strip():
        lines.extend(["", "## Additional instructions", "", extra_instructions.strip()])
    return "\n".join(lines) + "\n"
