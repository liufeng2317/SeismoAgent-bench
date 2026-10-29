# SeismoAgentBench Data Guide

The `data/` directory contains the observation-data entry points, reference catalogs, literature, and reproducible audits for the six seismological cases. This page defines only the directory structure, file responsibilities, and maintenance rules; case statistics are not duplicated here.

## Document Boundaries

| File | Sole responsibility | Excludes |
|---|---|---|
| [CASES_SUMMARY.md](../docs/data/CASES_SUMMARY.md) | Cross-case statistics for events, waveforms, stations, catalogs, official baselines, and literature assets | Detailed product provenance for an individual case |
| [CASE_DETAILS.md](../docs/data/CASE_DETAILS.md) | Case-by-case observation, research-catalog, official-catalog, literature, and limitation details | Cross-case aggregate tables |

For further details, consult `<case>/README.md`, `<case>/analysis/processing.yaml`, and the relevant source/catalog `README.md` first. Historical download logs and scientific discussion remain within the case directories and are not duplicated in the top-level documents.

## Six Cases

- [2011 Prague, Oklahoma](2011_prague_oklahoma/README.md)
- [2016 Kaikōura, New Zealand](2016_kaikoura_new_zealand/README.md)
- [2017 Maple Creek, Yellowstone](2017_maple_creek_yellowstone/README.md)
- [2018 Kīlauea, Hawaiʻi](2018_kilauea_hawaii/README.md)
- [2019 Ridgecrest, California](2019_ridgecrest_california/README.md)
- [2020 Magna, Utah](2020_magna_utah/README.md)

## Directory Structure

```text
data/
├── README.md
└── <case>/
    ├── README.md
    ├── analysis/
    │   ├── <CASE>_analysis.md
    │   └── processing.yaml
    ├── data/
    │   ├── catalogs/<SOURCE_ID>/
    │   │   ├── README.md
    │   │   ├── <source products>
    │   │   ├── raw/                 # Original release archives, when present
    │   │   └── analysis/            # Reproducible statistics, derived tables, and figures
    │   └── waveforms -> <external archive>
    │       ├── data/                # MiniSEED, organized by NET.STA
    │       ├── stations/            # StationXML, station manifests, and inventories
    │       └── waveform_inventory.json
    ├── references/<SOURCE_ID>/
    │   ├── paper/
    │   ├── supplement/              # Present only when needed
    │   └── parsed/
    └── scripts/observations/         # Station, metadata, download, and inventory tools
```

Waveforms are stored in external archives, and each case's `data/waveforms` is a symbolic link. The presence of a symbolic link does not imply data completeness; use the header inventory in `waveform_inventory.json` and the case observation README as the authoritative records.

## Content Boundaries

- `references/` contains only papers, supplementary materials, and reading/extraction results.
- `data/catalogs/` contains catalogs, phase picks, focal mechanisms, original release archives, and product-level statistics used for benchmark validation.
- `analysis/` contains case-level scientific designs, candidate windows, cross-product audits, and figures. Statistics for an individual product remain under that catalog's `analysis/` directory.
- `scripts/observations/` contains executable data-preparation tools and run logs; logs are not status manifests.
- Cross-case statistics are consolidated in `docs/data/CASES_SUMMARY.md`, with case-level detail in `docs/data/CASE_DETAILS.md`. Product stats JSON files and catalog READMEs remain the underlying evidence.

## Naming and Associations

- Case directories use lowercase `year_region_place` slugs.
- `SOURCE_ID` is the stable association key connecting papers, supplementary materials, and catalogs.
- Papers are named `<SOURCE_ID>__paper.pdf`; additional literature files use role-specific suffixes.
- Benchmark-readable catalogs are named `<SOURCE_ID>__catalog_<role>.<ext>`; original release files retain their original names under `raw/`.
- Each catalog README must declare its `source_ref`, provenance, schema, units, and known limitations.
- `event`, `relative_event`, `phase_pick`, and `focal_mechanism` are distinct statistical units and must not be added together.
- Different versions or overlapping catalogs for the same event population must not be summed into a “total event count”; report them by product.

## Status and Statistical Conventions

- All six cases have `window_status: frozen` (2026-10-28, with metrics v1); each `analysis/processing.yaml` records the frozen evaluation window, and the evaluation cohort mask is `workflows/tasks/<case>/expert/00_config/validation.yaml`. Statistics computed with data-level masks remain descriptive and may differ from evaluation cohort counts.
- “Waveform file count” means readable daily MiniSEED files in the external archive. “Candidate-window file count” is determined from the header time ranges recorded in the inventory.
- “Station manifest/metadata count” and “stations with downloaded waveforms” are reported separately. The former describes the design or discovery scope; the latter describes the local payload.
- An official operational catalog is a Q3 comparison baseline, not a high-resolution research truth catalog.
- Local omissions, partial status, and source-version discrepancies must remain explicit and must not be concealed by substituting similar products.

## Processing and Output Policy

- `analysis/processing.yaml` is the entry point for candidate-window and product declarations; a filename containing `benchmark` does not indicate a formal freeze.
- A catalog README is the manually maintained entry point for provenance, schema, units, version discrepancies, and limitations. `analysis/catalog_analysis.md` and the stats/figures directories contain generated products.
- Every derived record must preserve its source/product identity, native ID or source row number, and input-file hash. Cross-catalog event associations require an explicit crosswalk.
- Events, relative events, phase picks, focal mechanisms, and different versions of the same catalog must be processed separately; temporal or spatial overlap is not grounds for combining their counts.
- Original waveforms, catalogs, papers, supplementary materials, and OCR evidence must not be deleted merely because statistics have been generated. Caches, temporary fragments, and operating-system metadata are not retained as scientific data.

## Storage and Version Control

Git stores documentation, small normalized catalogs, schemas, configurations, and small reproducible statistics. Waveforms, original papers, publisher supplements, large phase tables, original archives, OCR intermediates, and run logs may remain local or in external archives; exclusion from ordinary Git must not be interpreted as absence.

Do not commit credentials, `.env` files, model caches, or temporary fragments. Before adding a large file, record its authoritative download location, version or DOI, SHA-256 checksum, and recovery method.

## Maintenance Sequence

1. After updating a source or downloading data, run the corresponding catalog or observation inventory first.
2. Update provenance and limitations in the source/catalog README.
3. Regenerate or inspect the relevant product statistics if catalog products have changed.
4. Update the case section in `docs/data/CASE_DETAILS.md`.
5. Synchronize the cross-case tables in `docs/data/CASES_SUMMARY.md`.
