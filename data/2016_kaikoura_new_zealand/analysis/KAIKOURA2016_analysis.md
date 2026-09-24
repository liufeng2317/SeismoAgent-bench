# KAIKOURA2016 — Case Analysis

> Current preparation state: `window_status: not_frozen` in [processing.yaml](processing.yaml). Earlier “frozen/v1” windows and counts below are retained as exploratory audit history, not approved evaluation inputs.


> **Source of truth:** This file is the detailed, mutable analysis record for `KAIKOURA2016`. The cross-case summary is maintained in [`docs/01_1_Case_details.md`](../../../docs/01_1_Case_details.md).

## Status

- Case ID: `KAIKOURA2016`
- Phase: reference calibration and data preparation
- Status: `v1 benchmark window frozen`
- Primary reference: Lanza et al. (2019) for location quality
- Secondary references: Tan et al. (2024) SUGAR for dense detection; Chamberlain et al. (2021) for dependent matched-filter expansion
- Frozen v1 primary window: 2016-12-01 to 2016-12-09 UTC
- Optional stress window: 2016-11-13 to 2016-11-20

## Scientific role

Complex multi-fault Mw 7.8 sequence. This is a hard case for 3-D location, relative relocation, changing station geometry, and uncertainty assessment.

## Case information from v0.2 inventory

| Field | Information |
|---|---|
| Region | Northern South Island, New Zealand |
| Sequence type | Mw 7.8 complex multi-fault rupture and aftershock sequence |
| Key event | Mw 7.8 Kaikōura earthquake on 2016-11-13 UTC / 2016-11-14 NZ local date |
| Primary study span | 2016-11-13 to 2017-05-13 |
| Network | GeoNet permanent network plus 24 STREWN temporary instruments |
| Raw waveform access | GeoNet FDSN and AWS Open Data |
| Expected difficulty | High |
| Primary role | Complex 3-D location/relocation and uncertainty |

Lanza starts from 2,768 GeoNet-reviewed approximately-ML≥3 events, obtains 2,655 simul2014 initial locations, and reports 2,013 final clustered HypoDD events (the local XML contains 2,012 HypoDD origins). The study uses phase and waveform cross-correlation differential times with 100 bootstrap relocation samples. Tan reports 46,440 relocated events and a 41,392-event clustered set, but with a different event population and quality target.

## Reference evaluation matrix

| Reference | Evaluation role | Time scope | Spatial scope | Quality tier | Network / observation condition |
|---|---|---|---|---|---|
| Lanza et al. (2019) | Primary: absolute/relative location, 3-D relocation and uncertainty | Full: 2016-11-13–2017-05-13; benchmark: 2016-12-01–12-08 | Kaikōura aftershock region covered by clustered events; freeze offshore/bbox rule | **Q1** location/relative relocation/uncertainty; **Q3** small-event completeness | 81 listed stations (24 STREWN + 57 GeoNet); 3-D model and bootstrap; XML benchmark 122 common-mask rows (generic M) |
| Tan et al. (2024) SUGAR | Secondary: high-rate detection, association and event separation | Same sequence; subset to primary window | Broader detected aftershock population; apply same spatial rule before comparison | **Q2** automatic detection/relative clusters; limited absolute uncertainty | GeoNet waveform data with computer-vision source detection |
| Chamberlain et al. (2021) GrowClust | Dependent secondary: long-duration matched-filter expansion and relative geometry | 2009-01-01–2020-01-01; benchmark subset to primary window | Broad fault-zone catalog; common 0–60 km mask gives 2,214 events | **Q2** overall; metric-specific **Q1** for reported relative relocations | 21 GeoNet stations for detection; STREWN/CRSZ added only for location; templates inherited from Lanza |
| GeoNet reviewed catalog | Baseline | Same frozen window | Same region | **Q3** operational baseline | GeoNet permanent network |

Lanza, Tan and Chamberlain should never be reduced to a single event-count leaderboard. Lanza is the location/uncertainty target; Tan is the dense detection target. The early 2016-11-13–11-20 window should remain a separate permanent-network stress condition.

## Reference products

