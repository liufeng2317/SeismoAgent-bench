# Bounded capacity resume

## Status

Complete.

## Implemented

- Added resume support for `execution_retryable` runs.
- Archived each previous attempt under `attempts/attempt-XXX/` before retrying.
- Added `--max-attempts` and `--retry-delay-s` to `run-codex`.
- Preserved one logical run identity while retaining per-attempt logs, transcripts and partial outputs.
- Refused to resume completed, usage-limit, ordinary-failure or timeout runs.

## Validation

- Focused runner and Codex CLI tests: 11 passed.
- Full test suite: 98 passed.
- Fake Codex test: first capacity failure was archived and the bounded second attempt was scored successfully.

## Decision

The retry policy is finite and explicit. Real model reruns should only be started with a selected maximum attempt count and delay; no unbounded background retry loop is enabled.

## Git

The implementation commit is recorded immediately before this document commit.
