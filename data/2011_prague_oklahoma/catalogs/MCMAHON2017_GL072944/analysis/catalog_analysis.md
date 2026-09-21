# MCMAHON2017_GL072944 catalog-local analysis

Independent subspace-detection/Bayesloc event and phase products; E and P records are analyzed separately.

- Parser version: `prague-local-v1-compact`
- Benchmark window: `[2011-11-11T00:00:00Z, 2011-11-19T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; event, phase and baseline products remain separate.

## Product summary

| Product | Kind | Full rows | Unique event IDs | Frozen selection |
|---|---|---:|---:|---:|
| `events_subspace` | `mcmahon_event` | 5446 | 5446 | 2328 |
| `phase_arrivals` | `mcmahon_phase` | 82537 | 5446 | 37171 |

## Product semantics

### `events_subspace`

McMahon subspace/Bayesloc E-record event catalog.

- Native input: `raw/MCMAHON2017_GL072944__catalog_subspace_5446events.txt`
- Derived output: `analysis/derived/events_subspace/MCMAHON2017_GL072944__events_subspace__normalized_v1.csv`
- Schema: `docs/schemas/catalog_event.schema.yaml`
- Statistics: `analysis/stats/events_subspace/`
- Figures: `analysis/figures/events_subspace/`

### `phase_arrivals`

McMahon P-record phase observations; row count is not an event count and release timestamps omit hour.

- Native input: `raw/MCMAHON2017_GL072944__catalog_subspace_5446events.txt`
- Derived output: `phase sample only; raw phase table is retained`
- Schema: `docs/schemas/catalog_parent_phase.schema.yaml`
- Statistics: `analysis/stats/phase_arrivals/`
- Figures: `analysis/figures/phase_arrivals/`

## Interpretation

Cochran, McMahon, Isken and ComCat are separate reference populations. McMahon P rows are pick-level observations and use parent E-record origin time for the frozen selection because the distributed P schema omits an hour token; the raw phase tokens are retained unchanged. Isken is a sparse manual relocation anchor, not a completeness catalog. Magnitude types remain source-native or unresolved.
