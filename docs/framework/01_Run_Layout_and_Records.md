# Run Layout and Records

This document is the single description of a run directory: where it lives, every file in it, and who writes each file.

## 1. Where runs live

Formal runs live at `workflows/tasks/<case>/runs/<variant>/<harness>/<model>/<run_id>/` (git-ignored). The case `run.sh` creates them:

- `VARIANT` (default `min`) selects `task_<variant>.json`; `AGENT` (default `claude`) selects `SeismoAgentBench/configs/agents/<agent>.yaml`; the model segment is that config's `model:` line unless `CLAUDE_MODEL` or `CODEX_MODEL` overrides it.
- `RUN_ID` defaults to the UTC launch time, `YYYYMMDDTHHMMSSZ`.
- `TIMEOUT` defaults to 172800 s (48 h) for `tools` and 86400 s (24 h) for the other variants.
- The script runs `python -m SeismoAgentBench run-claude` (or `run-codex`) with `--task`, `--input input.json`, `--run-root runs/<variant>/<harness>/<model>`, `--run-id`, `--agent-config`, `--environment-config configs/environments/seismoagent_eval.yaml`, a temporary env file and `--timeout`.
- With `DETACH=1` (default) the runner starts in its own session (`setsid nohup`) and writes its console output to `runs/<variant>/<harness>/<model>/runner-<run_id>.log`. The script waits up to 180 s for `record/runner.pid`, then deletes the temporary env file. `DETACH=0` runs attached.

The catalog-metrics scorer finds the case from this path depth; for a run stored anywhere else (for example a campaign run) it is skipped with a message naming the required layout.

Without `run.sh`, a run lands at `<run_root>/<run_id>/`. With `--campaign-id` it lands at `<run_root>/<task_id>/<run_id>/`; the campaign, variant and agent are recorded as `run_layout` in `record/provenance.json` and in the CLI output. A `run_id` is one path component. An existing run directory is an error unless `--resume` is given and the run is in `execution_retryable`.

## 2. Directory tree

```text
<run_id>/
├── control/          # framework snapshots, read by the Agent and the evaluator
├── work/             # the Agent's directory (BENCH_WORK = BENCH_OUTPUT)
│   └── input/        # read-only input view (BENCH_INPUT)
├── record/           # execution records
├── evaluation/       # scores and diagnostics, created by evaluation
├── attempts/         # earlier attempts, only after --resume
└── EXCLUDED.md       # only for a run stopped by a harness defect
```

## 3. control/

| File | Written by | Content |
| --- | --- | --- |
| `task_spec.json` | runner | the task spec, with `task_prompt_file` set to `task_prompt.md` |
| `task_prompt.md` | runner | the task prompt (`prompt_<variant>.md`) |
| `input_manifest.json` | runner | copy of the input file; only when `--input` is given |
| `output_contract.json` | runner | copy of the task's output contract; only when the task declares one |
| `agent_prompt.md` | runner | the rendered Agent prompt; for Claude Code the exact text sent on standard input, for Codex the last argv element; only with `run-claude` or `run-codex` |
| `agent_config.yaml` | run workflow | validated Agent config without secrets; only with `--agent-config` |
| `environment_config.yaml` | run workflow | the environment config; only with `--environment-config` |

## 4. work/

`work/` is the Agent's only writable directory and its current directory. `BENCH_WORK` and `BENCH_OUTPUT` both point to it. Output-contract paths are relative to it (for example `catalog.csv` and `picks.csv`); the Agent chooses any other layout.

`work/input/` is the input view (`BENCH_INPUT`): one symbolic link per input entry, named by the basename of the source path (not by the entry id), with the directory set read-only (mode 555). Data are not copied. Two entries with the same basename, or an entry whose path does not exist, are an error before the Agent starts. Without an input file the directory is created empty and read-only.

## 5. record/

