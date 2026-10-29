# Framework documentation

The reusable `SeismoAgentBench` framework, in reading order:

- [`00_Workflow_Specification.md`](00_Workflow_Specification.md) — purpose, principles and the stages from task package to evaluation, with run states and run variables.
- [`01_Run_Layout_and_Records.md`](01_Run_Layout_and_Records.md) — the run directory: who writes what in `control/`, `work/`, `record/` and `evaluation/`, how formal runs are launched, and excluded runs.
- [`02_Catalog_Metrics.md`](02_Catalog_Metrics.md) — pre-registered catalog metrics (v2 since 2026-10-30) and the trusted-catalog standard (§7a).
- [`03_Development_Process.md`](03_Development_Process.md) — how changes are defined, validated, confirmed and committed.

Elsewhere: task, manifest and output-contract schemas are in `SeismoAgentBench/task/schemas/`; agent and environment configurations in `SeismoAgentBench/configs/`; data-preparation schemas in [`docs/data/preparation/schemas/`](../data/preparation/schemas/); the September 2026 implementation logs in [`docs/archive/`](../archive/).
