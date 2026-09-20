# Shelly (2020) — paper reading and catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | David R. Shelly | Article title block |
| Title | *A High-Resolution Seismic Catalog for the Initial 2019 Ridgecrest Earthquake Sequence: Foreshocks, Aftershocks, and Faulting Complexity* | Local MinerU parse, title/abstract |
| Journal / DOI | *Seismological Research Letters*; DOI [10.1785/0220190309](https://doi.org/10.1785/0220190309) | Article citation block; DOI |
| Data release | USGS ScienceBase, DOI [10.5066/P9JN6H0N](https://doi.org/10.5066/P9JN6H0N) | Local Data S1 XML metadata |
| Article type | Research article whose primary contribution is a detected and precisely relocated event catalog | Abstract and Methods |
| Catalog relationship | Data S1 is the article-associated hypocentroid/event product; the large phase-arrival CSV in `catalogs/.../raw/` is a later combined USGS release and is auxiliary, not the same event table | Data S1 header/XML and local phase CSV schema |
| Parse status | MinerU output is available at `SHELLY2020_0220190309__paper__mineru.md`; quantitative claims below are checked against the local Data S1 and metadata | Local files |

## Scientific scope and observation conditions

- Sequence: the 2019 Ridgecrest, California, Mw 6.4 foreshock and Mw 7.1
  mainshock sequence. The article focuses on the first part of the sequence,
  including the foreshocks and the first 10+ days after the Mw 7.1 event
  (MinerU lines 35–38; Data S1 header).
- Article/Data S1 span: 2019-07-04 through 2019-07-16 UTC. The local file has
  its first origin at 2019-07-04 15:35:29.400 and last origin at
  2019-07-16 23:59:26.500 UTC.
- Network: SCSN/SCEDC routine catalog and short-period/broadband stations in
  real-time processing; the article names Caltech, USGS, UNAVCO and University
  of Nevada, Reno stations (MinerU lines 44, 107). A single fixed station count
  is not stated in the article; do not infer one from the later phase-arrival
  release.
- Waveform processing: continuous data at 100 samples/s, daily template scans,
  2–12 Hz bandpass. P templates are 2.5 s and S templates 4.0 s, beginning
  0.3 s before the catalog pick (MinerU lines 40, 44, 52).
- Depth datum: relocated depths are nominally referenced to a surface elevation
  of 0.7 km above sea level (Ridgecrest), not a universal sea-level hypocenter
  datum (MinerU line 60; Data S1 comments).

## Catalog-construction workflow

```text
SCSN routine events and picks (13,525 templates)
    → P/S waveform templates on available components
    → multichannel template matching in daily blocks
    → correlation and differential-time thresholds / weighting
    → combine catalog and correlation differential times
    → hypoDD double-difference relocation
    → retain events with ≥12 P and ≥12 S correlation differential times
    → calibrated magnitude for new detections + SCSN preferred magnitude for templates
    → Data S1 event catalog
```

### Templates and detection

- 13,525 routinely cataloged SCSN events were used as waveform templates; the
  final article product contains 34,091 detected and precisely located events,
  including more than 20,000 newly detected events (abstract and MinerU lines
  35, 44).
- Templates were scanned on 3–18 July in daily blocks. The summed correlation
  threshold was eight times the daily median absolute deviation; individual
  differential-time correlation used a seven-MAD threshold. Maximum differential
  times were 0.5 s for P and 0.85 s for S (MinerU line 52).
- The article combines 8.6 million correlation-derived P and 15.8 million
  correlation-derived S differential times with 6.6 million and 2.9 million
  SCSN catalog-derived P/S differential times, respectively (MinerU line 58).

### Relocation and magnitude

- All accepted differential times were passed to hypoDD with the 1-D velocity
  model listed in Table 1 (P velocity 4.74–7.8 km/s and constant Vp/Vs 1.73;
  MinerU lines 54–58).
- An event was considered well located only with at least 12 P and 12 S
  correlation-derived differential times; 34,091 events met this criterion
  (MinerU line 60).
- Newly detected magnitudes were calibrated to SCSN ML scaling. The article
  estimates that a factor of ten in amplitude corresponds to 0.831 magnitude
  units; SCSN catalog magnitudes are retained for template events (MinerU line
  62).

## Reported products and limitations

| Processing/product | Article value | Local audit / interpretation |
|---|---:|---|
| Routine template events | 13,525 | Article value; template population is inherited from SCSN |
| Final detected and relocated events | 34,091 | Data S1 has exactly 34,091 rows and unique IDs |
| Article span | 4–16 July 2019 | Local Data S1: 2019-07-04 15:35:29.400 to 2019-07-16 23:59:26.500 UTC |
| Relocation criterion | ≥12 P and ≥12 S correlation differential times | Criterion is not represented as a dedicated field in Data S1 |
| Review status | Mostly unreviewed; large errors may occur in a small subset | Article explicitly says to interpret the catalog in aggregate |
| Largest-event accuracy | Caution for Mw >~5, especially Mw 6.4 and 7.1 | Relative centroid locations are not the preferred absolute hypocenters for mainshocks |
| Completeness | Strongly time varying after both mainshocks | Coda saturation and changing noise make b-value/event-count comparisons conditional |

The Data S1 XML metadata has a copied/incorrect description that says depth is
“below Kilauea summit.” The Data S1 text header and the article methods identify
the Ridgecrest 0.7-km-asl surface datum; the latter is authoritative for this
case.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q1** for high-resolution detection and relative geometry; **Q2** for absolute hypocenters and completeness |
| Primary role | Dense event recovery, association stress, relative relocation and fault-geometry target |
| Suitable metrics | Event support/recall, temporal clustering, relative geometry, location residuals where available, sensitivity to overlapping events |
| Unsuitable metric | Universal absolute truth for Mw 6.4/Mw 7.1 hypocenters or stationary completeness/b-value estimates |
| Independence | Medium: shares SCSN/SCEDC waveform lineage with Ross and routine baseline, and uses routine SCSN templates |
| Canonical local input | `catalogs/SHELLY2020_0220190309/raw_article/SHELLY2020_0220190309__catalog_DataS1.txt` |
| Auxiliary input | `catalogs/SHELLY2020_0220190309/raw/Ridgecrest_2019_correlation_phase_arrivals.csv`; phase-level matched-filter release, not a substitute event catalog |

## Frozen Ridgecrest benchmark window

The case-wide v1 rule is the half-open UTC interval
`2019-07-04T00:00:00Z <= origin_time < 2019-07-07T00:00:00Z`, with the common
mask `35.45 <= latitude <= 36.05`, `-117.90 <= longitude <= -117.20`, and
`0 <= depth_km <= 20`.

| Field | Time-only selection | Common time/space/depth mask |
|---|---:|---:|
| Rows / unique IDs | 7,773 / 7,773 | 7,716 / 7,716 |
| Time range | 2019-07-04 15:35:29.400–2019-07-06 23:59:47.320 UTC | same |
| Latitude | 35.469906–36.036100°N | 35.485217–36.012817°N |
| Longitude | −117.943498–−117.213200°E | −117.819198–−117.255697°E |
| Depth | 0.089–556.580 km | 0.159–19.953 km |
| Magnitude | −0.34–7.10 | −0.10–7.10 |

## Local provenance and next actions

- Paper: `SHELLY2020_0220190309__paper.pdf`
- Parsed paper: `SHELLY2020_0220190309__paper__mineru.md`
- Event catalog: `../../../../catalogs/SHELLY2020_0220190309/raw_article/SHELLY2020_0220190309__catalog_DataS1.txt`
- Metadata: `../../../../catalogs/SHELLY2020_0220190309/raw_article/SHELLY2020_0220190309__metadata_DataS1.xml`
- Official release: [USGS P9JN6H0N](https://doi.org/10.5066/P9JN6H0N)
- Open action: derive station/day availability from waveform request logs if waveform-volume
  benchmarking is required; the event catalog itself does not encode station
  coverage or per-event uncertainty.
