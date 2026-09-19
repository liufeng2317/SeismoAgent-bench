# Official operational catalog snapshot

- `source_ref`: `USGS_TUL_COMCAT_2011`
- Provider: USGS ANSS ComCat
- Network/source: OGS/ANSS operational baseline
- Role: Q3 official operational baseline; not a high-resolution truth catalog.
- Query strategy: `daily chunks; 2011-11-04T00:00:00 to 2011-12-06T00:00:00`
- Downloaded UTC: 2026-09-19T16:42:23+00:00
- Returned data rows: 71
- Full snapshot: `USGS_TUL_COMCAT_2011__catalog_operational_full.csv` (published study span)
- Frozen-window snapshot: `USGS_TUL_COMCAT_2011__catalog_operational_benchmark.csv` (11 rows)
- Exact full and benchmark filters are versioned in `scripts/official_baseline_windows.json`.
- Service fields and rows are preserved; time chunks are merged and de-duplicated by stable event ID.
