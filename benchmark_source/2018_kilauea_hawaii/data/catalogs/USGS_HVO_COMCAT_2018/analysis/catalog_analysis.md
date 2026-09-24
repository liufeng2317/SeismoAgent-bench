# USGS_HVO_COMCAT_2018 catalog-local analysis

Official operational baseline. Full and frozen benchmark snapshots are separate products.

- Parser version: `kilauea-local-v2-compact`
- Benchmark window: `[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; outputs below are reproducible derived artifacts.

## Product summary

| Product | Kind | Full rows | Unique native IDs | Benchmark/time rows |
|---|---|---:|---:|---:|
| `operational_full` | `usgs_csv` | 40095 | 40095 | 495 |
| `operational_benchmark` | `usgs_csv` | 496 | 496 | 496 |

## Product semantics

### `operational_full`

Full HVO/ComCat operational snapshot.

- Native input: `USGS_HVO_COMCAT_2018__catalog_operational_full.csv`
- Derived output: `analysis/derived/operational_full/USGS_HVO_COMCAT_2018__operational_full__normalized_v1.csv`
- Schema: `docs/schemas/catalog_event.schema.yaml`
- Statistics: `analysis/stats/operational_full/`
- Figures: stats only in minimal profile

### `operational_benchmark`

Frozen HVO/ComCat benchmark snapshot.

- Native input: `USGS_HVO_COMCAT_2018__catalog_operational_benchmark.csv`
- Derived output: `analysis/derived/operational_benchmark/USGS_HVO_COMCAT_2018__operational_benchmark__normalized_v1.csv`
- Schema: `docs/schemas/catalog_event.schema.yaml`
- Statistics: `analysis/stats/operational_benchmark/`
- Figures: `analysis/figures/operational_benchmark/`

## Interpretation

Event products are summarized as event rows and unique native IDs. Phase/pick products are summarized by phase-row count, template/match IDs, station and phase composition; their row count is not an event count. The common summit mask is applied only where latitude, longitude and depth are available. Relative-coordinate products retain native coordinates and use time-only selection.
