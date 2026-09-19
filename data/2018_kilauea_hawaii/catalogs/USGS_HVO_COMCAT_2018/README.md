# Official operational catalog snapshot

- `source_ref`: `USGS_HVO_COMCAT_2018`
- Provider: USGS ComCat / HVO
- Network/source: HV operational baseline
- Role: Q3 official operational baseline; not a high-resolution truth catalog.
- Query strategy: `30-day chunks; 2018-04-29T00:00:00 to 2018-08-07T00:00:00`
- Downloaded UTC: 2026-09-19T16:46:55+00:00
- Returned data rows: 40095
- Full snapshot: `USGS_HVO_COMCAT_2018__catalog_operational_full.csv` (40,095 rows, 2018-04-29–08-07)
- Frozen-window snapshot: `USGS_HVO_COMCAT_2018__catalog_operational_benchmark.csv` (496 rows)
- Exact full and benchmark filters are versioned in `scripts/official_baseline_windows.json`.
- Service fields and rows are preserved; time chunks are merged and de-duplicated by stable event ID.
