# Implementation 67: Scorer handler dispatch

## Implemented

- Added a common `ScorerContext` passed to registered scorer handlers.
- Registered artifact-contract, catalog-basic and phase-picking-basic handlers.
- `evaluate_run` now executes declared handlers in order and writes their
  standard result files.
- Missing reference inputs produce an explicit `skipped` scorer-plan entry.
- Existing scientific metric implementations were not changed.

## Verification

- Full test suite: 121 tests passed before this stage.
- Workflow tests cover artifact, catalog and handler failure paths.
