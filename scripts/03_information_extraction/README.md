# Structured paper/catalog extraction

This directory contains the second-stage extraction utilities. They operate on
the already parsed materials under each reference's `parsed/paper/` and
`parsed/supplement/` directories and write structured results to:

```text
data/<case>/references/<SOURCE_ID>/parsed/extraction/<SOURCE_ID>__extraction.json
```

The JSON follows `docs/schemas/paper_catalog_extraction.schema.yaml`. Evidence
is embedded in the object that it supports. Article-reported counts and local
file counts must remain separate; unresolved discrepancies are represented as
warnings or `null`, not silently reconciled.

Validate one extraction (the original TAN-specific checker):

```bash
python scripts/03_information_extraction/validate_extraction.py \
  data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/extraction/TAN2024_JB028735__extraction.json
```

Validate every extraction currently present:

```bash
python scripts/03_information_extraction/validate_all_extractions.py
```

The batch checker verifies repository-local evidence and release paths, status
and human-review consistency, product-specific schemas, and row counts for CSV,
XLSX, and QuakeML products when a `product_id` is declared. It does not infer
missing article facts from catalog rows.

Quality tiers are normalized with:

```bash
python scripts/03_information_extraction/normalize_quality_tiers.py
```

`catalog.quality_tier` is the compact `Q1`--`Q4`/`unknown` value; the rationale
is retained in `catalog.quality_tier_detail`.

The one-time batch normalization pass also moves legacy reading-note evidence to
MinerU paper text when available, embeds evidence in findings/context objects,
and preserves stable supplement sidecars under parsed/supplement/.
