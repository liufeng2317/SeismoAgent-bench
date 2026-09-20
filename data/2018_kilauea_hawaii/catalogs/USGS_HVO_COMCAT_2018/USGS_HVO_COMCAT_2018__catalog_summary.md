# USGS_HVO_COMCAT_2018 — official operational baseline audit

## Provenance and query

| Field | Value |
|---|---|
| Provider | USGS ComCat / Hawaiian Volcano Observatory (HVO) |
| Operational source | `HV` HVO network via ComCat |
| Service | [`https://earthquake.usgs.gov/fdsnws/event/1/query`](https://earthquake.usgs.gov/fdsnws/event/1/query) |
| Configuration | [`scripts/00_catalog_downloading/official_baseline_windows.json`](../../../../scripts/00_catalog_downloading/official_baseline_windows.json), `2018_kilauea_hawaii` entry |
| Download timestamp | 2026-09-19T16:46:55Z (directory README) |
| Role | Q3 official operational baseline; not a high-resolution truth catalog |

The full snapshot covers `2018-04-29T00:00:00` to `2018-08-07T00:00:00`,
latitude 19.30–19.50°N, longitude −155.40–−155.15°E, and depth −2 to 30 km.
The frozen benchmark is `2018-05-01T00:00:00Z <= time < 2018-05-09T00:00:00Z`,
latitude 19.30–19.50°N, longitude −155.40–−155.15°E, and depth 0–20 km.
Thirty-day chunks were merged and de-duplicated by stable event ID.

## Files and integrity

| Snapshot | File | Rows | Unique `id` | SHA-256 |
|---|---|---:|---:|---|
| Full | [`USGS_HVO_COMCAT_2018__catalog_operational_full.csv`](./USGS_HVO_COMCAT_2018__catalog_operational_full.csv) | 40,095 | 40,095 | `b80a2553a29209c5ff2c46346f599e80362ef55578ad797491a784779ea1b41c` |
| Benchmark | [`USGS_HVO_COMCAT_2018__catalog_operational_benchmark.csv`](./USGS_HVO_COMCAT_2018__catalog_operational_benchmark.csv) | 496 | 496 | `456c2e509e19b33bd3d8c342e3568dd00f5963f627714c0cb837ab7c834d29c4` |

The native ComCat CSV schema is retained, including quality/error fields and
network/source/status metadata.  No duplicate IDs or malformed timestamps were
found.

## Local audit

| Selection | Time (observed UTC) | Latitude | Longitude | Depth (km) | Magnitude | Magnitude types | Status / type |
|---|---|---|---|---|---|---|---|
| Full | 2018-04-29T05:46:18.950Z – 2018-08-06T23:54:34.050Z | 19.300–19.49817°N | −155.400–−155.150°E | −1.75–29.43 | 0.37–5.4 | ml 36,125; md 3,907; mw 62; mh 1 | reviewed 31,640; automatic 8,455; earthquake 40,032; volcanic eruption 62; chemical explosion 1 |
| Frozen benchmark | 2018-05-01T06:34:32.670Z – 2018-05-08T22:37:36.770Z | 19.30033–19.4695°N | −155.38217–−155.15833°E | 0.06–15.26 | 0.74–4.66 | ml 340; md 156 | reviewed 414; automatic 82; all earthquake |

The full snapshot has 40,079 `hv` and 16 `us` network rows; location and
magnitude sources are `hv` for 40,086 rows and `us` for 9.  The benchmark is
entirely `hv`.  These source mixes are preserved rather than recoded.

## Q3 role and limitations

- Use as the official HVO/HV operational baseline for the summit condition and
  for comparison of origin-time/location interoperability with Shelly, Wei,
  Matoza, and Lengliné products.
- Do **not** use it as a high-resolution summit truth set.  The apparent event
  rate and quality change during the eruption, and the full snapshot includes
  automatic solutions, volcanic-eruption event types, and one chemical
  explosion.
- The benchmark mask removes negative-depth and deeper/full-island records; the
  full snapshot intentionally retains them to document the acquisition span.
- Magnitudes mix `ml`, `md`, `mw`, and `mh`; station/network metadata are not a
  substitute for the changing HVO station availability used by research
  catalogs.  Preserve the retrieval timestamp because live ComCat revisions can
  change historical fields.
