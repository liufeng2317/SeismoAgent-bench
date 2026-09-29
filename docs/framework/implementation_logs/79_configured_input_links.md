# Configured input links

## Implemented

- Added task-local `run_config.yaml` with an explicit `input_links` mapping.
- The runner creates only explicitly configured links under `work/input/`.
- The input manifest remains a data description and does not contain runtime link names.
- Added Ridgecrest mappings for `waveforms` and `stationxml`.

## Validation

- Validated relative, non-traversing link paths.
- Ran the focused input, prompt, and manifest tests successfully.
