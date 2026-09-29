# Implementation 61: Provenance interface cleanup

- Git commit: `9332426`
- Goal: keep the framework's public run record interface consistent after consolidating command files.
- Change: `run-codex` now returns `provenance.json`, evaluation reports infer Agent identity from provenance, and legacy command paths are listed only when present in older runs.
- Check: reporting, Agent-contract and Codex command tests passed; diff validation passed.
