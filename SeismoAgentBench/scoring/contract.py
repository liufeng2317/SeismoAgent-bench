"""Deterministic scoring of the task output contract."""

from __future__ import annotations

from typing import Any, Mapping

from SeismoAgentBench.task import ValidationError, validate_task


class ScoreError(ValueError):
    """Raised when a validated artifact result cannot be scored."""


def score_artifacts(task: Mapping[str, Any], validation: Mapping[str, Any]) -> dict[str, Any]:
    """Create a contract-compliance score from an artifact inventory.

    This scorer measures only declared-file compliance. It does not inspect
    scientific values, compare against a reference catalog or assign a
    scientific quality score.
    """
    try:
        validate_task(task)
    except ValidationError as exc:
        raise ScoreError(f"invalid task: {exc}") from exc
    if validation.get("validated") is not True:
        raise ScoreError("artifact validation must pass before scoring")
    inventory = validation.get("artifacts")
    if not isinstance(inventory, list):
        raise ScoreError("artifact validation result must contain an artifacts list")

    declared = {item["id"]: item for item in task["output_artifacts"]}
    seen: set[str] = set()
    for item in inventory:
        if not isinstance(item, Mapping) or not isinstance(item.get("id"), str):
            raise ScoreError("artifact inventory entries must have string ids")
        artifact_id = item["id"]
        if artifact_id in seen:
            raise ScoreError(f"duplicate artifact inventory id {artifact_id!r}")
        if artifact_id not in declared:
            raise ScoreError(f"artifact inventory contains undeclared id {artifact_id!r}")
        if not isinstance(item.get("bytes"), int) or item["bytes"] < 0:
            raise ScoreError(f"artifact {artifact_id!r} has invalid byte size")
        seen.add(artifact_id)

    required_ids = {item["id"] for item in task["output_artifacts"] if item["required"]}
    required_present = len(required_ids & seen)
    missing_required = sorted(required_ids - seen)
    if missing_required:
        raise ScoreError(f"required artifacts are absent from inventory: {', '.join(missing_required)}")
    optional_present = len(seen - required_ids)
    bytes_total = sum(item["bytes"] for item in inventory)
    return {
        "schema_version": 1,
        "status": "passed",
        "scorer": {"name": "artifact-contract", "version": "1"},
        "task": {"id": task["task_id"], "version": task["version"]},
        "metrics": {
            "declared_artifacts": len(declared),
            "present_artifacts": len(seen),
            "required_artifacts": len(required_ids),
            "required_artifacts_present": required_present,
            "optional_artifacts_present": optional_present,
            "total_bytes": bytes_total,
            "contract_compliance": 1.0,
        },
        "artifacts": list(inventory),
    }
