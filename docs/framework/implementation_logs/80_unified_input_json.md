# Unified input JSON

## Implemented

- Replaced the Ridgecrest task's separate manifest and runtime link config with one `input.json`.
- Each entry contains only `id`, absolute source `path`, `type` (`file` or `folder`), and optional `notes`.
- The entry ID is used directly as the run-local link name.
- The runner creates configured links under `work/input/` without copying source data.
- The input validator now restricts entries to the four task-level fields.

## Validation

- Updated the task launch script and task documentation.
- Ran all 76 framework tests successfully.
