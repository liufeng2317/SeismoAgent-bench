# Stage 36: Framework tree cleanup

## Objective

Remove generated or unreferenced files from the framework package without
changing runtime interfaces.

## Implemented

- Removed Python `__pycache__` directories from the source tree.
- Removed the unused example Ridgecrest input manifest from
  `task/examples/`; the maintained task manifest remains under the task
  package.
- Kept `utils/source_prepare/` because case scripts and source-registry tests
  still import it. It remains a data-preparation utility rather than an Agent
  runtime dependency.

## Validation

- Full test suite: 106 tests passed.
