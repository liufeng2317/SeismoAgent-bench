# Structured paper/catalog extraction

Canonical reviewed records live in:

```text
data/<case>/references/<SOURCE_ID>/parsed/extraction/<SOURCE_ID>__extraction.json
```

They follow `docs/schemas/paper_catalog_extraction.schema.yaml`. Evidence is embedded in the object it supports. Keep article-reported counts and local-file counts separate; unresolved facts remain warnings or `null`.

Validate all records:

```bash
python scripts/03_information_extraction/validate_all_extractions.py
```

Validate one record with the same checker:

```bash
python scripts/03_information_extraction/validate_all_extractions.py data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/extraction/TAN2024_JB028735__extraction.json
```

The checker verifies local evidence/release paths, status semantics, product schemas, and declared CSV/XLSX/QuakeML row counts. It also checks TAN's distinction between the released S11 intermediate product and the article-reported final population. Passing validation does not replace scientific review.

Reusable maintenance utilities:

- `normalize_quality_tiers.py`: normalize compact Q1–Q4/unknown labels while retaining rationale.
- `update_reference_extraction_links.py`: add missing extraction links to reference READMEs.

The hardcoded record-creation scripts and completed one-time migrations were removed during repository consolidation. They contained older copies of facts now maintained in the canonical JSON and could overwrite subsequent review. They are not an extraction pipeline or a prerequisite for validation.
