"""Registry for task-declared scorer identities."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from .aggregate import aggregate_catalog_score
from .contract import score_artifacts
from .picks import score_picks
from .reference import ReferenceSpec
from .scientific import score_catalogs


class ScorerUnavailable(ValueError):
    """Raised when a declared scorer lacks its optional reference input."""


class ScorerRegistryError(ValueError):
    """Raised when a task references an unknown scorer."""


@dataclass(frozen=True)
class ScorerDefinition:
    name: str
    version: str
    mode: str  # local | reference
    handler: Callable[["ScorerContext"], dict[str, Any]] | None = None


@dataclass(frozen=True)
class ScorerContext:
    task: Mapping[str, Any]
    output_dir: Path
    validation: Mapping[str, Any]
    reference_manifest: str | Path | None = None
    pick_reference: str | Path | None = None
    pick_time_tolerance_s: float = 0.5


class ScorerRegistry:
    """Small explicit registry shared by task validation and evaluation."""

    def __init__(self, definitions: tuple[ScorerDefinition, ...] = ()) -> None:
        self._definitions = {(item.name, item.version): item for item in definitions}

    def register(self, name: str, version: str, *, mode: str,
                 handler: Callable[[ScorerContext], dict[str, Any]] | None = None) -> None:
        if mode not in {"local", "reference"}:
            raise ScorerRegistryError(f"unsupported scorer mode: {mode}")
        key = (name, version)
        if key in self._definitions:
            raise ScorerRegistryError(f"scorer is already registered: {name}@{version}")
        self._definitions[key] = ScorerDefinition(name, version, mode, handler)

    def resolve(self, name: str, version: str) -> ScorerDefinition:
        try:
            return self._definitions[(name, version)]
        except KeyError as exc:
            raise ScorerRegistryError(f"scorer is not registered: {name}@{version}") from exc

    def plan(self, task: Mapping[str, Any]) -> list[dict[str, Any]]:
        evaluation = task.get("evaluation")
        scorers = evaluation.get("scorers", []) if isinstance(evaluation, Mapping) else []
        plan: list[dict[str, Any]] = []
        for item in scorers:
            definition = self.resolve(str(item["name"]), str(item["version"]))
            plan.append({"name": definition.name, "version": definition.version,
                         "mode": definition.mode, "status": "declared"})
        return plan


def default_scorer_registry() -> ScorerRegistry:
    return ScorerRegistry((
        ScorerDefinition("artifact-contract", "1", "local", _artifact_handler),
        ScorerDefinition("catalog-basic", "1", "reference", _catalog_handler),
        ScorerDefinition("phase-picking-basic", "1", "reference", _pick_handler),
    ))


def _artifact_handler(context: ScorerContext) -> dict[str, Any]:
    return {"output_file": "score.json", "result_key": "score",
            "payload": score_artifacts(context.task, context.validation)}


def _catalog_handler(context: ScorerContext) -> dict[str, Any]:
    if context.reference_manifest is None:
        raise ScorerUnavailable("catalog-basic requires reference_manifest")
    reference = ReferenceSpec.from_manifest(context.reference_manifest)
    candidates = [item for item in context.task["output_artifacts"]
                  if item["kind"].lower() == "catalog"]
    if len(candidates) != 1:
        raise ValueError("scientific scoring requires exactly one catalog output artifact")
    candidate = json.loads((context.output_dir / candidates[0]["path"]).read_text(encoding="utf-8"))
    scientific = score_catalogs(candidate, reference.load_catalog(),
                                reference_id=reference.reference_id,
                                reference_version=reference.version)
    return {"output_file": "scientific_score.json", "result_key": "scientific_score",
            "payload": scientific, "summary": aggregate_catalog_score(scientific),
            "reference": {"reference_id": reference.reference_id,
                          "version": reference.version, "role": reference.role}}


def _pick_handler(context: ScorerContext) -> dict[str, Any]:
    if context.pick_reference is None:
        raise ScorerUnavailable("phase-picking-basic requires pick_reference")
    candidates = [item for item in context.task["output_artifacts"]
                  if item.get("kind", "").lower() in {"picks", "phase_picks"}
                  or Path(item["path"]).name.lower() == "picks.csv"]
    if len(candidates) != 1:
        raise ValueError("pick scoring requires exactly one picks CSV output artifact")
    candidate = context.output_dir / candidates[0]["path"]
    if not candidate.is_file():
        raise ValueError(f"candidate picks file is missing: {candidate}")
    payload = score_picks(candidate, context.pick_reference,
                          time_tolerance_s=context.pick_time_tolerance_s,
                          reference_id=Path(context.pick_reference).stem)
    return {"output_file": "pick_scientific_score.json",
            "result_key": "pick_scientific_score", "payload": payload}
