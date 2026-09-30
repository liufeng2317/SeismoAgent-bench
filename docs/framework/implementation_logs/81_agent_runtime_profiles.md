# Stage 81: Agent runtime profiles and executable versions

## Objective

Provide one non-secret runtime profile format that can select a harness
executable and model, and record the installed executable version for a run.

## Implemented

- Extended `agent_config.yaml` validation with `executable`, `version_command`
  and non-secret `auth` metadata.
- Added a Codex profile at `configs/agents/codex.yaml`.
- `run-codex` can take its executable, model and reasoning effort from the
  profile; command-line values remain explicit overrides.
- The Codex launcher records a non-invasive version probe in
  `record/provenance.json` and the CLI result.
- Credentials remain external (`CODEX_HOME` or an env file); no credential
  value is loaded into a snapshot or provenance record.

## Validation

- Focused execution and Codex CLI tests passed: 14 tests.
- The version probe reports unavailable executables without aborting a run.

## Boundary

This stage defines the configuration and provenance boundary only. It does not
copy login files, implement authentication, or add a Claude adapter.

## Commit

The implementation and this record are committed together after the full test
suite passes.
