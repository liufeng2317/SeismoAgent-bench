# Phase-picking task

## Status

Complete.

## Implemented

- Added a Ridgecrest task dedicated to waveform preprocessing and phase-pick output.
- Defined required `preprocessing.json` and `picks.json` artifacts without mixing event location or magnitude estimation into this task.
- Added an ObsPy STA/LTA baseline that reads the manifest's MiniSEED and emits reproducible P-trigger records.
- Added a focused CLI test for the new task.

The baseline is a task and data-flow control. It is not a PhaseNet-quality picker and no scientific pick-quality score is claimed yet.

## Validation

- Focused phase-picking tests: 2 passed.
- Independent CLI run: `scored`; 3 traces processed and 30 pick records written.
- Full test suite: 87 passed.

## Git

The implementation commit is recorded immediately before this document commit.
