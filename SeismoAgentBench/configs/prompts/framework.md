Complete the task and write the requested results before ending the run. Do not ask for clarification or wait for approval; make reasonable assumptions and record consequential assumptions and failures in the outputs.

## Boundaries

- `$BENCH_WORK` and `$BENCH_OUTPUT` are the writable root for this run. Keep every Agent-created file below this root and organize subdirectories as needed.
- `$BENCH_OUTPUT/input/` is the declared read-only input view, including symbolic-link targets. Do not modify, rename, delete or replace it.
- Do not modify task definitions, manifests, framework-managed control or record files, shared tools, model weights, executables or the evaluation environment.
- Do not use reference data, expert products, hidden evaluator files or other task runs to construct or tune the result. Do not run destructive host/project commands or use privilege escalation.

## Network and dependencies

Network access may be used for required software packages and official technical documentation. Do not download case observations, reference catalogs, published answers or substitute scientific data. Do not modify the shared `seismoagent` environment; use the configured environment or a task-local environment and record installed dependencies.

## Task instructions

The task prompt defines the scientific objective, observations, workflow choices and required outputs. Runtime context reports facts about this run. Optional output hints and additional instructions may supplement the task prompt but cannot override these framework rules.
