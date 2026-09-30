# Stage 84: Framework configuration location

## Objective

Keep built-in Agent runtime profiles with the framework package while leaving
machine-specific credentials and overrides outside the package.

## Implemented

- Moved the Codex profile to `SeismoAgentBench/configs/agents/codex.yaml`.
- Removed the duplicate root-level `configs/agents` directory.
- Updated the runtime profile implementation record.

## Validation

- Focused configuration and Codex tests passed: 16 tests.
- Confirmed the new profile exists and the old path does not.
- Full test suite is required before commit.

## Boundary

This is a path and ownership change only; profile fields and runtime behavior
are unchanged.

## Commit

The migration and this record are committed together after the full test suite
passes.
