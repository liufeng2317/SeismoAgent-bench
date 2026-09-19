# Cochran et al. (2020) — paper reading

## Identity and role

| Field | Extracted information |
|---|---|
| Citation | Cochran et al. (2020), “Activation of optimally and unfavourably oriented faults in a uniform local stress field during the 2011 Prague, Oklahoma, sequence” |
| DOI | [10.1093/gji/ggaa153](https://doi.org/10.1093/gji/ggaa153) |
| Sequence | 2011 Prague, Oklahoma induced/triggered sequence; the M5.7 mainshock followed the M4.8 foreshock sequence |
| Local paper | `paper/COCHRAN2020_GJIGGAA153__paper.pdf` |
| Parsed text | `paper/COCHRAN2020_GJIGGAA153__paper__mineru.md` and `paper/mineru/` |
| Article type | Research article that extends a template-based detection and relocation catalog |
| Catalog relationship | The paper is a genuine catalog-construction/relocation paper, not only a geological interpretation paper. |

The article uses an enhanced catalog to study activation of multiple fault
planes in a nearly uniform local stress field. Its scientific conclusions
depend on the expanded event population and on relative relocations, so the
file should not be treated as an independent absolute-location truth set.

## Study scope and observations

- Continuous data were collected for roughly 90 days, from 7 November 2011
  through 31 January 2012 (the local catalog extends to 31 January).
- A temporary deployment of 31 seismometers was installed about one week after
  the M4.8 foreshock; 18 local-compass (LC) stations were within roughly
  10–15 km of the sequence. The network combines temporary local stations and
  regional/permanent observations.
- The original catalog supplied about 900 manually picked/template events.
  Its absolute location errors were reported as approximately 750 m
  horizontally and 1.3 km vertically; these values describe the starting
  catalog, not the final relative relocations.
- The paper reports 8,569 high-quality shear-wave-splitting measurements. This
  is a measurement count, not the number of earthquake rows in the catalog.

## Catalog-construction workflow

```text
900-event starting catalog
    → waveform templates from P/S windows
    → continuous template matching (2011-11-07 to 2012-01-31)
    → channel-consistency and correlation screening
    → GrowClust relative relocation
    → bootstrap uncertainty estimation
    → focal-mechanism / fault-activation analysis
```

### Detection and screening

- Templates used 2.0 s waveform windows, beginning 0.5 s before the manually
  picked P or S arrival.
- Matching was run on day-long continuous chunks. A detection was retained
  when at least nine channels exceeded 9 times the median absolute deviation
  threshold.
- Detections within 2 s were consolidated by retaining the one with the
  largest average correlation coefficient.
- The paper explicitly notes a temporal-selection effect: a template catalog
  based on the first part of the sequence is biased toward the first roughly
  ten days. The extended continuous search was intended to reduce that bias.

### Relocation and uncertainty

- Events were relatively relocated with GrowClust using the same velocity model
  as the original HypoDD/Sumy catalog.
- Differential waveform cross-correlation coefficients of at least 0.7 were
  used for the relocation links; template-to-template weights were increased
  by a factor of 100.
- One hundred bootstrap iterations were used to estimate location uncertainty.
- The resulting product is strongest for relative geometry and fault-plane
  structure. It should not be interpreted as a fully independent absolute
  hypocenter catalog.

## Product interpretation

| Aspect | Interpretation |
|---|---|
| Published event population | 8,811 rows in the local catalog release: 900 starting/template events plus 7,911 detected events. |
| Local file coverage | 2011-11-06 01:50:50 to 2012-01-31 23:50:19 UTC; the first row predates the paper’s stated 7 November template-search start because the release includes starting events. |
| Main quality strength | High-sensitivity template detection plus high-precision relative relocation and bootstrap uncertainty. |
| Main limitation | Template and waveform lineage creates dependence between detections and the starting catalog; completeness is time-varying and the absolute reference frame is inherited. |
| Appropriate benchmark role | Primary Q2 enhanced detection/location reference; Q1 relative-location/structural auxiliary when the metric explicitly evaluates relative geometry. |
| Inappropriate use | A universal ground truth for independent event existence, absolute depth, or magnitude completeness. |

## Benchmark extraction record

The benchmark uses the already frozen Prague core window rather than the full
paper span:

| Field | Frozen value |
|---|---|
| Time window | 2011-11-11 00:00:00 to 2011-11-19 00:00:00 UTC, half-open |
| Events in local primary subset | 2,078 |
| Spatial envelope | 35.4523–35.5576°N; −96.8723–−96.7334°E |
| Depth range | 1.02–9.62 km in the frozen subset |
| Magnitude range | approximately ML −0.96 to 3.22 |
| Network condition | 31-station heterogeneous RAMP/USArray/Oklahoma network; station availability must remain time masked |
| Waveform volume estimate | About 22.5 GB as a continuous 31 × 3C × 100 Hz × int32 upper bound for 8 days, before gaps and channel filtering |

These benchmark values come from the case analysis and local catalog audit;
they are not all claims made by the article itself. Any paper-versus-release
discrepancy must remain visible in downstream scoring metadata.

## Local provenance

- Paper PDF: `data/2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/paper/COCHRAN2020_GJIGGAA153__paper.pdf`
- MinerU extraction: `data/2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/paper/mineru/`
- Supplement: `data/2011_prague_oklahoma/references/COCHRAN2020_GJIGGAA153/supplement/`
- Catalog README: `data/2011_prague_oklahoma/catalogs/COCHRAN2020_GJIGGAA153/README.md`
- Catalog file: `data/2011_prague_oklahoma/catalogs/COCHRAN2020_GJIGGAA153/COCHRAN2020_GJIGGAA153__catalog_primary.txt`
