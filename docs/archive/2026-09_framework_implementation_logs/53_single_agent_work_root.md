# Implementation 53: Single Agent work root

- Git commits: `0a35b79` (implementation), `29180e2` (documentation)
- Goal: expose one Agent-controlled directory instead of framework-defined `home`, `tmp`, `work` and `output` subdirectories.
- Change: each run now contains `control/`, `work/`, `record/` and `evaluation/`. `BENCH_WORK` and `BENCH_OUTPUT` both point to `work/`; the Agent may create its own internal layout. Execution logs are stored in `record/execution.log`.
- Runtime details: HOME and TMPDIR are created under the system temporary directory and removed after the process exits.
- Check: 53 framework, execution, reporting, workflow, CLI and scoring tests passed. Scientific baseline tests requiring ObsPy in the system interpreter remain environment-dependent; the task-local Codex run uses the seismoagent interpreter explicitly.
