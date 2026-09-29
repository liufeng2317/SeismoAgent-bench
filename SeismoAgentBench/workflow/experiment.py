"""Serial execution of an already validated experiment plan."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from SeismoAgentBench.agent import AgentSpec
from SeismoAgentBench.execution import (ExperimentSpecError, expand_experiment,
                                        load_agent_config, load_experiment_spec)
from .run_agent import run_agent


def execute_experiment(spec_path: str | Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    """Execute planned units serially and return execution records.

    This function deliberately does not evaluate outputs. Each unit is run
    through the same `run_agent()` entrypoint used by the single-run CLI.
    """
    source = Path(spec_path).resolve()
    spec = load_experiment_spec(source)
    units = expand_experiment(spec)
    if limit is not None and (limit < 1 or limit > len(units)):
        raise ValueError("limit must be between 1 and the number of planned units")
    units = units[:limit] if limit is not None else units
    output_root = Path(spec["output_root"])
    if not output_root.is_absolute():
        output_root = (source.parent / output_root).resolve()
    results: list[dict[str, Any]] = []
    for index, unit in enumerate(units, start=1):
        task_spec = (source.parent / unit["task_spec"]).resolve()
        manifest = (source.parent / unit["input_manifest"]).resolve()
        config_path = (source.parent / unit["agent_config"]).resolve()
        config = load_agent_config(config_path)
        if config["harness"] != unit["harness"]:
            raise ExperimentSpecError(
                f"agent {unit['agent_id']} harness mismatch: "
                f"experiment={unit['harness']!r}, config={config['harness']!r}"
            )
        agent = AgentSpec.from_command(unit["agent_name"], unit["agent_version"], unit["command"])
        run_id = f"run_{index:03d}_{unit['agent_id']}_{unit['variant']}"
        result = run_agent(task_spec, manifest, agent, output_root, run_id,
                           agent_config=config)
        run = output_root / run_id
        (run / "record" / "experiment_unit.json").write_text(
            json.dumps(unit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        results.append(result)
    return results
