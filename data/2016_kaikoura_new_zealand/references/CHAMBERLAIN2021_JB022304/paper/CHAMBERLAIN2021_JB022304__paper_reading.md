# Chamberlain et al. (2021) — paper reading and catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | C. J. Chamberlain, W. B. Frank, F. Lanza, J. Townend, E. Warren Smith | PDF p. 1 title block |
| Title | *Illuminating the Pre-, Co-, and Post-Seismic Phases of the 2016 M7.8 Kaikōura Earthquake With 10 Years of Seismicity* | PDF p. 1 |
| Journal | *Journal of Geophysical Research: Solid Earth*, 126, e2021JB022304 | PDF p. 1 citation block |
| DOI | [10.1029/2021JB022304](https://doi.org/10.1029/2021JB022304) | DOI / article PDF |
| Article type | Research article that constructs a 10-year matched-filter catalog, then performs absolute and relative location/relocation | Abstract; Sections 2–3 |
| Official data/code release | Zenodo record [6763130](https://zenodo.org/record/6763130); article data availability says CSV and QuakeML are provided | PDF pp. 21–22 |
| Version status | The PDF includes a correction notice: the initial focal-mechanism catalog was erroneous; data, SI, figures and software were replaced. The corrected version is the version of record. | PDF p. 24 erratum |
| Local paper parse | `paper/CHAMBERLAIN2021_JB022304__paper__mineru.md`; MinerU `content_list` page indices were used as PDF-page anchors | Local parse audit |

This is a genuine catalog-construction paper. It is not an independent absolute
truth set: its template population is inherited from Lanza et al. (2019), and
its matched-filter detections are therefore conditioned on the morphology of
those templates.

## Scientific scope and observation conditions

- Sequence: the 2016 Mw 7.8 Kaikōura earthquake and the surrounding pre-, co-
and post-seismic activity in northern South Island, New Zealand.
- Catalog span: 1 January 2009 through 1 January 2020 (the latter is an
exclusive endpoint in the workflow description; PDF pp. 5, 8).
- Template selection: 2,654 Lanza et al. aftershocks plus the mainshock. The
starting set contains GeoNet events with `ML >= 3` between 13 November 2016 and
13 May 2017 UTC in −43.00 to −40.80° latitude and 172.75–175.20° longitude,
excluding 110 events with poorly constrained depths (PDF p. 5).
- Detection network: 21 GeoNet broadband and short-period stations. Strong-
motion instruments and temporary STREWN stations were excluded from the
matched-filter detection stage to avoid timing/network-density bias (PDF p. 5).
- Location-only additions: four STREWN stations around Cape Campbell and GeoNet
CRSZ were added to improve locations after detection; they did not define the
detection population (PDF p. 6).
- Focal-mechanism observations: STREWN and GeoNet strong-motion stations were
used for manual first-motion polarity, but their arrival timing was not used in
location (PDF p. 7).
- Waveform archive: GeoNet FDSN for permanent stations and IRIS FDSN for STREWN
(code Z1), as stated in the data availability section (PDF p. 21).

## Catalog-construction workflow

```text
Lanza ML>=3 template events
    -> 21-station continuous waveform extraction
    -> 30-Hz resampling and 1.5–12-Hz Butterworth filtering
    -> 4-s P/S template windows and SNR >= 4 channel mask
    -> EQcorrscan matched-filter detection
    -> cross-correlation phase-pick correction
    -> HYPOCENTER / 1-D Okada-model RMS quality control
    -> NonLinLoc absolute locations in NZ3D v2.2
    -> automatic Wood–Anderson amplitude picks and local magnitudes
    -> GrowClust and HypoDD relative relocation
    -> catalog + focal mechanisms for a template subset
```

### Templates and detection

- Continuous day-long data were detrended, frequency-domain resampled to 30 Hz,
filtered with a fourth-order Butterworth 1.5–12 Hz bandpass, and trimmed to 4 s
around P and S picks. Channels with SNR below 4 were removed; templates with
fewer than five stations were removed, leaving 2,584 templates (PDF p. 5).
- Detections were computed with EQcorrscan from 2009-01-01 through 2020-01-01,
using FFTW and, when available, the FMF GPU implementation (PDF p. 5).
- The parsed MinerU text renders the threshold as `10� ×` because a Unicode
symbol was replaced. The surrounding sentence indicates a summed-correlation
threshold of 10 times the median absolute deviation of the day-long stack,
together with mean normalized correlation > 0.15. Treat the exact symbol as
provisional until visually checked against the PDF before exact reproduction
(PDF p. 5; local parse contains U+FFFD).
- Detections from individual templates were separated by at least 4 s; within
1 s, only the highest-average-correlation detection was retained (PDF p. 5).

### Picking, association and absolute location

- A ±0.5 s cross-correlation window around the assumed pick was searched; a pick
was accepted when the maximum normalized correlation exceeded 0.4 (PDF p. 6).
- Requiring picks on at least five stations produced 33,343 detections and
899,460 phase picks. HYPOCENTER with the 1-D Okada et al. (2019) model was then
used to remove the largest-residual pick iteratively until RMS < 1 s or fewer
than five stations remained. This removed 30 events, leaving 33,328 events and
896,727 phase picks (PDF p. 6).
- NonLinLoc with the New Zealand-wide 3-D NZ3D v2.2 model was used for absolute
locations. All events were located; 32,939 were within the study region because
389 fell outside it (PDF p. 6).

### Magnitude and relative relocation

- Automatic amplitude picks were made on filtered, Wood–Anderson-simulated
traces. Local magnitudes were calibrated to moment magnitude using GeoNet
moment-tensor data and the Ristau scale (PDF p. 6).
- GrowClust and HypoDD 2.1b were both run. GrowClust used an average 1-D model
extracted from NZ3D; HypoDD used NZ3D v2.2. The authors report GrowClust because
its bootstrap uncertainties were more robust. Relative relocations were
obtained for 27,431 events (PDF pp. 6, 8).
- The catalog's local CSV has 50 events without a magnitude. The maximum local
magnitude is 6.3129, which includes the mainshock and is outside the reliable
range of an amplitude-based local-magnitude scale; the paper explicitly warns
about this (PDF p. 8).

### Focal mechanisms

- Manual P-polarity determinations were made for template events and inverted
with the Bayesian method of Walsh et al. (2009). Solutions required polarity
picks at more than eight stations (PDF p. 7).
- The abstract reports 1,755 mechanisms; the corrected local CSV contains 1,756
rows with complete strike/dip/rake/kappa/scalar-error fields. This one-row
difference is retained as an unresolved article-versus-release discrepancy,
not silently rounded away.

## Reported populations and quality controls

| Processing stage | Count | Evidence |
|---|---:|---|
| Lanza starting template events | 2,654 | PDF p. 5 |
| Templates after SNR/station filtering | 2,584 | PDF p. 5 |
| Cross-correlation detections after station-pick threshold | 33,343 events / 899,460 picks | PDF p. 6 |
| After HYPOCENTER RMS QC | 33,328 events / 896,727 picks | PDF p. 6 |
| Inside the study region after NonLinLoc | 32,939 | PDF p. 6 |
| GrowClust relative relocations | 27,431 | PDF pp. 6, 8 |
| Focal mechanisms | 1,755 in abstract; 1,756 complete rows locally | PDF p. 1 / corrected CSV |

The final catalog is dense and methodologically sophisticated, but it is not a
complete event census. It is template-conditioned, has time-varying detection
capability, and reports substantially different absolute and relative location
uncertainties. The study itself warns that an absence of subduction-interface
events may reflect the aftershock-derived template set (PDF p. 16 in the
article discussion).

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q2 dense matched-filter catalog**, with a **Q1 metric-specific relative-location/uncertainty subset** for the 27,431 GrowClust events |
| Primary role | Long-duration detection expansion, relative geometry, GrowClust uncertainty and complex-fault structure |
| Suitable metrics | Detection support, relative-location error, cluster geometry, station-coverage sensitivity, uncertainty calibration |
| Unsuitable metric | Universal completeness or absolute-location truth for all events; direct event-count ranking against Lanza/Tan |
| Dependence | High dependence on Lanza templates; shared GeoNet/IRIS waveform archives and NZ3D model |
| Canonical local input | Corrected focal-mechanism CSV, with the legacy CSV retained only for provenance comparison |
| Main limitation | No explicit relocation-status flag in the CSV; the paper's 27,431 relocated count cannot be reconstructed from a single obvious column without the Zenodo code/QuakeML lineage |

## Kaikōura frozen benchmark window

The case-level v1 rule is the half-open UTC window
`2016-12-01T00:00:00Z <= origin_time < 2016-12-09T00:00:00Z`, with the common
spatial/depth mask `-43.5 <= latitude <= -41.2`, `172.0 <= longitude <= 175.2`,
and `0 <= depth_km <= 60`. Applying the rule to the corrected CSV gives:

| Field | Time-only window | Common time/space/depth mask |
|---|---:|---:|
| Events / unique IDs | 2,273 / 2,273 | 2,214 / 2,214 |
| Time range | 2016-12-01 00:03:58.705 to 2016-12-08 23:54:15.046341 UTC | same |
| Latitude | −43.878229–−40.889090° | −42.973046–−41.500135° |
| Longitude | 172.602810–175.183344°E | 172.602810–175.183344°E |
| Depth | −2.980469–96.687500 km | 0.007812–45.515625 km |
| Local magnitude | 0.475050–5.303747; 2 missing | 0.475050–5.303747; 2 missing |
| Complete focal mechanisms | 114 | 113 |

The 59 time-window rows removed by the common mask include negative depths,
very deep solutions, and events outside the case latitude range. The 2,273
count is the catalog-local time audit; 2,214 is the comparable benchmark count.

## Local provenance and open actions

- Paper PDF: `data/2016_kaikoura_new_zealand/references/CHAMBERLAIN2021_JB022304/paper/CHAMBERLAIN2021_JB022304__paper.pdf`
- Parsed paper: `data/2016_kaikoura_new_zealand/references/CHAMBERLAIN2021_JB022304/paper/CHAMBERLAIN2021_JB022304__paper__mineru.md`
- Corrected canonical catalog: `data/2016_kaikoura_new_zealand/catalogs/CHAMBERLAIN2021_JB022304/CHAMBERLAIN2021_JB022304__catalog_growclust_corrected_focal_mechanisms.csv`
- Legacy Zenodo CSV: `data/2016_kaikoura_new_zealand/catalogs/CHAMBERLAIN2021_JB022304/CHAMBERLAIN2021_JB022304__catalog_growclust.csv`
- Official release: [Zenodo 5035841](https://zenodo.org/records/5035841) for the legacy product; corrected data/code archive is identified by the article as Zenodo 6763130.
- Required follow-up: preserve the Zenodo QuakeML/software archive if exact relocation-status flags, focal-mechanism provenance, or reproducibility of the 27,431 subset is required; visually verify the `10× MAD` threshold in the source PDF.
