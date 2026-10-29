# Implementation 54: Codex work path fix

- Git commit: `99c1fbe`
- Goal: make the Codex launcher use the single `work/` directory introduced in implementation 53.
- Cause: the runner had been migrated to `<run>/work`, but `run-codex` still constructed `-C <run>/agent/work`, causing an immediate `No such file or directory` failure.
- Change: the Codex command now receives `-C <run>/work`.
- Check: a fake Codex launcher completed with the expected `<run>/control`, `<run>/work`, and `<run>/record` structure; 23 CLI, execution and reporting tests passed.
