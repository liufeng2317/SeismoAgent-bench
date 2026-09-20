# Pang et al. (2020) — paper reading and catalog-construction audit

## Identity and evidence status

This note separates claims made in Pang et al. (2020) from measurements made on
the locally preserved ISC release.  Quantitative claims below are anchored to
the MinerU page number of the article PDF (the parsed `content_list_v2` has ten
article pages); local measurements are anchored to the catalog summary.

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | Guanning Pang, Keith D. Koper, Maria Mesimeri, Kristine L. Pankow, Ben Baker, Jamie Farrell, James Holt, J. Mark Hale, Paul Roberson, Relu Burlacu, James C. Pechmann, Katherine Whidden, Monique M. Holt, Amir Allam, and Christopher DuRoss | PDF p. 1 title block |
| Title | *Seismic Analysis of the 2020 Magna, Utah, Earthquake Sequence: Evidence for a Listric Wasatch Fault* | PDF p. 1 |
| Journal / year | *Geophysical Research Letters*, 47, e2020GL089798 (2020) | PDF p. 1 citation block |
| DOI | [10.1029/2020GL089798](https://doi.org/10.1029/2020GL089798) | PDF p. 1; local README |
| Article type | Research letter with matched-filter detections and a high-precision relative-relocation product | Abstract; §§3.3 and 3.5 |
| Catalog relationship | The article's relocated-aftershock catalog is deposited at the International Seismological Centre (ISC), DOI [10.31905/9IE6PAF2](https://doi.org/10.31905/9IE6PAF2). The local ISC text file is the release under audit, but it does not expose a separate relocation-status flag. | PDF p. 8 data-availability statement; local file audit |
| Supporting information | The article lists “Supporting Information S1”, but no Pang S1 file is currently staged in this repository. | PDF p. 1; local filesystem check |
| Local parsed paper | [`PANG2020_GL089798__paper__mineru.md`](./PANG2020_GL089798__paper__mineru.md) | MinerU output |

This is a genuine catalog-construction paper, but it is not a universal truth
catalog.  Its strongest product is relative geometry for events that correlate
well with the templates; its detection product is an enhanced, method-specific
catalog whose completeness changes with template coverage, station availability,
and correlation thresholds.

## Scientific scope

- **Sequence:** the 18 March 2020 (M_w 5.7) Magna earthquake and its
  aftershocks beneath the Salt Lake Valley, Utah, in the Wasatch fault system.
  The mainshock epicenter reported by the paper is approximately 40.751°N,
  112.078°W, with a hypocenter about 11.9 km below sea level (PDF p. 2).
- **Scientific question:** whether aftershock geometry and focal mechanisms
  support a shallow, west-dipping/listric Salt Lake City segment of the Wasatch
  fault and what that implies for seismic hazard (abstract; §§1 and 4).
- **Article processing span:** matched filtering used data from 17 March
  (one day before the mainshock) through 30 April 2020, within 40 km of the
  mainshock (PDF p. 5, §3.3).  The paper describes the first approximately six
  weeks after the mainshock; the UUSS routine count is explicitly “as of 30 April”.
- **Article-reported routine population:** 2,103 UUSS locations by 30 April,
  with 2,077 assigned at least one magnitude type (PDF p. 3, §2).
- **Article-reported enhanced population:** 5,501 new aftershocks from
  matched filtering, with no foreshocks under the stated association rules
  (PDF p. 5, §3.3).
- **Article-reported relocation population:** 5,623 aftershocks relocated with
  waveform differential times and hierarchical clustered relocation (PDF p. 6,
  §3.5; Fig. 3).  The mainshock and many larger aftershocks were not relocated
  because their waveforms correlated poorly with the numerous small-event
  templates.
- **Interpretive geometry:** most relocated events define a west-dipping zone at
  8–10 km depth; the preferred plane is approximately strike 159°, dip 21°W.
  A northern subcluster has strike 177°, dip 32°W; a southern subcluster has
  strike 126°, dip about 3°W; a smaller eastern cluster has strike 346°, dip
  63°E (PDF p. 6–7, §3.5).

## Observation and network conditions

| Item | Extracted information | Evidence / status |
|---|---|---|
| Regional network | UUSS combined urban–regional network had 203 seismograph stations: 40 broadband, 97 strong-motion, and 66 short-period sensors at the mainshock (PDF p. 3). | Article-reported; not a station-day availability matrix |
| Strong-motion coverage | 52 UUSS accelerometers within 50 km recorded the mainshock; eight UU NetQuakes and nine NSMP instruments were also used for the mainshock context (PDF p. 3). | Context, not the 39-station matched-filter subset |
| Temporary telemetered additions | Five UUSS temporary installations were added after the mainshock, all within 45 km (PDF p. 3). | Article-reported |
| Nodal deployment | 180 three-component 5-Hz Magseis Fairfield nodal geophones were deployed around the epicentral region in the following week, but Pang et al. explicitly state that nodal data were not used in their study (PDF p. 3). | Keep as a separate Baker observation condition |
| Matched-filter data subset | 39 seismograph stations and 226 channels within 40 km of the mainshock (PDF p. 5, §3.3). | This is the primary waveform condition for reproducing Pang |
| Waveform access | IRIS/EarthScope DMC and the COSMOS Virtual Data Center are named in the data-availability statement (PDF p. 8). | Access route, not a local waveform snapshot |
| Sampling / filter | Data were resampled to a nominal 100 Hz when needed, detrended, and filtered with a one-pass two-pole Butterworth 3–14 Hz bandpass (PDF p. 5). | Article-reported |

The 203-station network total, 39-station matched-filter subset, 52 nearby
accelerometers, and 180 nodal deployment are different quantities.  They must
not be collapsed into one “station count” in benchmark metadata.

## Catalog-construction workflow

```text
UUSS analyst catalog and picks
    → 39-station / 226-channel waveform selection within 40 km
    → 3–14 Hz preprocessing and 100-Hz normalization
    → P/S template extraction from catalog picks
    → channel-wise matched filtering
    → DBSCAN time association and duplicate suppression
    → correlation/RMS-ratio relative magnitudes
    → cross-correlation differential times
    → two-stage hierarchical clustered relative relocation
    → ISC event release
```

### Starting catalog and template preparation

The starting UUSS routine catalog supplied the template picks and initial
locations.  P templates used a −0.2 to 1.6 s window around a catalog pick and S
templates used −0.2 to 2.6 s.  Three-component stations contributed templates on
all available channels.  The paper reports 56,679 P templates and 30,491 S
templates (PDF p. 5, §3.3).

### Detection and association

- Absolute normalized correlation coefficients above 0.6 were retained.  A
  handful of channels used higher thresholds of 0.75–0.90 to limit excessive
  detections (PDF p. 5).
- Two detections from one template closer than 4 s were reduced to the one with
  the larger coefficient.
- DBSCAN grouped detection-derived origin-time estimates when they were within
  0.3 s and each cluster had at least five detections (P or S).
- Events within ±5 s of another detected event or a routine catalog event were
  suppressed; when several candidates remained, the one with the largest sum of
  absolute correlation coefficients was retained (PDF p. 5).
- These rules yielded the article-reported 5,501 new aftershocks and no
  foreshocks.  The local ISC file has 3,595 rows labelled `Template-Matching`,
  so the label count is not numerically identical to the article's 5,501 count;
  do not infer that the two populations are one-to-one without an event
  crosswalk.

### Magnitude estimation

For each new detection, Pang et al. calculated two relative magnitude
perturbations: one from the best-fit correlation scalar and one from an RMS
ratio.  The first was treated as a lower bound, the second as an upper bound,
and their average was used as the preferred estimate (PDF p. 5).  The local
ISC field is named `coda magnitude (Mc)` in the release header.  It should be
preserved as source-native `Mc`; it must not be silently relabelled as a
uniform local, moment, or relative magnitude scale.

### Relative relocation

Waveform cross-correlation differential travel times were inverted with a
hierarchical clustered relocation algorithm (Trugman & Shearer, 2017).  The
workflow first relocated routine catalog events and then added matched-filter
detections with lower weights.  The paper states that alternative station sets,
differential-time criteria, relocation algorithms, and starting locations were
tested for robustness (PDF p. 6, §3.5 and Tables S6–S7).  The mainshock and many
larger aftershocks were excluded from the relative relocation because their
waveforms were too complex to correlate with the small-event templates.

## Reported products and quality control

| Stage | Article-reported value | Local release / interpretation |
|---|---:|---|
| UUSS routine locations by 30 Apr | 2,103 (2,077 with a magnitude type) | Local blank-`eventType` rows total 2,144 and extend to 8 May; this is a release-versus-article discrepancy, not an assumed correction |
| New matched-filter aftershocks | 5,501 | Local rows labelled `Template-Matching`: 3,595 |
| Relocated aftershocks | 5,623 | The local text file has no relocation-status field, so this number cannot be reconstructed by a simple row filter |
| Event rejection | ≥5 detections, ≤0.3 s DBSCAN origin-time spread, ±5 s duplicate/catalog suppression | Parameters explicitly stated in PDF p. 5 |
| Relative-magnitude QC | correlation lower bound + RMS-ratio upper bound averaged | Source field remains `Mc` in ISC release |
| Completeness | No uniform (M_c) is claimed for the enhanced catalog in the main article | Use only for method-specific detection comparisons, not universal recall |

The article's scientific conclusions depend on a selective, well-correlating
subset.  Relative relocation quality is high for that subset, but the catalog
is not guaranteed to be complete at small magnitudes or for events whose
waveforms do not correlate with the template family.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q1** for relative geometry of the successfully clustered events; **Q2** for enhanced detection and event association; **Q3** for completeness or routine operational coverage |
| Primary role | High-precision relative-location target under the 39-station / 226-channel permanent-network condition |
| Secondary role | Matched-filter event recovery and relative-magnitude comparison |
| Independent comparison | Baker et al. ML/nodal release is useful as a secondary condition, but its 180-node deployment and pick-level product must not be merged with Pang's permanent-network target |
| Valid metrics | Matched-event origin-time/epicenter/depth residuals, relative fault-plane geometry, cluster recovery, correlation-threshold sensitivity |
| Invalid or unsafe metrics | Treating every non-Pang event as a false positive; universal completeness recall; direct comparison of source-native `Mc` with Baker `Mxc`, `M_d`, `M_l`, or `M_w` without calibration |
| Independence | Medium–High for a generic agent; lower if the agent uses the same UUSS templates, channels, and differential-time workflow |
| Main limitations | Article/local population mismatch; missing Pang S1; no relocation flag or pick-level uncertainty in the ISC text file; mainshock/larger events selectively excluded from relative relocation |

## Local provenance and remaining actions

- Paper PDF: [`PANG2020_GL089798__paper.pdf`](../../paper/PANG2020_GL089798__paper.pdf)
- MinerU text: [`PANG2020_GL089798__paper__mineru.md`](./PANG2020_GL089798__paper__mineru.md)
- ISC release: [`PANG2020_GL089798__catalog_primary.txt`](../../../../catalogs/PANG2020_GL089798/PANG2020_GL089798__catalog_primary.txt)
- Catalog audit: [`PANG2020_GL089798__catalog_summary.md`](../../../../catalogs/PANG2020_GL089798/PANG2020_GL089798__catalog_summary.md)
- ISC DOI: [10.31905/9IE6PAF2](https://doi.org/10.31905/9IE6PAF2)
- Paper DOI: [10.1029/2020GL089798](https://doi.org/10.1029/2020GL089798)

Before benchmark freeze, obtain Supporting Information S1 if exact Table S2,
Text S1–S3, and robustness parameters are needed.  Preserve both the strict
ISO-time window and the normalized-out-of-range-seconds sensitivity described
in the catalog summary.
