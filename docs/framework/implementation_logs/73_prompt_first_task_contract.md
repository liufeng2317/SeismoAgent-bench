# Prompt-first task contract

## Implemented

- Made `input_requirements`, `evaluation` and `output_contract` optional task
  metadata.
- Made the CLI manifest argument optional and allowed prompt-only tasks to run.
- Generated input and output tables only when the corresponding structured
  metadata is supplied.
- Exposed optional `BENCH_INPUT_MANIFEST` and `BENCH_OUTPUT_CONTRACT` paths
  only for supplied snapshots.
- Kept existing structured tasks and scorer integrations working unchanged.
- Removed `output_contract.json` and automatic framework evaluation from the
  phase-picking task; its output requirements now live in `task_prompt.md`.

## Validation

A prompt-only task was executed without a manifest or output contract. The full
test suite passed: 81 tests.
