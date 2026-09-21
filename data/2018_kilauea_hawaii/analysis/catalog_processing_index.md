# Kīlauea 2018 catalog-processing index

This file records the first complete catalog-processing pilot for
`2018_kilauea_hawaii`. Raw catalog files were not modified. Each source
bundle owns its parser under `catalogs/<SOURCE_REF>/scripts/`; all generated
outputs are under that bundle's `analysis/{derived,stats,figures}/`.

## Frozen selection rule

- Time: `2018-05-01T00:00:00Z <= t < 2018-05-09T00:00:00Z`.
- Summit comparison mask (when absolute coordinates exist):
  latitude `19.30–19.50°N`, longitude `-155.40–-155.15°`,
  depth `0–20 km`.
- Relative-coordinate products are reported with a time-only selection;
  the geographic mask is not silently applied.
- Event rows, phase/pick rows, and operational snapshots retain separate
  denominators.

## Identifier convention

Normalized event tables use a short sequential `event_id` (`E000001`,
`E000002`, …). The identifier is unique only within one `source_ref/product_id`
table and is not a cross-catalog identity. When the source provides an event
identifier it is preserved unchanged in `native_event_id`; when it does not,
that field remains empty. Phase products retain their native `match_id` and
`template_id` and do not invent event IDs. Any cross-catalog association must
be represented by an explicit crosswalk.

## Product audit

| Source / product | Native unit and role | Full rows | Frozen selection | Key local result |
|---|---|---:|---:|---|
| [SHELLY2019_GL085636](../catalogs/SHELLY2019_GL085636/analysis/catalog_analysis.md) / `events_s1` | event; primary summit reference | 44,188 | 1,902 time-only; **1,883 mask** | 44,188 unique native IDs; no duplicate IDs |
| SHELLY2019_GL085636 / `events_s2` | event; separate polarity-cluster product | 43,950 | 1,896 time-only; **1,877 mask** | 43,950 unique native IDs; do not concatenate with S1 |
| SHELLY2019_GL085636 / `phase_arrivals` | phase pick; auxiliary | 8,582,492 | 156,319 arrival rows | P 7,460,986; S 1,121,506; 25 stations; 1,258 template IDs; 235,122 match IDs |
| [WEI2022_EA001979](../catalogs/WEI2022_EA001979/analysis/catalog_analysis.md) / `events_s1` | event row; broad secondary reference | 375,736 | 11,640 time-only; **2,369 mask** | 1,930 masked rows have numeric magnitude; no explicit event-ID field |
| [MATOZA2021_EA001253](../catalogs/MATOZA2021_EA001253/analysis/catalog_analysis.md) / `relocated_events` | event; island-wide relocation auxiliary | 347,446 | 2,999 time-only; 1,130 relocated-coordinate mask; 1,190 starting-coordinate mask | 299,966 rows have `nbranch>1`; coordinate basis must remain explicit |
| [MATOZA2014_GL059819](../catalogs/MATOZA2014_GL059819/analysis/catalog_analysis.md) / `lp_events` | LP event; historical auxiliary | 12,290 | 0 in 2018 window | Native span is 1986–2009; no temporal overlap with v1 |
| [LENGLINE2021_EPSL116653](../catalogs/LENGLINE2021_EPSL116653/analysis/catalog_analysis.md) / `relative_events` | relative-coordinate event; dike auxiliary | 6,327 | 6,049 time-only | Native x/y retained; an **approximate** WGS84 derivative is available with explicit EN-axis and fixed-3-km assumptions |
| [USGS_HVO_COMCAT_2018](../catalogs/USGS_HVO_COMCAT_2018/analysis/catalog_analysis.md) / `operational_full` | event; Q3 operational baseline | 40,095 | 562 time-only; 495 recomputed mask | Use the separately downloaded canonical benchmark snapshot (496 rows) for the frozen official baseline |
| USGS_HVO_COMCAT_2018 / `operational_benchmark` | event; canonical baseline snapshot | 496 | **496** | Preserves the official downloaded query result and retrieval provenance |

### Interpretation

The counts are not interchangeable. Shelly S1/S2 are high-resolution summit
event products; the phase table is a pick-level product and its row count is
not an event count. Wei is broader and automatic, with changing onshore/offshore
network coverage and missing magnitudes. Matoza 2021 has separate starting and
relocated geometries. Lengliné is a relative migration coordinate table, and
Matoza 2014 is historical. Lengliné now has an assumption-labelled absolute derivative, but it is not a true absolute hypocenter catalog. HVO ComCat is an operational baseline, not a high-resolution truth set.

