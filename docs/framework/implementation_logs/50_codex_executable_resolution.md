# Stage 50: Codex executable resolution

- **Goal:** make the task-local Codex launcher robust to installations where `codex` resolves to its architecture directory.
- **Implemented:** `run.sh` now appends `/codex` when the resolved value is a directory and exits with a clear message when the final path is not executable.
- **Validation:** `bash -n workflows/workflow_tests/2019_ridgecrest_california_phasepicking/run.sh` passed; the reported launcher failure was reproduced as a directory path and diagnosed before rerunning the 1.4 GB task.
- **Git:** `5f5858c` (`Resolve Codex plugin executable path`).
