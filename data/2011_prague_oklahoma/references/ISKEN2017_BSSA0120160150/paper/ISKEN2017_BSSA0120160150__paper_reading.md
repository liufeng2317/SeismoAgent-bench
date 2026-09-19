# Isken & Mooney (2017) — paper reading and catalog-construction audit

## Extraction status and evidence convention

This note distinguishes article-reported facts from measurements made on the
locally preserved Table S3 transcription. The article PDF was parsed with
MinerU. Page numbers below refer to the 12-page MinerU `content_list_v2`
sequence (PDF page 1 is the GFZ/SSA cover page; the article title begins on
page 3). The official HTML supplement is the authority for the Table S3 cell
values.

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | Marius P. Isken and Walter D. Mooney | PDF p. 3, title block |
| Citation | Isken & Mooney (2017), “Relocated Hypocenters and Structural Analysis from Waveform Modeling of Aftershocks from the 2011 Prague, Oklahoma, Earthquake Sequence” | PDF p. 1/3 |
| Journal | *Bulletin of the Seismological Society of America*, 107(2), 553–562 | PDF p. 1 |
| DOI / landing page | [10.1785/0120160150](https://doi.org/10.1785/0120160150) | PDF p. 1 |
| Publication date | Published online 2017-02-21 | PDF p. 12 |
| Article type | Research article with a small manually picked/hypocenter-relocated aftershock reference and 2-D finite-difference waveform modeling | Abstract; Data; Methodology |
| Catalog relationship | Table S3 is an article-associated set of 13 relocated aftershocks; it is not a complete sequence catalog | Supplement title and PDF p. 3, 5–7 |
| Local paper | `paper/ISKEN2017_BSSA0120160150__paper.pdf` | Local provenance |
| Parsed text | `paper/mineru/ISKEN2017_BSSA0120160150__paper/full.md` and its `content_list_v2.json` | MinerU output |

The article's central scientific goal is to use relocation and waveform
modeling to assess focal depths and explain strong S-wave coda scattering in
the Prague sequence. Catalog construction is a means to that goal, so the
13-event product should be treated as a selective structural/location anchor,
not as a completeness target.

## Sequence and scientific scope

- The case is the induced/triggered 2011 Prague, Oklahoma earthquake sequence
  in the Cherokee platform. The paper highlights the M~5.7 mainshock on
  **2011-11-06 03:53:10 UTC**, the M~4.8 foreshock on **2011-11-05
  07:12:45 UTC**, and a later M~4.8 event on **2011-11-08 02:46:57 UTC**
  (PDF p. 3, Introduction).
- The analyzed aftershocks are reported as `M_L > 3` (PDF p. 3, abstract and
  p. 11, conclusion). The 13 rows in Table S3 carry **M_w 3.1–3.4**; do not
  silently equate the article's `M_L > 3` selection statement with the table's
  reported `M_w` column.
- Figure 1 describes the 13 aftershocks as occurring between **11 November
  and 31 December 2011** (PDF p. 3, Fig. 1 caption). The Table S3 rows actually
  span **2011-11-11 through 2011-12-09 UTC**; the latter is the reproducible
  range of the distributed table, not a claim that no other events occurred
  later in December.
- The scientific hypothesis is that the relocated hypocenters are primarily
  in the Precambrian basement (roughly 5–10 km), while heterogeneous
  Pennsylvanian sedimentary layers/paleochannels produce the observed coda
  (PDF p. 3 abstract; pp. 8–11 waveform-modeling discussion).

## Observation and network conditions

| Item | Extracted information | Evidence / unresolved detail |
|---|---|---|
| Temporary observations | Broadband three-component temporary deployments followed the early-November sequence | PDF p. 5, Data |
| ZQ/RAMP | Oklahoma RAMP (`ZQ`, Keranen 2011), accessed through IRIS | PDF p. 5; reference list |
| LA array | Linear large-aperture array of **10 seismographs** extending approximately **120 km east** from the main-event epicenters; recorded/compiled by USGS/Elizabeth Cochran | PDF p. 5, Data |
| Relocation station set | Manual P and S picks at **19 available stations** close to the epicentral area | PDF p. 6, Methodology |
| Components / phases | Direct P and secondary S arrivals visible on all components; record sections emphasize horizontal-component S coda | PDF p. 5, Fig. 3 caption |
| Waveform filter shown | Record section example high-pass filtered at approximately `f > 0.5 Hz` | PDF p. 5, Fig. 3 caption; exact notation is OCR-sensitive |
| Archive/provenance | LA data from USGS Pasadena; ZQ waveform and metadata via IRIS DMC/RAMP; downloads noted as 2013-08-21 | PDF p. 12, Data and Resources |
| Station metadata | Coordinates are said to be in electronic Table S1, but the station table is not included in the current local reference folder | **Missing local supplement product; do not infer station availability from the 13-event table** |

The 19-station manual-pick condition is important: the table's small location
errors are conditional on a dense temporary/local deployment and should not be
interpreted as the accuracy attainable from the operational network alone.

## Catalog-construction workflow

```text
2011 Prague aftershock waveforms from ZQ/RAMP and LA arrays
    → manual P- and S-phase picks at 19 local stations
    → 1-D velocity model based mainly on Toth et al. (2012) sonic-log model
    → HYPOINVERSE 2000 hypocenter inversion / relocation
    → Table S3: 13 selected `M_L > 3` aftershocks with errors, RMS and Mw
    → 2-D sofi2D finite-difference forward modeling (downstream interpretation)
```

### Starting population and selection

The article does not present a machine-readable complete event list or an
automatic detection threshold. It discusses 13 aftershocks selected for
relocation and waveform analysis, all represented by numbered rows in Table
S3. The table therefore has **selective event coverage** and should not be
used to estimate detection completeness, event-rate changes, or a magnitude
of completeness.

### Phase picking and location

- P and S arrivals were **manually picked** for every available station used
  in the relocation; the article states 19 stations (PDF p. 6).
- HYPOINVERSE (Klein, 1978; 2013) was used for hypocenter relocation.
- The 1-D velocity structure was largely based on Toth et al. (2012) and
  sonic-log constraints; model velocities were varied within minor bounds to
  fit a linear gradient and reduce RMS residual (PDF p. 6).
- Each event used **25–34 P/S arrivals**. Reported RMS travel-time residuals
  range **0.03–0.05 s**, with a mean of approximately **0.04 s**; horizontal
  and vertical location uncertainties are described as on the order of 1 km
  in the article text (PDF p. 7, Relocation of Aftershocks).
- Table S3 reports much smaller formal/summary values, ERH **0.1 km** and ERZ
  **0.1–0.2 km**. These values are table fields from the gradient half-space
  model and must not be conflated with the article's prose “on the order of 1
  km” statement. Preserve both statements and investigate the underlying
  HYPOINVERSE error definition before using them as a calibration target.

### Waveform modeling is downstream, not an event-inclusion rule

The paper then uses `sofi2D` finite-difference modeling to compare homogeneous
and heterogeneous shallow-crust models. The model domain is 120 km by 12 km,
with 10 m spatial resolution; the assumed `V_P/V_S` ratio is 1.734, Q is 1500
in basement and 1000 in sediment, and synthetic source depths span about 1–7
and 10 km (PDF pp. 6–8). These parameters validate depth interpretation and
coda behavior; they do **not** define catalog detection or quality filters.

## Table S3 product and field semantics

The official supplement labels the table:

> “Table S3. Relocations of 13 Aftershocks from the 2011 Oklahoma Earthquake
> Sequence Based on a Gradient, Half-Space Model.”

The local normalized CSV preserves the official row values and uses the
following fields:

| Field | Meaning / unit | Local range or behavior |
|---|---|---|
| `no` | Article row number; not a globally stable event ID | 1–13, unique within Table S3 |
| `time_utc` | Origin time, UTC, second precision in source table | 2011-11-11 19:19:00 to 2011-12-09 16:46:00; 13 unique values |
| `latitude_deg` | Hypocenter latitude, decimal degrees | 35.452–35.546°N |
| `longitude_deg` | Hypocenter longitude, decimal degrees | −96.897 to −96.737°E |
| `depth_km` | Hypocentral depth, km | 4.63–10.08 km; positive downward by article convention |
| `erh_km` | ERH, lateral/horizontal error, km | 0.1 for all 13 rows |
| `erz_km` | ERZ, depth error, km | 0.1–0.2 km |
| `rms_s` | RMS travel-time residual, s | 0.03–0.05 s; mean 0.0431 s |
| `Mw` | Moment magnitude as labeled by official table | 3.1–3.4; do not substitute `ML` |

The complete 13-row table is retained in
[`ISKEN2017_BSSA0120160150__catalog_relocated_tableS3.csv`](../../../catalogs/ISKEN2017_BSSA0120160150/ISKEN2017_BSSA0120160150__catalog_relocated_tableS3.csv),
with the downloaded official HTML source preserved beside it. The local CSV
contains 13 rows, no exact duplicate rows, and no missing cells. Its SHA-256
is recorded in the catalog summary.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q1 selective high-quality relocation anchor**, conditional on the article's manually picked local network and velocity model. It is not Q1 as a complete event-existence truth set. |
| Primary role | Absolute/depth-location and structural sanity anchor for clearly recorded `M_L > 3` aftershocks; check whether a workflow recovers plausible fault-plane/depth geometry. |
| Secondary role | Event-level cross-reference for the larger Cochran/McMahon catalogs. Match by origin time and space, not by `no`. |
| Completeness | Deliberately low/unknown; 13 selected events only. No rate, completeness, or recall metric should use Table S3 as denominator. |
| Independence | Moderate. It uses manual picks and HYPOINVERSE, so it is methodologically distinct from template matching/subspace workflows, but it shares the same sequence and partly overlapping waveforms/stations. |
| Suitable metrics | Origin-time/epicenter/depth residuals for matched events; consistency of geometry; uncertainty-aware location comparisons. |
| Unsuitable metrics | Detection recall, catalog event-count agreement, magnitude-completeness, daily rate, or claims that every agent event absent from S3 is false. |
| Core-window coverage | **7 of 13** rows fall in the Prague v1 half-open window `2011-11-11T00:00:00Z ≤ t < 2011-11-19T00:00:00Z`; the remaining 6 are outside it. |

The seven in-window rows are useful as a sparse structural anchor, but they do
not replace the Cochran primary catalog's 2,078-event core-window population.
Use a time/space crosswalk with explicit tolerance and preserve unmatched
events rather than dropping them silently.

## Local provenance and unresolved actions

- Paper PDF: `data/2011_prague_oklahoma/references/ISKEN2017_BSSA0120160150/paper/ISKEN2017_BSSA0120160150__paper.pdf`
- MinerU extraction: `data/2011_prague_oklahoma/references/ISKEN2017_BSSA0120160150/paper/mineru/`
- Catalog README: `data/2011_prague_oklahoma/catalogs/ISKEN2017_BSSA0120160150/README.md`
- Normalized catalog: `data/2011_prague_oklahoma/catalogs/ISKEN2017_BSSA0120160150/ISKEN2017_BSSA0120160150__catalog_relocated_tableS3.csv`
- Official source table: `data/2011_prague_oklahoma/catalogs/ISKEN2017_BSSA0120160150/ISKEN2017_BSSA0120160150__source_tableS3.html`
- Official supplement landing page: <https://www.seismosoc.org/Publications/BSSA_html/bssa_107-2/2016150-esupp/>

Remaining checks before using this reference in a scored benchmark:

1. Stage Table S1/S2 and any empirical/synthetic supplement files so station
   coordinates and velocity-model assumptions are separately auditable.
2. Confirm the precise meaning of ERH/ERZ and the discrepancy between formal
   table errors and the prose “on the order of 1 km” uncertainty statement.
3. Build a time/space crosswalk to Cochran and McMahon without treating table
   row numbers as shared IDs.
4. Keep the 13-event product out of completeness and event-recall scores.
