"""Small orchestration layer for the trusted-development workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from SeismoAgentBench.execution import run_command
from SeismoAgentBench.reporting import write_environment_record, write_evaluation_report
from SeismoAgentBench.scoring import (
    AggregationError, ArtifactValidationError, ReferenceError, ScoreError,
    ScientificScoreError, ReferenceSpec, aggregate_catalog_score, score_artifacts,
    score_catalogs, validate_artifacts,
)
from SeismoAgentBench.task import load_json


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _catalog_artifact(task: dict[str, Any], output: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    candidates = [item for item in task["output_artifacts"] if item["kind"].lower() == "catalog"]
    if len(candidates) != 1:
        raise ScientificScoreError("scientific scoring requires exactly one catalog output artifact")
    item = candidates[0]
    path = output / item["path"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScientificScoreError(f"cannot load candidate catalog: {exc}") from exc
    return item, value


def run_task(task_path: str | Path, manifest_path: str | Path, command: Sequence[str],
             run_root: str | Path, run_id: str, *, timeout: float = 600,
             reference_manifest: str | Path | None = None) -> dict[str, Any]:
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
    result["artifact_validation"] = "passed"
    reference_record = None
    if reference_manifest is not None:
        try:
            reference = ReferenceSpec.from_manifest(reference_manifest)
            _, candidate_catalog = _catalog_artifact(task, output)
            scientific = score_catalogs(
                candidate_catalog,
                reference.load_catalog(),
                reference_id=reference.reference_id,
                reference_version=reference.version,
            )
            summary = aggregate_catalog_score(scientific)
            _write_json(score_dir / "scientific_score.json", scientific)
            _write_json(score_dir / "task_summary.json", summary)
            result["scientific_scoring"] = "passed"
            reference_record = {"reference_id": reference.reference_id,
                                "version": reference.version, "role": reference.role}
        except (AggregationError, ReferenceError, ScientificScoreError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            failure = {"schema_version": 1, "status": "scoring_failed", "errors": [str(exc)]}
            _write_json(score_dir / "scientific_score.json", failure)
            result["state"] = "scoring_failed"
            result["scientific_scoring"] = "failed"
            result["scoring_error"] = str(exc)
            _write_json(run / "run_result.json", result)
            write_evaluation_report(run, result, reference=reference_record)
            return {"run": result, "artifacts": validation, "score": score, "scientific_score": failure}
    result["state"] = "scored"
    result["artifact_validation"] = "passed"
    _write_json(run / "run_result.json", result)
    write_evaluation_report(run, result, reference=reference_record)
    output_result = {"run": result, "artifacts": validation, "score": score}
    if reference_manifest is not None:
        output_result["scientific_score"] = scientific
        output_result["task_summary"] = summary
    return output_result
