# Official operational catalog snapshot

- `source_ref`: `USGS_SCSN_COMCAT_2019`
- Provider: USGS ANSS ComCat
- Network/source: SCSN/CI operational baseline via ComCat
- Role: Q3 official operational baseline; not a high-resolution truth catalog.
- Query strategy: `30-day chunks; 2019-07-04T00:00:00 to 2019-07-17T00:00:00`
- Downloaded UTC: 2026-09-19T16:46:43+00:00
- Returned data rows: 17959
- Full snapshot: `USGS_SCSN_COMCAT_2019__catalog_operational_full.csv` (17,959 rows, 2019-07-04–07-17)
- Frozen-window snapshot: `USGS_SCSN_COMCAT_2019__catalog_operational_benchmark.csv` (6,566 rows)
- Exact full and benchmark filters are versioned in `scripts/official_baseline_windows.json`.
- Service fields and rows are preserved; time chunks are merged and de-duplicated by stable event ID.
