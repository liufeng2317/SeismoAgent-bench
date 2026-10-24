# Official operational catalog snapshot

- `source_ref`: `USGS_UUSS_COMCAT_2017`
- Provider: USGS ANSS ComCat
- Network/source: UUSS/WY operational baseline via ComCat
- Role: Q3 official operational baseline; not a high-resolution truth catalog.
- Query strategy: `30-day chunks; 2017-06-11T00:00:00 to 2017-09-15T00:00:00`
- Time range (half-open): `2017-06-11T00:00:00` to `2017-09-15T00:00:00`
- Latitude: 44.7 to 44.84
- Longitude: -111.13 to -110.93
- Depth: -3 to 20 km
- Downloaded UTC: 2026-10-22T13:26:41+00:00
- Returned data rows: 2447
- Spatial and temporal filters are encoded in the query URL.
- Service fields and rows are preserved; time chunks are merged and de-duplicated by stable event ID.

## Snapshots (2026-10-22)

- Benchmark window 2017-06-11 → 06-19: `USGS_UUSS_COMCAT_2017__catalog_operational_benchmark.csv`, 626 rows, SHA-256 `6e3b1b935218637fc52db27e078202d410cd3911f086d64532bc75aca2f4de25`.
- Full span 2017-06-11 → 09-15: `USGS_UUSS_COMCAT_2017__catalog_operational_full.csv`, 2,447 rows, SHA-256 `ddf8b480e25be4716541a1a95e9e75968bdf02026601c8322961b47e3c53b887`.
- All rows network uu, status reviewed. Benchmark: M −0.5 to 4.36 (the Mw 4.4 anchor uu60203137 is included), depth median 7.5 km.

The query box was corrected on 2026-10-22. The earlier box (44.45–44.75 N, 110.55–110.15 W, 0–15 km) lay ~40 km east of the swarm and returned 5 unrelated events. The new box is the swarm footprint (events within 8 km of the Mw 4.4 epicentre span 44.729–44.808 N, 111.100–110.961 W) plus ~3 km. It excludes a separate cluster ~18 km east (~110.80 W, 51 events in the window), which is not part of the Maple Creek sequence. Depth limits are loose (−3 to 20 km) so that datum conventions never remove events; UUSS depths are below the local surface (see `data/models/velocity_models.json`).
