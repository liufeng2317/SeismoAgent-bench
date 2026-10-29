# Schema registry

The project keeps one canonical schema per semantic product type. Catalog-local
analysis outputs reference these files instead of carrying duplicated
`schema.yaml` files.

| Schema | Applies to |
|---|---|
| `paper_catalog_extraction.schema.yaml` | Paper and supplementary-information extraction JSON |
| `catalog_event.schema.yaml` | Normalized event catalogs, including operational baselines |
| `catalog_correlation_phase.schema.yaml` | Shelly-style correlation-derived P/S phase tables |
| `catalog_parent_phase.schema.yaml` | McMahon-style phase rows linked to parent event records |
| `catalog_relative_event.schema.yaml` | Relative-coordinate event tables |
| `catalog_absolute_approx.schema.yaml` | Explicitly approximate absolute-coordinate derivatives |

The case-level processing manifests are stored at
`data/<CASE_ID>/analysis/processing.yaml`. Product-specific `product_id` and
`kind` values remain in the statistics JSON and catalog analysis reports.
