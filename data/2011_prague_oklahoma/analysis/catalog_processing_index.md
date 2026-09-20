# Prague 2011 catalog-processing index

This is the compact catalog-processing pilot for `2011_prague_oklahoma`.
Native files are untouched; every reference bundle owns its parser under
`catalogs/<SOURCE_REF>/scripts/`, and generated products are kept under that
bundle's `analysis/{derived,stats,figures}/`.

## Frozen selection rule

- Canonical time window: `2011-11-11T00:00:00Z <= t < 2011-11-19T00:00:00Z`.
- Research common-mask sensitivity: latitude `35.4523–35.5576°N`, longitude
  `-96.8723–-96.7334°E`, depth `1.02–9.62 km` (the rounded Cochran audit
  envelope).
- `time_only` remains the primary Cochran/McMahon event-window denominator;
  `benchmark` is the rounded spatial/depth sensitivity and must not silently
  replace it.
- The official ComCat benchmark file preserves its original query rule
  (`0–20 km` depth); it is reported as a separate operational product.
- Event rows, McMahon phase rows, sparse Isken rows, and ComCat snapshots retain
  separate denominators.

## Identifier convention

Normalized event tables use a short sequential `event_id` (`E000001`,
`E000002`, …). The identifier is unique only within one `source_ref/product_id`
table and is not a cross-catalog identity. Source identifiers remain unchanged
in `native_event_id`; phase products retain their native phase/parent fields.
Any cross-catalog association must be represented by an explicit crosswalk,
not by comparing local `event_id` values.

## Product audit

| Source / product | Role and unit | Full rows | Time-only | Common / official selection | Key interpretation |
|---|---|---:|---:|---:|---|
| [COCHRAN2020_GJIGGAA153](../catalogs/COCHRAN2020_GJIGGAA153/analysis/catalog_analysis.md) / `events_primary` | Q2 enhanced event catalog | 8,811 | **2,078** | **2,076** rounded mask | Template-matched/GrowClust release; magnitude type unresolved |
| [MCMAHON2017_GL072944](../catalogs/MCMAHON2017_GL072944/analysis/catalog_analysis.md) / `events_subspace` | Q2 independent event catalog | 5,446 | 2,384 | 2,328 rounded mask | Subspace detection + Bayesloc; release is broader than paper-filtered 5,262 |
| MCMAHON2017_GL072944 / `phase_arrivals` | Pick-level auxiliary | 82,537 | **37,171** parent-event rows | — | P rows are not events; parent E-record time is used because release rows omit hour |
| [ISKEN2017_BSSA0120160150](../catalogs/ISKEN2017_BSSA0120160150/analysis/catalog_analysis.md) / `events_relocated` | Q1 sparse structural anchor | 13 | 7 | 5 | Manually selected Table S3 relocations; not a completeness catalog |
| [USGS_TUL_COMCAT_2011](../catalogs/USGS_TUL_COMCAT_2011/analysis/catalog_analysis.md) / `operational_full` | Q3 operational baseline | 71 | 15 | 11 recomputed | Full snapshot; routine catalog, not research truth |
| USGS_TUL_COMCAT_2011 / `operational_benchmark` | Q3 frozen baseline | 11 | 11 | **11 official** | Preserved downloaded query result and provenance |

## Interpretation

Cochran and McMahon are separate enhanced-detection populations with different
waveform/template lineages and release filters; they must not be concatenated.
Isken provides a high-quality but deliberately sparse location/fault anchor.
The McMahon phase table is a pick-level product and its 82,537 rows are not an
event count. ComCat is an operational baseline. Magnitudes remain source-native
or unresolved and should not be ranked across products without calibration.

The 2,078 Cochran time-only count is the canonical v1 primary denominator; 2,076
is the rounded spatial/depth sensitivity. The 11-row ComCat benchmark is retained
as downloaded, even though the rounded research mask also returns 11 rows.

## Compact output policy

The default profile is `minimal`, benchmark-first and PNG-only:

- event products: one `catalog_overview_v1.png` containing map, daily rate and
  depth panels;
- McMahon phase product: one `phase_overview_v1.png` containing phase, station
  and parent-event-rate panels;
- `operational_full`: statistics only; the frozen operational snapshot carries
  the baseline figure;
- all figures are 300-dpi PNG; SVG is not generated;
- use a bundle's `--full-plots` option only for exploratory diagnostics.

## Core figures

| Product | Figure |
|---|---|
| Cochran primary | [`catalog_overview_v1.png`](../catalogs/COCHRAN2020_GJIGGAA153/analysis/figures/events_primary/catalog_overview_v1.png) |
| McMahon events | [`catalog_overview_v1.png`](../catalogs/MCMAHON2017_GL072944/analysis/figures/events_subspace/catalog_overview_v1.png) |
| McMahon phase arrivals | [`phase_overview_v1.png`](../catalogs/MCMAHON2017_GL072944/analysis/figures/phase_arrivals/phase_overview_v1.png) |
| Isken sparse relocations | [`catalog_overview_v1.png`](../catalogs/ISKEN2017_BSSA0120160150/analysis/figures/events_relocated/catalog_overview_v1.png) |
| ComCat benchmark | [`catalog_overview_v1.png`](../catalogs/USGS_TUL_COMCAT_2011/analysis/figures/operational_benchmark/catalog_overview_v1.png) |

## Output layout

The case-level processing manifest is `analysis/processing.yaml`; it records the frozen window and all catalog products.

```text
catalogs/<SOURCE_REF>/
├── raw/                         # source-native files; untouched
├── scripts/                    # parser and README
└── analysis/
    ├── catalog_analysis.md
    ├── derived/<PRODUCT_ID>/    # normalized/sample tables; shared schemas in `docs/schemas/`
    ├── stats/<PRODUCT_ID>/      # full/time/mask JSON statistics
    └── figures/<PRODUCT_ID>/   # compact PNG figures only
```

Normalized tables remain local derived artifacts and are not substitutes for
the native provenance files. McMahon phase timestamps are retained verbatim in
the sample output; only the parent E-record origin time drives the frozen
selection.

## Next preparation steps

1. Build the Prague station-day/channel manifest for the 31-station reference
   condition and verify ZQ/TA/OK/US/GS archive availability.
2. Keep the 2011-11-04–11-11 changing-network interval as a separate stress
   window; do not mix it into the v1 score.
3. Resolve McMahon P-record timestamp semantics and recover the missing SI/Data
   Set files before attempting exact phase-level reproduction.
4. Construct an explicit origin-time/space crosswalk for Cochran, McMahon,
   Isken and ComCat; do not join native event IDs directly.

## Re-run commands

From the repository root:

```bash
python3 data/2011_prague_oklahoma/catalogs/COCHRAN2020_GJIGGAA153/scripts/run_catalog_analysis.py
python3 data/2011_prague_oklahoma/catalogs/MCMAHON2017_GL072944/scripts/run_catalog_analysis.py
```

Use `--only <product_id>` for a targeted product and `--full-plots` only when
an exploratory diagnostic is needed.
