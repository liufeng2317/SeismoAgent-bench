"""Evaluate a completed Agent run without starting the Agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from SeismoAgentBench.execution import ExecutionError
from SeismoAgentBench.reporting import write_evaluation_report
from SeismoAgentBench.scoring import (
    AggregationError,
    ArtifactValidationError,
    ReferenceError,
    ScoreError,
    ScientificScoreError,
    PickScoreError,
    ReferenceSpec,
    aggregate_catalog_score,
    score_artifacts,
    score_catalogs,
    validate_artifacts,
    score_picks,
)
from SeismoAgentBench.task import load_json, validate_output_contract


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


def _pick_artifact(task: dict[str, Any], output: Path) -> Path:
    candidates = [item for item in task["output_artifacts"]
                  if item.get("kind", "").lower() in {"picks", "phase_picks"}
                  or Path(item["path"]).name.lower() == "picks.csv"]
    if len(candidates) != 1:
        raise ScientificScoreError("pick scoring requires exactly one picks CSV output artifact")
    path = output / candidates[0]["path"]
    if not path.is_file():
        raise ScientificScoreError(f"candidate picks file is missing: {path}")
    return path


def evaluate_run(run_dir: str | Path, *, reference_manifest: str | Path | None = None,
                 pick_reference: str | Path | None = None,
                 pick_time_tolerance_s: float = 0.5) -> dict[str, Any]:
    """Evaluate a completed Agent run without starting the Agent."""
    run = Path(run_dir).resolve()
    result_path = run / "record" / "run_result.json"
    if not result_path.is_file():
        raise ExecutionError(f"run record is missing: {result_path}")
    result = load_json(result_path)
    if result["state"] != "completed":
        write_evaluation_report(run, result)
        return {"run": result, "score": None}

    task = load_json(run / "control" / "task_spec.json")
    contract_path = run / "control" / "output_contract.json"
    if contract_path.is_file():
        contract = load_json(contract_path)
        validate_output_contract(contract)
        task = dict(task)
        task["output_artifacts"] = contract["artifacts"]
    elif "output_artifacts" not in task:
        raise ExecutionError(f"output contract is missing: {contract_path}")
    # The Agent owns one work directory. Artifact paths are relative to it.
    output = run / "work"
    artifacts_path = run / "record" / "artifact_manifest.json"
    score_dir = run / "evaluation"
    try:
        validation = validate_artifacts(task, output)
    except ArtifactValidationError as exc:
        validation = {"validated": False, "errors": exc.errors, "artifacts": []}
        _write_json(artifacts_path, validation)
        result["state"] = "artifact_invalid"
        result["artifact_validation"] = "failed"
        _write_json(run / "record" / "run_result.json", result)
        write_evaluation_report(run, result)
        return {"run": result, "artifacts": validation, "score": None}

    _write_json(artifacts_path, validation)
    score_dir.mkdir(exist_ok=True)
    try:
        score = score_artifacts(task, validation)
    except ScoreError as exc:
        score = {"schema_version": 1, "status": "scoring_failed", "errors": [str(exc)]}
        _write_json(score_dir / "score.json", score)
        result["state"] = "scoring_failed"
        result["scoring_error"] = str(exc)
        _write_json(run / "record" / "run_result.json", result)
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
            _write_json(run / "record" / "run_result.json", result)
            write_evaluation_report(run, result, reference=reference_record)
            return {"run": result, "artifacts": validation, "score": score, "scientific_score": failure}
    if pick_reference is not None:
        try:
            pick_score = score_picks(_pick_artifact(task, output), pick_reference,
                                    time_tolerance_s=pick_time_tolerance_s,
                                    reference_id=Path(pick_reference).stem)
            _write_json(score_dir / "pick_scientific_score.json", pick_score)
            result["pick_scientific_scoring"] = "passed"
        except (PickScoreError, ScientificScoreError, OSError, UnicodeError) as exc:
            failure = {"schema_version": 1, "status": "scoring_failed", "errors": [str(exc)]}
            _write_json(score_dir / "pick_scientific_score.json", failure)
            result["state"] = "scoring_failed"
            result["pick_scientific_scoring"] = "failed"
            result["scoring_error"] = str(exc)
            _write_json(run / "record" / "run_result.json", result)
            write_evaluation_report(run, result, reference=reference_record)
            return {"run": result, "artifacts": validation, "score": score,
                    "pick_scientific_score": failure}
    result["state"] = "scored"
    result["artifact_validation"] = "passed"
    _write_json(run / "record" / "run_result.json", result)
    write_evaluation_report(run, result, reference=reference_record)
    output_result = {"run": result, "artifacts": validation, "score": score}
    if reference_manifest is not None:
        output_result["scientific_score"] = scientific
        output_result["task_summary"] = summary
    if pick_reference is not None:
        output_result["pick_scientific_score"] = pick_score
    return output_result
