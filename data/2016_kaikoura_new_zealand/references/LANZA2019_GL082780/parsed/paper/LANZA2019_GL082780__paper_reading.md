# Lanza et al. (2019) — paper reading and catalog-construction audit

## Extraction status and evidence convention

This note separates statements made by Lanza et al. from measurements made on
the locally preserved QuakeML release. The article PDF and its supporting
information are authoritative when a parsed text block and a local audit do
not agree. Main-paper anchors below refer to sections/figures in the MinerU
output; supplementary claims cite the specific Text S or Table S1 product.

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | F. Lanza, C. J. Chamberlain, K. Jacobs, E. Warren-Smith, H. J. Godfrey, M. Kortink, C. H. Thurber, M. K. Savage, J. Townend, S. Roecker, and D. Eberhart-Phillips | PDF title block, MinerU `content_list_v2` p. 1 |
| Citation | “Crustal Fault Connectivity of the M 7.8 2016 Kaikōura Earthquake Constrained by Aftershock Relocations” | PDF title block |
| Journal | *Geophysical Research Letters*, 46, 6487–6496 (2019) | PDF citation block |
| DOI / landing page | [10.1029/2019GL082780](https://doi.org/10.1029/2019GL082780) | DOI in article and local README |
| Article type | Research letter with a new high-precision aftershock relocation catalog; not an operational catalog paper | Abstract, §§2–4 |
| Catalog relationship | The paper's primary output is the relocated hypocenter/pick product distributed as Data Set S1 (QuakeML) | Main-paper acknowledgements/conclusion; Text SI Data Set S1 caption |
| Local paper | `paper/LANZA2019_GL082780__paper.pdf` | Local provenance |
| Parsed text | `parsed/LANZA2019_GL082780__paper__mineru.md` and `mineru/.../content_list_v2.json` | MinerU output |

The article is a genuine catalog-construction and relocation study. It starts
from a reviewed GeoNet event population, improves phase picks with REST/kpick,
uses a fixed 3-D model for initial locations, and applies 3-D HypoDD with
waveform differential times to a clustered subset. It is therefore an expert
location/relative-relocation reference, not an independent completeness or
small-event truth catalog.

## Scientific scope

- **Sequence:** the 14 November 2016 (UTC date convention in the paper)
  `M_w 7.8` Kaikōura earthquake and its northern South Island aftershocks.
  The sequence spans the complex multi-fault Marlborough fault system and the
  Hikurangi subduction-interface setting (Introduction, MinerU p. 2).
- **Question:** whether high-precision aftershock hypocenters reveal
  connections between mapped surface-rupturing faults and whether seismicity
  occurred on the subduction interface during the postseismic period
  (Introduction and §§5–6).
- **Article selection:** approximately 2,700 GeoNet-reviewed events with local
  magnitude `M_L >= 3`, between **2016-11-13 and 2017-05-13 UTC**, in the
  rectangle **40.80°S–43.00°S, 172.75°E–175.20°E** (main paper §2).
  The Text SI gives the more exact selected population as **2,768** events
  before REST; this is the source population, not the final QuakeML row count.
- **Reported populations:** REST successfully picked/located 2,765 of 2,768
  inputs (Text S1); simul2014 produced 2,655 initial locations (main §4.1);
  the article reports 2,013 clustered HypoDD events (main §4.2). The local
  XML has 2,655 event objects, of which 2,012 contain a HypoDD origin. Both
  article and local values must be retained until the one-event discrepancy is
  resolved.
- **Scientific emphasis:** the final catalog is optimized for fault geometry
  and location precision. The paper reports 92% of simul2014 and 99% of
  HypoDD locations above 18 km, and identifies only eight likely interface
  events (main §5.2 and conclusion). This is not evidence that the catalog is
  complete below the `M_L >= 3` selection threshold.

## Observation and network conditions

| Item | Extracted information | Evidence / status |
|---|---|---|
| Permanent network | Selected GeoNet short-period, broadband, and strong-motion instruments within roughly 300 km of Cape Campbell | Main §2; Table S1 |
| Temporary network | 24 STREWN instruments deployed in northern South Island/southern North Island; about six months from late Nov. 2016 to early May 2017 | Main §2; Text S1 Figure S1 caption |
| Station inventory | Table S1 contains 81 stations used in picking/relocation: 24 STREWN + 57 GeoNet entries | `grl59060-sup-0002-tables1.xlsx` audit |
| STREWN sensors | 10 three-component broadband and 14 three-component short-period sensors; Reftek 130/Taurus digitizers; GPS timing | Text SI Figure S1 caption |
| Sampling | Continuous STREWN recording at 100 samples/s | Text SI Figure S1 caption |
| Availability caveat | Some strong-motion sites were excluded after manual review for poor data quality/timing; Table S1 is not a station-day availability matrix | Text SI Figure S1 caption; no station-day file locally |
| Waveform archive | GeoNet waveforms plus STREWN data through IRIS DMC (network code Z1) | Main acknowledgements |
| Network stress | STREWN coverage is absent or incomplete for the earliest part of the sequence; location quality is poorer where station geometry and 3-D model resolution are sparse | Main §4; Text S2–S3 |

The 81-station inventory must not be interpreted as 81 continuously available
stations for every event. The benchmark should preserve permanent versus
temporary network flags and station-day gaps when waveform data are prepared.

## Catalog-construction workflow

```text
GeoNet-reviewed M_L >= 3 event list (2,768 inputs)
    → REST hybrid detection/onset estimation
    → kpick supplementation of S/P phases
    → phase uncertainty/residual and P–S pairing QC
    → simul2014 initial locations with fixed 3-D Vp/Vp/Vs model
    → HypoDD 3-D relocation using phase and waveform differential times
    → 100-sample bootstrap uncertainty assessment
    → QuakeML origins, magnitudes, picks, and arrival metadata
```

### Starting population and automated phase picking

REST combines a modified nearest-neighbor similarity detector with an
autoregressive onset estimator (main §3; Text S1). In the SI implementation,
traces are resampled to 100 Hz when needed and filtered 1–20 Hz with a
six-pole Bessel filter. A 420-s moving window with 60-s overlap and a
536 × 660 × 400 km, 4-km grid are used for the initial detection/location
stage (Text S1 §1.1).

REST is evaluated against manual picks for two subsets (48 events with
`M >= 3` and 103 events with `M >= 4`, drawn from 46 stations; Text S1
§1.2). kpick is then used to add S picks and some P picks. The published QC
retains S picks with estimated uncertainty <=0.6 s, paired P/S phases, and
absolute travel-time residual <2.0 s; the P residual threshold is 0.2 s
(Text S1 §1.2). The SI reports 114,140 high-quality P and 73,783 high-quality
S picks, whereas the distributed XML contains 110,810 P and 72,149 S pick
elements, all labelled `methodID=smi:local/REST`. This release-versus-SI count
and method-label difference is documented, not silently corrected.

### Initial and final location

The initial location uses `simul2014` with fixed New Zealand-wide 3-D Vp and
Vp/Vs models and a smaller 340 × 500 km inversion region (main §§3–4.1).
Pick uncertainty receives a 0–4 weight, with the highest weight for
uncertainty <0.02 s and the lowest for >0.5 s. The weighted RMS misfit falls
from 0.31 to 0.23 s; 110 events have poor depth constraints and are not used
for the clustered interpretation (main §4.1).

HypoDD 3-D uses 1,359,256 phase-derived and 187,138 waveform
cross-correlation differential times. Pairs are constrained to a maximum
hypocenter separation of 10 km and normalized cross-correlation coefficient
greater than 0.65. This removes about 24% of the initial events and gives the
reported 2,013-event clustered product (main §4.2). The SI explicitly notes
that these thresholds are a trade-off between event retention and velocity
heterogeneity (Text S5).

The article repeats the relocation for 100 bootstrap resamples. Median 95%
confidence error-ellipse semimajor axes are approximately 592, 358, and 426 m
in model-aligned x, y, and z directions (main §4.2). These are population-level
relative-location summaries; the local XML does not expose a complete per-event
bootstrap uncertainty table.

### Downstream interpretation (not event-inclusion rules)

The paper uses NonLinLoc as a diagnostic comparison, focal mechanisms for the
eight possible interface events, and fault/aftershock geometry figures. Those
products inform structural interpretation but are not additional catalog
filters. NonLinLoc tends to move events offshore/deeper near Kaikōura where
station coverage and velocity resolution are weaker (Text S2).

## Local QuakeML audit

The catalog file is the official Data Set S1 XML staged at
`catalogs/LANZA2019_GL082780/raw/grl59060-sup-0003-ds01.xml`. It contains one
QuakeML `event` object per row-like event, with event public IDs, one or two
origins, one magnitude element, and associated picks/arrivals.

| Field | Local audit result | Interpretation |
|---|---:|---|
| Event objects | **2,655** | 2,655 unique `smi:local/2017p...` event IDs; no exact duplicate IDs |
| Origin objects | 2,655 `SIMUL` + 2,012 `HypoDD` | 2,012 events have both; 643 have only SIMUL |
| Preferred origin behavior | 2,012 preferred HypoDD; 643 have no `preferredOriginID` and fall back to their sole SIMUL origin | Preserve this missing-link condition in normalization |
| Magnitudes | 2,655 values, generic type `M` | No `preferredMagnitudeID`; source magnitude scale is unresolved. Do not relabel as `M_L` without release metadata |
| Picks | 110,810 P + 72,149 S = **182,959** | All local pick methods are labelled `REST`; XML total is lower than SI high-quality totals |
| Stations in picks | **81** unique station codes | Matches Table S1 inventory count |
| Pick uncertainty | 0.02–0.55 s for populated XML pick uncertainties | These are pick-level fields, not event location error ellipses |
| Time precision | Six fractional digits in XML timestamps | Retain at least microsecond text precision during parsing; scoring may round explicitly |
| Full time range | 2016-11-13T11:02:56.460000Z – 2017-05-13T18:03:47.100000Z | UTC; local XML range |
| Full preferred-origin latitude | −43.28217 to −40.08467° | Broader than article selection rectangle because SIMUL-only/outlying origins are retained |
| Full preferred-origin longitude | 172.06067–175.26200°E | Same caveat |
| Full preferred-origin depth | −0.94–164.12 km | 16 negative-depth values and 35 values >=50 km; inspect method/quality before masking |
| Full magnitude range | 2.2–7.4 (`M`) | Generic source scale; not equivalent to article's stated `M_L >= 3` criterion |

The method split matters: preferred HypoDD origins span 2,012 events and depths
0.045–41.389 km, while the 643 SIMUL-only events include the negative and very
deep outliers. The XML has no `quality` child for HypoDD origins, whereas the
SIMUL origins expose used phase count, standard error, azimuthal gap, and
minimum distance. Do not infer that missing HypoDD quality fields mean zero
uncertainty.

## Frozen benchmark window

The Kaikōura case currently uses the half-open window
`2016-12-01T00:00:00Z <= origin_time < 2016-12-09T00:00:00Z`, with common mask
`-43.5 <= latitude <= -41.2`, `172.0 <= longitude <= 175.2`, and
`0 <= depth_km <= 60`. Applying the masks to the local XML gives:

| Selection | Events | Methods | Ranges |
|---|---:|---|---|
| Time only | 123 | 110 HypoDD + 13 SIMUL | lat −42.92922–−41.56183; lon 172.76817–175.18033; depth 1.921–75.91 km; generic `M` 2.2–5.8 |
| Time + common spatial/depth mask | **122** | 110 HypoDD + 12 SIMUL | lat −42.92922–−41.56183; lon 172.76817–175.18033; depth 1.921–37.01 km; generic `M` 2.2–5.8 |

The article's input description says `M_L >= 3`, but the XML's generic `M`
field has two masked rows below 3. Therefore the reproducible benchmark label
is **122 XML events under the common mask**, not “122 ML≥3 events.” A separate
`M >= 3` sensitivity count is 120, but it must not be used as the canonical
count until the source magnitude scale is resolved.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q1 location/relative-relocation reference** for the well-observed clustered population; **Q3 for small-event completeness** because the source is preselected at approximately `M_L >= 3` and excludes poorly clustered/offshore events |
| Primary role | Absolute/relative hypocenter quality, 3-D relocation geometry, and uncertainty calibration |
| Secondary role | Reference for fault connectivity and method-specific event matching against Tan SUGAR and Chamberlain GrowClust |
| Suitable metrics | Origin-time/epicenter/depth residuals for matched events; relative geometry; clustering/fault-plane structure; uncertainty-aware location scores |
| Unsuitable metrics | Universal detection recall, event-rate completeness, small-event magnitude-of-completeness, or treating every non-Lanza event as false |
| Independence | Medium–high relative to a generic agent because of reviewed input events, explicit pick validation, 3-D model, waveform differential times, and bootstrap checks; lower if the agent uses the same GeoNet/STREWN waveforms or templates |
| Main limitations | Generic magnitude field; one-event article/XML HypoDD count discrepancy; no complete station-day matrix; QuakeML pick totals/method labels differ from SI totals; sparse/offshore geometry is known to be weaker |

Lanza should remain the primary location reference in this case, while Tan's
SUGAR products serve the denser automatic-detection role and GeoNet serves the
operational baseline. Do not merge event IDs or rank the products by raw event
count.

## Local provenance and remaining actions

- Paper PDF: `data/2016_kaikoura_new_zealand/references/LANZA2019_GL082780/paper/LANZA2019_GL082780__paper.pdf`
- MinerU text: `data/2016_kaikoura_new_zealand/references/LANZA2019_GL082780/parsed/LANZA2019_GL082780__paper__mineru.md`
- Text SI: `data/2016_kaikoura_new_zealand/references/LANZA2019_GL082780/supplement/grl59060-sup-0001-text_si-s01.docx`
- Station Table S1: `data/2016_kaikoura_new_zealand/references/LANZA2019_GL082780/supplement/grl59060-sup-0002-tables1.xlsx`
- QuakeML Data Set S1: `data/2016_kaikoura_new_zealand/catalogs/LANZA2019_GL082780/raw/grl59060-sup-0003-ds01.xml`
- Supplement notes: `../parsed/supplement/LANZA2019_GL082780__supplement_notes.md`

Before benchmark freeze, resolve or explicitly retain:

1. the article's 2,013 versus local XML's 2,012 HypoDD-origin count;
2. the generic XML magnitude scale and the two masked rows below 3;
3. the difference between SI high-quality pick totals and XML pick totals;
4. station-day availability and the exact list of strong-motion sites excluded;
5. a reproducible event crosswalk to Tan SUGAR, Chamberlain GrowClust, and the
   GeoNet operational baseline without treating any one product as universal
   ground truth.

