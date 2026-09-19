# MAGNA2020 — Case Analysis

> **Source of truth:** This file is the detailed, mutable analysis record for `MAGNA2020`. The cross-case summary is maintained in [`docs/01_Case_details.md`](../../../docs/01_Case_details.md).

## Status

- Case ID: `MAGNA2020`
- Phase: reference calibration and data preparation
- Status: `v1 benchmark window frozen`
- Primary reference: Pang et al. (2020)
- Secondary reference: Baker et al. (2021) ML/nodal catalog
- Frozen v1 core window: 2020-03-18 to 2020-03-26 UTC

## Scientific role

Moderate mainshock-aftershock sequence with a dense permanent network and a later temporary nodal deployment. It is a useful medium-scale end-to-end data case with complementary reference methods.

## Case information from v0.2 inventory

| Field | Information |
|---|---|
| Region | Salt Lake Valley, Utah, USA |
| Sequence type | Mw 5.7 mainshock–aftershock sequence in an extensional normal-fault setting |
| Key event | Mw 5.7 on 2020-03-18 near Magna |
| Pang study span | 2020-03-18 to 2020-05-01 |
| Pang configuration | 39 stations / 226 channels for matched filtering within 40 km |
| Raw waveform access | EarthScope/IRIS DMC and COSMOS |
| Expected difficulty | Medium |
| Primary role | Medium-scale end-to-end reconstruction and relative relocation |

Pang reports 5,501 new aftershocks and 5,623 high-precision relocated aftershocks. Baker reports approximately 142,000 P picks, 188,000 S picks and more than 5,000 locations using 180 temporary geophones.

## Reference evaluation matrix

| Reference | Evaluation role | Time scope | Spatial scope | Quality tier | Network / observation condition |
|---|---|---|---|---|---|
| Pang et al. (2020) | Primary: detection enhancement and relative relocation | Full: 2020-03-18–05-01; benchmark: 2020-03-18–03-25 | Within approximately 40 km matched-filter region; freeze exact bbox | **Q1** relative location; **Q2** enhanced detection and absolute location | 39 stations / 226 channels, permanent/telemetered UUSS-compatible observations |
| Baker et al. (2021) | Secondary: ML picks, dense nodal detection, pick-level comparison | 2020-03-18–04-30; subset to primary window | Magna sequence and temporary-array footprint | **Q2** ML detection/picks; network-specific completeness | 180 temporary 5-Hz geophones deployed within ~35 km; must be a separate nodal condition |
| UUSS authoritative catalog | Baseline: operational catalog recovery | Same frozen window | Same primary region | **Q3** operational baseline | UUSS regional network |

Pang and Baker must not be merged into a single target because their station sets and observation regimes are materially different. Reference independence is `Medium–High` for the pair, conditional on the Agent not reproducing either workflow.

## Reference products

| Product | Role | Current issue |
|---|---|---|
| Pang et al. (2020) | Primary matched-filter and relative-relocation reference | Confirm exact catalog file, 39-station/226-channel configuration, and window subset. |
| Baker et al. (2021) | Secondary ML/nodal and pick-level reference | Nodal observation regime must remain separate from Pang's permanent-network task. |
| UUSS authoritative catalog | Baseline | Confirm release and stable event identifiers. |

## Calibration checklist

- [ ] Download Pang catalog and metadata.
- [ ] Obtain Baker catalog; verify whether raw nodal waveforms are needed or only the catalog is used.
- [ ] Inspect event, pick, magnitude, and relocation fields.
- [ ] Confirm the station/channel set used for the primary target.
- [ ] Subset all products to 2020-03-18 through 2020-03-25.
- [ ] Quantify overlap and population differences between Pang and Baker.

## Window and data preparation

The v1 raw-waveform task should use the Pang-compatible permanent/telemetered network. The Baker nodal array should be retained as a separate secondary condition, not silently merged into the same input.

### Frozen v1 benchmark window

| Field | Frozen value |
|---|---|
| Time window | 2020-03-18 00:00:00 to 2020-03-26 00:00:00 UTC (8 days) |
| Spatial rule | 40.69–40.84°N, −112.14 to −111.94°W, depth −1.3–13.1 km |
| Event counts | Pang: 4,102 events with valid Mc > −4 in the local catalog (4,163 rows including missing-magnitude sentinels); Baker is pick-level and is not assigned an event count here |
| Observed ranges | Pang valid rows: lat 40.693–40.837°, lon −112.135 to −111.939°, depth −1.28–13.02 km, Mc −3.9–5.67 |
| Network condition | Pang primary: 39 permanent/telemetered stations and 226 channels; Baker secondary: 180 temporary 5-Hz geophones, kept as a separate nodal condition |
| Waveform volume | Pang design upper bound: ~28.3 GB for 39 × 3 components × 100 Hz × int32 × 8 days; Baker nodal upper bound: ~130.6 GB at 180 × 3 × 100 Hz × int32 × 8 days |
| Reference quality and role | Pang: Q1 relative relocation/Q2 enhanced event detection; Baker: Q2 ML/pick-level/nodal detection; UUSS: Q3 operational baseline |

