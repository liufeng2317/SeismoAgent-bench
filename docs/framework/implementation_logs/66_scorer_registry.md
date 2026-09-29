# Implementation 66: Scorer registry

## Implemented

- Added an explicit registry for versioned scorer identities.
- Registered artifact-contract, catalog-basic and phase-picking-basic scorers.
- Evaluation now validates the task's declared scorer list and writes
  `evaluation/scorer_plan.json` before running score calculations.
- Existing scorer functions and scientific metrics remain unchanged.

## Verification

- Registry and workflow tests pass.
- Unknown scorer names fail before a score is produced.
