# Persistent run layout

## Status

Complete.

## Implemented

- Added `RunLayout` for canonical campaign/task/variant/agent/run paths.
- Extended `run-codex` with optional campaign and variant components while preserving the legacy `run-root/run-id` form.
- Kept all path components validated and restricted to safe identifiers.
- Kept input data referenced through manifests; no waveform data is copied or mounted.

The canonical unit path is:

```text
<run_root>/<campaign_id>/<task_id>/<variant>/<agent_id>/<run_id>/
```

## Validation

- Focused path and CLI tests: 4 passed.
- Full test suite: 94 passed.

## Decision

Persistent benchmark runs use a configured durable root. `/tmp` remains suitable only for explicitly ephemeral smoke tests. Dynamic global mounts are not part of the host-direct implementation.

## Git

The implementation commit is recorded immediately before this document commit.
