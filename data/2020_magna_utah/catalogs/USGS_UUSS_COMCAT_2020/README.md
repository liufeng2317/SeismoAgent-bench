# Official operational catalog snapshot

- `source_ref`: `USGS_UUSS_COMCAT_2020`
- Provider: USGS ANSS ComCat
- Network/source: UUSS operational baseline via ComCat
- Role: Q3 official operational baseline; not a high-resolution truth catalog.
- Query strategy: `30-day chunks; 2020-03-18T00:00:00 to 2020-05-02T00:00:00`
- Downloaded UTC: 2026-09-19T16:46:52+00:00
- Returned data rows: 2078
- Full snapshot: `USGS_UUSS_COMCAT_2020__catalog_operational_full.csv` (2,078 rows, 2020-03-18–05-02)
- Frozen-window snapshot: `USGS_UUSS_COMCAT_2020__catalog_operational_benchmark.csv` (1,432 rows)
- Exact full and benchmark filters are versioned in `scripts/00_catalog_downloading/official_baseline_windows.json`.
- Service fields and rows are preserved; time chunks are merged and de-duplicated by stable event ID.
