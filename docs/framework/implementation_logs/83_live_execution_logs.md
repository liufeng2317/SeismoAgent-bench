# Stage 83: Live execution logs

## Objective

Make human-readable and structured execution records available while an Agent
process is still running.

## Implemented

- The runner now streams process output line by line to both
  `record/execution.log` and `record/execution.jsonl`.
- The human log receives UTC timestamps as each line arrives.
- The JSONL log remains strict JSON Lines for machine consumers.
- Timeout, nonzero exit and empty-output paths continue to be recorded.
- The temporary raw output file is no longer needed.

## Validation

- Added a test that observes both logs before the child process exits.
- Focused runner and transcript tests passed: 14 tests.
- Full test suite is required before commit.

## Boundary

This change affects new runs only. It does not rewrite logs from an already
running or completed run.

## Commit

The implementation and this record are committed together after the full test
suite passes.
