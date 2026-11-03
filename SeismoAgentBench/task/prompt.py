"""Render task instructions with optional structured run metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .validation import load_json, load_task, validate_manifest


_DEFAULT_FRAMEWORK_PROMPT = (Path(__file__).resolve().parents[1] / "configs" / "prompts" / "framework.md")


def _package_policy(policy: str | None) -> str:
    if policy == "run_local":
        return ("only into a virtual environment you create under `$BENCH_OUTPUT` "
                "(`$PYTHON -m venv --system-site-packages $BENCH_OUTPUT/venv`, then use its `bin/python`); "
                "the shared environment is read-only and pip refuses to install into it")
    return _cell(policy or "allowed")


def _load_framework_prompt(path: str | Path | None) -> str:
    source = _DEFAULT_FRAMEWORK_PROMPT if path is None else Path(path)
    try:
        text = source.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise FileNotFoundError(f"framework prompt not found: {source}") from exc
    if not text:
        raise ValueError(f"framework prompt must not be empty: {source}")
    return text


def _cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def render_agent_prompt(task_path: str | Path, manifest_path: str | Path | None = None,
                        *, extra_instructions: str | None = None,
                        runtime_context: Mapping[str, Any] | None = None,
                        framework_prompt_path: str | Path | None = None) -> str:
    """Render task instructions, framework rules and run-specific context."""
    task_source = Path(task_path).resolve()
    task = load_task(task_source)
    manifest = None
    if manifest_path is not None:
        manifest = load_json(manifest_path)
        validate_manifest(manifest, task=task, check_paths=False)

    runtime = runtime_context or {}
    python = runtime.get("python") if isinstance(runtime.get("python"), Mapping) else {}
    framework_prompt = _load_framework_prompt(framework_prompt_path)
    lines = [
        "<task_prompt>",
        f"# Task: {task.get('title') or task['task_id']}",
        "",
        task["task_prompt"].strip(),
        "</task_prompt>",
        "",
        "<framework_instructions>",
        framework_prompt,
        "</framework_instructions>",
        "",
        "<runtime_context>",
        "## Working directory",
        "",
        "Working directory: `$BENCH_WORK`",
        "Output directory: `$BENCH_OUTPUT`",
        "",
        "## Input data",
        "",
    ]
    if manifest is not None:
        lines.extend([
            "Input directory: `$BENCH_INPUT` (also available as `$BENCH_OUTPUT/input/`).",
        ])
    else:
        lines.append("Input directory: not configured for this run.")
    lines.extend([
        "",
        "## Environment and network",
        "",
        f"- Operating system: {_cell(runtime.get('operating_system') or 'recorded by the framework')}",
        f"- Architecture: {_cell(runtime.get('architecture') or 'recorded by the framework')}",
        f"- Python: `{_cell(python.get('executable') or '$PYTHON')}` ({_cell(python.get('version') or 'selected at run time')})",
        f"- Conda environment: {_cell(runtime.get('conda_environment') or 'selected at run time')}",
        f"- Network policy: {_cell(runtime.get('network_policy') or 'allowed')}",
        f"- Package installation: {_package_policy(runtime.get('package_installation'))}",
    ])
    budget = runtime.get("time_budget_s")
    if isinstance(budget, (int, float)) and not isinstance(budget, bool) and budget > 0:
        lines.append(
            f"- Time budget: {int(budget)} s (~{budget / 3600:.1f} h) wall clock from run start; "
            "the run is terminated at the deadline")
    if task.get("output_artifacts"):
        lines.extend([
            "",
            "<output_hints>",
            "These are optional structured hints. The task prompt remains the primary output instruction.",
            "",
            "## Declared output artifacts",
            "",
            "| ID | Path | Kind | Required |",
            "|---|---|---|---|",
        ])
        for artifact in task["output_artifacts"]:
            lines.append("| " + " | ".join([
                _cell(artifact["id"]), _cell(artifact["path"]), _cell(artifact["kind"]),
                "yes" if artifact["required"] else "no",
            ]) + " |")
        lines.append("</output_hints>")
    lines.append("</runtime_context>")
    if extra_instructions and extra_instructions.strip():
        lines.extend(["", "<additional_instructions>", extra_instructions.strip(), "</additional_instructions>"])
    return "\n".join(lines) + "\n"