| Product | Role | Current issue |
|---|---|---|
| Lanza et al. (2019) | Primary location/relocation reference | Paper reading, Text SI/Table S1, and the 134.8 MB Data Set S1 XML are audited. Narrative SI remains under `references/LANZA2019_GL082780/supplement/`; the XML is correctly staged under `catalogs/LANZA2019_GL082780/raw/` and ignored by Git because it exceeds remote-file limits. Local audit: 2,655 event objects, 2,012 HypoDD origins, 123 time-only / 122 common-mask rows. Magnitude type is generic `M`, so 122 must not be called 122 ML≥3. |
| Tan et al. (2024) SUGAR | Secondary high-rate detection reference | Paper, five supplements, Table S10 (67,660-event catalog), Table S11 (46,440 relocated events), and 1,165 associated `.dat` phase files (1,172 ZIP entries including metadata) are staged under `references/TAN2024_JB028735/` and `catalogs/TAN2024_JB028735/`. The final 41,392-event cluster-filtered product is described in the paper but is not separately released as a CSV. |
| GeoNet reviewed catalog | Baseline | Confirm release and stable identifiers. |
| Chamberlain et al. (2021) GrowClust | Dependent secondary catalog | Paper reading and catalog audit are complete: [`paper_reading`](../references/CHAMBERLAIN2021_JB022304/parsed/paper/CHAMBERLAIN2021_JB022304__paper_reading.md) and [`catalog_summary`](../catalogs/CHAMBERLAIN2021_JB022304/README.md). Use the corrected 33,328-unique-event CSV as canonical; retain the legacy 34,704-row export only for provenance comparison. |

## Calibration checklist

- [x] Obtain and audit the Chamberlain corrected catalog and Lanza Data Set S1 XML.
- [x] Extract the Lanza station inventory (81 listed stations; station-day availability remains unresolved).
- [ ] Verify UTC/local-date conventions around the mainshock.
- [ ] Separate the article's approximate ML>=3 selection from the XML generic-M sensitivity and small-event detection evaluation.
- [ ] Subset Lanza and Tan catalogs independently to the same time/space window.
- [ ] Document 3-D velocity-model and bootstrap uncertainty fields.

## Window and data preparation

The 2016-12-01 to 2016-12-08 window is preferred because the temporary STREWN deployment was active. The early post-mainshock window should be treated separately because permanent-network coverage and event overlap are different.

### Frozen v1 benchmark window

| Field | Frozen value |
|---|---|
| Time window | 2016-12-01 00:00:00 to 2016-12-09 00:00:00 UTC (8 days) |
| Event counts | Lanza: 123 XML rows time-only / 122 after the common mask (120 generic-M≥3 sensitivity only); Tan S10: 9,720 SUGAR events; Tan S11: 6,973 relocated events / 6,955 after the common mask; Chamberlain corrected: 2,273 time-only / 2,214 after the common 0–60 km mask |
| Spatial rule | −43.5 to −41.2°S, 172.0 to 175.2°E, depth 0–60 km; apply the same mask to all products before comparison |
| Observed ranges | Lanza common-mask: lat −42.929 to −41.562°, lon 172.768–175.180°E, depth 1.921–37.01 km, generic M 2.2–5.8; Tan S11: lat −43.157 to −41.490°, lon 172.325–174.692°E, depth −1.56–59.64 km, M −0.53–4.87; Chamberlain common-mask: lat −42.973 to −41.500°, lon 172.603–175.183°E, depth 0.008–45.516 km, ML 0.475–5.304 |
| Network condition | 46 GeoNet/STREWN stations, 3-component channels where available; retain permanent versus temporary station flags |
| Waveform volume | Design upper bound: ~33.5 GB for 46 × 3 components × 100 Hz × int32 × 8 days continuous; use actual GeoNet gaps in the prepared manifest |
| Reference quality and role | Lanza: Q1 absolute/relative location and uncertainty, low completeness (generic-M XML); Tan S10/S11: Q2 high-rate detection/relative relocation; Chamberlain: Q2 dependent matched-filter expansion, Q1 only for its reported relative-location subset; GeoNet: Q3 operational baseline |

## Main risks

