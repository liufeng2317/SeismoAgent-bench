"""Workflow entrypoint for executing one declared Agent."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from SeismoAgentBench.agent.contract import AgentSpec
from SeismoAgentBench.execution import (run_command, tools_snapshot, write_agent_config_snapshot,
                                        write_environment_config_snapshot)
from SeismoAgentBench.reporting import write_environment_record


def run_agent(task_path: str | Path, manifest_path: str | Path | None, agent: AgentSpec,
              run_root: str | Path, run_id: str, *, timeout: float = 600,
              reference_manifest: str | Path | None = None,
              extra_env: Mapping[str, str] | None = None,
              resume: bool = False,
              agent_config: Mapping[str, Any] | None = None,
              environment_config: Mapping[str, Any] | None = None,
              agent_prompt: str | None = None,
              auth_source_home: str | Path | None = None,
              runtime_context: Mapping[str, Any] | None = None,
              stdin_text: str | None = None) -> dict[str, Any]:
    """Execute one Agent and write execution records, without evaluation."""
    result = run_command(task_path, manifest_path, agent.command, run_root, run_id,
                         timeout=timeout, extra_env=extra_env, resume=resume,
                         agent_prompt=agent_prompt, auth_source_home=auth_source_home,
                         stdin_text=stdin_text)
    run = Path(run_root).resolve() / run_id
    if agent_config is not None:
        write_agent_config_snapshot(run, agent_config)
    if environment_config is not None:
        write_environment_config_snapshot(run, environment_config)
    write_environment_record(run, result, runtime_context=runtime_context)
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
    if (run / "control/environment_config.yaml").is_file():
        references["environment_config"] = "control/environment_config.yaml"
    if (run / "control/agent_prompt.md").is_file():
        references["prompt"] = "control/agent_prompt.md"
    provenance = {
        "schema_version": 1,
        "agent": {"name": agent.name, "version": agent.version},
        "command": {"argv": list(agent.command), "kind": "agent"},
        "references": references,
        "tools": tools_snapshot(),
    }
    (record_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["agent"] = {"name": agent.name, "version": agent.version,
                        "provenance": "record/provenance.json"}
    run_result = json.loads((record_dir / "run_result.json").read_text(encoding="utf-8"))
    run_result["agent"] = result["agent"]
    run_result["command"] = {"provenance": "record/provenance.json"}
    tmp = record_dir / f".run_result.json.{os.getpid()}.tmp"  # atomic, as the monitor writes it
    tmp.write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, record_dir / "run_result.json")
    return {"run": run_result}
