# Data-preparation schemas

One canonical schema per semantic product type of the case data preparation. The catalog-local analysis scripts (`data/<case>/data/catalogs/*/scripts/run_catalog_analysis.py`) and their reports cite these files instead of carrying their own `schema.yaml`; the extraction contract ([`../02_Extraction_Contract.md`](../02_Extraction_Contract.md)) validates against the first one. The benchmark framework does not read them: task, manifest and output-contract schemas are in `SeismoAgentBench/task/schemas/`.

| Schema | Applies to |
|---|---|
| `paper_catalog_extraction.schema.yaml` | Paper and supplementary-information extraction JSON |
| `catalog_event.schema.yaml` | Normalized event catalogs, including operational baselines |
| `catalog_correlation_phase.schema.yaml` | Shelly-style correlation-derived P/S phase tables |
| `catalog_parent_phase.schema.yaml` | McMahon-style phase rows linked to parent event records |
| `catalog_relative_event.schema.yaml` | Relative-coordinate event tables |

The case-level processing manifests are stored at `data/<CASE_ID>/analysis/processing.yaml`. Product-specific `product_id` and `kind` values remain in the statistics JSON and catalog analysis reports.
