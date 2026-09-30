# Stage 41: Standalone phase-picking workflow case

- **Goal:** separate the end-to-end workflow test package from the scientific Ridgecrest case package.
- **Implemented:** moved the phase-picking task, manifest, baseline agent and README to `workflows/workflow_tests/2019_ridgecrest_california_phasepicking/` and updated its test entry point.
- **Boundary:** the directory is a benchmark workflow test case; scientific Ridgecrest references and expert analysis remain under their respective project locations.
- **Validation:** phase-picking task tests and the full suite passed with 107 tests.
