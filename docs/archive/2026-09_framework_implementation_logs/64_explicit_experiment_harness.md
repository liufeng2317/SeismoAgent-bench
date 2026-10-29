# Implementation 64: Explicit experiment harness

## Implemented

- Experiment Agent entries now declare `harness` explicitly.
- The experiment plan carries the harness into every expanded run unit.
- Execution rejects a run when the experiment harness and `agent_config.yaml`
  harness disagree.
- Existing command-based and Python test runners remain unchanged; this stage
  only establishes the runner boundary.

## Verification

- Execution, CLI planning and workflow experiment tests passed.
- Full test suite: 119 tests passed.
