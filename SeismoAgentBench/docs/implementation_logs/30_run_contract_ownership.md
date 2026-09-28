# Stage 30: Run contract ownership layout

## Objective

Separate task and runtime control records from the Agent-owned workspace and
from evaluation outputs.

## Implemented

Each new run now uses:

```text
<task_id>/<run_id>/
  control/      task_spec.json, input_manifest.json
  agent/        work/, output/, home/, tmp/, execution.log
  record/       run_result.json, environment.json, artifact_manifest.json
  evaluation/   compatibility score and report files
```

The Agent receives `BENCH_TASK_SPEC` and `BENCH_INPUT_MANIFEST` pointing into
`control/`, and writes through `BENCH_WORK` and `BENCH_OUTPUT` under `agent/`.
Run records are written by the runner under `record/`.

The existing workflow still performs compatibility artifact scoring so current
smoke tasks remain executable. Moving that scorer to a separate external
`evaluate` command is the next bounded stage. The previously generated
Ridgecrest runs were migrated to the same ownership layout.

## Validation

- Control files and Agent workspace are created in separate directories.
- Retry archives preserve the separated layout.
- Ridgecrest phase-picking and catalog task tests pass.
- Full test suite: 99 tests passed.
