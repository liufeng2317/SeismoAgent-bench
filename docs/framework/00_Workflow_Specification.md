# Workflow Specification

This document states the purpose, principles and stage sequence of a SeismoAgentBench run: task package, run, records, evaluation.

## 1. Purpose and scope

SeismoAgentBench runs a coding Agent (Claude Code or Codex CLI) on a seismic catalog-construction task and evaluates what it produced. The package `SeismoAgentBench/` is dataset-independent; everything specific to a case lives in its task package `workflows/tasks/<case>/` and its data under `data/<case>/`.

The runner records a command execution on the host. It is not a security sandbox: every run record carries `execution_profile: trusted-development` and `formal_evaluation_eligible: false`.

Every file and directory a run produces is described in [01_Run_Layout_and_Records.md](01_Run_Layout_and_Records.md). The metric definitions are in [02_Catalog_Metrics.md](02_Catalog_Metrics.md).

## 2. Principles

1. The task package is the case contract. Generic modules contain no case paths, catalogs, expert answers, station lists or plotting rules.
2. The task prompt is the primary contract for the Agent. The output contract and the input file add machine-readable details; they do not replace the prompt.
3. Execution and evaluation are separate. The runner never scores; the evaluator never starts the Agent and can be repeated on the same run.
4. A process exit status describes execution only. It is never read as a scientific score.
5. Runs are never overwritten. Each run gets a new `run_id`; an existing run directory is an error unless the run is resumed from `execution_retryable`, and a resumed attempt archives the previous one first.
6. The Agent writes only below its work directory. Control and record files are written by the framework.
7. Reference catalogs and expert products are kept out of the Agent's prompt and input view. The framework prompt forbids using them, and the scorer's leakage scan checks the Agent's tool-call inputs ([02_Catalog_Metrics.md](02_Catalog_Metrics.md) §9).
8. Every run is traceable: control snapshots of the task, the exact Agent prompt, the launcher argv without credentials, the executable version, the `seismotools` commit and the event stream.

## 3. Stage sequence

```text
task package → run → records → evaluation
```

### 3.1 Task package

A task package `workflows/tasks/<case>/` holds:

| File | Content |
| --- | --- |
| `task_<variant>.json` | task spec for one variant (`min`, `tools`, `guided`) |
| `prompt_<variant>.md` | the task prompt the spec names in `task_prompt_file` |
| `output_contract.json`, `output_contract_min.json` | required output artifacts; each spec names one in `output_contract` |
| `input.json` | the input file: read-only data entries for the Agent |
| `run.sh` | the launcher for formal runs |
| `evaluation/metrics.yaml` | the case configuration of the catalog-metrics scorer |

A task spec requires `task_id`, `version` and `task_prompt_file`. Optional fields are `title`, `summary`, `output_contract`, `category`, `software`, `required_system_packages`, `taxonomy`, `input_requirements`, `reference_requirements` and `evaluation` (validated in `SeismoAgentBench/task/validation.py`). A spec has no fields for permitted tools, execution limits or failure policy: the tool policy is stated in the prompt (`taxonomy.tool_policy` only labels it), the time budget is the runner timeout set by `run.sh`, and failures are classified by the runner (§4). Every task spec declares the scorers `artifact-contract@1` and `catalog-metrics@1` under `evaluation.scorers`.

An output contract lists artifacts with `id`, `path`, `kind`, `required` and an optional column `schema`; paths are relative to the Agent's work directory.

The input file has `schema_version` 1, `case_id`, an optional `description` and a non-empty list of `entries`. Each entry has `id`, an absolute `path`, `type` (`file` or `folder`) and optional `notes` (`SeismoAgentBench/task/schemas/input_manifest.schema.json`). The runner checks the schema, unique entry ids, absolute paths and types. It does not check that the paths exist; an entry whose path is missing is left out of the input view.

### 3.2 Run

`run.sh` starts `python -m SeismoAgentBench run-claude` (or `run-codex` with `AGENT=codex`). The command:

1. loads the Agent config (`configs/agents/<harness>.yaml`, whose `harness` must match the command), the environment config (only `mode: host-direct` is supported) and the env file with credentials, of which only the variable names are recorded;
2. renders the Agent prompt: the task prompt, the framework rules (`configs/prompts/framework.md`), the runtime context with the time budget, the output hints from the output contract and the additional instructions passed with `--prompt`;
3. builds the launcher argv and runs the Agent through the runner (`execution/runner.py`).

The runner creates the run directory and its control snapshots, links the input view, and starts the Agent with the work directory as current directory. The process gets a reduced environment (`PATH=/usr/bin:/bin`, a fresh `HOME` and `TMPDIR` under a temporary runtime root, one BLAS thread), the run variables below, and the env-file values. Claude Code receives the Agent prompt on standard input; Codex receives it as the last argv element. The runner streams the output into the record, rewrites the run result every 300 s as a heartbeat, kills the process group at the timeout, stops processes the Agent left running, and keeps non-hidden files from the temporary `HOME`.

