# KAIKOURA2016 — Case Analysis

> **Source of truth:** This file is the detailed, mutable analysis record for `KAIKOURA2016`. The cross-case summary is maintained in [`docs/01_Case_details.md`](../../../docs/01_Case_details.md).

## Status

- Case ID: `KAIKOURA2016`
- Phase: reference calibration and data preparation
- Status: `v1 benchmark window frozen`
- Primary reference: Lanza et al. (2019) for location quality
- Secondary reference: Tan et al. (2024) SUGAR for dense detection
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

Lanza starts from approximately 2,700 GeoNet-reviewed ML≥3 events, obtains 2,655 initially relocated events and retains 2,013 final clustered hypoDD events. The study uses phase and waveform cross-correlation differential times with 100 bootstrap relocation samples. Tan reports 46,440 relocated events and a 41,392-event clustered set, but with a different event population and quality target.

## Reference evaluation matrix

| Reference | Evaluation role | Time scope | Spatial scope | Quality tier | Network / observation condition |
|---|---|---|---|---|---|
| Lanza et al. (2019) | Primary: absolute/relative location, 3-D relocation and uncertainty | Full: 2016-11-13–2017-05-13; benchmark: 2016-12-01–12-08 | Kaikōura aftershock region covered by clustered events; freeze offshore/bbox rule | **Q1** location/relative relocation/uncertainty; **Q3** small-event completeness | GeoNet permanent + 24 STREWN temporary instruments; 3-D model and bootstrap |
| Tan et al. (2024) SUGAR | Secondary: high-rate detection, association and event separation | Same sequence; subset to primary window | Broader detected aftershock population; apply same spatial rule before comparison | **Q2** automatic detection/relative clusters; limited absolute uncertainty | GeoNet waveform data with computer-vision source detection |
| GeoNet reviewed catalog | Baseline | Same frozen window | Same region | **Q3** operational baseline | GeoNet permanent network |

Lanza and Tan should never be reduced to a single event-count leaderboard. Lanza is the location/uncertainty target; Tan is the dense detection target. The early 2016-11-13–11-20 window should remain a separate permanent-network stress condition.

## Reference products

| Product | Role | Current issue |
|---|---|---|
| Lanza et al. (2019) | Primary location/relocation reference | Paper and supplement are staged under `references/LANZA2019_GL082780/`; supplement includes text SI, Tables 1, and the 134.8 MB relocation/source XML. Exact station subset and benchmark-window event count still need extraction. It is not a completeness target for small events. |
| Tan et al. (2024) SUGAR | Secondary high-rate detection reference | Paper, five supplements, Table S10 (67,660-event catalog), Table S11 (46,440 relocated events), and 1,172 associated phase files are staged under `references/TAN2024_JB028735/` and `catalogs/TAN2024_JB028735/`. The final 41,392-event cluster-filtered product is described in the paper but is not separately released as a CSV. |
| GeoNet reviewed catalog | Baseline | Confirm release and stable identifiers. |
| Chamberlain et al. (2021) GrowClust | Dependent secondary catalog | Original Zenodo CSV and a separately staged corrected focal-mechanism CSV are available under `catalogs/CHAMBERLAIN2021_JB022304/`; retain both schemas for cross-version comparison. |

## Calibration checklist

- [ ] Obtain distributed catalogs and supporting uncertainty products.
- [ ] Extract the STREWN and GeoNet station list from the supplementary material.
- [ ] Verify UTC/local-date conventions around the mainshock.
- [ ] Separate ML>=3 relocation evaluation from small-event detection evaluation.
- [ ] Subset Lanza and Tan catalogs independently to the same time/space window.
- [ ] Document 3-D velocity-model and bootstrap uncertainty fields.

## Window and data preparation

The 2016-12-01 to 2016-12-08 window is preferred because the temporary STREWN deployment was active. The early post-mainshock window should be treated separately because permanent-network coverage and event overlap are different.

### Frozen v1 benchmark window

| Field | Frozen value |
|---|---|
| Time window | 2016-12-01 00:00:00 to 2016-12-09 00:00:00 UTC (8 days) |
| Event counts | Lanza: 122 ML≥3 relocated events after the common 0–60 km mask; Tan S10: 9,720 SUGAR events; Tan S11: 6,973 relocated events in the same window |
| Spatial rule | −43.5 to −41.2°S, 172.0 to 175.2°E, depth 0–60 km; apply the same mask to all products before comparison |
| Observed ranges | Lanza: lat −42.930 to −41.562°, lon 172.768–175.180°E, depth 2.67–37.01 km; Tan S11: lat −43.157 to −41.490°, lon 172.325–174.692°E, depth −1.56–59.64 km, M −0.53–4.87 |
| Network condition | 46 GeoNet/STREWN stations, 3-component channels where available; retain permanent versus temporary station flags |
| Waveform volume | Design upper bound: ~33.5 GB for 46 × 3 components × 100 Hz × int32 × 8 days continuous; use actual GeoNet gaps in the prepared manifest |
| Reference quality and role | Lanza: Q1 absolute/relative location and uncertainty, low completeness; Tan S10/S11: Q2 high-rate detection/relative relocation; GeoNet: Q3 operational baseline |

