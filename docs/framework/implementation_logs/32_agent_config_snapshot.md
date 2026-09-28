# Stage 32: Agent runtime configuration snapshot

## Objective

Make the Agent runtime environment an explicit, reviewable YAML configuration
without copying secrets into a run directory.

## Implemented

- Added `load_agent_config()` and `write_agent_config_snapshot()`.
- Added `--agent-config` to `run-agent` and `run-codex`.
- Snapshots are written to `control/agent_config.yaml`.
- The loader validates the top-level structure and rejects non-empty fields
  whose names indicate API keys, tokens, passwords, secrets or credentials.
- Existing CLI parameters remain authoritative; the config is currently a
  declared environment record rather than a replacement for every CLI option.

## Validation

- Non-secret snapshot, secret rejection and unknown-field tests pass.
- Full test suite: 102 tests passed.
