# Explicit task input paths

## Implemented

- Added the Ridgecrest waveform directory and StationXML file as absolute
  paths in the task prompt.
- Kept `BENCH_INPUT_MANIFEST` as an optional detailed metadata source rather
  than the primary description of the input data.
- Kept `BENCH_OUTPUT` for the dynamic per-run output boundary; output paths
  must remain run-specific.

## Validation

The task prompt remains valid and the existing framework test suite continues
to pass.
