# SHELLY2019_GL085636 — catalog summary and reproducible audit

## Provenance and products

- Source article: Shelly & Thelen (2019), DOI [10.1029/2019GL085636](https://doi.org/10.1029/2019GL085636).
- USGS data release: [10.5066/P9DMIFMW](https://doi.org/10.5066/P9DMIFMW), metadata publication date 2020-01-03.
- Canonical event products:
  - `SHELLY2019_GL085636__catalog_S1.txt`: high-resolution hypocentroid catalog;
  - `SHELLY2019_GL085636__catalog_S2.txt`: same event family with correlation-derived polarity-cluster number.
- Pick-level auxiliary product: `raw/Kilauea_2018_correlation_phase_arrivals.csv` from USGS ScienceBase release [10.5066/P13JCJ2I](https://doi.org/10.5066/P13JCJ2I). It is not interchangeable with S1/S2.
- Article Figure SI is kept under the reference supplement; raw header/metadata files remain under `raw/`.

## Checksums and native formats

| File | Rows | SHA-256 | Role |
|---|---:|---|---|
| `SHELLY2019_GL085636__catalog_S1.txt` | 44,188 | `6868428a91ce91b04283b3776633961a6373d257edbf7eb79ea99db154ee8abf` | Canonical high-resolution event catalog |
| `SHELLY2019_GL085636__catalog_S2.txt` | 43,950 | `112b8079cbc9970b7db5b8910bad90a7b9d30e3db19161deae22fb0307d3db13` | Polarity-cluster event catalog |
| `raw/Kilauea_2018_correlation_phase_arrivals.csv` | 8,582,492 | `be6bab5bca8dff5355d763495ac2f9a5c54d157f80b0f315095e3d3caf1d8dc4` | Auxiliary P/S arrival rows; local-only |

S1 has 14 whitespace-delimited fields (`year month day hour minute second
lat lon depth x y z magnitude eventID`); S2 has 12 fields, adding a leading
`cluster#` and omitting x/y/z. The raw header files document the same formats.
The event IDs are Shelly/USGS local identifiers and are explicitly not HVO IDs.

- `depth` is in kilometres below the Kīlauea summit datum, nominally 1.2 km
above sea level; negative values are valid source values and are not silently
clipped.
- S1 and S2 have unique event IDs and no exact duplicate rows.
- S2's 43,950 IDs are a subset of S1's 44,188 IDs; 238 S1 events have no
polarity-cluster row. On shared IDs, S2 rounds latitude/longitude but retains the
same depth and magnitude.

## Full-file audit

| Field | S1 | S2 / auxiliary |
|---|---:|---:|
| Rows / unique event IDs | 44,188 / 44,188 | 43,950 / 43,950 |
| Origin time | 2018-04-29 01:24:11.320 to 2018-08-06 23:54:33.800 UTC | same event span |
| Latitude | 19.329439–19.469961°N | 19.32944–19.46996°N |
| Longitude | −155.365674–−155.193571°E | −155.36567–−155.19357°E |
| Depth | −0.729–27.3 km | −0.729–27.3 km |
| Magnitude | −1.17–5.4; no missing values | −1.17–5.4; no missing values |
| Negative summit-referenced depths | 254 | 253 |
| Polarity clusters | not present | 50 labels; cluster 1 has 8,383 rows (largest) |
| Phase-arrival rows | — | 8,582,492: 7,460,986 P + 1,121,506 S |
| Phase CSV stations/network | — | 25 unique stations, all `HV` in local release |
| Phase CSV time span | — | 2018-04-29 00:27:50.5581–2018-08-06 23:55:36.9803 UTC |

The phase CSV has `template_id`, `match_id`, `network`, `station`, `phase`,
`arrival`, `weight`, `mag`, `ccmax`, `ccdiff`, and `chanloc`. It is a many-row
phase product, so its row count must not be compared directly to event counts.

## Frozen summit benchmark mask

Case rule:

```text
2018-05-01T00:00:00Z <= origin_time < 2018-05-09T00:00:00Z
19.30 <= latitude <= 19.50
-155.40 <= longitude <= -155.15
0 <= depth_km <= 20
```

| Product | Time-only rows | Common-mask rows | Time range in time-only selection |
|---|---:|---:|---|
| S1 | 1,902 | **1,883** | 2018-05-01 00:13:40.880–2018-05-08 23:56:20.560 UTC |
| S2 | 1,896 | **1,877** | 2018-05-01 00:13:40.880–2018-05-08 23:56:20.560 UTC |

The common mask removes 19 S1 rows and 19 S2 rows, mostly because of negative
summit-referenced depth or the explicit spatial/depth boundary. These are
comparison rules, not a claim that every excluded source is physically invalid.

## Benchmark role and limitations

- **Quality tier:** Q1 relative-location/geometry reference for retained events;
Q2 dense detection/completeness reference within the summit network condition.
- **Best use:** high-rate event recovery, relative hypocentroid geometry,
polarity-cluster structure, and sequence-rate response conditional on network
availability.
- **Not a universal truth catalog:** HVO template dependence, changing run
conditions, approximate magnitudes, and summit-referenced depths limit absolute
and cross-domain comparisons.
- **Alignment verdict:** S1/S2 and the article headline (44,188 events,
2,823 templates, 10P+10S retention) are aligned. The phase CSV is an aligned
auxiliary pick release, not the article's event table; use separate metrics.

## Local outputs

- Paper reading: `../../references/SHELLY2019_GL085636/paper/SHELLY2019_GL085636__paper_reading.md`
- Case synthesis: `../../analysis/KILAUEA2018_analysis.md`
- Future plots should be written under a dedicated `figures/` directory or
`raw/` derivative area without modifying the source-native catalogs.
