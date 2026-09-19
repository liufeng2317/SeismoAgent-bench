# Official operational catalog snapshot

- `source_ref`: `USGS_UUSS_COMCAT_2017`
- Provider: USGS ANSS ComCat
- Network/source: UUSS/WY operational baseline via ComCat
- Role: Q3 official operational baseline; not a high-resolution truth catalog.
- Query strategy: `30-day chunks; 2017-06-11T00:00:00 to 2017-09-15T00:00:00`
- Downloaded UTC: 2026-09-19T16:46:14+00:00
- Returned data rows: 9
- Full snapshot: `USGS_UUSS_COMCAT_2017__catalog_operational_full.csv` (published scan span)
- Frozen-window snapshot: `USGS_UUSS_COMCAT_2017__catalog_operational_benchmark.csv` (5 rows)
- Exact full and benchmark filters are versioned in `scripts/official_baseline_windows.json`.
- Service fields and rows are preserved; time chunks are merged and de-duplicated by stable event ID.
