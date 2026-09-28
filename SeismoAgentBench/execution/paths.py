"""Stable, filesystem-only run layout for benchmark evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_ID = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


class RunLayoutError(ValueError):
    """Raised when a run layout component is unsafe or incomplete."""


def _check(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise RunLayoutError(f"{label} must match [a-z0-9][a-z0-9_.-]*")
    return value


@dataclass(frozen=True)
class RunLayout:
    """Canonical persistent path for one benchmark unit."""

    root: Path
    campaign_id: str
    task_id: str
    variant: str
    agent_id: str
    run_id: str

    def __post_init__(self) -> None:
        if not self.root.is_absolute():
            raise RunLayoutError("run root must be absolute")
        for value, label in ((self.campaign_id, "campaign_id"), (self.task_id, "task_id"),
                             (self.variant, "variant"), (self.agent_id, "agent_id"),
                             (self.run_id, "run_id")):
            _check(value, label)

    @property
    def unit_root(self) -> Path:
        return (self.root / self.campaign_id / self.task_id / self.variant /
                self.agent_id / self.run_id)

    @property
    def run_root(self) -> Path:
        return self.unit_root.parent

    def record(self) -> dict[str, str]:
        return {
            "root": str(self.root),
            "campaign_id": self.campaign_id,
            "task_id": self.task_id,
            "variant": self.variant,
            "agent_id": self.agent_id,
            "run_id": self.run_id,
            "unit_root": str(self.unit_root),
        }
