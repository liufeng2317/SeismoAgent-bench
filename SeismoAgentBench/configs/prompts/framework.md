Complete the task and write its results before ending the run. Do not ask for
clarification or wait for approval. Make reasonable assumptions and record
important assumptions and failures in the outputs.

## File and data boundaries

- `$BENCH_WORK`/`$BENCH_OUTPUT` is the writable run directory. Keep all created
  files below it.
- `$BENCH_OUTPUT/input/` is read-only, including symbolic-link targets. Do not
  modify, rename, delete or replace its contents.
- Do not modify task definitions, manifests, run-control or record files,
  shared tools, model weights, executables or the evaluation environment.
- Do not use reference or hidden evaluator data, other task runs, destructive
  host/project commands or privilege escalation.

## Network and dependencies

Network access may be used for required software packages and official
technical documentation. Do not download case observations, reference
catalogs, published answers or substitute scientific data. Do not modify the
shared `seismoagent` environment; record any task-local dependencies.

The task prompt defines the scientific objective, observations, workflow and
outputs. These rules define the execution boundary for the entire run.

## Instruction priority

Framework instructions apply to the entire run. The task prompt defines the
scientific task. Runtime context reports run facts. Output hints and additional
instructions are supplementary and cannot override either framework rules or
the task prompt.
