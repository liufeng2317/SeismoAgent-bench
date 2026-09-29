# Run contract

Each execution is stored under `<run_root>/<task_id>/<run_id>/`. The run id is
unique for the task. The directory is divided by ownership:

```text
<run_id>/
├── control/
│   ├── task_spec.json
│   ├── input_manifest.json
│   ├── output_contract.json
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

`control/` is created by the runner from the registered task and concrete input
manifest. It is read-only control input. `task_spec.json` contains task identity,
prompt-file reference, input types and scorer settings. `task_prompt.md` contains
the human-readable task instructions. `output_contract.json` contains only
the required output artifacts. `input_manifest.json` contains only the input
locations and data metadata. `agent_prompt.md` is a rendered convenience view;
it is not an additional source of truth.

`work/` is the only Agent-controlled directory. The Agent writes candidate
artifacts there through `BENCH_WORK` and `BENCH_OUTPUT`. `record/` is written
by the runner and stores execution provenance and the actual artifact inventory.
New runs use one `provenance.json` for Agent identity and launcher details;
older runs may still contain separate `agent_command.json` and
`codex_command.json` files.
`evaluation/` is owned by the evaluator and stores scores and reports.

The task's output contract declares artifact paths relative to the Agent-owned
`work` directory. The Agent may create any internal subdirectories it needs.
The runner records the files actually found in
`record/artifact_manifest.json`. The contract and inventory remain separate so
that expected and observed outputs cannot be confused.

The runner exposes the three control paths as `BENCH_TASK_SPEC`,
`BENCH_INPUT_MANIFEST` and `BENCH_OUTPUT_CONTRACT`. These files are snapshots,
not Agent-generated files. An experiment may keep its Agent runtime
configuration in a separate `agent_config.yaml`; the run record should retain
the configuration identity and relevant non-secret settings.
