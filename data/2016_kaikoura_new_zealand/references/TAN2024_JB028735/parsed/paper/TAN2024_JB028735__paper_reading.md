# Tan et al. (2024) — paper reading and SUGAR catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | Fengzhou Tan, Honn Kao, Kwang Moo Yi, Edwin Nissen, Chet Goerzen, Jesse Hutchinson, Dawei Gao, Amir M. Farahbod | PDF title block |
| Title | *Next Generation Seismic Source Detection by Computer Vision: Untangling the Complexity of the 2016 Kaikōura Earthquake Sequence* | PDF title/abstract |
| Journal / DOI | *Journal of Geophysical Research: Solid Earth*; DOI [10.1029/2024JB028735](https://doi.org/10.1029/2024JB028735) | Article metadata |
| Article type | Research article that introduces SUGAR and constructs a machine-assisted event catalog, then relocates a quality-controlled subset with GrowClust | Abstract; §§2–4 |
| Local paper parse | `parsed/TAN2024_JB028735__paper__mineru.md` | MinerU output; quantitative claims below retain section/figure/SI anchors |
| Public products | Wiley SI S09–S12 and Zenodo software/phase archive [10.5281/zenodo.10937462](https://doi.org/10.5281/zenodo.10937462) | Local files and article Data Availability statement |

This is a genuine catalog-construction paper, not merely a review or method
proposal. Its catalog is a strong dense-detection reference, but it should not
be treated as an absolute-location truth set: the neural network is trained for
the Kaikōura station geometry, the initial search uses a fixed 10-km depth, and
the authors expect absolute errors of a few kilometres after relocation.

## Scientific scope and observation conditions

- Sequence: the 13 November 2016 (M_w 7.8) Kaikōura earthquake and its
  immediate aftershock sequence in northern South Island, New Zealand.
- Application span: 48.5 days from the mainshock origin on 2016-11-13 through
  2016-12-31 23:59 UTC (PDF §4; Table S10). The local S10 maximum timestamp is
  `2016-12-31T23:59:15.180Z`.
- Main application network: 46 GeoNet stations listed in Table S9 (all local
  `geonet` entries, with vertical and two horizontal channels). The paper notes
  small approximately ±1-s timing errors at 9 selected stations; tests found
  little effect on the result (PDF §4; Tables S8–S9).
- Waveform archive: GeoNet seismic waveforms. The workflow uses the New Zealand
  3-D seismic velocity model 2.3 for the real-data application (PDF §4).
- The network and model are sequence/site specific. Reproducing SUGAR in a new
  case would require retraining or transfer learning; the authors explicitly
  caution against applying the Kaikōura-trained model unchanged (PDF §5).

## Catalog-construction workflow

```text
GeoNet waveforms + 46-station geometry
    -> 5–20 Hz preprocessing and minute-wise median normalization
    -> source-scanning brightness video (4-km grid, fixed 10-km depth)
    -> 3-D U-Net semantic segmentation / prediction-score video
    -> candidate merging from brightness and U-Net maxima
    -> guided P/S picking (Earthquake Transformer for real data)
    -> time/amplitude association and maximum-intersection location
    -> local-magnitude estimation with station correction
    -> SUGAR event catalog (Table S10)
    -> waveform cross-correlation (1–10 Hz, 2-s P/S windows)
    -> GrowClust relocation (Table S11)
    -> retain clusters with >=10 events (reported 41,392-event final set)
```

### Detection and initial location

- Brightness videos are built hourly on a 4-km latitude/longitude grid with a
  fixed 10-km search depth. Waveforms are stacked from 1.5 s before to 4.5 s
  after predicted arrivals after 5–20 Hz filtering (PDF §2.2.1).
- The 3-D U-Net input is a 60×60×60 pixel block; output is a 20×20×20 central
  block, with 0.5-s time pixels and 4-km horizontal pixels (PDF §2.1–2.2.2).
  Training uses 194,559 synthetic samples for 20 epochs; this is a synthetic
  training workflow, not supervised training on the released event catalog.
- For the real application the prediction-score threshold is 1.0. The paper
  reports >0.93 precision in the synthetic test at this setting and chooses it
  for the Kaikōura run (PDF §3.1 and §4; SI S2/S8).
- Guided phase picking uses Earthquake Transformer for real data. Candidate
  phases are selected from the 20 closest stations and within predicted-arrival
  windows; fewer than two qualified P or two qualified S phases deletes a
  candidate. The final association thresholds are distance-dependent P/S time
  residual limits plus magnitude residual `dm < 1.2` (PDF §2.2.3, Equations 5–7).
- Maximum-intersection refinement searches ±6 km in latitude/longitude and
  0–60 km depth. An event is retained when the intersection quality is
  (Q_e >= 0.6) or the total phase count is at least 10 (PDF §2.2.3).
- Magnitudes use a local Richter-style equation with Rhoades et al. (2021)
  constants, synthesized Wood–Anderson amplitudes, a factor-of-two P-wave
  amplitude correction, and a station correction in the final pass (PDF
  §2.2.3–2.2.4). The intermediate phase-reference magnitude is not the final
  catalog magnitude.

### Relocation and quality control

- S10 contains 67,660 detected/located events. The paper manually adds GeoNet
  solutions for the (M_w 7.8) mainshock and the largest aftershock because the
  point-source/training assumptions and Earthquake Transformer are unreliable
  for very large events (PDF §4; Table S10).
- GrowClust uses 1–10 Hz filtered waveforms and 2-s windows around P/S picks (or
  predicted arrivals). Event pairs require at least eight cross-correlation
  coefficients above 0.65. This yields 46,440 relocated events in Table S11
  (PDF §4; Table S11).
- The paper then retains only clusters with at least 10 events, reporting a
  41,392-event high-quality set. A separate 41,392-row table is not included in
  the local Wiley supplements; S11 is the released 46,440-row intermediate.
- Relative bootstrap uncertainties are reported below 1 km. Absolute errors are
  not directly estimated and are expected to be a few kilometres because most
  travel-time residuals are below 1 s (PDF §4).

## Reported products and quality controls

| Stage / product | Article value | Local evidence |
|---|---:|---|
| GeoNet comparison catalog | 10,861 events in the 13 Nov–31 Dec region/time comparison | PDF §1 / §4 |
| SUGAR catalog S10 | 67,660 events | S10 local audit: 67,660 unique rows |
| GrowClust relocated S11 | 46,440 events | S11 local audit: 46,440 unique rows; every S11 ID is in S10 |
| Cluster-filtered final set | 41,392 events (clusters ≥10) | Article §4; no separate local table |
| Additional focal mechanisms | 55 (12 events >M4 plus 43 smaller events) | Table S12 has 55 data rows |
| Station inventory | 46 stations | Table S9 has 46 rows, all `geonet` |
| Associated phases | Article says associated SUGAR phases are public | Local archive has 1,165 `.dat` phase files, 1,382,337 phase rows, 68,462 event IDs and 45 station codes; archive also contains macOS metadata entries |

The paper's 67,660 and 46,440 counts align exactly with the local S10/S11
row counts. The 41,392 value is a post-S11 cluster filter and must not be
silently substituted for the released S11 table.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q2** dense detection/association and relative relocation; metric-specific Q1 only for the reported clustered relative geometry, not absolute location |
| Primary role | High-rate event recovery, phase-association stress testing, and comparison of overlapping-event detection |
| Suitable metrics | Detection recall/precision against explicitly defined comparison catalogs; origin-time/relative-location error; cluster geometry; phase-count and relocation-support analysis |
| Unsuitable metrics | Treating SUGAR as universal absolute truth, direct b-value comparison without magnitude calibration, or applying its trained model to a different station geometry without retraining |
| Independence | Medium–High from Lanza/Chamberlain event tables because the detection workflow is different and uses synthetic training, but not observationally independent: it uses the same regional GeoNet waveform archive and a related velocity-model context |
| Main biases | Site-specific network geometry; fixed-depth initial scan; large-event miss/manual insertion; early-sequence waveform overlap; depth-dependent error (larger near <3 km and >17 km); released S11 precedes the final ≥10-event cluster filter |

For this benchmark, use S10 for dense detection and S11 for released relocated
geometry. If the final 41,392 cluster membership is required, obtain or
recompute it from the S11 `cluster id`/`events in cluster` fields rather than
claiming that S11 itself is the final product.

## Frozen Kaikōura benchmark window

Use the case rule
`2016-12-01T00:00:00Z <= origin_time < 2016-12-09T00:00:00Z`, with the common
case mask `-43.5 <= latitude <= -41.2`, `172.0 <= longitude <= 175.2`, and
`0 <= depth_km <= 60`.

| Product | Time-only rows | Common-mask rows | Common-mask ranges |
|---|---:|---:|---|
| S10 SUGAR catalog | 9,720 | **9,720** | lat −43.420057–−41.218655; lon 172.032762–175.133776; depth 0–60 km; M −0.53–4.87 |
| S11 released relocated table | 6,973 | **6,955** | lat −43.157440–−41.490090; lon 172.325240–174.692110; depth 0.008–59.641 km; M −0.53–4.87 |

The 18 S11 time-window rows removed by the common mask have negative depth or
lie outside the common geographic bounds. S10's values happen to all satisfy
the current case mask in this window; that is a property of this selection,
not a guarantee for other windows.

## Local provenance and open actions

- Paper PDF: `data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/paper/TAN2024_JB028735__paper.pdf`
- Parsed paper: `.../parsed/TAN2024_JB028735__paper__mineru.md`
- Supporting PDF and tables: `.../supplement/2024jb028735-sup-0001-supporting information si-s01.pdf` and `.../si-s09.xlsx`–`si-s12.xlsx`
- Canonical catalog files: `.../catalogs/TAN2024_JB028735/TAN2024_JB028735__catalog_sugar_S10.xlsx` and `...__catalog_sugar_relocated_S11.xlsx`
- Phase archive: `.../TAN2024_JB028735__phases_associated.zip`; extracted `.dat` files are under `phases/`.
- Required follow-up: keep station-day availability and the final ≥10-event cluster membership explicit; do not label the generic S10/S11 magnitude column as a separate ML scale without calibration.
