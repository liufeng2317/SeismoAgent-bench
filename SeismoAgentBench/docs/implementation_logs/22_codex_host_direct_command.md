# Codex host-direct command layer

## Status

Complete.

## Implemented

- Added `CodexCommandSpec` for deterministic construction of non-interactive `codex exec --json` argv.
- Explicitly records model, working directory, reasoning effort and host-direct mode.
- Keeps credentials and proxy configuration outside the command record.
- Added validation for absolute run directories and supported reasoning-effort values.

This stage does not authenticate, call the model or claim sandbox isolation. It only fixes the command interface before the live adapter is added.

## Validation

- Focused Codex command tests: 3 passed.
- Existing execution runner tests: 5 passed.
- Full test suite: 90 passed.

## Git

The implementation commit is recorded immediately before this document commit.
