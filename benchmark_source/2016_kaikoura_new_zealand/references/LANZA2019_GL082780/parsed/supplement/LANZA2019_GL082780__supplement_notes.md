# Lanza et al. (2019) — supporting-information audit

## Source bundle

The local supporting-information bundle for DOI [10.1029/2019GL082780](https://doi.org/10.1029/2019GL082780) contains:

| Product | Local path | Role | Status |
|---|---|---|---|
| Text SI (S1–S6, Figs. S1–S13, Table S2/captions) | `grl59060-sup-0001-text_si-s01.docx` | Processing methods, error discussion, figure/table captions | present |
| Table S1 workbook | `grl59060-sup-0002-tables1.xlsx` | Station list used for picking and relocation | present |
| Data Set S1 | `grl59060-sup-0003-ds01.xml` | QuakeML relocated origins and phase picks | catalog product; staged under `catalogs/LANZA2019_GL082780/raw/` |

The publisher's Text SI says that the separately uploaded Data Set S1 contains
the catalog of relocated hypocenters and P/S pick times. It is therefore not a
second narrative supplement: it is the machine-readable catalog and is audited
in the catalog summary.

## Processing details extracted from Text SI

### Input population and REST

- REST was applied to **2,768 GeoNet-selected events**. Three events failed to
  be picked/located, leaving **2,765** events with REST results.
- Traces were resampled to 100 Hz when needed and bandpass filtered from 1–20
  Hz with a six-pole Bessel filter. The REST detection window was 420 s with
  60 s overlap. The grid-search volume was 536 × 660 × 400 km with 4 km grid
  spacing; its northwestern corner was 171.38°E, 39.0°S (Text S1, §1.1).
- The initial final pick totals were 117,568 P and 91,659 S arrivals. kpick
  added 16,245 S and 1,599 P arrivals. After removing S picks with uncertainty
  >0.6 s, unpaired S picks, and picks with absolute travel-time residual ≥2 s,
  73,783 S picks remained. A 0.2 s P residual threshold left 114,140 P picks
  (Text S1, §1.1).

The XML release contains 110,810 P and 72,149 S pick elements, all with
`methodID=smi:local/REST`. This is lower than the Text SI high-quality totals
and does not expose a separate `kpick` method label. Treat the published XML
as the authoritative released pick product, but retain this count discrepancy
as an unresolved provenance issue rather than silently reconstructing picks.

### Location and relocation

- Initial locations use **simul2014** with fixed New Zealand-wide 3-D Vp and
  Vp/Vs models (smaller 340 × 500 km inversion region). Pick uncertainty is
  weighted from 0–4; uncertainty <0.02 s receives the highest weight and >0.5
  s the lowest (main paper §4.1; Text SI).
- The Text SI/main paper report **2,655 simul2014 initial locations**. **110
  events with poor depth constraints are excluded** from the final clustered
  interpretation; the released QuakeML nevertheless retains 2,655 event
  objects, while only the clustered subset has HypoDD origins.
- HypoDD 3-D uses phase-derived and waveform cross-correlation differential
  times. Event-pair separation is ≤10 km and normalized cross-correlation is
  >0.65 in the paper's analysis. The published final text reports 2,013
  clustered events; the local XML contains **2,012 `HypoDD` origins**. This
  one-event discrepancy must remain explicit until the publisher's original
  release metadata resolves it.
- Relocation is repeated for 100 bootstrap samples. Median 95% error-ellipse
  semimajor axes are approximately 592, 358, and 426 m in model-aligned x, y,
  and z directions (main paper §4.2; Text S4/S5). These are population-level
  summaries, not per-row uncertainties in the XML.

### Network and station product

Table S1 contains **81 stations** used in picking/relocation:

- **24 STREWN** temporary three-component instruments (10 broadband and 14
  short-period sensors); continuous 100 samples/s recording with GPS timing;
- **57 GeoNet** permanent/strong-motion stations selected within roughly 300 km
  of Cape Campbell.

The main paper describes the 24 STREWN instruments as operating for about six
months from late November 2016 to early May 2017. Text SI Figure S1 identifies
some strong-motion sites excluded after manual review for poor data quality or
timing. The station table is a static inventory, not a station-day
availability matrix; availability must not be inferred from the 81-station
count.

## Quality and interpretation notes

- Text S2 finds NonLinLoc agrees with simul2014/HypoDD near Cape Campbell but
  tends to place events offshore and deeper near Kaikōura where coverage and
  velocity resolution are poorer. This motivates retaining the algorithm and
  network provenance in benchmark comparisons.
- Text S3 reports little systematic bias when STREWN stations are removed;
  mean changes are approximately 0.013 km in depth, 0.047 km in latitude, and
  0.046 km in longitude. These are network-sensitivity checks, not absolute
  location errors.
- Text S4 estimates most simul2014 model-related absolute uncertainties are
  <2 km for an assumed slowness uncertainty of ~0.02 s/km; this is an upper
  bound estimate and should not be confused with the much smaller relative
  HypoDD bootstrap semiaxes.
- Text S5 explicitly calls the 10 km event-pair and cross-correlation
  thresholds somewhat arbitrary; they trade event retention against velocity
  heterogeneity and relative-location uncertainty.

## Evidence anchors

- Main paper: `parsed/paper/LANZA2019_GL082780__paper__mineru.md`, especially the
  `Data Sets`, `Methods`, §§4.1–4.2, and §6 conclusion blocks (MinerU
  `content_list_v2` pages 2–7).
- Text SI: `Text S1` for REST and pick QC; `Text S2` for NonLinLoc;
  `Text S3–S5` for network bias, absolute error, and HypoDD thresholds;
  Figure S1 caption and `Table S1` caption for station instrumentation;
  `Data Set S1` caption for QuakeML semantics.

