# ROSS2019_SCIENCE — SCEDC QTM catalog summary and reproducible audit

## Provenance and native schema

- Source article: Ross et al. (2019), DOI [10.1126/science.aaz0109](https://doi.org/10.1126/science.aaz0109).
- Official release: [SCEDC QTM Ridgecrest catalog](https://scedc.caltech.edu/data/qtm-ridgecrest.html).
- Local archive: `raw/ROSS2019_SCIENCE__catalog_qtm.tar.gz`, containing one
  file named `ridgecrest_qtm.cat`.
- Archive SHA-256: `dcb0035f69c6ea9a960e45544f31bdacb38cb7f502c3d29af827da4ff6850849`.
- Archive member: 111,918 whitespace-delimited data rows, no header row.

The official SCEDC schema is:

| Columns | Meaning |
|---|---|
| 1–6 | relocated origin time: year, month, day, hour, minute, second |
| 7 | `eID`, event ID |
| 8–10 | `latR`, `lonR`, `depR`, relocated latitude/longitude/depth (degrees, km) |
| 11 | event magnitude |
| 12–14 | `qID`, `cID`, `nbranch` (event serial, cluster serial, total events in cluster) |
| 15–17 | `qnpair`, `qndiffP`, `qndiffS` (pair/P/S differential-time counts) |
| 18–19 | `rmsP`, `rmsS` differential-time RMS (s) |
| 20–22 | `eh`, `ez`, `et` horizontal/vertical/origin-time errors (km, km, s) |
| 23–25 | `latC`, `lonC`, `depC` initial/catalog location |

SCEDC defines a successfully relocated solution as `nbranch > 1`. Rows with
`nbranch = 1` have zero differential-time support in the local release and
should not be silently treated as GrowClust relocations.

## Full archive audit

| Field | Value |
|---|---:|
| Rows / unique event IDs | 111,918 / 111,918 |
| Duplicate IDs / duplicate origin times | 0 / 13 |
| Origin time | 2019-07-04 03:14:14.128–2019-07-25 14:59:51.550 UTC |
| Relocated latitude | 35.305300–36.137000°N |
| Relocated longitude | −118.016000–−117.011500°E |
| Relocated depth | −0.740–24.900 km |
| Magnitude | −2.82–7.10 |
| `nbranch > 1` rows | 46,512 |
| `nbranch = 1` rows | 65,406 |
| Distinct cluster IDs | 68,112 |
| Differential P/S counts | `qndiffP` 0–817; `qndiffS` 0–991 |
| Differential RMS | `rmsP` 0–0.48 s; `rmsS` 0–0.76 s |
| Error fields | `eh` −1–0.989 km; `ez` −1–1.425 km; `et` −1–0.198 s; −1 denotes unavailable in this release |

The archive therefore combines an initial/operational population with the
successfully relocated subset. For relative-location metrics use `nbranch > 1`
and retain all error/QC fields.

## Frozen benchmark-window audit

Case-wide rule: `2019-07-04T00:00:00Z <= time < 2019-07-07T00:00:00Z`, latitude
35.45–36.05°N, longitude −117.90–−117.20°, depth 0–20 km, applied to the
relocated (`latR`, `lonR`, `depR`) fields.

| Field | Time-only | Common mask |
|---|---:|---:|
| Rows | 12,806 | 12,768 |
| `nbranch > 1` rows | 6,470 | 6,463 |
| Distinct clusters | 6,977 | 6,943 |
| Time range | 2019-07-04 03:14:14.128–2019-07-06 23:59:47.190 UTC | 2019-07-04 03:26:19.848–2019-07-06 23:59:47.190 UTC |
| Latitude | 35.374180–36.111680°N | 35.501700–36.049560°N |
| Longitude | −117.909630–−117.011500°E | −117.895500–−117.222500°E |
| Depth | −0.417–24.500 km | 0.018–19.700 km |
| Magnitude | −0.82–7.10 | −0.82–7.10 |

The count `12,768` is not a count of successfully relocated events; the
metric-specific relocated target is `6,463` under the same mask.

## Quality and limitations

- **Tier:** Q1 structural/relative relocation for `nbranch > 1`; Q2–Q3 for
  initial-only rows and absolute mainshock depths.
- The Mw 7.1 mainshock depth is explicitly poorly constrained; use the SCSN
  hypocenter for that event.
- The local archive has 13 duplicate origin times but unique event IDs; retain
  IDs for joins and do not deduplicate on time alone.
- Detailed article processing parameters are in Science DC1, which is missing
  locally. This summary therefore uses only the official SCEDC schema and local
  field audit for exact reproducibility.

## Local outputs

- Paper reading: `../../references/ROSS2019_SCIENCE/paper/ROSS2019_SCIENCE__paper_reading.md`
- Case synthesis: `../../analysis/RIDGE2019_analysis.md`
- Raw archive is preserved unchanged; extract an ignored working copy only when
  generating plots or normalized derivatives.
