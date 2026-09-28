# Retryable provider failures

## Status

Complete.

## Implemented

- Added log-based classification for provider capacity and usage-limit failures.
- Capacity failures now use `execution_retryable` with `failure_reason: capacity`.
- Usage-limit failures remain `execution_failed` with `failure_reason: usage_limit` and are not retryable.
- Generic nonzero exits and timeouts retain their existing semantics.
- Partial output is never scored when the agent process exits unsuccessfully.

## Validation

- Focused execution and Codex adapter tests: 9 passed.
- Full test suite: 96 passed.

## Decision

Automatic resume/backoff is a separate step. This stage only makes the failure decision explicit and preserves the evidence needed for a later retry.

## Git

The implementation commit is recorded immediately before this document commit.
