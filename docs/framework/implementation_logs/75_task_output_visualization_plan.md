# Task output visualization plan

## Implemented

- Simplified the phase-picking task procedure to a plan, reusable script and
  result sequence.
- Replaced the JSON task plan requirement with the human-readable
  `task_plan.md` required by this task.
- Defined three task-specific figures: station/raw waveform,
  preprocessing stages and phase-pick results.
- Defined `picks.csv` as the phase-pick output and removed the unnecessary
  `pick_examples.json` requirement.
- Updated the deterministic baseline to emit the same task-specific files.

## Validation

The baseline compiles and the framework test suite passes: 81 tests.
