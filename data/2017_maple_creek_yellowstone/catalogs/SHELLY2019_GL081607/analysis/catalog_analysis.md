# SHELLY2019_GL081607 catalog-local analysis

Correlation-derived phase-arrival product associated with Shelly & Hardebeck (2019); event-level relocated tables are not present locally.

- Parser version: `maple-local-v1-compact`
- Benchmark window: `[2017-06-11T00:00:00Z, 2017-06-19T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; outputs below are reproducible derived artifacts.

## Product summary

| Product | Kind | Full rows | Unique native IDs | Benchmark/time rows |
|---|---|---:|---:|---:|
| `phase_arrivals` | `phase_csv` | 6260580 | n/a | 1591090 |

## Product semantics

### `phase_arrivals`

Shelly/USGS correlation-derived phase arrivals; match_id and template_id are not located event IDs.

- Native input: `raw/Yellowstone_2017_correlation_phase_arrivals.csv`
- Derived output: `phase sample only; raw phase table is retained`
- Statistics: `analysis/stats/phase_arrivals/`
- Figures: `analysis/figures/phase_arrivals/`

## Interpretation

Event products are summarized as event rows and unique native IDs. Phase/pick products are summarized by phase-row count, template/match IDs, station and phase composition; their row count is not an event count. The common Maple Creek mask is applied only where latitude, longitude and depth are available. Phase products retain time-only selection because they have no event coordinates.
