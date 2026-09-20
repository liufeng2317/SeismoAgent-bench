# USGS_TUL_COMCAT_2011 catalog-local analysis

Official operational baseline; full and frozen benchmark snapshots are separate products.

- Parser version: `prague-local-v1-compact`
- Benchmark window: `[2011-11-11T00:00:00Z, 2011-11-19T00:00:00Z)`
- Plot profile: minimal, benchmark-first, PNG-only; use `--full-plots` for optional diagnostics.
- Raw files are unchanged; event, phase and baseline products remain separate.

## Product summary

| Product | Kind | Full rows | Unique event IDs | Frozen selection |
|---|---|---:|---:|---:|
| `operational_full` | `usgs_csv` | 71 | 71 | 11 |
| `operational_benchmark` | `usgs_csv` | 11 | 11 | 11 |

## Product semantics

### `operational_full`

Full OGS/ANSS ComCat operational snapshot.

- Native input: `USGS_TUL_COMCAT_2011__catalog_operational_full.csv`
- Derived output: `analysis/derived/operational_full/USGS_TUL_COMCAT_2011__operational_full__normalized_v1.csv`
- Statistics: `analysis/stats/operational_full/`
- Figures: stats only in minimal profile

### `operational_benchmark`

Frozen official operational benchmark snapshot.

- Native input: `USGS_TUL_COMCAT_2011__catalog_operational_benchmark.csv`
- Derived output: `analysis/derived/operational_benchmark/USGS_TUL_COMCAT_2011__operational_benchmark__normalized_v1.csv`
- Statistics: `analysis/stats/operational_benchmark/`
- Figures: `analysis/figures/operational_benchmark/`

## Interpretation

Cochran, McMahon, Isken and ComCat are separate reference populations. McMahon P rows are pick-level observations and use parent E-record origin time for the frozen selection because the distributed P schema omits an hour token; the raw phase tokens are retained unchanged. Isken is a sparse manual relocation anchor, not a completeness catalog. Magnitude types remain source-native or unresolved.
