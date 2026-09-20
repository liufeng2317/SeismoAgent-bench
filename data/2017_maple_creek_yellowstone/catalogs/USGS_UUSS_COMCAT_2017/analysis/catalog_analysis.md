# USGS_UUSS_COMCAT_2017 catalog-local analysis

Official operational baseline; the local Shelly release is phase-only and remains separate.

- Parser version: `maple-local-v1-compact`
- Benchmark window: `[2017-06-11T00:00:00Z, 2017-06-19T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; outputs below are reproducible derived artifacts.

## Product summary

| Product | Kind | Full rows | Unique native IDs | Benchmark/time rows |
|---|---|---:|---:|---:|
| `operational_full` | `usgs_csv` | 9 | 9 | 5 |
| `operational_benchmark` | `usgs_csv` | 5 | 5 | 5 |

## Product semantics

### `operational_full`

Full UUSS/WY ComCat operational snapshot.

- Native input: `USGS_UUSS_COMCAT_2017__catalog_operational_full.csv`
- Derived output: `analysis/derived/operational_full/USGS_UUSS_COMCAT_2017__operational_full__normalized_v1.csv`
- Statistics: `analysis/stats/operational_full/`
- Figures: stats only in minimal profile

### `operational_benchmark`

Frozen UUSS/WY operational benchmark snapshot.

- Native input: `USGS_UUSS_COMCAT_2017__catalog_operational_benchmark.csv`
- Derived output: `analysis/derived/operational_benchmark/USGS_UUSS_COMCAT_2017__operational_benchmark__normalized_v1.csv`
- Statistics: `analysis/stats/operational_benchmark/`
- Figures: `analysis/figures/operational_benchmark/`

## Interpretation

Event products are summarized as event rows and unique native IDs. Phase/pick products are summarized by phase-row count, template/match IDs, station and phase composition; their row count is not an event count. The common Maple Creek mask is applied only where latitude, longitude and depth are available. Phase products retain time-only selection because they have no event coordinates.