## Main risks

1. Pang and Baker use materially different network configurations.
2. Nodal data volume can dominate the computational task.
3. Relative relocation quality does not imply accurate mainshock absolute location.

## Sources

- `../references/PANG2020_GL089798/paper/PANG2020_GL089798__paper.pdf`
- Pang et al. (2020), DOI: https://doi.org/10.1029/2020GL089798
- Baker et al. (2021), DOI: https://doi.org/10.1785/0220200316
- Pang catalog, ISC DOI: https://doi.org/10.31905/9IE6PAF2
- Baker catalog, ISC DOI: https://doi.org/10.31905/LGR1456Y
## Full inventory record (migrated from `docs/01_Case_details.md`)
### 2020 Magna, Utah Earthquake Sequence

## Literature and catalog gap audit

### Verified core catalog set

- Pang high-resolution catalog: ISC DOI https://doi.org/10.31905/9IE6PAF2.
- Baker ML/nodal catalog: ISC DOI https://doi.org/10.31905/LGR1456Y; distributed as `BAKER2021_0220200316__catalog_picks.csv` with a README.
- Local Baker copy: `../catalogs/BAKER2021_0220200316/BAKER2021_0220200316__catalog_picks.csv` (329,611 data rows; official README retained alongside it).
- Local Pang copy: `../catalogs/PANG2020_GL089798/PANG2020_GL089798__catalog_primary.txt` (5,739 events; ISC high-resolution catalog release).
- UUSS authoritative catalog: operational baseline.

### Audit conclusion

**Sufficiency verdict:** Sufficient for Phase I: both Pang high-resolution and Baker ML/nodal catalog files are now downloaded and schema-checked locally. Permanent-network versus nodal conditions must remain explicitly separated.

#### A. Case information

| Field | Information |
|---|---|
| **Case ID** | MAGNA2020 |
| **Region** | Salt Lake Valley, Utah, USA |
| **Sequence type** | Mw 5.7 mainshock–aftershock sequence in an extensional normal-fault setting |
| **Key event** | Mw 5.7 earthquake on 2020-03-18 near Magna |
| **Scientific significance** | Very well recorded by the UUSS regional/urban network; multiple complementary enhanced catalogs exist, including high-precision template/DD relocation and a large-N ML/nodal catalog. |
| **Primary reference span** | Pang catalog: 2020-03-18 to 2020-05-01; matched-filter waveform processing used 2020-03-17 to 2020-04-30 |
| **Recommended compact benchmark window** | **2020-03-18 to 2020-03-25 (7 days)** |
| **Network context** | Dense UUSS permanent network plus rapid temporary deployments; Pang used 39 stations / 226 channels for matched filtering. |
| **Raw waveform access** | Pang et al. state that seismic data are available from IRIS/EarthScope DMC and COSMOS. UU network data are openly distributed through EarthScope; UU is also present in EarthScope Open Data on AWS. |
| **Expected benchmark difficulty** | Medium |
| **Primary benchmark role** | Moderate-size end-to-end reconstruction; template-matching enhancement; high-precision relative relocation; comparison of conventional and ML enhanced catalogs. |

##### Key sources

- Pang et al. (2020), *Seismic Analysis of the 2020 Magna, Utah, Earthquake Sequence: Evidence for a Listric Wasatch Fault*. DOI: <https://doi.org/10.1029/2020GL089798>
- Pang high-resolution catalog, ISC DOI: <https://doi.org/10.31905/9IE6PAF2>
- Baker et al. (2021), *Monitoring the 2020 Magna, Utah, Earthquake Sequence with Nodal Seismometers and Machine Learning*. DOI: <https://doi.org/10.1785/0220200316>
- Baker ML catalog, ISC DOI: <https://doi.org/10.31905/LGR1456Y>
- University of Utah Regional Seismic Network (UU): <https://doi.org/10.7914/SN/UU>

#### B. Reference catalog candidates

##### B1. Primary reference — Pang et al. (2020) high-resolution catalog