| File | Written by | Content |
| --- | --- | --- |
| `run_result.json` | runner; run workflow; evaluator; `finalize` | run id, task id and version, state, `failure_reason`, `exit_code`, `attempt`, `timeout_s`, start and finish times, the names (never values) of injected environment variables, `execution_profile`, `formal_evaluation_eligible`; heartbeat fields `heartbeat_at`, `elapsed_s` and `execution_log_bytes` every 300 s; `leftover_processes_stopped` and `runtime_home_preserved` when they apply. The run workflow adds `agent` and points `command` to `provenance.json`; the evaluator writes its state and check fields |
| `execution.jsonl` | runner | every output line of the Agent process as one JSON event; non-JSON lines become `console.line` events |
| `execution.log` | runner | readable summary of the same events, each line prefixed with its UTC arrival time |
| `usage_summary.json` | runner; `finalize` | tokens, cost and turns from `execution.jsonl` (partial when written by `finalize`) |
| `timeline.json` | runner | event arrival times and gaps from `execution.log` |
| `runner.pid` | runner | runner pid, host, process start time; read by `status`, `finalize` and `run.sh` |
| `environment.json` | run workflow | runtime facts (Python, OS, architecture, Conda environment, network and installation policy, time budget) and the work, input and output directories |
| `provenance.json` | run workflow; CLI | Agent name and version, references to the control files, `tools` (the `seismotools` path, commit and dirty flag), and `launcher`: executable and version, argv, `prompt_via` (`stdin` or `argv`), model, working directory, `credentials_included: false`. A prompt on argv is replaced by `<BENCH_AGENT_PROMPT>`. A campaign run adds `run_layout`. `environment_integrity`: whether the shared Conda environment's installed packages changed during the run (`changed`, `added`, `removed`; entry names only) |
| `artifact_manifest.json` | evaluator | the result of the output-contract check |
| `runtime_home/` | runner | non-hidden files the Agent left in its temporary `HOME`; only when there are any |

No transcript file is written; `execution.jsonl` is the transcript.

`attempts/attempt-NNN/` holds everything except `control/` from an attempt that `--resume` replaced.

## 6. evaluation/

`evaluation/` is written by `python -m SeismoAgentBench evaluate` and by `python -m SeismoAgentBench.scoring.catalog_metrics`; neither touches `work/`.

| File | Written by | Content |
| --- | --- | --- |
| `scorer_plan.json` | evaluate | declared scorers with mode and status (`declared`, `scored`, `skipped`) |
| `score.json` | evaluate | `artifact-contract@1` result |
| `metrics.json` | evaluate or `catalog_metrics run` | `catalog-metrics@1` result |
| `<scorer>_failure.json` | evaluate | the error of a scorer that raised |
| `report.json` | evaluate | state, task, Agent and an index of the run's records |
| `location_diagnostics.png`, `audit_sample.csv`, `audit/` | `catalog_metrics run`, `audit` | diagnostics and blind-review package ([02_Catalog_Metrics.md](02_Catalog_Metrics.md) §9) |
| `swap/` | `catalog_metrics swap` | the run's picks relocated with the expert locator: `inputs/`, `nll/`, `catalog_relocated.csv`, `swap.json` |

Older runs may also hold `metrics_v1.json` (v1 scores, [02_Catalog_Metrics.md](02_Catalog_Metrics.md) §12) and `rescue/` (a reference-only score of outputs recovered outside `work/`). A run scored only with `catalog_metrics run` has `metrics.json` without `report.json`, `scorer_plan.json` or `score.json`.

## 7. Excluded runs

A run stopped by a harness defect, not by the Agent's own work, gets an `EXCLUDED.md` file at its root, written by hand with the reason. `catalog_metrics summary` leaves it out of the summary and the export and lists it under `excluded_runs` ([02_Catalog_Metrics.md](02_Catalog_Metrics.md) §11).

## 8. Tracked exports

Runs are not tracked in git. `catalog_metrics summary` writes the tracked per-case results under `workflows/tasks/<case>/evaluation/agents/` ([02_Catalog_Metrics.md](02_Catalog_Metrics.md) §9).

## 9. Monitoring and closing

- `python -m SeismoAgentBench status --run-dir <run>` reads the run result, the runner pid and the log, and reports state, elapsed and idle time and which contract artifacts exist. It changes nothing.
- `python -m SeismoAgentBench finalize --run-dir <run>` closes a run left in `preparing` or `running` whose runner is gone: state `interrupted`, `failure_reason: runner_lost`, a partial usage summary, `finished_at` from the newest file in `work/`, and removal of the orphaned runtime root. It refuses while the runner pid is alive unless `--force` is given.

## 10. Experiment harness

`plan-experiment` and `execute-experiment` run the units of an experiment YAML serially through the same run workflow, without evaluation. This path is secondary and not used for formal runs. Each unit is stored at `<output_root>/run_<NNN>_<agent_id>_<variant>/` with the default 600 s timeout and the unit's own command (no rendered prompt), and adds `record/experiment_unit.json` and `record/unit_result.json`. The batch writes `summary.json` and `summary.md` under `<output_root>/_batches/<batch_id>/`; these summarize execution states only.

## 11. Ownership

- The Agent writes only below `work/`. The framework prompt states this; the runner does not enforce it beyond the read-only input view.
- The runner, the run workflow and the CLI write `control/` and `record/`.
- The evaluator writes `evaluation/`, `record/artifact_manifest.json` and the evaluation fields of `record/run_result.json`. It never starts the Agent and can run again on the same run.
- `EXCLUDED.md` is written by hand.
- After the Agent exits, nothing writes to `work/`.
