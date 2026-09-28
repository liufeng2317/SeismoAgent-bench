# Deterministic baseline agent

## Status

Complete.

## Implemented

- Added a task-local deterministic Ridgecrest baseline command.
- The command writes a non-empty, contract-valid catalog with two fixed candidate events.
- The existing external CLI now runs this command through the normal workflow and produces artifact validation, reference matching, scientific scoring, task summary and evaluation report files.

This baseline is an infrastructure control. It is not a PhaseNet picker, a Gamma locator, a NonLinLoc run, or a scientific benchmark result.

## Validation

- Ridgecrest package tests: 5 passed.
- Full test suite: 84 passed.
- Independent CLI run: `scored`; 2 candidate events, 2 matched events, precision 1.0, recall 1.0, F1 1.0.

## Git

The implementation commit is recorded immediately before this document commit.
