"""Thin command-line entrypoint for external benchmark workers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Sequence

from SeismoAgentBench.agent import AgentError, AgentSpec
from SeismoAgentBench.execution import (CodexCommandError, CodexCommandSpec, ExecutionError,
                                        AgentConfigError, RunLayout, expand_experiment,
                                        load_agent_config, load_env_file, load_experiment_spec,
                                        probe_executable_version, resolve_auth)
from SeismoAgentBench.task import load_json, render_agent_prompt
from SeismoAgentBench.workflow import evaluate_run, execute_experiment, run_agent


_RUN_FAILURES = {"execution_failed", "execution_timeout", "artifact_invalid", "scoring_failed"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m SeismoAgentBench")
    commands = parser.add_subparsers(dest="action", required=True)
    run = commands.add_parser("run-agent", help="run one agent through the standard workflow")
    run.add_argument("--task", required=True, help="task specification JSON")
    run.add_argument("--input", "--manifest", dest="manifest", help="optional input JSON")
    run.add_argument("--agent-name", required=True)
    run.add_argument("--agent-version", required=True)
    run.add_argument("--run-root", required=True)
    run.add_argument("--run-id", required=True)
    run.add_argument("--agent-config", help="YAML Agent runtime configuration snapshot")
    run.add_argument("--timeout", type=float, default=600)
    run.add_argument("--reference-manifest", help="optional authorized reference manifest")
    run.add_argument("command", nargs=argparse.REMAINDER,
                     help="agent command; place it after `--`")
    evaluate = commands.add_parser("evaluate", help="evaluate a completed Agent run")
    evaluate.add_argument("--run-dir", required=True, help="completed run directory")
    evaluate.add_argument("--reference-manifest", help="optional authorized reference manifest")
    evaluate.add_argument("--pick-reference", help="optional reference picks CSV")
    evaluate.add_argument("--pick-time-tolerance-s", type=float, default=0.5)
    plan = commands.add_parser("plan-experiment", help="validate and expand an experiment spec")
    plan.add_argument("--spec", required=True, help="experiment YAML specification")
    execute = commands.add_parser("execute-experiment", help="execute an experiment plan serially")
    execute.add_argument("--spec", required=True, help="experiment YAML specification")
    execute.add_argument("--limit", type=int, help="execute only the first N planned units")
    codex = commands.add_parser("run-codex", help="run one Codex CLI agent in host-direct mode")
    codex.add_argument("--task", required=True)
    codex.add_argument("--input", "--manifest", dest="manifest", help="optional input JSON")
    codex.add_argument("--agent-name", required=True)
    codex.add_argument("--agent-version", required=True)
    codex.add_argument("--run-root", required=True)
    codex.add_argument("--run-id", required=True)
    codex.add_argument("--agent-config", help="YAML Agent runtime configuration snapshot")
    codex.add_argument("--campaign-id")
    codex.add_argument("--variant", default="base")
    codex.add_argument("--codex-bin", help="Codex executable; defaults to agent config")
    codex.add_argument("--model", help="optional model slug; omit to use Codex default routing")
    codex.add_argument("--prompt", help="optional additional instructions appended to the rendered task prompt")
    codex.add_argument("--reasoning-effort")
    codex.add_argument("--env-file", help="external KEY=VALUE file; values are never recorded")
    codex.add_argument("--codex-home", help="external CODEX_HOME path")
    codex.add_argument("--timeout", type=float, default=600)
    codex.add_argument("--reference-manifest")
    codex.add_argument("--resume", action="store_true")
    codex.add_argument("--max-attempts", type=int, default=1)
    codex.add_argument("--retry-delay-s", type=float, default=0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.action == "run-agent":
            command = list(args.command)
            if command and command[0] == "--":
                command = command[1:]
            agent = AgentSpec.from_command(args.agent_name, args.agent_version, command)
            agent_config = load_agent_config(args.agent_config) if args.agent_config else None
            result = run_agent(args.task, args.manifest, agent, args.run_root, args.run_id,
                               timeout=args.timeout, reference_manifest=args.reference_manifest,
                               agent_config=agent_config)
        elif args.action == "evaluate":
            result = evaluate_run(args.run_dir, reference_manifest=args.reference_manifest,
                                  pick_reference=args.pick_reference,
                                  pick_time_tolerance_s=args.pick_time_tolerance_s)
        elif args.action == "plan-experiment":
            spec = load_experiment_spec(args.spec)
            result = {"experiment": spec["experiment_id"],
                      "output_root": spec["output_root"],
                      "concurrency": spec["concurrency"],
                      "units": expand_experiment(spec)}
        elif args.action == "execute-experiment":
            runs = execute_experiment(args.spec, limit=args.limit)
            result = {"spec": str(Path(args.spec).resolve()), "runs": runs}
        else:
            if args.max_attempts < 1 or args.retry_delay_s < 0:
                raise CodexCommandError("max_attempts must be >= 1 and retry_delay_s must be >= 0")
            agent_config = load_agent_config(args.agent_config) if args.agent_config else None
            if agent_config is not None and agent_config.get("harness") != "codex":
                raise CodexCommandError("run-codex requires an Agent config with harness: codex")
            auth = resolve_auth(agent_config)
            configured_env_file = args.env_file or auth.get("env_file")
            configured_codex_home = args.codex_home or auth.get("codex_home")
            env = load_env_file(configured_env_file) if configured_env_file else {}
            configured = (agent_config or {}).get("config", {})
            codex_bin = args.codex_bin or (agent_config or {}).get("executable")
            if not isinstance(codex_bin, str) or not codex_bin:
                raise CodexCommandError("--codex-bin or agent config executable is required")
            model = args.model if args.model is not None else (agent_config or {}).get("model")
            reasoning_effort = args.reasoning_effort or configured.get("reasoning_effort", "medium")
            if not isinstance(reasoning_effort, str):
                raise CodexCommandError("reasoning_effort must be a string")
            effective_root = Path(args.run_root).resolve()
            if args.campaign_id:
                task_id = load_json(args.task)["task_id"]
                layout = RunLayout(effective_root, args.campaign_id, task_id,
                                   args.variant, args.agent_name, args.run_id)
                effective_root = layout.run_root
            rendered_prompt = render_agent_prompt(args.task, args.manifest,
                                                   extra_instructions=args.prompt)
            spec = CodexCommandSpec(codex_bin, model,
                                    str(effective_root / args.run_id / "work"),
                                    rendered_prompt, reasoning_effort=reasoning_effort)
            agent = AgentSpec.from_command(args.agent_name, args.agent_version, spec.argv())
            result = None
            for attempt in range(args.max_attempts):
                result = run_agent(
                    args.task, args.manifest, agent, effective_root, args.run_id,
                    timeout=args.timeout, reference_manifest=args.reference_manifest,
                    extra_env=env, resume=args.resume or attempt > 0,
                    agent_config=agent_config,
                    agent_prompt=rendered_prompt,
                    auth_source_home=configured_codex_home,
                )
                if result["run"]["state"] != "execution_retryable" or attempt + 1 >= args.max_attempts:
                    break
                if args.retry_delay_s:
                    time.sleep(args.retry_delay_s)
            assert result is not None
            run = effective_root / args.run_id
            record_dir = run / "record"
            record_dir.mkdir(exist_ok=True)
            provenance_path = record_dir / "provenance.json"
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            launcher = spec.record()
            version_command = (agent_config or {}).get("version_command", ["--version"])
            launcher["executable_version"] = probe_executable_version(codex_bin, version_command)
            argv = list(launcher["argv"])
            if argv and argv[-1] == rendered_prompt:
                argv[-1] = "<BENCH_AGENT_PROMPT>"
            launcher["argv"] = argv
            provenance["launcher"] = launcher
            provenance["command"] = {"kind": "codex", "reference": "launcher.argv"}
            provenance_path.write_text(
                json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            result["codex"] = {"provenance": "provenance.json",
                               "execution_log": "execution.log",
                               "execution_jsonl": "execution.jsonl",
                               "executable_version": launcher["executable_version"],
                               "injected_environment_keys": sorted(env)}
            if args.campaign_id:
                result["run_layout"] = layout.record()
            result["codex"]["authentication"] = {
                "mode": auth["mode"],
                "env_file_configured": bool(configured_env_file),
                "codex_home_configured": bool(configured_codex_home),
            }
    except (AgentError, AgentConfigError, CodexCommandError, ExecutionError, OSError, ValueError) as exc:
        print(json.dumps({"state": "cli_error", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.action in {"plan-experiment", "execute-experiment"}:
        return 0
    return 0 if result["run"]["state"] in {"completed", "scored"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
