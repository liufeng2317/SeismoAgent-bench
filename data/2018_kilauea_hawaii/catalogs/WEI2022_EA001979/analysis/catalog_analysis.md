# WEI2022_EA001979 catalog-local analysis

Broader onshore/offshore event catalog. Magnitude-available and all-row populations remain separate.

- Parser version: `kilauea-local-v2-compact`
- Benchmark window: `[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; outputs below are reproducible derived artifacts.

## Product summary

| Product | Kind | Full rows | Unique native IDs | Benchmark/time rows |
|---|---|---:|---:|---:|
| `events_s1` | `wei` | 375736 | n/a | 2369 |

## Product semantics

### `events_s1`

Wei combined onshore/offshore event rows; native release has no stable event ID.

- Native input: `WEI2022_EA001979__catalog_S1.txt`
- Derived output: `analysis/derived/events_s1/WEI2022_EA001979__events_s1__normalized_v1.csv`
- Statistics: `analysis/stats/events_s1/`
- Figures: `analysis/figures/events_s1/`

## Interpretation

Event products are summarized as event rows and unique native IDs. Phase/pick products are summarized by phase-row count, template/match IDs, station and phase composition; their row count is not an event count. The common summit mask is applied only where latitude, longitude and depth are available. Relative-coordinate products retain native coordinates and use time-only selection.
