"""Small orchestration layer for the trusted-development workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from SeismoAgentBench.execution import run_command
from SeismoAgentBench.reporting import write_environment_record, write_evaluation_report
from SeismoAgentBench.scoring import ArtifactValidationError, ScoreError, score_artifacts, validate_artifacts
from SeismoAgentBench.task import load_json


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_task(task_path: str | Path, manifest_path: str | Path, command: Sequence[str],
             run_root: str | Path, run_id: str, *, timeout: float = 600) -> dict[str, Any]:
    """Run a task, validate its output and write a deterministic score record.

    A non-zero command exit is returned as an execution result without scoring.
    A successful command with invalid declared outputs is returned as
    ``artifact_invalid``. Scientific scoring is outside this orchestration
    layer.
    """
    result = run_command(task_path, manifest_path, command, run_root, run_id, timeout=timeout)
    run = Path(run_root).resolve() / run_id
    write_environment_record(run, result)
    if result["state"] != "completed":
        write_evaluation_report(run, result)
        return {"run": result, "score": None}

    task = load_json(run / "task_spec.json")
    output = run / "output"
    artifacts_path = run / "artifacts.json"
    score_dir = run / "score"
    try:
        validation = validate_artifacts(task, output)
    except ArtifactValidationError as exc:
        validation = {"validated": False, "errors": exc.errors, "artifacts": []}
        _write_json(artifacts_path, validation)
        result["state"] = "artifact_invalid"
        result["artifact_validation"] = "failed"
        _write_json(run / "run_result.json", result)
        write_evaluation_report(run, result)
        return {"run": result, "artifacts": validation, "score": None}

    _write_json(artifacts_path, validation)
    score_dir.mkdir()
    try:
        score = score_artifacts(task, validation)
    except ScoreError as exc:
        score = {"schema_version": 1, "status": "scoring_failed", "errors": [str(exc)]}
        _write_json(score_dir / "score.json", score)
        result["state"] = "scoring_failed"
        result["scoring_error"] = str(exc)
        _write_json(run / "run_result.json", result)
        write_evaluation_report(run, result)
        return {"run": result, "artifacts": validation, "score": score}
    _write_json(score_dir / "score.json", score)
    result["state"] = "scored"
    result["artifact_validation"] = "passed"
    _write_json(run / "run_result.json", result)
    write_evaluation_report(run, result)
    return {"run": result, "artifacts": validation, "score": score}
