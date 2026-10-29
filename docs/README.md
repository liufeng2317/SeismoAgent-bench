# Documentation

Files are named `NN_Title_Case.md`, numbered in reading order within each folder; dated records are `YYYY-MM-DD_...`. One line per paragraph or list item, no manual line wrapping.

| Folder | Holds | Start with |
|---|---|---|
| [`research/`](research/) | the research: questions and benchmark design, expert-experience evidence and the checker, the paper outline, the scoring method, status, work plan and the complete score table, a one-page Chinese overview (`research_map.html`), dated progress summaries | [`research/README.md`](research/README.md) |
| [`framework/`](framework/) | the reusable benchmark framework: workflow, run layout and records, catalog metrics with the trusted-catalog standard, development process | [`framework/README.md`](framework/README.md) |
| [`data/`](data/) | the cases and their data: case registry (tiers, frozen windows, primary references), case data inventory, candidate case pool; `preparation/` holds the case record standard, the extraction contract, the MinerU parsing audit and the data-preparation schemas | [`data/00_Case_Registry.md`](data/00_Case_Registry.md) |
| [`archive/`](archive/) | records that are no longer maintained: the 2026-09-24 repository cleanup, the September 2026 framework implementation logs, external GeoDataBench Codex notes | — |

Elsewhere in the repository:

- Case-specific scientific interpretation: `data/<case>/analysis/`; catalog provenance: `data/<case>/data/catalogs/*/README.md`.
- Task packages, the human-in-loop (expert) workflow and per-case evaluation results: `workflows/tasks/<case>/` (`expert/docs/`, `evaluation/`).
- Agent and environment configuration, including the evaluation environment's pinned requirements and host tool installer: `SeismoAgentBench/configs/`.
