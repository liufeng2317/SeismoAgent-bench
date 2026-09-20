# PANG2020_GL089798 — local catalog audit

## Provenance and file identity

| Field | Value |
|---|---|
| Source reference | Pang et al. (2020), DOI [10.1029/2020GL089798](https://doi.org/10.1029/2020GL089798) |
| Data release | ISC dataset [10.31905/9IE6PAF2](https://doi.org/10.31905/9IE6PAF2) |
| Original archive | [`raw/Pang2020_ISC_magna.zip`](./raw/Pang2020_ISC_magna.zip) |
| Archive contents | `README` and `magna.txt` |
| Normalized/local file | [`PANG2020_GL089798__catalog_primary.txt`](./PANG2020_GL089798__catalog_primary.txt) |
| Format | Whitespace-delimited text; source header describes `date time latitude longitude depth coda magnitude eventId eventType` |
| Archive SHA-256 | `0ad7892bf27bc35ed184abe62274e36008b79f8e7346c5af32251fb50bb8042e` |
| Local-file SHA-256 | `e26957771d2ad607c610fd91d211eac3bb32297d8ec3225fe1d8e9a83d5cb48a` |
| Archive/local identity | Byte-for-byte identical `magna.txt` and local file; no normalization was applied |

## Row and field audit

The source file contains **5,739 data rows**, matching the archive README.  All
5,739 `eventId` values are unique (zero duplicate IDs).  The eighth field is
empty for 2,144 rows and exactly `Template-Matching` for 3,595 rows; an empty
value is retained as `UUSS/other` below because the source does not define a
second event-type label.

| Field | Local result |
|---|---|
| Data rows / unique event IDs | 5,739 / 5,739 |
| Date-time range (after parsing all numeric seconds) | 2020-03-18 13:09:31.530 to 2020-05-08 18:54:03.355 UTC |
| Latitude | 40.6933–40.8562°N |
| Longitude | −112.1713–−111.9383°E |
| Depth | −1.28–13.02 km relative to sea level (source convention) |
| `Mc`/coda-magnitude field | −9.9–5.67; 5,659 rows have `Mc > −4`; 80 rows have `Mc ≤ −4` sentinel/low values |
| Event-type labels | 3,595 `Template-Matching`; 2,144 blank/`UUSS/other` |
| Pick/station/uncertainty fields | Not present; this is an event-level release |
| Time precision | Millisecond text precision in ordinary rows |

The local date range extends to 8 May even though the article describes UUSS
locations through 30 April and matched filtering through 30 April.  The file
should therefore be treated as a release snapshot, not silently clipped to the
article's processing endpoint.  The local file also contains 8 non-canonical
second fields (`-0.xxx` or `60.xxx`).  They are preserved byte-for-byte.  A
strict ISO parser rejects 8 rows globally (7 in the benchmark window); a
normalizing parser interprets them as the adjacent second and gives the
sensitivity counts below.

### Low/negative magnitude convention

The source header calls column 6 “coda magnitude (Mc)”.  Values at or below
−4 are not missing in the text syntax, but their sentinel-like distribution
must not be interpreted as a calibrated negative magnitude population without
additional release documentation:

```text
-9.9: 1, -8.8: 8, -7.7: 6, -6.6: 5, -5.6: 1,
-5.5: 4, -5.0: 48, -4.5: 1, -4.4: 5, -4.1: 1  (80 rows)
```

For benchmark filtering, retain the source value and expose both an all-row
count and a `Mc > -4` sensitivity count; do not replace these values with NaN
in the canonical copy.

## Frozen benchmark window audit

The case-level v1 window is the half-open interval
`2020-03-18T00:00:00Z <= origin_time < 2020-03-26T00:00:00Z`.  The common
spatial/depth mask is:

```text
40.69 <= latitude <= 40.84°N
-112.14 <= longitude <= -111.94°E
-1.3 <= depth_km <= 13.1
```

Counts below use a **strict parser** that excludes the 7 in-window rows with
non-canonical seconds.  The normalized-parser sensitivity is shown separately.

| Selection | Rows | `Mc > -4` | Template-Matching / UUSS-other | Notes |
|---|---:|---:|---:|---|
| Time only, strict | 4,163 | 4,102 | 2,707 / 1,456 | This is the existing case-level event-count convention |
| Time + common spatial/depth mask, strict | 4,162 | 4,101 | 2,706 / 1,456 | Recommended cross-catalog mask |
| Time only, normalize `-0.xxx`/`60.xxx` seconds | 4,170 | 4,108 | 2,713 / 1,457 | Sensitivity only |
| Time + spatial/depth mask, normalized | 4,169 | 4,108 | 2,712 / 1,457 | Sensitivity only |

Strict time-only ranges are latitude 40.6933–40.8368°N, longitude
−112.1375–−111.9387°E, depth −1.28–13.02 km, and `Mc` −8.8–5.67.  For the
strict common mask, the ranges are latitude 40.6933–40.8368°N, longitude
−112.1375–−111.9413°E, depth −1.28–13.02 km; the `Mc > -4` subset spans
−3.9–5.67.  The one-row difference between the time-only and spatial counts is
an event outside the longitude/depth/latitude mask, not a duplicate.

## Article-versus-release alignment

| Quantity | Article | Local audit | Interpretation |
|---|---:|---:|---|
| UUSS routine events | 2,103 by 30 Apr (2,077 with a magnitude type) | 2,144 blank-eventType rows, extending to 8 May | Release snapshot has a broader/different routine subset |
| New matched-filter events | 5,501 | 3,595 rows labelled `Template-Matching` | Labels/counts are not numerically aligned; require event crosswalk before claiming equivalence |
| Relocated aftershocks | 5,623 | No relocation-status column | Cannot reconstruct the article's relocated subset from this text file alone |
| Mainshock/larger events | Often not relatively relocated | Rows are not flagged by relocation status | Preserve all rows; use article caveat in scoring |

This alignment table is deliberately not a correction.  The ISC file is the
canonical local artifact; the article values remain the authoritative method
report.  A future crosswalk should use event IDs and origin times against the
supplementary tables rather than infer membership from `eventType` alone.

## Benchmark role and normalization rules

- **Role:** primary high-resolution relative-location/detection reference for
  the permanent UUSS-compatible condition; secondary for matched-filter
  completeness; not a universal operational baseline.
- **Quality:** Q1 for relative geometry of the retained correlated events; Q2
  for enhanced detection/association; Q3 for completeness because the template
  family and station thresholds select the population.
- **Normalization:** preserve `eventId` as a string; parse date and time in UTC;
  retain raw time text and flag seconds outside `[0,60)`; preserve source
  `Mc` and `eventType`; do not synthesize picks or relocation flags.
- **Comparison:** compare with Baker at the event-time/event-location level only
  after separating the permanent network from the nodal condition.  Magnitude
  fields are not commensurate (`Mc` versus Baker `Mxc`/`M_d`/`M_l`/`M_w`).

No plot or transformed catalog is committed by this audit.  Any derived plot
should be written beside the raw file and record the strict versus normalized
time policy in its metadata.
