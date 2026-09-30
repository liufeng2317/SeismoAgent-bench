# Implementation 52: Phase-picking runtime

- Git commit: `5a1df9c`
- Goal: let the task-local Codex run use the preinstalled `seismoagent` scientific Python environment.
- Change: `workflows/tasks/2019_ridgecrest_california_phasepicking/run.sh` now passes a temporary runtime environment file containing the Codex proxy settings, the seismoagent `PATH`, and `PYTHON`. The task prompt explicitly forbids dependency installation and network access.
- Check: `bash -n` passed and the configured interpreter imported ObsPy 1.4.2. A real run completed with all four required artifacts and an artifact-contract score of 1.0.
- Run: `codex-phasepicking-20260929T022000Z`
