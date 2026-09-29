# Unified input JSON

## Implemented

- Replaced the Ridgecrest task's separate manifest and runtime link config with one `input.json`.
- Each entry retains the absolute source `path` and declares its run-local `link_path`.
- The runner creates configured links under `work/input/` without copying source data.
- The input manifest validator now checks relative, non-traversing link paths.

## Validation

- Updated the task launch script and task documentation.
- Ran all 82 framework tests successfully.
