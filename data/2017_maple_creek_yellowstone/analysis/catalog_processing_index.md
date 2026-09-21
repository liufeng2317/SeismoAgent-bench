# Maple Creek 2017 catalog-processing index

This is the compact catalog-processing index for `2017_maple_creek_yellowstone`.
Raw catalog files are untouched. Each available source owns its parser under
`catalogs/<SOURCE_REF>/scripts/`; generated outputs stay under that bundle's
`analysis/{derived,stats,figures}/`.

## Frozen selection rule

- Time: `2017-06-11T00:00:00Z <= t < 2017-06-19T00:00:00Z`.
- Research mask (event products with absolute coordinates): latitude
  `44.45–44.75°N`, longitude `-110.55–-110.15°E`, depth `0–15 km`.
- The Shelly release is phase-level and has no event coordinates; only its
  time-only phase selection is reported.
- Event rows and phase/pick rows retain separate denominators.

## Identifier convention

Normalized event tables use a short sequential `event_id` (`E000001`,
`E000002`, …). The identifier is unique only within one `source_ref/product_id`
table and is not a cross-catalog identity. Source identifiers remain unchanged
in `native_event_id`. The Shelly phase product retains native `match_id` and
`template_id` and does not invent event IDs. Any cross-catalog association must
be represented by an explicit crosswalk.

## Product audit

| Source / product | Role and unit | Full rows | Frozen selection | Interpretation |
|---|---|---:|---:|---|
| [SHELLY2019_GL081607](../catalogs/SHELLY2019_GL081607/analysis/catalog_analysis.md) / `phase_arrivals` | correlation-derived P/S phase rows; primary high-resolution auxiliary | 6,260,580 | 1,591,090 phase rows | 115,448 match IDs; 1,147 template IDs; 27 network-station pairs in the eight-day window; not an event-origin catalog |
| [PANG2019_GL082376](../catalogs/PANG2019_GL082376/PANG2019_GL082376__catalog_summary.md) | independent relocated event catalog; secondary reference | not staged | not computable locally | Article reports 3,345 events and 3,257 GrowClust relocations; machine-readable table is still missing |
| [USGS_UUSS_COMCAT_2017](../catalogs/USGS_UUSS_COMCAT_2017/analysis/catalog_analysis.md) / `operational_benchmark` | official operational event baseline | 9 snapshot rows | **5** | Q3 baseline only; not a completeness truth set |

The Shelly article's 15,912 well-located and 30,411 magnitude populations are
article-level values and must not be substituted with the local phase-row count.
Pang remains a genuine catalog-building paper, but its event table is not yet
available locally. The five ComCat rows are retained as a reproducible official
baseline and must not be merged with research catalogs.

## Compact output policy

- Shelly phase product: one `phase_overview_v1.png`; full phase statistics are
  retained without creating event-level maps.
- USGS benchmark: one `catalog_overview_v1.png`; full snapshot is statistics-only.
- All figures are 300-dpi PNG; SVG is not generated.
- Use each bundle's `--full-plots` option only for exploratory diagnostics.

## Core figures

| Product | Figure |
|---|---|
| Shelly phase arrivals | [`phase_overview_v1.png`](../catalogs/SHELLY2019_GL081607/analysis/figures/phase_arrivals/phase_overview_v1.png) |
| USGS operational benchmark | [`catalog_overview_v1.png`](../catalogs/USGS_UUSS_COMCAT_2017/analysis/figures/operational_benchmark/catalog_overview_v1.png) |

## Output layout

The case-level processing manifest is `analysis/processing.yaml`; it records the frozen window and all catalog products.

```text
catalogs/<SOURCE_REF>/
├── raw/                         # source-native files; untouched
├── scripts/                    # catalog-local parser
└── analysis/
    ├── catalog_analysis.md
    ├── derived/<PRODUCT_ID>/    # normalized/sample tables; shared schemas in `docs/schemas/`
    ├── stats/<PRODUCT_ID>/      # full/time/mask JSON statistics
    └── figures/<PRODUCT_ID>/   # compact PNG figures only
```

## Next preparation steps

1. Acquire and checksum Pang's 3,345-event machine-readable table before any
   event-level Shelly–Pang comparison.
2. Keep phase timing, event detection, absolute location and relative location
   as separate benchmark tasks.
3. Build station-day/channel manifests for the 27-station Shelly phase release
   and the 24-station Pang relocation design before waveform download.
4. Create an explicit cross-catalog event crosswalk; never join local
   `event_id` values directly.

## Re-run commands

From the repository root:

```bash
python3 data/2017_maple_creek_yellowstone/catalogs/SHELLY2019_GL081607/scripts/run_catalog_analysis.py
python3 data/2017_maple_creek_yellowstone/catalogs/USGS_UUSS_COMCAT_2017/scripts/run_catalog_analysis.py
```
