# SHELLY2019_GL085636 catalog-local analysis

Primary summit event products plus a large phase-arrival auxiliary. S1, S2 and phase rows are never merged.

- Parser version: `kilauea-local-v2-compact`
- Benchmark window: `[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; outputs below are reproducible derived artifacts.

## Product summary

| Product | Kind | Full rows | Unique native IDs | Benchmark/time rows |
|---|---|---:|---:|---:|
| `events_s1` | `shelly_s1` | 44188 | 44188 | 1883 |
| `events_s2` | `shelly_s2` | 43950 | 43950 | 1877 |
| `phase_arrivals` | `phase_csv` | 8582492 | n/a | 156319 |

## Product semantics

### `events_s1`

Shelly high-resolution hypocentroid product S1.

- Native input: `SHELLY2019_GL085636__catalog_S1.txt`
- Derived output: `analysis/derived/events_s1/SHELLY2019_GL085636__events_s1__normalized_v1.csv`
- Statistics: `analysis/stats/events_s1/`
- Figures: `analysis/figures/events_s1/`

### `events_s2`

Shelly polarity-cluster product S2; separate event table.

- Native input: `SHELLY2019_GL085636__catalog_S2.txt`
- Derived output: `analysis/derived/events_s2/SHELLY2019_GL085636__events_s2__normalized_v1.csv`
- Statistics: `analysis/stats/events_s2/`
- Figures: `analysis/figures/events_s2/`

### `phase_arrivals`

USGS correlation-derived phase arrivals; template_id and match_id are not event IDs.

- Native input: `raw/Kilauea_2018_correlation_phase_arrivals.csv`
- Derived output: `phase sample only; raw phase table is retained`
- Statistics: `analysis/stats/phase_arrivals/`
- Figures: `analysis/figures/phase_arrivals/`

## Interpretation

Event products are summarized as event rows and unique native IDs. Phase/pick products are summarized by phase-row count, template/match IDs, station and phase composition; their row count is not an event count. The common summit mask is applied only where latitude, longitude and depth are available. Relative-coordinate products retain native coordinates and use time-only selection.