| Variable | Value | Set |
| --- | --- | --- |
| `BENCH_TASK_SPEC` | `control/task_spec.json` | always |
| `BENCH_WORK` | `work/` | always |
| `BENCH_OUTPUT` | `work/` (same as `BENCH_WORK`) | always |
| `BENCH_INPUT` | `work/input/` | always |
| `BENCH_INPUT_MANIFEST` | `control/input_manifest.json` | only with an input file |
| `BENCH_OUTPUT_CONTRACT` | `control/output_contract.json` | only when the task declares an output contract |
| `PYTHON` | the Python of the environment config (`run.sh` also writes it to the env file) | when configured |

The Agent calls scientific tools directly through its shell. The tool-adapter classes in `SeismoAgentBench/agent/tools.py` are not used in runs. Tool provenance is the `seismotools` commit and dirty flag in `record/provenance.json` together with the Agent's tool calls in `record/execution.jsonl`.

### 3.3 Records

The runner, the run workflow and the CLI write `control/` and `record/`; the Agent writes `work/`. [01_Run_Layout_and_Records.md](01_Run_Layout_and_Records.md) lists every file and who writes it. `python -m SeismoAgentBench status --run-dir <run>` probes a run read-only; `finalize` closes a run whose runner died.

### 3.4 Evaluation

`python -m SeismoAgentBench evaluate --run-dir <run>` is the only scoring path (`workflow/evaluate_run.py`):

1. Only runs in `completed`, `scored`, `artifact_invalid` or `scoring_failed` are evaluated; for any other state only `evaluation/report.json` is written.
2. The artifacts in `work/` are checked against `control/output_contract.json`. A failure sets `artifact_invalid`.
3. The scorers declared in the task spec are resolved in the registry (`scoring/registry.py`) and written to `evaluation/scorer_plan.json`, then run in order. A scorer that lacks an optional input is recorded as `skipped`. A scorer that raises sets `scoring_failed`. Without `artifact-contract@1` the run is also `scoring_failed`.
4. Otherwise the run is `scored`. The state is written back to `record/run_result.json`.

Registered scorers are `artifact-contract@1` and `catalog-metrics@1` (local), and `catalog-basic@1` and `phase-picking-basic@1` (reference-based, declared by no task). `catalog-metrics@1` is the shared code in `SeismoAgentBench/scoring/catalog_metrics/`, configured per case by `workflows/tasks/<case>/evaluation/metrics.yaml`; it is skipped when the run is not at the formal run path. Its own CLI (`python -m SeismoAgentBench.scoring.catalog_metrics`) also scores baselines, summarizes repeated runs and prepares audits ([02_Catalog_Metrics.md](02_Catalog_Metrics.md) §9).

## 4. Run states

| State | Set by | Meaning |
| --- | --- | --- |
| `preparing`, `running` | runner | live run |
| `completed` | runner | the Agent process exited with code 0 |
| `execution_failed` | runner | non-zero exit; `failure_reason` is `nonzero_exit`, `quota_exhausted`, `usage_limit`, `max_turns_exceeded`, or `launcher_error` when the process could not start |
| `execution_retryable` | runner | non-zero exit with `failure_reason` `capacity` or `rate_limited`; `--max-attempts` retries it, and `--resume` starts a new attempt in the same run directory |
| `execution_timeout` | runner | the timeout was reached and the process group killed |
| `interrupted` | runner or `finalize` | `failure_reason` `runner_signal:SIGTERM` or `runner_signal:SIGINT`; `runner_lost` when `finalize` closes a run whose runner died |
| `artifact_invalid` | evaluator | the output contract check failed |
| `scoring_failed` | evaluator | a declared scorer failed, or `artifact-contract@1` is not declared |
| `scored` | evaluator | `artifact-contract@1` scored and no declared scorer failed |

The runner ignores `SIGHUP`, so a closed terminal does not end a run. `cli_error` is not a run state: when the CLI cannot prepare or record a run it prints `{"state": "cli_error", ...}` on standard error and exits with code 2. The `run-*` and `evaluate` commands exit 0 for `completed` or `scored` and 3 otherwise.

## 5. Package layout

| Path | Responsibility |
| --- | --- |
| `SeismoAgentBench/task/` | task, input-file and output-contract validation; prompt rendering; schemas |
| `SeismoAgentBench/execution/` | runner, Claude and Codex launchers, run layout, configs, runtime probe, status and finalize, experiment plans |
| `SeismoAgentBench/workflow/` | run one Agent, evaluate one run, execute an experiment |
| `SeismoAgentBench/agent/` | the Agent identity and command (`AgentSpec`) |
| `SeismoAgentBench/scoring/` | artifact checks, scorer registry, catalog metrics |
| `SeismoAgentBench/reporting/` | environment, evaluation-report, event-log and batch records |
| `SeismoAgentBench/configs/` | Agent configs, environment configs, framework prompt |
| `SeismoAgentBench/utils/` | source registry and catalog utilities used by data preparation |
| `workflows/tasks/<case>/` | task packages, case evaluation configuration, runs |
| `data/<case>/` | case data, reference evidence and preparation scripts |
| `seismotools/` | versioned scientific tools offered to the Agent |

A module is created only when it has an implemented responsibility and a caller.