## Main risks

1. Lanza and Tan optimize different event populations.
2. Temporary-network availability must be matched exactly.
3. Absolute and relative location errors must not be conflated.

## Sources

- `../references/LANZA2019_GL082780/paper/LANZA2019_GL082780__paper.pdf`
- `../references/TAN2024_JB028735/paper/TAN2024_JB028735__paper.pdf`
- Lanza et al. (2019), DOI: https://doi.org/10.1029/2019GL082780
- Tan et al. (2024), DOI: https://doi.org/10.1029/2024JB028735
## Full inventory record (migrated from `docs/01_Case_details.md`)
### 2016 Kaikōura Earthquake Sequence

## Literature and catalog gap audit

### Added dependent reference — Chamberlain et al. (2021) matched-filter/GrowClust catalog

- Public catalog: https://zenodo.org/record/5035841
- Local copy: `../catalogs/CHAMBERLAIN2021_JB022304/CHAMBERLAIN2021_JB022304__catalog_growclust.csv` (34,704 event rows; Zenodo CSV export, SHA-256 recorded in `data/REFERENCES_MANIFEST.md`).
- Method: matched-filter workflow using Lanza events as templates followed by GrowClust relocation.
- Recommended role: **Q2 dense-detection/relative-location secondary reference**.
- Limitation: it is not independent of Lanza because the template population derives from that catalog; use it to measure catalog expansion and dense relative structure, not as an independent absolute-location truth set.

### Verified core products

- Lanza supporting dataset includes arrival times, final relocations and uncertainty information in compressed QuakeML supporting data.
- Tan SUGAR provides associated phases and supporting tables, with code/sample data on Zenodo/GitHub.
- GeoNet FDSN event service provides the operational baseline and stable public event IDs.

### Additional scientific context

Cesca et al. (2017), DOI https://doi.org/10.1016/j.epsl.2017.08.024, provides a rupture/aftershock interpretation but only a much smaller event population; retain it as structural context rather than a principal catalog target.

### Audit conclusion

**Sufficiency verdict:** Sufficient after adding Chamberlain as a dependent secondary catalog, which is now locally available. Lanza–Tan–Chamberlain–GeoNet covers location, dense detection, dependent relative expansion, and operational baseline; no single catalog should be used for all dimensions.

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
| **Initial event population** | ~2,700 GeoNet-reviewed events with ML ≥ 3 |
| **Span** | 2016-11-13 to 2017-05-13 UTC |
| **Stations** | **24 STREWN temporary instruments + selected GeoNet permanent instruments**; exact total used should be extracted from Table S1 before benchmark freeze |
| **Picking** | REST automatic phase picking, explicitly compared on a 138-event subset with analyst picks |
| **Initial relocation** | simul2014 using a 3-D velocity model |
| **Final relocation** | hypoDD 3-D with phase and waveform cross-correlation differential times |
| **Differential-time data** | 1,359,256 phase-derived + 187,138 cross-correlation-derived differential times |
| **simul2014 relocated events** | 2,655 |
| **Final clustered hypoDD events** | **2,013** |
| **Independent uncertainty assessment** | 100 bootstrap relocation samples |
| **Reported median 95% error-ellipse semiaxes** | ~592 m, 358 m, 426 m in the model-aligned x/y/z directions |
| **Data access** | GeoNet permanent waveforms + temporary STREWN data described in the study; supporting information includes relocation products/uncertainties |
| **Provisional reference quality** | **High** |
| **Reference independence** | **High–Medium** relative to a generic modern Agent because it uses reviewed events, explicit pick validation, 3-D relocation, waveform cross-correlation, and bootstrap uncertainty |
| **Best benchmark use** | Location/relocation quality, relative geometry, uncertainty calibration |
| **Main limitation** | Focuses on ML≥3, well-observed events and discards many poorly clustered/offshore events; not a completeness target for small earthquakes. |

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
| Chamberlain et al. (2021), DOI 10.1029/2021JB022304 | Useful matched-filter/GrowClust comparison, but the study spans a much longer interval and should not be a core target in the short-window benchmark |

#### C. Benchmark suitability

| Field | Assessment |
|---|---|
| **Recommended for core benchmark?** | **Yes, but use after the easier U.S. cases are operational** |
| **Primary target** | Lanza et al. for location reliability |
| **Secondary target** | Tan et al. for high-rate detection/association stress testing |
| **Baseline** | GeoNet reviewed catalog |
| **Recommended primary window** | 2016-12-01 to 2016-12-08 |
| **Optional stress window** | 2016-11-13 to 2016-11-20 |
| **Short-window target event count** | Lanza 122; Tan S10 9,720; Tan S11 6,973 after the common time/space/depth mask |
| **Approximate waveform volume** | ~33.5 GB continuous upper bound for 46 stations × 3C × 100 Hz × int32 × 8 days |
| **Expected compute cost** | High |
| **Key benchmark risk** | Primary and secondary catalogs optimize different event populations and use different network/time conditions; direct event-count ranking would be misleading |
| **Overall assessment** | Excellent hard benchmark for the later benchmark tier, especially for location robustness and complex sequence handling. |

---

---
