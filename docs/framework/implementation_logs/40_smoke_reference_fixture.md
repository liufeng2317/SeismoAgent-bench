# Stage 40: Smoke reference fixture separation

- **Goal:** keep test-only reference data out of the case task package.
- **Implemented:** moved the two-event Ridgecrest smoke reference to `tests/fixtures/ridgecrest_smoke_reference/`; the task package now contains only task inputs and task code.
- **Portability:** reference manifests may use a path relative to their own directory; the resolver converts it to an absolute path when loading.
- **Validation:** Ridgecrest package and reference tests passed; the full suite passed with 107 tests.
