# Agent entrypoint contract

## Status

Complete.

## Commit

| Git ID | Implemented content | Validation |
| --- | --- | --- |
| `e0f494d` | Added `AgentSpec` and `run_agent`, recording agent name, version and command in `agent_command.json` while reusing the standard task workflow. | 2 agent tests and 54 full-suite tests passed. |

## Result

Agents now have one minimal launch contract. The contract records identity and invocation details but does not prescribe an agent framework, model, scientific tool or isolation backend.
