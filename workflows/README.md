# Workflows

This directory contains executable project workflows that use the reusable
`SeismoAgentBench` package.

- `data_preparation/` contains repository-wide source preparation, parsing,
  extraction and catalog-audit entry points.
- `tasks/` contains benchmark task packages and case-specific expert workflows.

The package implementation remains under `SeismoAgentBench/`; framework tests
remain under the repository-level `tests/` directory. Scientific source data
and case-local scripts remain under `data/<case>/`.
