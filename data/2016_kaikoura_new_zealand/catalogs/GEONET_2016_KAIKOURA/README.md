# Official operational catalog snapshot

- `source_ref`: `GEONET_2016_KAIKOURA`
- Provider: GeoNet
- Network/source: GeoNet operational baseline
- Role: Q3 official operational baseline; not a high-resolution truth catalog.
- Query strategy: `30-day chunks; 2016-11-13T00:00:00 to 2017-05-14T00:00:00`
- Downloaded UTC: 2026-09-19T16:48:25+00:00
- Returned data rows: 15948
- Exact full and benchmark filters are versioned in `scripts/00_catalog_downloading/official_baseline_windows.json`.
- Full snapshot: `GEONET_2016_KAIKOURA__catalog_operational_full.txt` (15,948 rows, 2016-11-13–2017-05-14)
- Frozen-window snapshot: `GEONET_2016_KAIKOURA__catalog_operational_benchmark.txt` (1,507 rows)
- The raw service exports are unmodified; preserve both snapshots when comparing benchmark runs.
