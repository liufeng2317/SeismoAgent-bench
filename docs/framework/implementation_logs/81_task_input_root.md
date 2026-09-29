# Task input root

## Implemented

- Simplified the phase-picking task input configuration to one read-only
  waveform data root.
- The Agent discovers waveform and station metadata files recursively below
  that root instead of receiving separate input entries for each file.
- Updated the task prompt and deterministic baseline to use the run-local
  input view.

## Validation

- Framework test suite: 76 tests passed.
- Task baseline compiles successfully.
