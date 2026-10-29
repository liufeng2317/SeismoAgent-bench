# Stage 87: Workflow directory organization

## Objective

Group executable project workflows under one top-level directory while keeping
reusable package code and framework tests separate.

## Changes

- Moved repository-wide source preparation entry points from `scripts/` to
  `workflows/data_preparation/`.
- Moved benchmark task packages and case-specific expert workflows from
  `tasks/` to `workflows/tasks/`.
- Added `workflows/README.md` defining the boundary between workflows,
  `SeismoAgentBench/`, `tests/`, and `data/`.
- Updated active code, documentation, registries and run commands to the new
  paths. Fixed project-root resolution for moved data-preparation scripts and
  the phase-picking runner.
- Kept case-local scripts under `data/<case>/scripts/`; they are scientific
  source utilities, not repository-wide workflow entry points.

## Validation

- `python -B -m unittest discover -s tests -v` — 89 tests passed.
- All Python files under `workflows/data_preparation/` parsed successfully.
- `git diff --check` passed.
- Untracked local data and `docs/reference/` were not staged.
