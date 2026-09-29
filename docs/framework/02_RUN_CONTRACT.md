# Run contract

Each execution is stored under `<run_root>/<task_id>/<run_id>/`. The run id is
unique for the task. The directory is divided by ownership:

```text
<run_id>/
├── control/
│   ├── task_spec.json
│   ├── input_manifest.json   # optional snapshot
│   ├── output_contract.json  # optional structural hint
│   ├── task_prompt.md
│   └── agent_prompt.md       # optional rendered view
├── work/                     # the only Agent-controlled directory
├── record/
│   ├── run_result.json
│   ├── environment.json
│   ├── provenance.json
│   ├── transcript.jsonl
│   └── artifact_manifest.json
└── evaluation/        # created after the Agent exits
    ├── report.json
    └── score files
```

`control/` is created by the runner from the task and, when supplied, the
concrete input manifest. It is read-only control input. `task_spec.json`
contains task identity and the prompt-file reference. `task_prompt.md` is the
primary task contract and contains the task instructions, input description
and output requirements. `input_manifest.json` and `output_contract.json` are
optional machine-readable snapshots. `agent_prompt.md` is a rendered
convenience view; it is not an additional source of truth.

`work/` is the only Agent-controlled directory. The Agent writes candidate
artifacts there through `BENCH_WORK` and `BENCH_OUTPUT`. `record/` is written
by the runner and stores execution provenance and the actual artifact inventory.
New runs use one `provenance.json` for Agent identity and launcher details.
`evaluation/` is owned by the evaluator and stores scores and reports.

When supplied, the task's output contract declares artifact paths relative to
the Agent-owned `work` directory. The Agent may create any internal
subdirectories it needs. The runner records the files actually found in
`record/artifact_manifest.json`. Without a contract, output interpretation is
left to the external evaluator.

Experiment runs also write `record/unit_result.json`. A completed experiment
writes `summary.json` and `summary.md` under its batch directory; these files
summarize execution states only and do not replace external evaluation reports.
Evaluation writes `evaluation/scorer_plan.json` before scoring. It records the
registered scorer identities and whether each scorer is local or reference-based.
Registered handlers then execute those declarations in order. A reference-based
scorer without its reference input is recorded as `skipped`; it does not receive
an implicit score. The external evaluator may run again on a completed run (or
on a previous evaluation state) without starting the Agent or changing `work/`.
Execution failure and timeout states remain non-evaluable.

The runner always exposes `BENCH_TASK_SPEC` and exposes
`BENCH_INPUT_MANIFEST`/`BENCH_OUTPUT_CONTRACT` only when the corresponding
optional files are supplied. These files are snapshots, not Agent-generated
files. An experiment MUST declare an Agent `harness` and
keep its runtime configuration in a separate `agent_config.yaml`. The declared
harness and configuration harness MUST match; the run record should retain the
configuration identity and relevant non-secret settings.
