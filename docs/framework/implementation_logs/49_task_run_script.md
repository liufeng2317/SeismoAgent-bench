# Stage 49: Task-local run script

- **Goal:** reduce case execution to one reproducible command.
- **Implemented:** added `workflows/tasks/2019_ridgecrest_california_phasepicking/run.sh`; it resolves the project and task paths, runs the Codex task with the task-local manifest and run store, then invokes external evaluation. `RUN_ID`, `PYTHON` and `CODEX_BIN` remain optional overrides.
- **Validation:** `bash -n workflows/tasks/2019_ridgecrest_california_phasepicking/run.sh` passed.
- **Git:** `ba141d9` (`Add task-local phase picking run script`).
