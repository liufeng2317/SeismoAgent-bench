# Configured input links

## Implemented

- Added optional `link_path` to each input-manifest entry.
- The runner creates only explicitly configured links under `work/input/`.
- Prompt rendering now shows the configured link path and no longer assumes that an entry ID is the runtime name.
- Added Ridgecrest mappings for `waveforms` and `stationxml`.

## Validation

- Validated relative, non-traversing link paths.
- Ran the focused input, prompt, and manifest tests successfully.
