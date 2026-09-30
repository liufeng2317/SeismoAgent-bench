# Stage 82: External authentication profiles

## Objective

Allow a runtime profile to select an external authentication source without
copying credentials into the run directory or recording secret values.

## Implemented

- Added authentication modes `external_profile`, `env_file` and `codex_home`.
- A profile may point to an env file or Codex home; command-line options remain
  explicit overrides.
- The runner loads the selected source only into the child process environment.
- Run output records only the mode and whether a source was configured.
- Added validation and resolution tests without using real credentials.

## Validation

- Focused authentication, configuration and Codex tests passed: 18 tests.

## Boundary

The framework does not perform interactive login, refresh tokens, or copy
authentication files. A future adapter may implement provider-specific login
preparation behind this same external-source boundary.

## Commit

The implementation and this record are committed together after the full test
suite passes.
