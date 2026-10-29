# Core test suite cleanup

## Implemented

- Removed case-specific Ridgecrest and PhasePicking tests from the framework
  regression suite.
- Removed batch experiment planning/execution tests while the supported path is
  the single-run evaluation workflow.
- Removed detailed source-download and scientific-reference regression tests
  from the default suite; those behaviors remain available in the source and
  scoring packages for later focused testing.
- Kept tests for Agent contracts, host-direct execution, run records, task
  metadata, artifact contracts, basic catalog/pick validation, scorer registry,
  source metadata registry, CLI execution, and the single-run workflow.

## Validation

The retained suite contains 20 test files and runs with:

```bash
python -B -m unittest discover -s tests -p 'test_*.py'
```

Validation result: 78 tests passed.
