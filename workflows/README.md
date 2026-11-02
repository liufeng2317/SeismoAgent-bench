# Workflows

This directory contains executable project workflows that use the reusable
`SeismoAgentBench` package.

- `data_preparation/` contains repository-wide source preparation, parsing,
  extraction and catalog-audit entry points.
- `tasks/` contains full benchmark task packages and case-specific expert workflows.
- `workflow_tests/` contains lightweight end-to-end workflow test cases used to verify the runner.
- `development/` holds the tooling used to develop and test the checker and the
  knowledge between formal runs: `replay/` (offline replay of recorded runs, iteration
  tier A), `backend_tier_b/` (generator, description and tools view of the back-end
  task arms, tier B; the per-case arm files live in `tasks/<case>/backend/`) and
  `tools_case_validation/` (checks of the `seismotools/` interfaces and of the checker
  on case data, kept outside the tool library, which Agents read).

The package implementation remains under `SeismoAgentBench/`; framework tests
remain under the repository-level `tests/` directory. Scientific source data
and case-local scripts remain under `data/<case>/`.