1. Lanza and Tan optimize different event populations.
2. Temporary-network availability must be matched exactly.
3. Absolute and relative location errors must not be conflated.
4. Lanza's distributed XML preserves a generic `M` scale and 2,012 HypoDD origins versus the article's 2,013; retain both discrepancies.
5. Chamberlain's matched-filter detections inherit Lanza template selection; treat the catalog as a dependent expansion, not a fourth independent truth layer.
6. The corrected CSV has 1,756 complete focal-mechanism rows while the abstract says 1,755; retain this release discrepancy in any focal-mechanism metric.

## Sources

- `../references/LANZA2019_GL082780/paper/LANZA2019_GL082780__paper.pdf`
- `../references/LANZA2019_GL082780/parsed/paper/LANZA2019_GL082780__paper_reading.md`
- `../catalogs/LANZA2019_GL082780/README.md`
- `../references/TAN2024_JB028735/paper/TAN2024_JB028735__paper.pdf`
- `../references/TAN2024_JB028735/parsed/paper/TAN2024_JB028735__paper_reading.md`
- `../catalogs/TAN2024_JB028735/README.md`
- `../references/CHAMBERLAIN2021_JB022304/parsed/paper/CHAMBERLAIN2021_JB022304__paper_reading.md`
- `../catalogs/CHAMBERLAIN2021_JB022304/README.md`
- Lanza et al. (2019), DOI: https://doi.org/10.1029/2019GL082780
- Tan et al. (2024), DOI: https://doi.org/10.1029/2024JB028735
## Full inventory record (migrated from `docs/01_1_Case_details.md`)
### 2016 Kaikōura Earthquake Sequence

## Literature and catalog gap audit

### Added dependent reference — Chamberlain et al. (2021) matched-filter/GrowClust catalog

- Public catalog: https://zenodo.org/record/5035841
- Canonical local copy: `../catalogs/CHAMBERLAIN2021_JB022304/CHAMBERLAIN2021_JB022304__catalog_growclust_corrected_focal_mechanisms.csv` (33,328 unique events; SHA-256 recorded in the catalog summary).
- Legacy comparison copy: `../catalogs/CHAMBERLAIN2021_JB022304/CHAMBERLAIN2021_JB022304__catalog_growclust.csv` (34,704 rows, duplicate/malformed legacy export; do not use for benchmark counts).
- Method: matched-filter workflow using Lanza events as templates followed by NonLinLoc, GrowClust and HypoDD relocation.
- Recommended role: **Q2 dense-detection/relative-location secondary reference**, with a metric-specific Q1 subset for the reported GrowClust relocations.
- Limitation: it is not independent of Lanza because the template population derives from that catalog; use it to measure catalog expansion and dense relative structure, not as an independent absolute-location truth set.

### Verified core products

- Lanza supporting dataset includes arrival times, final relocations and uncertainty information in compressed QuakeML supporting data.
- Tan SUGAR provides associated phases and supporting tables, with code/sample data on Zenodo/GitHub.
- GeoNet FDSN event service provides the operational baseline and stable public event IDs.

### Additional scientific context

Cesca et al. (2017), DOI https://doi.org/10.1016/j.epsl.2017.08.024, provides a rupture/aftershock interpretation but only a much smaller event population; retain it as structural context rather than a principal catalog target.

### Audit conclusion

**Sufficiency verdict:** Sufficient after auditing Lanza as the primary location reference and adding Tan/Chamberlain as complementary detection and dependent-expansion layers. Lanza–Tan–Chamberlain–GeoNet covers location, dense detection, dependent relative expansion, and operational baseline; no single catalog should be used for all dimensions.

#### A. Case information

