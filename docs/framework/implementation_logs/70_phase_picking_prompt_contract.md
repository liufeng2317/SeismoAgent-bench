# Phase-picking prompt contract

## Implemented

- Rewrote the task prompt into objective, input scope, procedure and output
  sections.
- Kept the phase-picking method open to the Agent while requiring parameters,
  assumptions and quality checks to be recorded.
- Required the saved processing script to be executed for the final outputs.
- Declared the CSV interchange fields `station`, `phase` and
  `arrival_time_utc` in the output contract so the task prompt and scorer use
  the same schema.
- Updated the deterministic task baseline to emit the canonical fields.

## Validation

Task, artifact and workflow tests passed: 25 tests in the targeted run.
