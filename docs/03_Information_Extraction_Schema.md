# Information extraction schema

This document defines the minimum information to extract from every verified
paper, supplementary product, and catalog before agent reproduction begins.
The extraction has three layers:

1. **Paper-level facts** — what the article actually did;
2. **Catalog-level facts** — what the distributed file contains;
3. **Case-level synthesis** — whether and how the products can be compared.

## Paper-level extraction

For each `SOURCE_ID`, create `<SOURCE_ID>__paper_reading.md` beside the source
paper and record the following.

### Bibliographic identity

- title;
- authors;
- journal, year, volume, pages;
- DOI and authoritative landing page;
- article type: research article, data paper, overview, dissertation, or
  auxiliary context;
- relationship to the associated catalog.

### Scientific scope

- scientific question;
- earthquake/volcanic sequence and key events;
- study time range and time standard;
- spatial and depth range;
- magnitude range and completeness target;
- intended scientific role of the resulting catalog.

### Observation and network

- waveform archive and data access route;
- permanent and temporary networks;
- station count and channel/sample-rate information;
- deployment dates and changing network conditions;
- waveform preprocessing and quality masks;
- missing-data and station-availability handling.

### Catalog construction workflow

Describe the actual processing chain, including method names and important
parameters:

```text
waveform selection
    → detection
    → phase picking
    → association
    → initial location
    → magnitude estimation
    → differential-time / waveform processing
    → relocation
    → quality control
    → published catalog
```

For every stage record whether it was manual, analyst-assisted, automatic,
template-based, or dependent on a pre-existing catalog.

### Reported products and quality control

- initial event population;
- detected event population;
- associated event population;
- located and relocated populations;
- final published event count;
- event and phase rejection criteria;
- location and magnitude uncertainties;
- station/phase thresholds;
- clustering criteria;
- whether the final product is complete, high quality, or deliberately
  selective.

### Benchmark interpretation

- evaluation role;
- quality tier (Q1–Q4);
- expected independence from an agent workflow;
- shared waveform/template/routine-catalog lineage;
- suitable and unsuitable metrics;
- limitations and unresolved ambiguities;
- exact local paper/supplement/catalog paths.

Every numerical statement should be traceable to a page, table, figure,
supplement file, or catalog README. If the article and local file disagree,
record both values and explain the discrepancy.

## Catalog-level extraction

For each `CATALOG_ID`, create `<CATALOG_ID>__catalog_summary.md` beside the
catalog README. Preserve the source-native file and record:

- source reference and release URL/DOI;
- file name, format, version, and checksum;
- event count and row count;
- stable event-ID behavior and duplicate count;
- time range and time precision;
- latitude, longitude, and depth ranges;
- magnitude fields, types, and ranges;
- uncertainty, phase, station, and quality fields;
- missing-value conventions;
- spatial/time/depth mask used for the frozen benchmark window;
- event count after each mask;
- known outliers and excluded records;
- normalization rules and generated figures.

Catalog plots belong under `catalogs/<CATALOG_ID>/raw/` or its designated
catalog product directory. The cross-catalog interpretation belongs in the
case `analysis/` directory.

## Case-level synthesis

The case analysis should answer:

- Which catalog is primary, secondary, auxiliary, and Q3 baseline?
- Which products are genuinely independent?
- Which products measure detection, association, absolute location, relative
  location, or uncertainty?
- What common window and spatial/depth mask can be applied?
- How many events remain in each product after the common mask?
- Which waveform and station conditions are comparable?
- Which metrics are valid for each comparison?
- What data or metadata is still missing before benchmark freeze?

Do not collapse catalogs into a single leaderboard count when they target
different event populations or use different networks.

## Required output files

```text
references/<SOURCE_ID>/paper/<SOURCE_ID>__paper_reading.md
references/<SOURCE_ID>/supplement/<SOURCE_ID>__supplement_notes.md  # if needed
catalogs/<CATALOG_ID>/<CATALOG_ID>__catalog_summary.md
analysis/<CASE>__literature_synthesis.md
analysis/<CASE>__catalog_comparison.md
```