| Field | Information |
|---|---|
| **Case ID** | KAIKOURA2016 |
| **Region** | Northern South Island, New Zealand |
| **Sequence type** | Mw 7.8 complex multi-fault rupture and aftershock sequence |
| **Key event** | Mw 7.8 Kaikōura earthquake on 2016-11-13 UTC / 2016-11-14 NZ local date |
| **Scientific significance** | Exceptionally complex rupture involving many faults; aftershock location is a demanding test of station geometry, 3-D structure, dense overlapping seismicity, and relocation. |
| **Primary high-precision study span** | 2016-11-13 to 2017-05-13 |
| **Temporary network timing** | 24 STREWN instruments operated from late Nov. 2016 to early May 2017 |
| **Recommended compact benchmark window** | **Primary location benchmark:** 2016-12-01 to 2016-12-08, when the temporary network is active. **Optional hard detection benchmark:** 2016-11-13 to 2016-11-20 using permanent-network coverage. |
| **Network context** | GeoNet permanent network + temporary STREWN network in high-precision relocation study |
| **Raw waveform access** | GeoNet waveforms are openly available through FDSN; GeoNet recommends FDSN for normal requests and AWS Open Data for large volumes. |
| **Expected benchmark difficulty** | High |
| **Primary benchmark role** | Complex multi-fault location/relocation; 3-D velocity-model use; network-geometry effects; dense aftershock detection. |

##### Key sources

- Lanza et al. (2019), *Crustal Fault Connectivity of the Mw 7.8 2016 Kaikōura Earthquake Constrained by Aftershock Relocations*. DOI: <https://doi.org/10.1029/2019GL082780>
- Tan et al. (2024), *Next Generation Seismic Source Detection by Computer Vision: Untangling the Complexity of the 2016 Kaikōura Earthquake Sequence*. DOI: <https://doi.org/10.1029/2024JB028735>
- GeoNet FDSN: <https://www.geonet.org.nz/data/access/FDSN>
- GeoNet seismic waveforms: <https://www.geonet.org.nz/data/types/seismic_waveforms>

#### B. Reference catalog candidates

##### B1. Primary reference — Lanza et al. (2019) high-precision aftershock relocation

| Field | Information |
|---|---|
| **Priority** | **Primary for location quality** |
| **Reference type** | Expert-reviewed-event + high-precision 3-D relocation reference |
| **Paper** | GRL DOI 10.1029/2019GL082780 |
| **Initial event population** | 2,768 GeoNet-reviewed events selected at approximately ML ≥ 3 (article summary often rounds this to ~2,700) |
| **Span** | 2016-11-13 to 2017-05-13 UTC |
| **Stations** | **81 listed stations: 24 STREWN temporary + 57 GeoNet entries**; station-day availability is not encoded in Table S1 |
| **Picking** | REST automatic phase picking, explicitly compared on a 138-event subset with analyst picks |
| **Initial relocation** | simul2014 using a 3-D velocity model |
| **Final relocation** | hypoDD 3-D with phase and waveform cross-correlation differential times |
| **Differential-time data** | 1,359,256 phase-derived + 187,138 cross-correlation-derived differential times |
| **simul2014 relocated events** | 2,655 |
| **Final clustered hypoDD events** | **2,013** |
| **Independent uncertainty assessment** | 100 bootstrap relocation samples |
| **Reported median 95% error-ellipse semiaxes** | ~592 m, 358 m, 426 m in the model-aligned x/y/z directions |
| **Data access** | GeoNet permanent waveforms + temporary STREWN data; local Data Set S1 QuakeML is staged under `catalogs/LANZA2019_GL082780/raw/` (ignored from Git because it is 131.6 MB) |
| **Provisional reference quality** | **High** |
| **Reference independence** | **High–Medium** relative to a generic modern Agent because it uses reviewed events, explicit pick validation, 3-D relocation, waveform cross-correlation, and bootstrap uncertainty |
| **Best benchmark use** | Location/relocation quality, relative geometry, uncertainty calibration |
| **Main limitation** | Focuses on approximately ML≥3, well-observed events and discards many poorly clustered/offshore events; the released XML uses generic `M`, reports 2,012 HypoDD origins rather than the article's 2,013, and is not a completeness target for small earthquakes. |

##### B2. Secondary reference — Tan et al. (2024) SUGAR catalog

