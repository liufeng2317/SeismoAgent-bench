# Stage 33: Experiment specification planning

## Objective

Represent a batch experiment independently from a single Agent run and expand
it into a deterministic list of run units.

## Implemented

- Added YAML loading and validation for `experiment_spec.yaml`.
- Required fields are `experiment_id`, `output_root`, `concurrency`, `agents`
  and `tasks`.
- Each Agent declares an `id` and an `agent_config` path.
- Each task declares a path and optional variants.
- Added `expand_experiment()` for stable Agent × task × variant expansion.
- Added the read-only planning command:

  ```bash
  python -m SeismoAgentBench plan-experiment --spec experiment.yaml
  ```

The command prints units but does not create runs or start Agents.

## Validation

- Duplicate Agent IDs and malformed specifications are rejected.
- Planning CLI output is deterministic and does not execute a task.
- Full test suite: 105 tests passed.

## Next boundary

The next stage may add a bounded executor for these planned units. Planning and
execution remain separate so that a plan can be reviewed before any Agent is
started.
