# USGS_SCSN_COMCAT_2019 — official operational baseline audit

## Provenance and query

| Field | Value |
|---|---|
| Provider | USGS ANSS ComCat |
| Operational source | Southern California Seismic Network (`CI`) via ComCat |
| Service | [`https://earthquake.usgs.gov/fdsnws/event/1/query`](https://earthquake.usgs.gov/fdsnws/event/1/query) |
| Configuration | [`scripts/00_catalog_downloading/official_baseline_windows.json`](../../../../scripts/00_catalog_downloading/official_baseline_windows.json), `2019_ridgecrest_california` entry |
| Download timestamp | 2026-09-19T16:46:43Z (directory README) |
| Role | Q3 official operational baseline; not a high-resolution truth catalog |

The full snapshot uses `2019-07-04T00:00:00` to `2019-07-17T00:00:00`,
latitude 35.45–36.05°N, longitude −117.95–−117.20°E, and depth 0–20 km.
The frozen benchmark is `2019-07-04T00:00:00Z <= time < 2019-07-07T00:00:00Z`,
latitude 35.45–36.05°N, longitude −117.90–−117.20°E, and depth 0–20 km.
Thirty-day chunks were merged and de-duplicated by stable event ID.

## Files and integrity

| Snapshot | File | Rows | Unique `id` | SHA-256 |
|---|---|---:|---:|---|
| Full | [`USGS_SCSN_COMCAT_2019__catalog_operational_full.csv`](./USGS_SCSN_COMCAT_2019__catalog_operational_full.csv) | 17,959 | 17,959 | `c1c61e21b7c7cf687566cfcb4ccf92120f47a78fa36ddfcb4349316ee0b82db5` |
| Benchmark | [`USGS_SCSN_COMCAT_2019__catalog_operational_benchmark.csv`](./USGS_SCSN_COMCAT_2019__catalog_operational_benchmark.csv) | 6,566 | 6,566 | `2e6f472c88874431042138c468d91259156213e70d0126205ca55ac25c35036e` |

The ComCat service fields are preserved.  IDs and timestamps are unique and
valid in both snapshots.  One full-snapshot row has an empty magnitude field;
the benchmark has no missing magnitude values.

## Local audit

| Selection | Time (observed UTC) | Latitude | Longitude | Depth (km) | Magnitude | Magnitude types | Status / type |
|---|---|---|---|---|---|---|---|
| Full | 2019-07-04T04:03:01.480Z – 2019-07-16T23:58:52.910Z | 35.47817–36.05°N | −117.94567–−117.204°E | 0.0–19.98 | 0.0–7.1 (one missing) | ml 17,605; mlr 235; mw 103; mh 15; missing 1 | automatic 9,255; reviewed 8,704; earthquake 17,956; quarry blast 3 |
| Frozen benchmark | 2019-07-04T04:03:01.480Z – 2019-07-06T23:59:47.120Z | 35.4935–36.0495°N | −117.89117–−117.268°E | 0.0–19.09 | 0.14–7.1 | ml 6,289; mlr 223; mw 52; mh 2 | all reviewed; earthquake 6,564; quarry blast 2 |

The full snapshot contains 17,956 `ci` and 3 `us` network rows; one event is
located by `us`.  The benchmark has 6,564 `ci` and 2 `us` rows.  Preserve the
quarry-blast event types rather than silently treating all rows as earthquakes.

## Q3 role and limitations

- Use as the official SCSN/CI operational baseline for event-ID, origin-time,
  and routine-location comparison with Shelly, Ross, Liu, and AWR products.
- Do **not** use it as the primary high-resolution Ridgecrest catalog or as a
  completeness truth set.  Research products include matched-filter and
  relative-relocation events below routine reporting thresholds.
- The full snapshot includes automatic solutions, mixed `ci`/`us` sources, and
  three quarry blasts; the frozen benchmark is all reviewed but still retains
  two quarry blasts.  Filter by `type` explicitly for earthquake-only analyses.
- Magnitude scales (`ml`, `mlr`, `mw`, `mh`) and later ComCat revisions should
  remain source-native.  Keep query parameters, download timestamp, and both
  checksums with every benchmark run.
