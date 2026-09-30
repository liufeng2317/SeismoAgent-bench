# Workflows

This directory contains executable project workflows that use the reusable
`SeismoAgentBench` package.

- `data_preparation/` contains repository-wide source preparation, parsing,
  extraction and catalog-audit entry points.
- `tasks/` contains full benchmark task packages and case-specific expert workflows.
- `workflow_tests/` contains lightweight end-to-end workflow test cases used to verify the runner.

The package implementation remains under `SeismoAgentBench/`; framework tests
remain under the repository-level `tests/` directory. Scientific source data
and case-local scripts remain under `data/<case>/`.
