# Waveform-driven baseline agent

## Status

Complete.

## Implemented

- Added a task-local agent that reads the manifest's MiniSEED and StationXML files with ObsPy.
- Ranked non-overlapping ten-second vertical-component amplitude windows.
- Converted the strongest windows into contract-valid candidate events and used StationXML coordinates for the station-based location proxy.
- Kept the existing CLI, catalog contract and scientific scorer unchanged.

This is a data-access and candidate-generation control. It is not a phase picker, an origin-time estimator, or a scientific earthquake locator.

## Validation

- Waveform-specific Ridgecrest test passed.
- Independent CLI run: `scored`; one candidate event was generated from the real waveform input.
- Full test suite: 85 passed.
- The candidate did not match the official reference under the current time and horizontal-distance policy, which is an expected diagnostic of this deliberately simple baseline.

## Git

The implementation commit is recorded immediately before this document commit.
