# Implementation 57: Control snapshot separation

- Git commit: `c122cbc`
- Goal: make the run-level `control/` directory unambiguous and avoid mixing task semantics with output requirements.
- Change: each new run writes `task_spec.json`, `input_manifest.json`, and `output_contract.json` as separate immutable snapshots. The rendered `agent_prompt.md` remains a convenience view. `BENCH_OUTPUT_CONTRACT` exposes the output contract explicitly. The evaluator accepts both this layout and older runs with embedded `output_artifacts`.
- Check: focused runner, agent-contract and scoring tests passed; Python compilation and `git diff --check` passed. The existing CLI fixture smoke test did not finish in this host environment and remains unresolved.
