"""Render task instructions with optional structured run metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .validation import load_json, load_task, validate_manifest


def _cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def render_agent_prompt(task_path: str | Path, manifest_path: str | Path | None = None,
                        *, extra_instructions: str | None = None,
                        runtime_context: Mapping[str, Any] | None = None) -> str:
    """Render the task prompt and optional manifest/contract hints."""
    task_source = Path(task_path).resolve()
    task = load_task(task_source)
    manifest = None
    if manifest_path is not None:
        manifest = load_json(manifest_path)
        validate_manifest(manifest, task=task, check_paths=False)

    runtime = runtime_context or {}
    python = runtime.get("python") if isinstance(runtime.get("python"), Mapping) else {}
    lines = [
        f"# Task: {task.get('title') or task['task_id']}",
        "",
        task["task_prompt"].strip(),
        "",
        "## Runtime context",
        "",
        "### Working directory",
        "",
        "`$BENCH_WORK` is the Agent working directory and the same directory exposed as `$BENCH_OUTPUT`.",
        "",
        "### Input data",
        "",
    ]
    if manifest is not None:
        lines.extend([
            "Input data for this run is available under `$BENCH_OUTPUT/input/` (the same directory exposed as `$BENCH_INPUT`).",
            "The `input/` directory and everything below it are read-only, including symbolic-link targets; do not modify or delete them.",
        ])
    else:
        lines.append("No separate input directory is configured for this run.")
    lines.extend([
        "",
        "### Output location",
        "",
        "`$BENCH_OUTPUT` is the Agent output root. Write all task results below it.",
        "",
        "### Environment and network",
        "",
        f"- Operating system: {_cell(runtime.get('operating_system') or 'recorded by the framework')}",
        f"- Architecture: {_cell(runtime.get('architecture') or 'recorded by the framework')}",
        f"- Python: `{_cell(python.get('executable') or '$PYTHON')}` ({_cell(python.get('version') or 'selected at run time')})",
        f"- Conda environment: {_cell(runtime.get('conda_environment') or 'selected at run time')}",
        f"- Network policy: {_cell(runtime.get('network_policy') or 'allowed')}",
        "",
        "Network access and additional Python package installation are allowed. Use the designated evaluation environment or a task-local environment; do not modify the original shared `seismoagent` environment. Record installed dependencies and commands needed to reproduce the run.",
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
        "### Execution rules",
        "",
        "- Do not modify task files, manifests or framework-managed run-control files.",
        "- Keep all Agent-created files below `$BENCH_OUTPUT`.",
        "",
    ])
    if extra_instructions and extra_instructions.strip():
        lines.extend(["", "## Additional instructions", "", extra_instructions.strip()])
    return "\n".join(lines) + "\n"
