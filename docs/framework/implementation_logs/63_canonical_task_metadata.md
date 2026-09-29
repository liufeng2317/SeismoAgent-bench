# Implementation 63: Canonical task metadata

## Git

`e56023b` — `standardize task metadata contract`

## Implemented

- Added canonical task metadata for category, software, taxonomy, input requirements and evaluation scorers.
- Made `task_prompt.md`, external `output_contract.json`, `input_requirements` and `evaluation.scorers` the required task-definition fields.
- Removed support for inline prompts, `input_types`, inline output artifacts and the singular `scorer` field in task sources.
- Updated the Ridgecrest task packages and test fixtures.

## Verification

- Full test suite: 119 tests passed.
- Existing task packages and manifests load and validate successfully.
- Large input data and reference products were not added to the commit.
