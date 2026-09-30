# Stage 85: Per-run Codex authentication copy

## Objective

Use the same per-run `auth.json` handling as the reference Agent runner while
keeping credentials outside the run and source data directories.

## Implemented

- Validate the external Codex auth directory and `auth.json` as private,
  non-symlink paths.
- Copy `auth.json` into a temporary per-run `CODEX_HOME` with directory mode
  `700` and file mode `600`.
- Remove the temporary home with the existing runtime cleanup after the child
  process exits or times out.
- Keep only authentication mode and source-configured flags in run results.
- Added lifecycle tests for child visibility, source preservation and cleanup.

## Validation

- Focused authentication, runner, configuration and Codex tests passed: 25 tests.
- Full test suite is required before commit.

## Boundary

The source login directory must already exist and contain a valid `auth.json`;
the framework does not perform interactive login or refresh credentials.

## Commit

The implementation and this record are committed together after the full test
suite passes.
