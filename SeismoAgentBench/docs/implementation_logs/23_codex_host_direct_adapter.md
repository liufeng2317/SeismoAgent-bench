# Codex host-direct adapter

## Status

Complete with an external capacity follow-up.

## Implemented

- Added `run-codex` to the command-line entrypoint.
- Connected Codex command construction to the existing `run_agent` and task scoring workflow.
- Added external env-file injection for authentication and proxy variables without recording their values.
- Captured `codex_command.json` and `transcript.jsonl` for each run.
- Added a fake-Codex integration test covering output scoring and transcript capture.

## Validation

- Focused adapter and execution tests passed.
- Full test suite: 91 passed.
- Real Ridgecrest host-direct run reached the model, read three waveforms and wrote three picks. The model then returned `Selected model is at capacity` during the final turn; the run was correctly recorded as `execution_failed` and was not scored.

## Decision

The adapter and evidence capture are complete. Capacity retry and a retryable failure state are a separate follow-up; no score is inferred from the partial output.

## Git

The implementation commit is recorded immediately before this document commit.
