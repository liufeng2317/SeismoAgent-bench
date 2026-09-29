# Run-local input view

## Implemented

- Created `work/input/` for every run.
- Linked each existing declared manifest entry into that directory using its manifest ID.
- Added `BENCH_INPUT` and documented the relative `input/` view in rendered prompts.
- Kept source data outside the run and avoided copying large files.

## Validation

- Verified directory and file input links with a synthetic runner test.
- Verified prompt-only runs still work without a manifest.
