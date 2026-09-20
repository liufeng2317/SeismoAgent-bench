# Information extraction contract

This document defines the structured extraction performed **after** PDF and
supplement parsing. It is an extraction contract, not a prose reading-note
template.

## 1. Evidence-first input policy

Each source must be extracted from all available parsed material:

```text
references/<SOURCE_ID>/parsed/paper/
references/<SOURCE_ID>/parsed/supplement/
catalogs/<CATALOG_ID>/
```

The extractor must inspect both the paper and its supplements. A catalog's
construction details may be described primarily in a supporting-information
PDF, DOCX, table, or data dictionary rather than in the article body.

The original PDF and original data files remain authoritative when parsed text,
OCR, or a prior note conflicts with them. Parsed Markdown is the working text
layer; it is not evidence by itself unless it includes a locator back to the
source artifact.

Every non-trivial value must reference one or more evidence objects. Missing
values must be represented as `null` with a `status`/`note`, not guessed from
context.

## 2. Three storage layers

| Layer | Location | Purpose |
|---|---|---|
| Source files | `paper/`, `supplement/`, `catalogs/*/raw/` | Immutable PDFs, tables, catalogs, and archives |
| Parsed text | `parsed/paper/`, `parsed/supplement/` | MinerU Markdown, DOCX/XLSX/TXT derivatives and images |
| Structured extraction | `parsed/extraction/*.json` | Machine-readable facts, workflow, products, and evidence |

`paper_reading.md` and `catalog_summary.md` are legacy human-readable notes.
They may be retained for navigation, but new factual extraction should be
written to JSON and should not depend on prose notes as the canonical record.
Case-level comparison remains in `data/<CASE>/analysis/`.

## 3. Compact extraction object

Create one JSON object per source:

```text
references/<SOURCE_ID>/parsed/extraction/<SOURCE_ID>__extraction.json
```

The JSON has four substantive blocks plus extraction QA:

1. `article` — short identity and scientific context;
2. `catalog` — event populations, catalog fields, release facts, quality and evaluation role;
3. `construction_workflow` — input data and ordered catalog-construction stages;
4. `additional_information` — supplementary products, catalog-based findings, benchmark context and missing information;
5. `extraction_quality` — completion status and unresolved questions.

Evidence is embedded inside each block or object it supports. Each `evidence`
entry contains a source path, a precise locator, and a short note. There is no
independent evidence table whose meaning must be reconstructed later.

## 4. What to extract

### 4.1 `article` (brief)

Keep only title, authors, year, journal/DOI, article type, sequence, scientific
question, and relationship to the catalog. Do not reproduce a long literature
review.

### 4.2 `catalog` (main target)

Combine event information and catalog information here. Record the event
definition, distinct event/phase/measurement populations, article/local counts,
time and spatial scope, release files, schema fields, uncertainties, quality
tier, evaluation role, suitable metrics, and limitations. Article-reported and
local-audit values remain separate fields. When a source releases more than one
product (for example S10/S11/S12), use `product_semantics`,
`local_audit.product_counts`, and one `product_schemas.<product_id>` per
product; do not collapse them into a single generic schema.

### 4.3 `construction_workflow` (central scientific process)

Record the upstream data and the ordered source-to-catalog workflow. Each stage
should include input, output, method, software/model, parameters, QC rules,
intermediate result, analyst intervention, dependencies, and local evidence.
Supplementary material must be checked because thresholds, station conditions,
data dictionaries, and intermediate catalog counts may only appear there.

### 4.4 `additional_information` (secondary but useful)

Keep supplementary station/phase/focal-mechanism/structural/uncertainty products,
catalog-based findings, benchmark interpretation, and missing information in
one compact block. Do not create independent top-level sections for each of
these unless a later use case proves it necessary.

## 5. Extraction workflow

1. Enumerate `parsed/paper/`, `parsed/supplement/`, and the associated catalog files.
2. Read the paper and all relevant supplements together.
3. Fill `article` briefly.
4. Build the `catalog` object, explicitly separating populations and article/local counts.
5. Reconstruct `construction_workflow.stages` in source-to-product order.
6. Put non-primary products, findings, benchmark use, and gaps in `additional_information`.
7. Add evidence directly to each factual object.
8. Write and validate the JSON against the YAML template.
9. Update the case-level analysis only after the source JSON is reviewed.

The repository batch checker is
`scripts/03_information_extraction/validate_all_extractions.py`. It checks
evidence/release paths, product-specific schemas, status versus human-review
flags, and locally measurable row counts. A `partial` extraction is expected
when the paper, supplement, or final release is incomplete; it must not be
promoted to `verified` merely because the JSON parses.

`verified` means all locally available, in-scope materials have been reconciled and the record passes automated checks. A field may still be listed as missing when the source explicitly does not report it (for example, a fixed station count); that is different from an unparsed or unavailable source. `blocked` is reserved for a source that cannot yet be parsed, and `draft` for a known catalog whose machine-readable release is not locally verified.

Use `null` or `[]` when a field is not reported. Do not turn a missing value into
a generic claim such as “standard processing”.
