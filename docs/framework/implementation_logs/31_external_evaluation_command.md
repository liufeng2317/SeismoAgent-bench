# Stage 31: External evaluation command

## Objective

Separate Agent execution from output validation and scoring. An Agent run must
finish before an evaluator reads its artifacts.

## Implemented

- `run-agent` and `run-codex` now execute the Agent and return a completed run;
  they do not score the output.
- Added `evaluate --run-dir <path>` to evaluate an existing run.
- Added optional `--reference-manifest` to `evaluate` for scientific scoring.
- Added `evaluate_run()` as the evaluator API.
- Kept the Python `run_task()` wrapper temporarily for compatibility with older
  internal callers; new CLI workflows use separate execution and evaluation.
- Evaluation writes `record/artifact_manifest.json` and files under
  `evaluation/`.

## Example

```bash
python -m SeismoAgentBench run-agent ... --run-id run_001 -- agent-command
python -m SeismoAgentBench evaluate \
  --run-dir /path/to/runs/task_id/run_001
```

## Validation

- Phase-picking and Ridgecrest catalog smoke tests run and evaluate in two
  separate subprocess calls.
- Full test suite: 99 tests passed.
