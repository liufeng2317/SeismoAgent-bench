# TAN2024_JB028735 — SUGAR catalog summary and reproducible audit

## Provenance and release lineage

- Source article: Tan et al. (2024), DOI [10.1029/2024JB028735](https://doi.org/10.1029/2024JB028735).
- Table S10 is the detected/located SUGAR catalog (67,660 rows).
- Table S11 is the released GrowClust-relocated subset (46,440 rows). The paper's
  final cluster-size-filtered count is 41,392, but a separate 41,392-row file is
  not present locally.
- Tables S09 and S12 are station and focal-mechanism auxiliaries, respectively.
- The Zenodo phase archive is preserved separately from the event tables.

## Checksums and native formats

| File | Native role | Rows / entries | SHA-256 |
|---|---|---:|---|
| `TAN2024_JB028735__catalog_sugar_S10.xlsx` | Table S10 event catalog | 67,660 data rows; header `A1:K67661` | `56ab37e5bf3f90f61d2b48512e780a1f3cc6cda3d35de3a548dcdc8d5daa10ac` |
| `TAN2024_JB028735__catalog_sugar_relocated_S11.xlsx` | Table S11 GrowClust relocations | 46,440 data rows; header `A1:M46441` | `02c2d9a1d1e53537c20bc376248194780ea92883a15e04ebad454fbed1677020` |
| `TAN2024_JB028735__phases_associated.zip` | Associated phase archive | 1,165 `.dat` files (1,172 ZIP entries including dirs/metadata) | `30a3b6bf86be10957a6fe774e7c4c84655361d66d13b6a9b24ac67b99db88504` |
| `2024jb028735-sup-0002-table si-s09.xlsx` | Table S09 station inventory | 46 stations | `60398cef624c361bcad8c79b9799b4655456967e2afcd4a294b93aaca739e6e8` |
| `2024jb028735-sup-0005-table si-s12.xlsx` | Table S12 focal mechanisms | 55 solutions | `f6919107aba081183b7613f7ed913b9c99ea2eaa7f4d8533121615793956720a` |

S10 and S11 are also retained under the reference supplement with identical
checksums; the catalog directory is the canonical working location.

## Schema and full-file audit

### S10 — SUGAR detections

Columns are `Time`, `Lat`, `Lon`, `Dep`, `M`, `Picks`, `AI score`, `Brightness`,
`Q`, `Residual`, and `ID`. The local audit finds:

- 67,660 rows, 67,660 unique IDs, zero exact duplicate rows;
- time `2016-11-13T11:02:56.346094Z` to `2016-12-31T23:59:15.180000Z`;
- latitude −43.420057 to −41.218655°, longitude 172.015873 to 175.133776°;
- depth 0–60 km; magnitude −0.56 to 7.82;
- picks 4–1,000; AI score 0–46,773.46; brightness 0–46,773.46;
  Q 0–1; residual 0–3.962 (native units);
- no blank cells in the 10 numeric/string columns under the local XML audit.

The ID is stable within S10 and links all 46,440 S11 rows; it is not an
external GeoNet event identifier.

### S11 — GrowClust relocations

Columns are `year`, `month`, `day`, `hour`, `minute`, `second`, `id`,
`latRelocate`, `lonRelocate`, `depRelocate`, `magnitude`, `cluster id`, and
`events in cluster`. The local audit finds:

- 46,440 rows, 46,440 unique IDs, zero duplicate rows;
- every S11 ID is present in S10; 21,220 S10 detections have no S11 relocation;
- time `2016-11-13T11:05:14.450Z` to `2016-12-31T23:52:52.789Z`;
- relocated latitude −43.157440 to −41.360050°, longitude 172.276050 to
  175.048500°;
- relocated depth −1.556 to 60.714 km; magnitude −0.56 to 5.37;
- 2,152 cluster IDs; cluster sizes in the local table range from 2 to 2,841.

The article's final 41,392 count corresponds to retaining clusters with at least
10 events. Recompute that filter from the cluster fields if exact membership is
needed; do not infer it from row order.

## Associated phase archive and auxiliaries

The extracted archive contains 1,165 `.dat` files (plus `.DS_Store` and
`__MACOSX` metadata entries in the ZIP), 1,382,337 phase rows, 68,462 distinct
phase-file event IDs, and 45 station codes. Phase counts are 679,865 `Pg` and
702,472 `Sg`; this is a pick-level product, not another event catalog. Table S09
lists 46 GeoNet stations, so the difference between 45 phase stations and 46
inventory rows is retained rather than silently filled.

Table S12 contains 55 focal-mechanism solutions with columns `Time`, `Lat`,
`Lon`, `Dep`, `Strike`, `Dip`, `Rake`, and `M`, matching the paper's 12 M>4 plus
43 smaller-event additions. Table S09 contains `net`, `sta`, latitude,
longitude, vertical/east/north channel codes, and elevation; all 46 rows have
network label `geonet`.

## Frozen Kaikōura benchmark mask

```text
2016-12-01T00:00:00Z <= origin_time < 2016-12-09T00:00:00Z
-43.5 <= latitude <= -41.2
172.0 <= longitude <= 175.2
0 <= depth_km <= 60
```

| Product | Time-only rows | Common-mask rows | Time-only ranges (lat/lon/depth/M) |
|---|---:|---:|---|
| S10 | 9,720 | **9,720** | −43.420057–−41.218655 / 172.032762–175.133776 / 0–60 / −0.53–4.87 |
| S11 | 6,973 | **6,955** | −43.157440–−41.490090 / 172.325240–174.692110 / −1.556–59.641 / −0.53–4.87 |

S11 common-mask ranges after excluding the 18 out-of-mask rows are lat
−43.157440–−41.490090, lon 172.325240–174.692110, depth 0.008–59.641 km,
and magnitude −0.53–4.87. The magnitude column is retained in its native scale;
no conversion to ML/Mw is applied here.

## Benchmark role and limitations

- **Quality tier:** Q2 dense detection and relative relocation; metric-specific
  Q1 for the reported clustered relative geometry only.
- **Best use:** high-rate detection/association, event separation in overlapping
  waveforms, and comparison of relative spatial structure.
- **Not universal truth:** SUGAR is site/network specific, uses a fixed-depth
  initial scan, has larger depth errors near the shallow/deep edges, and
  manually inserts the mainshock/largest aftershock. S11 is an intermediate
  released product, not the final 41,392-row cluster-filtered set.
- **Alignment verdict:** S10/S11 row counts, ID lineage, and frozen-window
  counts reproduce the article's reported 67,660/46,440 values. The 41,392
  article value remains a derived filter that must be reconstructed explicitly.

## Local outputs and normalization

- Paper reading: `../../references/TAN2024_JB028735/parsed/paper/TAN2024_JB028735__paper_reading.md`
- Case synthesis: `../../analysis/KAIKOURA2016_analysis.md`
- Source-native XLSX files are not rewritten. For analysis, parse S10 ISO-8601
  timestamps as UTC and S11 split time fields as UTC; preserve negative depths
  and all native magnitude values.
- No catalog figures have been generated yet; future plots belong under a
  dedicated `figures/` directory and must cite the source checksum.