The Wei count now reproduces the canonical case audit (2,369) because
timezone-naive `SourceTime` values are explicitly interpreted as UTC. The
HVO 495 versus 496 difference is intentional: 495 is a mask recomputed from
the full snapshot, while 496 is the preserved official benchmark file.

## Output layout

The case-level processing manifest is `analysis/processing.yaml`; it records the frozen window and all catalog products.

```text
catalogs/<SOURCE_REF>/
├── raw/                         # source-native files; untouched
├── scripts/
│   └── run_catalog_analysis.py
└── analysis/
    ├── catalog_analysis.md
    ├── derived/<PRODUCT_ID>/    # normalized/sample tables; shared schemas in `docs/schemas/`
    ├── stats/<PRODUCT_ID>/      # full/time/mask JSON statistics
    └── figures/<PRODUCT_ID>/   # compact PNG figures only
```

The default plotting profile is deliberately compact and benchmark-first:
`catalog_overview_v1.png` is used for event products, `phase_overview_v1.png`
for the phase product, and `relative_overview_v1.png` plus the explicitly
assumption-labelled Lengliné absolute derivative map for relative coordinates.
The historical Matoza 2014 product and the full HVO snapshot remain statistics-
only by default. All figures are 300-dpi PNG; SVG is not generated. Use each
catalog script's `--full-plots` option only for exploratory diagnostics.

## Core figures

Only benchmark-oriented PNG figures are exposed by default:

| Product | Figure |
|---|---|
| Shelly S1 | [`catalog_overview_v1.png`](../catalogs/SHELLY2019_GL085636/analysis/figures/events_s1/catalog_overview_v1.png) |
| Shelly S2 | [`catalog_overview_v1.png`](../catalogs/SHELLY2019_GL085636/analysis/figures/events_s2/catalog_overview_v1.png) |
| Shelly phase arrivals | [`phase_overview_v1.png`](../catalogs/SHELLY2019_GL085636/analysis/figures/phase_arrivals/phase_overview_v1.png) |
| Wei | [`catalog_overview_v1.png`](../catalogs/WEI2022_EA001979/analysis/figures/events_s1/catalog_overview_v1.png) |
| Matoza 2021 relocated | [`catalog_overview_v1.png`](../catalogs/MATOZA2021_EA001253/analysis/figures/relocated_events/catalog_overview_v1.png) |
| Lengliné native relative | [`relative_overview_v1.png`](../catalogs/LENGLINE2021_EPSL116653/analysis/figures/relative_events/relative_overview_v1.png) |
| Lengliné approximate absolute | [`absolute_approx_map_v1.png`](../catalogs/LENGLINE2021_EPSL116653/analysis/figures/relative_events/absolute_approx_map_v1.png) |
| HVO operational benchmark | [`catalog_overview_v1.png`](../catalogs/USGS_HVO_COMCAT_2018/analysis/figures/operational_benchmark/catalog_overview_v1.png) |

Normalized event tables are intentionally local derived artifacts and remain
subject to the repository's data-file ignore policy; the source-native files
are the provenance anchor. The large Shelly phase profile is cached by the
raw-file SHA-256, so rerunning the script does not rescan the 580 MB table
unless `--force` is supplied.

## Pilot conclusions

1. **Primary summit task:** Shelly S1 is the principal high-resolution
   detection/relative-location reference; S2 is a separate sensitivity product.
2. **Broad detection/location cross-check:** Wei should be compared only after
   applying the same space/time mask and retaining its 1,930 numeric-magnitude
   subset as a separate sensitivity population.
3. **Official baseline:** HVO `operational_benchmark` is the Q3 baseline;
   it must not be merged with research catalogs.
4. **Auxiliary products:** Matoza 2021, Lengliné, and Matoza 2014 answer
   different scientific questions and should remain product-specific.
5. **Next preparation step:** derive station/channel/day manifests and waveform
   download windows; do not infer waveform volume from event-row counts.

## Re-run commands

From the repository root:

```bash
python3 data/2018_kilauea_hawaii/catalogs/SHELLY2019_GL085636/scripts/run_catalog_analysis.py
python3 data/2018_kilauea_hawaii/catalogs/WEI2022_EA001979/scripts/run_catalog_analysis.py
```

Use `--only <product_id>` for a targeted product and `--force` only when
the raw source has changed or the parser has been deliberately revised.
