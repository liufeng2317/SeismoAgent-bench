# Documentation

Project documentation is separated by purpose:

- [`research/`](research/) — the research: questions and benchmark design, expert-experience evidence and the checker, the paper outline, and progress ([index](research/README.md)).
- [`data/`](data/) — the cases and their data: [case registry](data/CASE_REGISTRY.md) (the six Phase I cases, tiers, windows, primary references), [candidate case pool](data/CASE_POOL.md), [six-case data summary](data/CASES_SUMMARY.md), [case-by-case details](data/CASE_DETAILS.md), and [`preparation/`](data/preparation/) (collection standard, literature extraction schema, paper parsing audit).
- [`framework/`](framework/) — reusable benchmark workflow, run contracts, evaluation metrics, implementation constraints and implementation logs.
- [`framework/schemas/`](framework/schemas/) — shared task and catalog schemas used by the framework and source-analysis scripts.
- [`archive/`](archive/) — dated records that are no longer maintained (e.g. the 2026-09-24 repository cleanup).

Case-specific scientific interpretation remains under `data/<case>/analysis/`; case-specific expert workflow documentation remains under `workflows/tasks/<case>/expert/docs/`; per-case evaluation results are under `workflows/tasks/<case>/evaluation/`.
