# Stage 35: Completion evaluation summary

## Objective

Provide a provisional, task-independent evaluation summary while scientific
location and catalog criteria are still being defined.

## Implemented

- Added `evaluate-runs --run-dir ...` for evaluating multiple completed runs.
- The summary reports total runs, scored runs, completion fraction and state
  counts.
- It reuses the existing artifact contract evaluator and does not introduce
  location, phase-pick accuracy or catalog quality metrics.

## Example

```bash
python -m SeismoAgentBench evaluate-runs \
  --run-dir runs/task/run_001 \
  --run-dir runs/task/run_002
```

## Validation

- Single-run execution followed by multi-run evaluation passes.
- Full test suite: 107 tests passed.
