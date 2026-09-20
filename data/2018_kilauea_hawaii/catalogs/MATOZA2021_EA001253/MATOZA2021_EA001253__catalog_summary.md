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

The source README defines columns 8–10 (`latR/lonR/depR`) as relocated
coordinates and columns 23–25 (`latC/lonC/depC`) as starting coordinates. The
local audit therefore gives 1,130 summit-mask rows (984 successfully relocated)
when the relocated coordinates are used, versus 1,190 rows (1,044 with
`nbranch > 1`) when the starting coordinates are used. This distinction is
material near the summit-box boundary and is retained rather than collapsed
into one count. (Earlier versions of this summary had these two labels
reversed.)

### Frozen-window ranges

All rows below use the half-open UTC time rule above. `nbranch > 1` is the
release's successful-relocation flag; it is reported separately from the
coordinate basis. Magnitude is the native `mag` field (zeros are retained as
published and are not recoded as missing).

| Coordinate basis / selection | Rows | `nbranch > 1` | Time range (UTC) | Latitude (°) | Longitude (°) | Depth (km) | Magnitude |
|---|---:|---:|---|---:|---:|---:|---:|
| Relocated (`latR/lonR/depR`), time-only | 2,999 | 2,579 | 2018-05-01T00:13:40.685–2018-05-08T23:56:20.588 | 18.911330–19.883330 | −155.788620–−154.618830 | −7.915–63.517 | 0.00–6.90 |
| Relocated + summit mask | 1,130 | 984 | same | 19.300520–19.495500 | −155.396330–−155.150200 | 0.007–19.237 | 0.00–4.66 |
| Starting (`latC/lonC/depC`) + summit mask | 1,190 | 1,044 | same | 19.300330–19.491170 | −155.396330–−155.150160 | 0.000–18.640 | 0.00–4.66 |

For metrics that require a relocated event geometry, use the second row and
filter `nbranch > 1` (984 events). For provenance or starting-catalog bias
analysis, retain the third row and its 1,044-event successfully relocated
subset; do not compare the two counts as if they were different event
populations.

## Benchmark role and limitations

- **Q1 relative location auxiliary:** use `latR/lonR/depR`, nbranch, cluster and
  error fields for relative-geometry checks.
- **Q2 broad reference:** useful for island-wide/flank detection and network-era
  sensitivity, but not a standalone absolute truth set.
- No event reassociation was performed; all triggers and phase association come
  from HVO. Preserve CUSP/AQMS era and variable-channel coverage as observation
  metadata.
