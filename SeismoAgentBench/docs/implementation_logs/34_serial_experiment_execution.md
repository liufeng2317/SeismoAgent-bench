# Stage 34: Serial experiment execution

## Objective

Execute an approved experiment plan in a deterministic serial order without
mixing execution with evaluation.

## Implemented

- Experiment agents now declare `id`, `name`, `version`, `config` and
  `command`.
- Experiment tasks now declare `id`, `task_spec`, `input_manifest` and
  `variants`.
- Added `execute_experiment()` to expand and execute units in declaration
  order.
- Added the CLI command:

  ```bash
  python -m SeismoAgentBench execute-experiment --spec experiment.yaml
  ```

- Added `--limit N` for a bounded smoke run.
- Each unit receives a stable run id and records its expanded unit under
  `record/experiment_unit.json`.
- Execution does not call the evaluator or create score files.

## Validation

- One-unit Ridgecrest-style execution test passed without evaluation output.
- Full test suite: 106 tests passed.

Parallel scheduling and automatic batch evaluation remain separate future
stages.
