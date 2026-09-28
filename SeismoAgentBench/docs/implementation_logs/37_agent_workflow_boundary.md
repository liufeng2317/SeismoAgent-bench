# Stage 37: Agent workflow boundary cleanup

## Objective

Keep `agent/` limited to Agent identity and command contracts, moving run
orchestration into `workflow/`.

## Implemented

- Moved the implementation of `run_agent()` to `workflow/run_agent.py`.
- Updated CLI and experiment execution to import the workflow entrypoint.
- Kept `agent.contract.run_agent` as a thin compatibility shim for existing
  callers.
- `AgentSpec` remains in `agent/contract.py`; it no longer imports execution
  or reporting modules at import time.

## Validation

- Focused Agent, CLI, workflow and execution tests passed.
- Full test suite: 106 tests passed.
