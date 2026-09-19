# Cochran et al. (2020) — paper reading and catalog-construction audit

## Extraction status and evidence convention

This note separates claims made by the article from measurements made on the
local catalog file. Article claims are anchored to a section, figure, table,
or supporting-information item in the parsed MinerU text; local-file claims
are anchored to the catalog summary and its reproducible audit. The PDF is the
authoritative source if the parsed text and a local note disagree.

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | Elizabeth S. Cochran, Robert J. Skoumal, Devin McPhillips, Zachary E. Ross, Katie M. Keranen | PDF first page; MinerU title block |
| Citation | Cochran et al. (2020), “Activation of optimally and unfavourably oriented faults in a uniform local stress field during the 2011 Prague, Oklahoma, sequence” | PDF title page |
| Journal | *Geophysical Journal International*, 222, 153–168 | PDF first page |
| Publication history | Received 2019-02-19; accepted 2020-03-17; Advance Access 2020-03-29 | PDF first page |
| DOI / landing page | [10.1093/gji/ggaa153](https://doi.org/10.1093/gji/ggaa153) | DOI link |
| Article type | Research article with a new template-matched and relatively relocated event catalog; the paper also contains S-wave-splitting and fault-geometry analysis | Summary, Data and Methods, Template matching, Results |
| Local paper | `paper/COCHRAN2020_GJIGGAA153__paper.pdf` | Local provenance |
| Parsed text | `paper/COCHRAN2020_GJIGGAA153__paper__mineru.md` and `paper/mineru/` | MinerU output |

The article is a genuine catalog-construction/relocation paper, but its
scientific conclusions use the catalog to study fault activation and stress
orientation. The product is therefore not an independent absolute-location
truth set: the detections inherit waveform/template and velocity-model
lineage from the starting catalog.

## Sequence and scientific scope

- The sequence is the induced/triggered 2011 Prague, Oklahoma sequence. The
  M5.7 mainshock occurred on **2011-11-06 03:53:10 UTC**, about 20 h after the
  M4.8 foreshock; the largest M4.8 aftershock occurred about 48 h later
  (Introduction, Summary).
- The scientific question is whether the activated fault planes are optimally
  oriented in the local stress field, and what the expanded seismicity implies
  about pore-pressure triggering and fault structure. Catalog enhancement is
  the enabling method, not the only research objective (Summary; Introduction).
- The temporary deployment recorded continuous data for about 90 days through
  **2012-02-01** (Data and Methods). The template search itself covers
  **2011-11-07–2012-01-31** (Template matching section).
- The 900-event starting catalog contains manually picked P and S arrivals and
  events from 2011-11-07 through the end of 2011. Its quoted absolute location
  errors are about 750 m horizontally and 1.3 km vertically; those errors do
  not describe the final GrowClust relative uncertainties (Data and Methods).
- In the article's qualitative description, 94% of the final events lie at
  1.5–6 km depth; the sequence spans approximately 1–10 km (Results, Fig. S4).

## Observation and network conditions

| Item | Extracted information | Evidence / unresolved detail |
|---|---|---|
| Deployment | 31 seismometers installed in approximately one week after the M4.8 foreshock | Data and Methods |
| Local network | 18 LC stations within roughly 10–15 km of the activated faults | Data and Methods; Fig. 1 |
| Other observations | Temporary local stations plus regional/permanent observations | Data and Methods |
| Continuous duration | About 90 days, through 2012-02-01 | Data and Methods |
| Station metadata | Dataloggers, sensors, and sample rates are referred to Sumy et al. (2014) supplementary information | The current paper/SI note does not reproduce the full station/channel table; this remains a benchmark metadata task |
| Waveform preprocessing | 2-s P/S template windows; day-long continuous chunks; cross-correlations summed over phases and channels | Template matching section |
| Availability mask | Not published as a station-day matrix in the current local note | Must be retained when waveform data are staged; do not assume all 31 stations were available for every sample |

## Catalog-construction workflow

```text
900-event Sumy starting catalog with manual P/S picks
    → 2-s P/S waveform templates (0.5 s pre-arrival)
    → day-long continuous template matching, 2011-11-07–2012-01-31
    → channel threshold and 2-s duplicate suppression
    → differential-waveform-time calculation
    → GrowClust relative relocation using the inherited velocity model
    → 100 bootstrap location-uncertainty estimates
    → FaultID/structural analysis (downstream scientific product)
```

### Starting catalog and template formation

The article explicitly attributes the 900-event starting catalog to Sumy et al.
(2017), with manually picked P and S arrivals and relocated hypocentres. Each P or S template uses a 2.0-s window beginning
0.5 s before the picked arrival. If the S arrival occurs before the end of the
P window, the P window is shortened to the S–P time (Template matching
section). This makes the enhanced catalog dependent on the event families
represented in the starting catalog.

### Detection and screening

- Matching is performed against day-long continuous data; correlation
  functions are summed across all template phases and channels.
- A detection is declared when **at least nine channels** exceed a threshold
  of **9 × the median absolute deviation**. The paper does not state that this
  threshold is a magnitude-completeness threshold.
- If detections occur within a 2.0-s window, the one with the largest average
  correlation is retained (Template matching section).
- The ≥0.7 correlation coefficient is a **relocation differential-time link
  criterion**, not the event-detection threshold. Keeping these two thresholds
  separate is essential when reproducing the workflow.

### Relative relocation and uncertainty

- Detections are relocated with GrowClust using default parameters and the
  same velocity model used for the original HypoDD/Sumy catalog.
- Differential times are calculated from waveform cross-correlation pairs;
  pairs with correlation coefficient ≥0.7 are included.
- Template–template pair weights are multiplied by 100 so the better-resolved
  starting events anchor the detections.
- GrowClust bootstrap resampling of input P/S observations uses 100 iterations
  for location uncertainty (Template matching section).
- The article reports median relative uncertainties of **112 m horizontal**
  and **133 m vertical** for relocated detections (Results, immediately after
  the final-catalog count). These are not absolute errors and should not be
  attached to all 8,811 rows without checking row-level fields.

### Downstream fault-geometry processing (not catalog construction)

The paper applies FaultID after relocation. DBSCAN clustering uses at least ten
neighbors and `Dpoint = [1000, 500, 100] m`; RANSAC plane fitting uses
`Dplane = [300, 150, 100] m`, 1,000 random trials per cluster, and rejects
planes with fewer than `[500, 100, 20]` events at the corresponding stages
(Fault identification section; Fig. S1). These parameters describe the
structural interpretation and should not be mistaken for event inclusion rules.

### Separate S-wave-splitting analysis

MFAST is applied to 900 starting events on LC stations, yielding **8,569
high-quality (A/B, δt < 0.20 s) measurements**. This is a measurement count,
not an earthquake-row count, and must never be used as the catalog population
(S-wave splitting section; Results).

## Published product and local-file audit

| Aspect | Article-reported value | Local-file audit / interpretation |
|---|---|---|
| Final population | **8,811 events = 900 templates + 7,911 relocated detections** | Local file has 8,811 rows and 8,811 unique IDs |
| File coverage | Article search starts 2011-11-07; paper describes 90 days through 2012-02-01 | First local row is 2011-11-06 because the release includes starting events; last row is 2012-01-31 23:50:19.578 UTC |
| Time precision | — | Six-part time schema; seconds retain milliseconds (three decimals) |
| Coordinates | Sequence described at roughly 1–10 km depth | Local full-file ranges: lat 35.45013–35.56470°N; lon −96.87954–−96.72730°E; depth 0.261–13.280 km |
| Magnitude | Article gives examples (e.g., M1.71 template; detections about −0.8 to 1.86) but does not define a machine-readable magnitude column in the parsed article | Local range is **−1.36–4.99**. Magnitude type/units are **unresolved**; do not label this field ML until release metadata or SI confirms it |
| Relative uncertainty | Median 112 m horizontal / 133 m vertical for relocated detections | Applies to the relocated detection population, not automatically to templates or every row |
| Lineage | Template-matched detections from the Sumy starting catalog and same velocity model | Not independent of the starting catalog, template family, or waveform archive |

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality/role | **Q2 enhanced-detection and relative-location reference**. It can serve as a **metric-specific Q1 structural auxiliary** for differential geometry, but not as a blanket Q1 truth catalog. |
| Suitable metrics | Event-support recovery, relative geometry, clustering/fault-plane structure, and release-level QC; absolute-location metrics only with explicit inherited-reference caveats |
| Unsuitable metrics | Universal event-existence truth, independent absolute depth/location truth, or magnitude-completeness claims |
| Independence | Reduced when an agent uses the same LC waveforms, templates, or inherited velocity model; report shared-lineage conditions with every score |
| Population bias | Starting templates are concentrated in the first roughly ten days; family/template sensitivity and station availability make completeness time-varying (Results, Fig. S4) |

## Frozen benchmark extraction record

The current Prague v1 time window is retained as a half-open UTC interval. The
two masks below must not be conflated:

| Selection | Event count | Ranges / meaning |
|---|---:|---|
| Time-only: `2011-11-11T00:00:00Z ≤ t < 2011-11-19T00:00:00Z` | **2,078** | Local rows in the stable-network interval; lat 35.45231–35.55757°N, lon −96.87233–−96.73343°E, depth 1.016–9.618 km, magnitude −0.96–3.22 |
| Time + rounded displayed bounds (`lat 35.4523–35.5576`, `lon −96.8723–−96.7334`, `depth 1.02–9.62 km`) | **2,076** | Two rows fall outside the rounded bounds (one at lon −96.87233; one at depth 1.016 km). This is a reproducible secondary mask, not the source of the 2,078 count |

The canonical v1 event-selection rule is the half-open **time-only** window,
which yields **2,078** rows. The exact spatial/depth envelope reported above is
descriptive and derived from those rows; it is not a second exclusion mask.
Retain 2,076 only as the explicitly rounded-mask sensitivity audit. The rule
must be copied verbatim into the benchmark manifest and scoring code.

The continuous-data upper bound for 31 stations × 3 components × 100 Hz ×
int32 × 8 days is **25,712,640,000 bytes = 25.71264 GB decimal ≈ 23.95 GiB**,
before gaps, compression, channel filtering, or station-day availability.

## Local provenance and unresolved actions

- Paper PDF: `data/2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/paper/COCHRAN2020_GJIGGAA153__paper.pdf`
- MinerU extraction: `data/2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/paper/mineru/`
- Supplement: `data/2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/supplement/`
- Catalog README: `data/2011_prague_oklahoma/catalogs/COCHRAN2020_GJIGGAA153/README.md`
- Catalog file: `data/2011_prague_oklahoma/catalogs/COCHRAN2020_GJIGGAA153/COCHRAN2020_GJIGGAA153__catalog_primary.txt`
- Remaining checks: verify the catalog-release URL and magnitude definition from
  the official supplementary package; extract station/channel/sample-rate and
  station-day availability metadata; generate plots without modifying the
  source file.
