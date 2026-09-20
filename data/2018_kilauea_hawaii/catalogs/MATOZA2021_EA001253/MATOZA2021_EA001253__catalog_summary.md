# MATOZA2021_EA001253 — island-wide relocation catalog summary

## Provenance and schema

- Source: Matoza et al. (2021), DOI [10.1029/2020EA001253](https://doi.org/10.1029/2020EA001253).
- Canonical file: `MATOZA2021_EA001253__catalog_islandwide.txt`.
- Original archive: `raw/HVO1DXC8618V2.zip`; SHA-256
  `e014836d546ba2b210e06e4aa2119ad254ba22830bb31eec54449b06d457e4ae`.
- Canonical file SHA-256: `1e3b7c878e93b0f426b312c41fbe6cadd01be15cd452cfef1ad605e645a76877`.
- The 2025 archive README defines 26 whitespace-delimited fields. `nbranch > 1`
  means successfully relocated; `nbranch == 1` retains starting coordinates.
  Cluster IDs are only unique within each polygon, so use `(cID, polynum)`.

## Full-file audit

- 347,446 rows; 299,966 relocated (`nbranch > 1`) and 47,480 unrelocated,
  matching the revised archive README. Event IDs are unique in the local file.
- Time span: 1986-01-01 02:45:11.425 to 2018-12-31 23:27:25.830 UTC.
- Relocated-coordinate ranges: latitude 18.5633–21.1791°, longitude
  −156.49609–−154.37070°, depth −0.003–202.48 km, magnitude −0.77–9.0.
- Starting-coordinate ranges: latitude 13.5714–26.1626°, longitude
  −162.0372–−149.4608°, depth −12.208–291.2 km. These broad ranges include
  offshore/remote starting solutions; use the paper's geographic mask explicitly.
- The article reports 347,445/275,009 and 79%, whereas the revised local release
  reports 347,446/299,966. Both are preserved as versioned facts.

## Frozen Kīlauea summit window

```text
2018-05-01T00:00:00Z <= origin_time < 2018-05-09T00:00:00Z
19.30 <= latitude <= 19.50
-155.40 <= longitude <= -155.15
0 <= depth_km <= 20
```

Using relocated coordinates: 2,999 rows fall in the time window; 1,190 satisfy
the summit mask, of which 1,044 have `nbranch > 1`. Using starting coordinates
gives 1,130 mask rows, of which 984 are successfully relocated. The distinction
is retained because the source file contains both coordinate versions.

## Benchmark role and limitations

- **Q1 relative location auxiliary:** use `latR/lonR/depR`, nbranch, cluster and
  error fields for relative-geometry checks.
- **Q2 broad reference:** useful for island-wide/flank detection and network-era
  sensitivity, but not a standalone absolute truth set.
- No event reassociation was performed; all triggers and phase association come
  from HVO. Preserve CUSP/AQMS era and variable-channel coverage as observation
  metadata.
