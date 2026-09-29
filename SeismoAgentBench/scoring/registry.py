"""Registry for task-declared scorer identities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class ScorerRegistryError(ValueError):
    """Raised when a task references an unknown scorer."""


@dataclass(frozen=True)
class ScorerDefinition:
    name: str
    version: str
    mode: str  # local | reference


class ScorerRegistry:
    """Small explicit registry shared by task validation and evaluation."""

    def __init__(self, definitions: tuple[ScorerDefinition, ...] = ()) -> None:
        self._definitions = {(item.name, item.version): item for item in definitions}

    def register(self, name: str, version: str, *, mode: str) -> None:
        if mode not in {"local", "reference"}:
            raise ScorerRegistryError(f"unsupported scorer mode: {mode}")
        key = (name, version)
        if key in self._definitions:
            raise ScorerRegistryError(f"scorer is already registered: {name}@{version}")
        self._definitions[key] = ScorerDefinition(name, version, mode)

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
        ScorerDefinition("artifact-contract", "1", "local"),
        ScorerDefinition("catalog-basic", "1", "reference"),
        ScorerDefinition("phase-picking-basic", "1", "reference"),
    ))
