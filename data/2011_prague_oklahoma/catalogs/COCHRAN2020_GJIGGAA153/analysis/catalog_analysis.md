# COCHRAN2020_GJIGGAA153 catalog-local analysis

Primary enhanced-detection and relative-location event product; canonical window counts and rounded common-mask counts remain separate.

- Parser version: `prague-local-v1-compact`
- Benchmark window: `[2011-11-11T00:00:00Z, 2011-11-19T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; event, phase and baseline products remain separate.

## Product summary

| Product | Kind | Full rows | Unique event IDs | Frozen selection |
|---|---|---:|---:|---:|
| `events_primary` | `cochran_event` | 8811 | 8811 | 2076 |

## Product semantics

### `events_primary`

Cochran extended template-matched event catalog; magnitude type remains unresolved.

- Native input: `COCHRAN2020_GJIGGAA153__catalog_primary.txt`
- Derived output: `analysis/derived/events_primary/COCHRAN2020_GJIGGAA153__events_primary__normalized_v1.csv`
- Statistics: `analysis/stats/events_primary/`
- Figures: `analysis/figures/events_primary/`

## Interpretation

Cochran, McMahon, Isken and ComCat are separate reference populations. McMahon P rows are pick-level observations and use parent E-record origin time for the frozen selection because the distributed P schema omits an hour token; the raw phase tokens are retained unchanged. Isken is a sparse manual relocation anchor, not a completeness catalog. Magnitude types remain source-native or unresolved.
