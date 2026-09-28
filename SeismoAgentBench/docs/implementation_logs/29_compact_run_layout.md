# Stage 29: Compact run layout

## Objective

Reduce the persistent run directory to the minimum stable hierarchy while
preserving campaign, variant and agent identity in run metadata.

## Implemented

- Migrated the four existing Codex runs to:

  ```text
  <run-root>/<task_id>/<run_key>/
  ```

- Used `run_key = <run_id>__<campaign_id>` for the historical runs because
  each campaign had reused `run_001`.
- Updated `RunLayout` so new runs use `<task_id>/<run_id>` and record the
  remaining identity fields as metadata.
- Added a run-root `index.json` mapping historical paths and identities.

## Validation

- All four migrated `run_result.json` files remain readable.
- Existing outputs, scores and retry `attempts/` directories remain in place.
- Full test suite: 99 tests passed.

## Current layout

```text
runs/
  <task_id>/
    <run_id>/
      input_manifest.json
      output/
      score/
      run_result.json
```

`campaign_id`, `variant` and `agent_id` remain in the run command and layout
metadata; they are no longer additional directory levels.
