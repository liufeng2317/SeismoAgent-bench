"""Workflow entrypoint for executing one declared Agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from SeismoAgentBench.agent.contract import AgentSpec
from SeismoAgentBench.execution import run_command, write_agent_config_snapshot
from SeismoAgentBench.reporting import write_environment_record


def run_agent(task_path: str | Path, manifest_path: str | Path | None, agent: AgentSpec,
              run_root: str | Path, run_id: str, *, timeout: float = 600,
              reference_manifest: str | Path | None = None,
              extra_env: Mapping[str, str] | None = None,
              resume: bool = False,
              agent_config: Mapping[str, Any] | None = None,
              agent_prompt: str | None = None) -> dict[str, Any]:
    """Execute one Agent and write execution records, without evaluation."""
    result = run_command(task_path, manifest_path, agent.command, run_root, run_id,
                         timeout=timeout, extra_env=extra_env, resume=resume,
                         agent_prompt=agent_prompt)
    run = Path(run_root).resolve() / run_id
    if agent_config is not None:
        write_agent_config_snapshot(run, agent_config)
    write_environment_record(run, result)
    record_dir = run / "record"
    record_dir.mkdir(exist_ok=True)
    references = {
        "task": "control/task_spec.json",
        "task_prompt": "control/task_prompt.md",
        "environment": "record/environment.json",
    }
    if (run / "control/input_manifest.json").is_file():
        references["input_manifest"] = "control/input_manifest.json"
    if (run / "control/output_contract.json").is_file():
        references["output_contract"] = "control/output_contract.json"
    if (run / "control/agent_prompt.md").is_file():
        references["prompt"] = "control/agent_prompt.md"
    provenance = {
        "schema_version": 1,
        "agent": {"name": agent.name, "version": agent.version},
        "command": {"argv": list(agent.command), "kind": "agent"},
        "references": references,
    }
    (record_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["agent"] = {"name": agent.name, "version": agent.version,
                        "provenance": "record/provenance.json"}
    run_result = json.loads((record_dir / "run_result.json").read_text(encoding="utf-8"))
    run_result["agent"] = result["agent"]
    run_result["command"] = {"provenance": "record/provenance.json"}
    (record_dir / "run_result.json").write_text(
        json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"run": run_result}
