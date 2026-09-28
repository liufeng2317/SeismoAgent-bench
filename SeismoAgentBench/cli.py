"""Thin command-line entrypoint for external benchmark workers."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from SeismoAgentBench.agent import AgentError, AgentSpec, run_agent
from SeismoAgentBench.execution import ExecutionError


_RUN_FAILURES = {"execution_failed", "execution_timeout", "artifact_invalid", "scoring_failed"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m SeismoAgentBench")
    commands = parser.add_subparsers(dest="action", required=True)
    run = commands.add_parser("run-agent", help="run one agent through the standard workflow")
    run.add_argument("--task", required=True, help="task specification JSON")
    run.add_argument("--manifest", required=True, help="input manifest JSON")
    run.add_argument("--agent-name", required=True)
    run.add_argument("--agent-version", required=True)
    run.add_argument("--run-root", required=True)
    run.add_argument("--run-id", required=True)
    run.add_argument("--timeout", type=float, default=600)
    run.add_argument("command", nargs=argparse.REMAINDER,
                     help="agent command; place it after `--`")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    try:
        agent = AgentSpec.from_command(args.agent_name, args.agent_version, command)
        result = run_agent(args.task, args.manifest, agent, args.run_root, args.run_id,
                           timeout=args.timeout)
    except (AgentError, ExecutionError, OSError, ValueError) as exc:
        print(json.dumps({"state": "cli_error", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["run"]["state"] == "scored" else 3


if __name__ == "__main__":
    raise SystemExit(main())
