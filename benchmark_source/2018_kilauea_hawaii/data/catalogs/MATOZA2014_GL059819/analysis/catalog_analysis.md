# MATOZA2014_GL059819 catalog-local analysis

Historical LP event product, retained as auxiliary context rather than a 2018 denominator.

- Parser version: `kilauea-local-v2-compact`
- Benchmark window: `[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; outputs below are reproducible derived artifacts.

## Product summary

| Product | Kind | Full rows | Unique native IDs | Benchmark/time rows |
|---|---|---:|---:|---:|
| `lp_events` | `matoza14` | 12290 | 12290 | n/a |

## Product semantics

### `lp_events`

Historical LP summit catalog, 1986–2009; no 2018 benchmark overlap.

- Native input: `MATOZA2014_GL059819__catalog_lp_summit.txt`
- Derived output: `analysis/derived/lp_events/MATOZA2014_GL059819__lp_events__normalized_v1.csv`
- Schema: `docs/schemas/catalog_event.schema.yaml`
- Statistics: `analysis/stats/lp_events/`
- Figures: stats only in minimal profile

## Interpretation

Event products are summarized as event rows and unique native IDs. Phase/pick products are summarized by phase-row count, template/match IDs, station and phase composition; their row count is not an event count. The common summit mask is applied only where latitude, longitude and depth are available. Relative-coordinate products retain native coordinates and use time-only selection.
