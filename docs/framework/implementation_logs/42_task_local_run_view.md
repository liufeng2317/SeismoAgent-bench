# Stage 42: Task-local run view

- **Goal:** make durable run results directly discoverable from the standalone phase-picking task.
- **Implemented:** added `tasks/2019_ridgecrest_california_phasepicking/runs`, a relative symbolic link to the task-specific directory under the external durable `runs/` store.
- **Storage rule:** the link exposes results without copying them into the repository; execution continues to use the configured run root and stable task ID.
- **Validation:** the link resolves to the existing Ridgecrest phase-picking run directory; no run data was added to Git.
