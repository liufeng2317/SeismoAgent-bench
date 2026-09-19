# WEI2022_EA001979 — catalog summary and reproducible audit

## Provenance

- Source article: Wei et al. (2022), DOI [10.1029/2021EA001979](https://doi.org/10.1029/2021EA001979).
- Release: article Data Set S1; Dryad [10.5061/dryad.np5hqbzw9](https://doi.org/10.5061/dryad.np5hqbzw9), version 8 (`located_catalog_full_final.txt`).
- Local file: `WEI2022_EA001979__catalog_S1.txt`; preserve this source-native file.
- Native format: whitespace-delimited text with one header row and 14 columns; no event ID column.
- SHA-256: `f95ae0b17eb519c169c17248b9986eb15885c2a42ca28102a1d25ca7a28eb339`.
- Local byte size: 44,665,223 bytes; 375,736 data rows plus one header line.

## Native schema and missing values

Header:

```text
SourceTime Lat Lon Dep AzimuthalGap MinDist Nobs RMS StdX StdY StdZ Mag MagType StdMag
```

| Field | Interpretation / audit |
|---|---|
| `SourceTime` | UTC ISO-8601 origin time with 6 fractional-second digits; unique in the local file (0 exact duplicate timestamps) |
| `Lat`, `Lon` | Degrees; longitude is negative west |
| `Dep` | Depth in km relative to the catalog datum/topography convention; negative values occur and must not be clipped globally |
| `AzimuthalGap`, `MinDist` | Location geometry in degrees/km as distributed |
| `Nobs` | Number of observations used/retained by the location product |
| `RMS` | Location residual/misfit in seconds (paper QC threshold is generally <1 s, with documented relaxation for high-observation events) |
| `StdX`, `StdY`, `StdZ` | Location standard-error fields in the source-native convention; units/coordinate basis should be confirmed from SI Table S1/S2 before metric calibration |
| `Mag` | Numeric (M_d) or (M_L) when measurable; `Unk` otherwise |
| `MagType` | `d` = duration/coda magnitude, `l` = local magnitude, `Unk` = no magnitude |
| `StdMag` | Magnitude standard deviation; `0.00` commonly accompanies `Unk` and should not be interpreted as zero uncertainty |

There are no malformed rows. The file contains 219,396 `d`, 88,621 `l`, and
67,719 `Unk` magnitude-type rows. Numeric magnitude values are present for
308,017 rows; the global numeric range is −2.25 to 7.14. The paper's final
catalog count is therefore an event-row count, not a count restricted to rows
with measured magnitude.

## Full-file audit

| Field | Local value |
|---|---|
| Data rows / unique stable IDs | 375,736 / no explicit ID field |
| Exact duplicate `SourceTime` rows | 0 |
| Time range | 2018-03-01T00:10:39.787552Z – 2018-09-30T23:59:32.912631Z |
| Latitude | 18.691332–20.392835°N |
| Longitude | −156.289628–−154.385413°E |
| Depth | −4.121094–69.853516 km |
| Numeric magnitude | −2.25–7.14; 308,017 rows |
| Magnitude types | `d`: 219,396; `l`: 88,621; `Unk`: 67,719 |
| `Nobs` | 4–227 |
| `RMS` | 0.000548675–9.92166 s |
| `AzimuthalGap` | 11.601–359.987° |
| `MinDist` | 0.0029–135.2407 km |

Negative depths and very large uncertainty values are present in the native
release. They are retained for provenance; benchmark masks must state whether
they are excluded rather than silently normalizing them.

## Frozen Kīlauea summit benchmark mask

The case-level v1 rule is the half-open UTC interval
`2018-05-01T00:00:00Z ≤ SourceTime < 2018-05-09T00:00:00Z`, with:

```text
19.30° ≤ Lat ≤ 19.50°
−155.40° ≤ Lon ≤ −155.15°
0 km ≤ Dep ≤ 20 km
```

Applying this mask to the local file gives **2,369 event rows**. Of these,
**1,930 rows have numeric magnitudes** (`d` or `l`); the older case summary's
“Wei 1,930 events” value counted only this magnitude-available subset. Both
counts should be retained until the benchmark task explicitly chooses whether
its detection metric requires a magnitude.

| Field | All 2,369 masked rows | Numeric-magnitude subset (1,930) |
|---|---:|---:|
| Time | 2018-05-01T00:38:16.361021Z – 2018-05-08T23:54:09.815983Z | 2018-05-01T00:38:16.361021Z – 2018-05-08T23:54:09.815983Z |
| Latitude | 19.300249–19.498780°N | same spatial mask |
| Longitude | −155.397044–−155.150027°E | same spatial mask |
| Depth | 0.017090–19.902344 km | same depth mask |
| Magnitude | −0.79–5.82 for rows where present | −0.79–5.82 |
| `Nobs` | 4–92 | 4–92 |
| `RMS` | 0.0038433–3.75352 s | 0.0038433–3.75352 s |
| `StdX` | 0.2075–57.8142 | 0.2075–49.193 |
| `StdY` | 0.2868–56.3724 | 0.2868–48.1481 |
| `StdZ` | 0.2662–26.7032 | 0.2662–26.7032 |
| `MagType` | `d`: 1,554; `l`: 376; `Unk`: 439 | `d`: 1,554; `l`: 376 |

The mask is a summit-task comparison with Shelly & Thelen, not a claim that
Wei's entire island/offshore catalog has summit-only support. Network labels and
deployment dates must be retained when constructing waveform subsets.

## Construction and quality summary

```text
STA/LTA triggers on filtered components
  → travel-time-window association
  → polarization/kurtosis P/S picks
  → NonLinLoc 3-D location + topography mask
  → ≥1 P, ≥4 valid arrivals, weight/RMS quality checks
  → location-based re-association and second location
  → coda/duration or local magnitude
  → duplicate removal and final Data Set S1
```

The article reports 650,899 associated trigger/event candidates, 503,339
successfully located events, 420,963 locations used in re-association, and a
final 375,736-event release. The distributed product is automatic and
heterogeneous rather than a manually reviewed truth set. Offshore OBS picks
are explicitly described as lower quality; some events were removed when only
KSFG supplied a P pick. The event-rate changes around nodal-array deployment
are observation-process effects as well as possible seismicity changes.

## Benchmark role and relation to other Kīlauea products

- **Quality tier:** Q2 broad enhanced-detection/3-D-location reference.
- **Primary use:** secondary target for broad-island, flank, and offshore
  detection/association/location; independent cross-check against HVO routine
  and Shelly summit products.
- **Shelly relation:** Shelly & Thelen uses summit waveform templates,
  correlation-derived differential times, and hypoDD to produce a dense
  relative-location summit catalog. Wei uses STA/LTA, automatic P/S picking,
  NonLinLoc, and mixed onshore/offshore networks. They must not be merged or
  ranked without a common space/time/network mask.
- **HVO relation:** HVO is the Q3 operational baseline; Wei reports more events
  and lower estimated \(M_c\), but the gain partly reflects temporary arrays and
  network-dependent detection.
- **Independence:** medium–high methodological independence from Shelly, but
  shared waveform archives and comparison catalogs remain common lineage.

## Known limitations and follow-up

1. The local file has no event IDs; use source time plus row hash only as a
   reproducibility key, not as a cross-catalog physical association.
2. Confirm the units/definitions of `StdX/StdY/StdZ`, `AzimuthalGap`, and
   `MinDist` from the local SI before uncertainty metrics are frozen.
3. Parse `Wei2022_Kilauea_SI.pdf` to archive exact Text S1–S11/Table S1–S4
   detector, station, and comparison parameters.
4. Generate catalog map, depth section, daily-rate/network-availability plot,
   magnitude-frequency plot, and missing-magnitude mask under this catalog
   directory without modifying the raw file.
