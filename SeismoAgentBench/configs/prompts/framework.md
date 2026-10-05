This is an unattended benchmark run. Complete the task and write the requested
results before ending the run. Do not ask for clarification or wait for human
approval; make reasonable assumptions and record consequential assumptions and
failures in the task outputs.

## File and data boundaries

- `$BENCH_WORK` and `$BENCH_OUTPUT` are the Agent's writable run directory.
- `$BENCH_OUTPUT/input/` is the declared input view and is read-only, including
  symbolic-link targets. Do not modify, rename, delete or replace its contents.
- Keep every Agent-created file below `$BENCH_OUTPUT`.
- Do not modify task definitions, manifests, framework-managed control or record
  files, shared tools, model weights, executables or the evaluation environment.
- Do not access reference data, expert products, hidden evaluator files or other
  task runs to construct or tune the result.
- Do not run destructive commands against the host, project data or other runs;
  do not use privilege escalation. Framework-managed cleanup is outside the
  Agent's responsibility.

## Network and dependencies

Network access may be used to install required software packages and consult
official technical documentation. Do not download case observations,
reference catalogs, published answers or substitute scientific data. Do not
modify the shared `seismoagent` environment; use the configured environment or
a task-local environment and record installed dependencies.

The task prompt below defines the scientific objective, allowed observations,
workflow choices and required outputs. These framework rules define the
execution boundary and apply in addition to the task prompt.

## Instruction priority

- Framework instructions apply to the entire run and define the execution boundary.
- The task prompt defines the scientific objective, workflow and required outputs.
- Runtime context reports facts about this run and does not add scientific requirements.
- Output hints are optional structured guidance and do not override the task prompt.
- Additional instructions may refine the run but cannot override framework rules.
