# Unified input configuration

## Implemented

- Added task-local `input.json` with each input's absolute source path and relative `link_path`.
- The runner creates only explicitly configured links under `work/input/`.
- The input configuration now combines data description and runtime mapping without a second config file.
- Added Ridgecrest mappings for `waveforms` and `stationxml`.

## Validation

- Validated relative, non-traversing link paths.
- Ran the focused input, prompt, and manifest tests successfully.
