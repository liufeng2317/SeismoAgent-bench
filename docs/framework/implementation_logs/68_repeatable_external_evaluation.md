# Repeatable external evaluation

## Commit

Implementation commit: `194631a` (`allow repeatable external evaluation`).

## Implemented

- Allow `evaluate_run()` to re-evaluate runs whose previous state is `scored`,
  `artifact_invalid`, or `scoring_failed`.
- Reset only the evaluation state in memory before validation and scorer
  dispatch; preserve the previous state in `run_result.json` as
  `previous_evaluation_state`.
- Keep execution failures, timeouts, and in-progress states non-evaluable.
- Reuse the existing `work/` directory and never start the Agent during a
  repeat evaluation.

## Validation

The workflow and CLI tests cover a completed run followed by a second direct
evaluation. The full test suite is run before the commit.
