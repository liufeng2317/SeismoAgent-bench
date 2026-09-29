# Implementation 65: Unit and batch result records

## Implemented

- Each experiment unit now writes `record/unit_result.json`.
- Each serial experiment writes a timestamped batch directory containing
  `summary.json` and `summary.md`.
- Batch summaries record Agent execution states and run locations only;
  evaluation remains an external operation.

## Verification

- Full test suite: 119 tests passed before this stage.
- Workflow tests verify both unit and batch records.
