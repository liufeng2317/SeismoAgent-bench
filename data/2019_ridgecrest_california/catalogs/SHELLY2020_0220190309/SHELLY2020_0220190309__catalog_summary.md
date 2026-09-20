# SHELLY2020_0220190309 — catalog summary and reproducible audit

## Provenance and product distinction

- Source article: Shelly (2020), DOI [10.1785/0220190309](https://doi.org/10.1785/0220190309).
- Official article data release: USGS ScienceBase DOI [10.5066/P9JN6H0N](https://doi.org/10.5066/P9JN6H0N).
- **Canonical event catalog:** `raw_article/SHELLY2020_0220190309__catalog_DataS1.txt`.
- Metadata: `raw_article/SHELLY2020_0220190309__metadata_DataS1.xml`.
- **Auxiliary phase release:** `raw/Ridgecrest_2019_correlation_phase_arrivals.csv` and its XML. It contains phase arrivals for template matches and must not be counted as a 5.7-million-event catalog.

## Canonical Data S1 schema and checksum

The text file has comments followed by eleven whitespace-delimited fields:
`YYYY MM dd hh mm ss.sss lat lon depth mag ID`. Depth is in km relative to
an approximately 0.7-km-asl surface datum. IDs are stable strings in the local
file; no header row is present in the data section.

| File | Bytes | Data rows | Unique IDs | Duplicate IDs | Duplicate origin times | SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| `raw_article/SHELLY2020_0220190309__catalog_DataS1.txt` | 2,592,275 | 34,091 | 34,091 | 0 | 2 | `aaa79453a2c599fe2b386a544c78e8e98383492aacf57212a8dc98d82373a9f1` |

## Full catalog audit

| Field | Range / value |
|---|---|
| Origin time | 2019-07-04 15:35:29.400 to 2019-07-16 23:59:26.500 UTC |
| Latitude | 35.469906–36.036100°N |
| Longitude | −117.943498–−117.213200°E |
| Depth | 0.089–556.580 km |
| Magnitude | −0.34–7.10; mixed SCSN preferred and calibrated ML values |
| Negative magnitudes | 195 rows |
| Missing fields | None detected in the eleven native columns |

The 556.58-km depth is an obvious catalog outlier for this local sequence and
is retained in the raw product. The common benchmark mask removes it without
editing the source file.

## Frozen benchmark-window audit

Rule: `2019-07-04T00:00:00Z <= time < 2019-07-07T00:00:00Z`; latitude
35.45–36.05°N; longitude −117.90–−117.20°; depth 0–20 km.

| Field | Time-only | Common mask |
|---|---:|---:|
| Rows / unique IDs | 7,773 / 7,773 | 7,716 / 7,716 |
| Time range | 2019-07-04 15:35:29.400–2019-07-06 23:59:47.320 UTC | same |
| Latitude | 35.469906–36.036100°N | 35.485217–36.012817°N |
| Longitude | −117.943498–−117.213200°E | −117.819198–−117.255697°E |
| Depth | 0.089–556.580 km | 0.159–19.953 km |
| Magnitude | −0.34–7.10 | −0.10–7.10 |

The 57 rows excluded by the common mask are not deleted; the mask is only a
comparison rule shared by the six-case benchmark.

## Auxiliary phase-arrival release audit

`raw/Ridgecrest_2019_correlation_phase_arrivals.csv` is a row-per-template /
match / station / phase table with columns
`template_id,match_id,network,station,phase,arrival,weight,mag,ccmax,ccdiff,chanloc`.
It has 5,703,270 data rows (SHA-256
`0b77237b497265ebc94768acd955a9de5eb4c7f78f130922254e4c9ed4122d9f`), 209,213
unique `match_id` values, 6,744 template IDs, 30 network-station pairs and
P/S counts of 2,536,859 / 3,166,411. Arrival times span 2019-07-04
00:56:40.090300 to 2019-07-16 23:59:55.419000 UTC. This product is useful for
pick-level and station-coverage analyses but is not the article's 34,091-row
event catalog.

## Benchmark role and limitations

- **Tier:** Q1 for relative-location/detection structure; Q2 for absolute
  location and completeness.
- The file contains no event-level uncertainty, station-count or relocation-
  quality columns. Use article thresholds and the separate phase release for
  method-level checks.
- The catalog is mostly unreviewed and template-conditioned. Event rates and
  small-magnitude completeness change sharply during coda-saturated intervals.
- For the Mw 6.4 and Mw 7.1 events, prefer the SCSN hypocenter or another
  absolute-location product over the correlation-derived centroid.

## Local outputs

- Paper reading: `../../references/SHELLY2020_0220190309/parsed/paper/SHELLY2020_0220190309__paper_reading.md`
- Case synthesis: `../../analysis/RIDGE2019_analysis.md`
- Raw files remain unchanged under `raw_article/` and `raw/`; any figures or
  normalized derivatives should be written below a separate `figures/` or
  `derived/` directory.
