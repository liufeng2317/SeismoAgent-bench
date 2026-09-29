# Runtime prompt simplification

## Implemented

- Removed internal task, manifest and working-directory variables from the
  user-facing runtime section of the rendered prompt.
- Kept only `$BENCH_OUTPUT` as the Agent-facing output boundary.
- Left framework environment variables available to the process environment;
  they are runtime interfaces, not task instructions.

## Validation

The rendered prompt now ends with an output-location section and the full test
suite passes: 81 tests.
