# QuakeFlow (Zhu et al., 2022) — paper and evaluation audit

## Scope and evidence convention

This note separates the peer-reviewed QuakeFlow workflow paper from the
locally supplied catalog-QC evaluation document. Claims about the workflow and
the Hawaii application are extracted from the MinerU text of the GJI paper;
claims about catalog comparison/QC practice are taken from the evaluation
document. Neither document is treated as a machine-readable Hawaii event
catalog. Local-file observations are explicitly labelled as such.

## Identity and local provenance

| Item | Result | Evidence / status |
|---|---|---|
| Article | W. Zhu, A. B. Hou, R. Yang, A. Datta, S. M. Mousavi, W. L. Ellsworth & G. C. Beroza, “QuakeFlow: a scalable machine-learning-based earthquake monitoring workflow with cloud computing” | Local PDF title/author block |
| Journal / DOI | *Geophysical Journal International*, 232(1), 684–693; [10.1093/gji/ggac355](https://doi.org/10.1093/gji/ggac355) | Local README and article citation |
| Publication evidence | Accepted 2022-08-31; article body reports the Puerto Rico and Hawaiʻi applications | MinerU article text |
| Code release | QuakeFlow code DOI [10.5281/zenodo.7023970](https://doi.org/10.5281/zenodo.7023970); source repository [AI4EPS/QuakeFlow](https://github.com/AI4EPS/QuakeFlow) | Article Data Availability |
| Evaluation document | `QUAKEFLOW_GJI_GGAC355__evaluation.pdf`; catalog-QC slides/notes supplied locally, bibliographic identity not verified | It is not assumed to be a second peer-reviewed article |
| Article PDF SHA-256 | `7a0d011e41b075837b1474b1ccde4062b274f464d10d93471c170f0dea6b3a16` | Local-file audit |
| Evaluation PDF SHA-256 | `65973b92710bcce5eb4bcd4ac07dc47667ed2855beafa30e3c6cf8d4c0124e63` | Local-file audit |

The GJI paper is a genuine workflow/method paper and does report a Hawaii
experiment. It is not, by itself, evidence that a Hawaii event table was
published or deposited. The code DOI is a code release, not a catalog DOI.

## Scientific purpose and what was actually run

The paper's primary objective is to make large-scale earthquake monitoring
portable and computationally scalable: continuous waveforms are processed by
containerized machine-learning components in batch or streaming mode on
Kubernetes/Kubeflow. The scientific Hawaii example is used to demonstrate
enhanced volcanic-earthquake detection and broad magmatic-system structure,
not to publish a benchmark-ready event table.

The paper states that Hawaii processing found more than an order of magnitude
more events than the standard HVO catalog and revealed deep Pahala activity,
rift-system seismicity, and lineations toward Kīlauea. Those are article-level
claims; no exact Hawaii event count, event ID range, frozen time window, or
downloadable row-level table is given in the local article text.

## Input data and observation conditions

| Component | Article-reported information | Benchmark consequence |
|---|---|---|
| Waveforms | Continuous seismic waveforms retrieved with ObsPy from seismic data centres; the article Data Availability names the HVO, USGS, and Puerto Rico networks | Source networks are identifiable, but a Hawaii request manifest is not supplied |
| Hawaii network | **66 HVO stations** were used for the Hawaii application | This is an article station count, not a local station/channel-day inventory; do not replace the case's separate HVO/Shelly/Wei manifests with it |
| Time/space scope | Hawaii figures show a broad-island application; the article text does not state a machine-readable start/end time or exact bounding box | It cannot be aligned to the Kīlauea summit v1 window without a reconstruction run |
| Station availability | No station-day, channel, sample-rate, gap, or response table is included in the local article/evaluation files | Waveform volume and coverage cannot be audited from this reference |
| Reference catalog | HVO standard catalog is shown as an orange comparison in the figures; no frozen query or local HVO snapshot is embedded in the paper | The HVO/USGS baseline staged elsewhere must not be relabeled as QuakeFlow output |

## Workflow and catalog construction

The article's generic batch/stream workflow is:

```text
continuous waveforms (ObsPy / SeedLink)
    → PhaseNet P/S phase picks
    → GaMMA probabilistic phase association
       + approximate origin location and magnitude
    → optional/available relocation components (HypoDD is described in the
      workflow architecture)
    → event records in MongoDB / Kafka web application
```

Important distinctions for the Hawaii application:

1. PhaseNet is a pretrained convolutional neural network that predicts P and S
   characteristic functions and arrival times.
2. GaMMA clusters picks using a probabilistic Gaussian-mixture formulation and
   uses arrival time, phase type, amplitude, and pick quality to estimate an
   approximate event location and magnitude.
3. The paper describes HypoDD as a relocation component in the general
   workflow. However, the Hawaii results explicitly state that the plotted
   earthquakes are located with PhaseNet arrival-time measurements and suggest
   adding cross-correlation arrival times in future work. Therefore a released
   Hawaii QuakeFlow table must not be assumed to contain HypoDD or high-
   precision relative locations.
4. The streaming implementation uses SeedLink, Kafka, Spark Streaming,
   FastAPI, and MongoDB. These are deployment components, not evidence of a
   deposited event catalog.

## Catalog fields and quality control

### What the GJI article exposes

The Hawaii article figures contain event frequency, approximate magnitude,
map views, and depth cross-sections. The text says the magnitudes are
approximately estimated during GaMMA association. It does **not** provide a
machine-readable schema, stable event IDs, exact magnitude type, pick table,
origin uncertainty, relocation flag, or per-event QC status. No local file can
therefore be audited for fields, row count, coordinate/depth/magnitude ranges,
or checksum.

### What the supplied evaluation document contributes

The evaluation PDF is useful methodological context, not a Hawaii catalog. It
recommends:

- matching enhanced and reference events by explicit origin-time and spatial
  tolerances (the approximately 5 s / 25 km values are illustrative examples,
  not QuakeFlow-Hawaii benchmark rules);
- separating `MATCH`, `MISSED`, and `NEW` events;
- inspecting map views, depth sections, magnitude-frequency distributions,
  magnitude/time and rate plots, and waveform/pick overlays;
- checking false detections in coda/noise, association failures, unrealistic
  depths, quarry blasts/infrasound/teleseismic signals, and uneven station
  geometry;
- saving the exact reference-catalog snapshot because operational catalogs
  change after analyst review.

The examples in the document are for Puerto Rico, Ridgecrest, SCSN, Texas, and
other regions. They do not supply a Hawaii QuakeFlow event file or a
Hawaii-specific validation table.

## Article–catalog alignment decision

| Question | Decision |
|---|---|
| Is this a genuine catalog-construction work? | **Yes, at the workflow/application level.** The paper says QuakeFlow generated Hawaii results from HVO waveforms. |
| Is a dedicated Hawaii event catalog locally staged? | **No.** Only the paper, code references, and evaluation document are local. |
| Can HVO/USGS, Shelly, Wei, Matoza, or Lengliné files stand in for QuakeFlow output? | **No.** They are independent products and must retain their own `source_ref`. |
| Can the paper's “>10×” statement be used as a local event count? | **No.** It is a qualitative/article-level comparison without a released numerator, denominator, or frozen query. |
| Can it be a Q1/Q2 reference catalog now? | **No.** It is methodological context / a future reproduction target, not a scored reference layer. |

## Benchmark role and limitations

- **Current role:** context for a modern PhaseNet → GaMMA workflow and for
  designing catalog-QC checks; not a truth catalog and not a baseline row count.
- **Method independence:** potentially useful as a cross-method comparison
  because its detector/associator differ from the Shelly matched-filter and
  Wei/Matoza products, but independence cannot be scored until an original
  output is obtained and its waveform/network lineage is recorded.
- **Known limitations:** approximate GaMMA magnitudes; association and
  location errors; no explicit Hawaii QC thresholds in the article; broad,
  unspecified time/space scope; changing HVO station availability; and no
  published row-level uncertainty or relocation-membership table in the local
  materials.
- **Interpretation risk:** “more events than HVO” does not imply higher
  precision or completeness. The article itself notes hyperparameter-dependent
  false-positive/false-negative trade-offs in the workflow discussion.

## Acquisition / reproduction gate

Keep the manifest catalog status **missing** until one of the following is
available:

1. an author/repository/DOI file explicitly identified as the Hawaii QuakeFlow
   event output; or
2. a reproducible local run with a pinned QuakeFlow code revision, model
   versions, HVO station/channel inventory, exact waveform time span and
   spatial bounds, all association/QC parameters, and a checksum of the
   generated event and pick tables.

For a future Kīlauea reproduction, preserve at least:
`event_id`, `origin_time_utc`, `latitude`, `longitude`, `depth_km`, approximate
`magnitude`, magnitude method, associated pick count, station count, pick
probabilities, location/association uncertainty, and a `source_ref` that
distinguishes QuakeFlow output from the HVO comparison catalog.

## Local paths

- Article PDF: `QUAKEFLOW_GJI_GGAC355__paper.pdf`
- Article MinerU text: `QUAKEFLOW_GJI_GGAC355__paper__mineru.md`
- Evaluation PDF: `QUAKEFLOW_GJI_GGAC355__evaluation.pdf`
- Evaluation MinerU text: `QUAKEFLOW_GJI_GGAC355__evaluation__mineru.md`
- Existing availability decision: `../README.md` (paper/code-ready,
  catalog-missing)