| Field | Information |
|---|---|
| **Priority** | **Primary** |
| **Reference type** | High-precision relative-location + detection-enhancement reference |
| **Public catalog** | ISC DOI 10.31905/9IE6PAF2 |
| **Catalog span** | 2020-03-18 to 2020-05-01 |
| **Reference waveform processing span** | 2020-03-17 to 2020-04-30 |
| **Stations / channels** | **39 stations / 226 channels** for matched filtering within 40 km |
| **Routine UUSS catalog at analysis time** | 2,103 finalized earthquakes as of Apr. 30 in the study description |
| **Detection method** | Matched filtering/template matching |
| **New detections** | **5,501 new aftershocks** |
| **Association** | DBSCAN on origin-time estimates with minimum detection criteria |
| **Relative relocation** | Waveform cross-correlation differential times + hierarchical clustered relocation / GrowClust-style method |
| **High-precision relocated events** | **5,623 aftershocks** |
| **Robustness analysis in paper** | Alternative station sets, differential-time acceptance criteria, relocation algorithm, and starting locations were explicitly tested |
| **Raw data source** | IRIS/EarthScope DMC + COSMOS |
| **Open access** | Catalog public at ISC; source seismic data described as available from IRIS and COSMOS |
| **Provisional reference quality** | **High** |
| **Reference independence** | **Medium–High** relative to a modern generic Agent; high-precision cross-correlation relocation is valuable as an external target even if the Agent uses some of the same raw observations |
| **Best benchmark use** | Relative geometry, template-enhanced event recovery, relocation quality |
| **Main limitation** | Mainshock and some larger aftershocks were not relatively relocated because their waveforms correlate poorly with small events. |

##### B2. Secondary reference — Baker et al. (2020/2021) ML + nodal catalog

| Field | Information |
|---|---|
| **Priority** | Secondary |
| **Reference type** | Independent ML detection/picking/association reference |
| **Paper** | Baker et al. (2021), SRL, DOI 10.1785/0220200316 |
| **Catalog release** | ISC DOI 10.31905/LGR1456Y; CC BY-SA 3.0 |
| **Span** | 2020-03-18 to 2020-04-30 |
| **Temporary array** | 180 three-component 5-Hz geophones deployed within 35 km by day 6; 250 samples/s |
| **Processing** | Deep-learning U-Net P/S detectors + two-step association combining ML and a grid-based interferometric approach |
| **P picks** | ~142,000 |
| **S picks** | ~188,000 |
| **Earthquake locations** | **>5,000** |
| **Operational-catalog recovery** | 95% of UUSS authoritative events; total events roughly doubled relative to the ~2,300 UUSS catalog in the study comparison |
| **Pick validation** | Reported P/S pick standard deviations of 0.05 s / 0.09 s relative to analyst times at backbone stations |
| **Open access** | Catalog public at ISC; raw nodal-data access should be independently checked before using this as a waveform benchmark input |
| **Provisional reference quality** | Medium–High |
| **Reference independence** | Medium; strong if the benchmark Agent does not use the same U-Net workflow |
| **Best benchmark use** | Pick-level comparison, ML catalog completeness, high-density temporary-array condition |
| **Main limitation** | Nodal deployment changes the observational regime and data volume; it should not silently be mixed with the 39-station Pang benchmark. |

##### B3. Baseline

| Product | Role |
|---|---|
| UUSS authoritative catalog | Operational baseline |
| UU network waveforms | Main raw waveform source for a compact benchmark |
| COSMOS strong-motion data | Optional additional data, not necessary for benchmark v1 |

#### C. Benchmark suitability

| Field | Assessment |
|---|---|
| **Recommended for core benchmark?** | **Yes** |
| **Primary target** | Pang et al. high-resolution catalog |
| **Secondary target** | Baker et al. ML/nodal catalog |
| **Recommended v1 input** | Use Pang-compatible permanent/temporary telemetered network, not all 180 nodal sensors |
| **Recommended window** | 2020-03-18 to 2020-03-25 |
| **Short-window target event count** | Pang 4,102 valid-magnitude events; Baker remains pick-level rather than an event-count target |
| **Approximate waveform volume** | Pang ~28.3 GB continuous upper bound; Baker nodal condition ~130.6 GB upper bound for 180 stations × 3C × 100 Hz × 8 days |
| **Expected compute cost** | Medium |
| **Key benchmark risk** | Two excellent catalogs use materially different network configurations; comparisons must keep the observation set explicit |
| **Overall assessment** | Excellent medium-scale benchmark with unusually rich independent catalog products. |

---

---
