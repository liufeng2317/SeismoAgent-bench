"""Experiment specification validation and deterministic unit expansion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

class ExperimentSpecError(ValueError):
    """Raised when an experiment specification is invalid."""


def load_experiment_spec(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        value = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ExperimentSpecError(f"cannot load experiment spec {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExperimentSpecError("experiment spec must be a YAML mapping")
    required = {"experiment_id", "output_root", "concurrency", "agents", "tasks"}
    missing = sorted(required - set(value))
    if missing:
        raise ExperimentSpecError(f"experiment spec is missing: {', '.join(missing)}")
    if not isinstance(value["experiment_id"], str) or not value["experiment_id"]:
        raise ExperimentSpecError("experiment_id must be a non-empty string")
    if not isinstance(value["output_root"], str) or not value["output_root"]:
        raise ExperimentSpecError("output_root must be a non-empty path")
    if not isinstance(value["concurrency"], int) or value["concurrency"] < 1:
        raise ExperimentSpecError("concurrency must be a positive integer")
    agents = value["agents"]
    if not isinstance(agents, list) or not agents:
        raise ExperimentSpecError("agents must be a non-empty list")
    agent_ids: set[str] = set()
    for item in agents:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ExperimentSpecError("each agent must have a non-empty id")
        if item["id"] in agent_ids:
            raise ExperimentSpecError(f"duplicate agent id: {item['id']}")
        agent_ids.add(item["id"])
        if not isinstance(item.get("config"), str) or not item["config"]:
            raise ExperimentSpecError(f"agent {item['id']} must declare config")
        if not isinstance(item.get("name"), str) or not item["name"]:
            raise ExperimentSpecError(f"agent {item['id']} must declare name")
        if not isinstance(item.get("version"), str) or not item["version"]:
            raise ExperimentSpecError(f"agent {item['id']} must declare version")
        if not isinstance(item.get("command"), list) or not item["command"] or any(not isinstance(v, str) or not v for v in item["command"]):
            raise ExperimentSpecError(f"agent {item['id']} command must be a non-empty string list")
    tasks = value["tasks"]
    if not isinstance(tasks, list) or not tasks:
        raise ExperimentSpecError("tasks must be a non-empty list")
    for item in tasks:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ExperimentSpecError("each task must have a non-empty id")
        for field in ("task_spec", "input_manifest"):
            if not isinstance(item.get(field), str) or not item[field]:
                raise ExperimentSpecError(f"task {item['id']} must declare {field}")
        variants = item.get("variants", ["base"])
        if not isinstance(variants, list) or not variants or any(not isinstance(v, str) or not v for v in variants):
            raise ExperimentSpecError(f"task {item['path']} variants must be a non-empty string list")
    return dict(value)


def expand_experiment(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand agents × tasks × variants in stable declaration order."""
    units: list[dict[str, Any]] = []
    for agent in spec["agents"]:
        for task in spec["tasks"]:
            for variant in task.get("variants", ["base"]):
                units.append({
                    "experiment_id": spec["experiment_id"],
                    "agent_id": agent["id"],
                    "agent_name": agent["name"],
                    "agent_version": agent["version"],
                    "agent_config": agent["config"],
                    "command": list(agent["command"]),
                    "task_id": task["id"],
                    "task_spec": task["task_spec"],
                    "input_manifest": task["input_manifest"],
                    "variant": variant,
                })
    return units
