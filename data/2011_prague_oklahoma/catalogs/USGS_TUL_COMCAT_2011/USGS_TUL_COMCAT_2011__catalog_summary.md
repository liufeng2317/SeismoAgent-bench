# USGS_TUL_COMCAT_2011 — official operational baseline audit

## Provenance and query

| Field | Value |
|---|---|
| Provider | USGS ANSS ComCat |
| Operational source | OGS/Tulsa (`tul`) attribution through ComCat |
| Service | [`https://earthquake.usgs.gov/fdsnws/event/1/query`](https://earthquake.usgs.gov/fdsnws/event/1/query) |
| Configuration | [`scripts/00_catalog_downloading/official_baseline_windows.json`](../../../../scripts/00_catalog_downloading/official_baseline_windows.json), `2011_prague_oklahoma` entry |
| Download timestamp | 2026-09-19T16:42:23Z (directory README) |
| Role | Q3 official operational baseline; not a high-resolution truth catalog |

The full snapshot used daily chunks over `2011-11-04T00:00:00` to
`2011-12-06T00:00:00`, latitude 35.35–35.66°N, longitude −96.95–−96.53°E,
and depth 0–20 km.  The frozen benchmark query is half-open
`2011-11-11T00:00:00Z <= time < 2011-11-19T00:00:00Z`, latitude
35.4523–35.5576°N, longitude −96.8723–−96.7334°E, and depth 0–20 km.

## Files and integrity

| Snapshot | File | Rows | Unique `id` | SHA-256 |
|---|---|---:|---:|---|
| Full | [`USGS_TUL_COMCAT_2011__catalog_operational_full.csv`](./USGS_TUL_COMCAT_2011__catalog_operational_full.csv) | 71 | 71 | `7a89e367f2296a8e5cd8abe99e86756dc041f600010a9306c3097c133d8d6c0c` |
| Benchmark | [`USGS_TUL_COMCAT_2011__catalog_operational_benchmark.csv`](./USGS_TUL_COMCAT_2011__catalog_operational_benchmark.csv) | 11 | 11 | `4a3edd5fd565aaa55a6ddbb2fc0e71189d6a0007af6bbd648dc292a4432932e9` |

The ComCat CSV header and service fields are preserved.  There are no duplicate
IDs or malformed timestamps in either snapshot.

## Local audit

| Selection | Time (observed UTC) | Latitude | Longitude | Depth (km) | Magnitude | Magnitude types | Source/status |
|---|---|---|---|---|---|---|---|
| Full | 2011-11-05T07:12:45Z – 2011-12-03T05:05:08Z | 35.454–35.604°N | −96.887–−96.730°E | 0.1–9.3 | 1.4–5.7 | ml 44, mwr 9, md 9, mblg 8, mww 1 | `us` network; reviewed; location `tul` 64 / `us` 7 |
| Frozen benchmark | 2011-11-11T19:19:16Z – 2011-11-18T07:41:08Z | 35.464–35.543°N | −96.869–−96.752°E | 3.1–7.4 | 2.2–3.3 | ml 10, md 1 | `us` network; all reviewed; location/magnitude source `tul` |

Native fields include origin time, latitude/longitude/depth, magnitude and
magnitude type, network/event ID, update time, quality fields (`nst`, `gap`,
`dmin`, `rms`, errors), and source/status attributes.  This release contains
only earthquake-type rows.

## Q3 role and limitations

- Use as a reproducible operational anchor for the Prague window, event-ID
  interoperability, and conservative routine-catalog recovery.
- Do **not** use it as the primary Cochran/McMahon event population or as a
  completeness estimate.  The 11-row benchmark snapshot is much smaller than
  the enhanced research catalogs because ComCat reflects routine reporting and
  the exact OGS/ANSS source attribution.
- Magnitude scales are mixed (`ml`, `md`, `mblg`, `mwr`, `mww`); compare source
  native values or harmonize explicitly.
- Keep the query mask, retrieval timestamp, update fields, and checksums with
  every scoring run.  The snapshot is a historical export and can differ from
  a future live ComCat response.