| Field | Information |
|---|---|
| **Priority** | Secondary; primary for high-rate detection stress test |
| **Reference type** | Large automatic detection/location + relocated catalog |
| **Paper** | JGR: Solid Earth DOI 10.1029/2024JB028735; open access |
| **Method** | SUGAR: 3-D image-segmentation/computer-vision source detection and location |
| **Detected sequence size** | Paper reports ~5× more events than analyst GeoNet catalog; the application produced a large aftershock catalog |
| **Relocated events** | **46,440** after strict correlation-pair requirements |
| **Final high-quality relocated set** | **41,392 events** after retaining clusters with ≥10 events |
| **Relative relocation** | GrowClust with cross-correlation constraints |
| **Reported uncertainty interpretation** | Relative bootstrap uncertainties <1 km; authors note absolute uncertainties are not accurately known and are expected to be a few km |
| **Waveform source** | GeoNet |
| **Code/data access** | SUGAR code and associated phases are public on [Zenodo 10.5281/zenodo.10937462](https://doi.org/10.5281/zenodo.10937462) and [GitHub](https://github.com/tanfengzhou/SUGAR_kaikoura); supporting catalog tables S10/S11 are archived locally |
| **Provisional reference quality** | Medium–High |
| **Reference independence** | Medium–High relative to conventional phase-pick/associate/location workflows |
| **Best benchmark use** | Dense early aftershock detection and event separation; cross-method comparison |
| **Main limitation** | Automatic method with different quality target from Lanza; not an absolute-location truth set. |

##### B3. Baseline / additional methodological reference

| Product | Role |
|---|---|
| GeoNet reviewed catalog | Operational baseline |
| Chamberlain et al. (2021), DOI 10.1029/2021JB022304 | Dependent matched-filter/GrowClust comparison; use corrected CSV (2,214 common-mask events) for expansion/relative-geometry metrics, not as an independent truth catalog |

#### C. Benchmark suitability

| Field | Assessment |
|---|---|
| **Recommended for core benchmark?** | **Yes, but use after the easier U.S. cases are operational** |
| **Primary target** | Lanza et al. for location reliability |
| **Secondary target** | Tan et al. for high-rate detection/association stress testing; Chamberlain for dependent matched-filter expansion and relative geometry |
| **Baseline** | GeoNet reviewed catalog |
| **Recommended primary window** | 2016-12-01 to 2016-12-08 |
| **Optional stress window** | 2016-11-13 to 2016-11-20 |
| **Short-window target event count** | Lanza 122 released XML rows after the common mask (120 generic-M≥3 sensitivity); Tan S10 9,720; Tan S11 6,973 time-only / 6,955 common-mask; Chamberlain corrected 2,214 after the common mask (2,273 time-only) |
| **Approximate waveform volume** | ~33.5 GB continuous upper bound for 46 stations × 3C × 100 Hz × int32 × 8 days |
| **Expected compute cost** | High |
| **Key benchmark risk** | Primary and secondary catalogs optimize different event populations and use different network/time conditions; direct event-count ranking would be misleading |
| **Overall assessment** | Excellent hard benchmark for the later benchmark tier, especially for location robustness and complex sequence handling. |

---

---

## Catalog processing

Processing entry points and product declarations are in [processing.yaml](processing.yaml). Shared identifier and output rules are maintained in [data organization](../../README.md#processing-and-output-policy). File-level counts, schemas and figures belong to the catalog README and its generated analysis, rather than a second case index.

### Product-specific processing matrix

| Catalog | Product(s) | Role | Special handling |
|---|---|---|---|
| Chamberlain | corrected GrowClust; legacy release | Primary corrected event/focal-mechanism reference | Compare legacy IDs and focal mechanisms; never concatenate. |
| Lanza | QuakeML preferred origins | Relocated event reference | Prefer HypoDD origin; retain SIMUL-only events and origin method. |
| Tan SUGAR | S10, S11, phase archive, S12 | Detection, relocation, picks, mechanisms | Keep S10/S11 separate; reconstruct 41,392 cluster filter; phase rows are not events. |
| GeoNet | Full and frozen operational snapshots | Q3 baseline | Preserve EventID and native M/ML labels; not high-resolution truth. |

### Expected outputs

- Event products: compact map, daily rate, and depth panel where coordinates exist.
- Chamberlain: corrected-versus-legacy release comparison.
- Lanza: origin-method composition and preferred-origin map.
- Tan: S10/S11 maps and cluster-size distribution; phase station/phase summary; S12 focal-mechanism counts.
- GeoNet: operational benchmark map/rate figure; full snapshot statistics-only.

Existing catalog summaries contain the detailed file-level audits. The parsers must reproduce those counts and preserve strict/normalized parsing sensitivities.
