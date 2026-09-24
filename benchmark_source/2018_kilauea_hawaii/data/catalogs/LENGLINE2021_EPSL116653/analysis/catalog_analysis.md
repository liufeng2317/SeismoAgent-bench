# LENGLINE2021_EPSL116653 catalog-local analysis

Relative-coordinate dike-propagation detections. Spatial mask is intentionally not applied.

- Parser version: `kilauea-local-v2-compact`
- Benchmark window: `[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; outputs below are reproducible derived artifacts.

## Product summary

| Product | Kind | Full rows | Unique native IDs | Benchmark/time rows |
|---|---|---:|---:|---:|
| `relative_events` | `lengline` | 6327 | n/a | 6049 |

## Product semantics

### `relative_events`

Relative x/y/time dike-propagation detections; no universal depth, magnitude or event ID.

- Native input: `raw/loc_events.txt`
- Derived output: `analysis/derived/relative_events/LENGLINE2021_EPSL116653__relative_events__normalized_v1.csv`
- Schema: `docs/schemas/catalog_relative_event.schema.yaml`
- Statistics: `analysis/stats/relative_events/`
- Figures: `analysis/figures/relative_events/`

## Interpretation

Event products are summarized as event rows and unique native IDs. Phase/pick products are summarized by phase-row count, template/match IDs, station and phase composition; their row count is not an event count. The common summit mask is applied only where latitude, longitude and depth are available. Relative-coordinate products retain native coordinates and use time-only selection.
