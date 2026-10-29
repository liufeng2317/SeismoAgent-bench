# Implementation 55: Reproducible task artifact

- Git commit: `9edb253`
- Goal: ensure a successful task run retains the code that produced its scientific artifacts.
- Change: phase-picking output contract now requires `processing_script.py`. The Agent prompt requires saving and executing the script from `$BENCH_OUTPUT` and disallows dependence on unrecorded temporary scripts. The deterministic baseline copies its entrypoint into this artifact.
- Check: task, prompt, execution, scoring and Codex tests passed (`48 passed, 1 skipped`); Python compilation and `git diff --check` passed.
- Limitation: the earlier run `codex-phasepicking-20260929T034500Z` predates this contract and therefore has no persisted processing script. Future runs must produce it.
