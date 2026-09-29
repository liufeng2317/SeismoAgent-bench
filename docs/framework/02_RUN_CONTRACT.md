# Run contract

Each execution is stored under `<run_root>/<task_id>/<run_id>/`. The run id is
unique for the task. The directory is divided by ownership:

```text
<run_id>/
├── control/
│   ├── task_spec.json
│   └── input_manifest.json
├── agent/
│   ├── work/
│   ├── output/
│   ├── home/
│   ├── tmp/
│   └── execution.log
├── record/
│   ├── run_result.json
│   ├── environment.json
│   ├── agent_command.json
│   ├── codex_command.json
│   ├── transcript.jsonl
│   └── artifact_manifest.json
└── evaluation/        # created after the Agent exits
    ├── report.json
    └── score files
```

`control/` is created by the runner from the registered task and the concrete
input manifest. It is supplied to the Agent as read-only input. `agent/` is the
Agent workspace; the Agent writes its candidate artifacts there through
`BENCH_WORK` and `BENCH_OUTPUT`. `record/` is written by the runner and stores
execution provenance and the actual artifact inventory. `evaluation/` is owned
by the evaluator and stores scores and reports.

The task's output contract declares artifact paths relative to the Agent-owned
`work` directory. The Agent may create any internal subdirectories it needs.
The runner records the files actually found in
`record/artifact_manifest.json`. The contract and inventory remain separate so
that expected and observed outputs cannot be confused.

`task_spec.json`, `input_manifest.json` and `agent_config` are configuration
snapshots, not Agent-generated files. An experiment may keep its Agent runtime
configuration in a separate `agent_config.yaml`; the run record should retain
the configuration identity and relevant non-secret settings.
