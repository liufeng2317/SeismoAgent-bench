# ISKEN2017_BSSA0120160150 catalog-local analysis

Sparse manual relocation anchor for event-by-event location and structural checks.

- Parser version: `prague-local-v1-compact`
- Benchmark window: `[2011-11-11T00:00:00Z, 2011-11-19T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; event, phase and baseline products remain separate.

## Product summary

| Product | Kind | Full rows | Unique event IDs | Frozen selection |
|---|---|---:|---:|---:|
| `events_relocated` | `isken_event` | 13 | 13 | 5 |

## Product semantics

### `events_relocated`

Sparse manually selected Table S3 relocations; high-quality location anchor, not a completeness catalog.

- Native input: `ISKEN2017_BSSA0120160150__catalog_relocated_tableS3.csv`
- Derived output: `analysis/derived/events_relocated/ISKEN2017_BSSA0120160150__events_relocated__normalized_v1.csv`
- Schema: `docs/schemas/catalog_event.schema.yaml`
- Statistics: `analysis/stats/events_relocated/`
- Figures: `analysis/figures/events_relocated/`

## Interpretation

Cochran, McMahon, Isken and ComCat are separate reference populations. McMahon P rows are pick-level observations and use parent E-record origin time for the frozen selection because the distributed P schema omits an hour token; the raw phase tokens are retained unchanged. Isken is a sparse manual relocation anchor, not a completeness catalog. Magnitude types remain source-native or unresolved.
