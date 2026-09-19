# RIDGE2019 — Case Analysis

> **Source of truth:** This file is the detailed, mutable analysis record for `RIDGE2019`. The cross-case summary is maintained in [`Docs/01_Case_details.md`](../../../Docs/01_Case_details.md).

## Status

- Case ID: `RIDGE2019`
- Phase: reference calibration and data preparation
- Status: `v1 benchmark window frozen`
- Primary reference: Shelly (2020)
- Secondary reference: Ross et al. (2019)
- Frozen v1 core window: 2019-07-04 to 2019-07-07 UTC (72 hours)

## Scientific role

Dense foreshock-mainshock-aftershock sequence with extreme event overlap and complex fault geometry. This is the preferred first case for validating the data-preparation pipeline.

## Case information from v0.2 inventory

| Field | Information |
|---|---|
| Region | Eastern California / Southern California, USA |
| Sequence type | Major foreshock–mainshock–aftershock sequence; complex strike-slip fault system |
| Key events | Mw 6.4 on 2019-07-04; Mw 7.1 about 34 h later on 2019-07-06 |
| Scientific significance | Intersecting/orthogonal fault structures and multiple high-resolution catalogs |
| Full Shelly span | 2019-07-04 to 2019-07-16 |
| Network | Dense Caltech/USGS Southern California Seismic Network (SCSN; CI) |
| Raw waveform access | Public through SCEDC |
| Expected difficulty | High |
| Primary role | Dense detection, association, relative relocation and fault geometry |

Shelly reports 13,525 routine template events and 34,091 detected and precisely located events. Ross provides a GrowClust-format relocated product with differential-time counts, residuals and estimated errors.

## Reference evaluation matrix

| Reference | Evaluation role | Time scope | Spatial scope | Quality tier | Network / observation condition |
|---|---|---|---|---|---|
| Shelly (2020) | Primary: detection recovery, association stress, relative geometry | Full: 2019-07-04–07-16; benchmark: inter-mainshock core or 2019-07-04–07-07 extended window | Ridgecrest sequence region; exact benchmark bbox to be frozen | **Q1** detection/relative location; **Q2** absolute location/completeness | SCSN/CI continuous waveforms; template-derived high-resolution product |
| Ross et al. (2019) QTM/GrowClust | Secondary: fault geometry and relocation diagnostics | Published sequence window; subset to the primary benchmark window | Same SCSN Ridgecrest region; exclude/flag poorly constrained Mw 7.1 depth | **Q1** relative structure; **Q2–Q3** absolute mainshock depth | SCSN/SCEDC waveform lineage; correlation/relocation product |
| SCSN routine catalog | Baseline: operational recovery and completeness comparison | Same frozen window | Same region | **Q3** operational baseline | Routine SCSN network/catalog |

The primary benchmark should not combine these products into one undifferentiated truth set. Shelly and Ross are complementary and share raw-data lineage, so independence is `Medium`.

## Reference products

| Product | Role | Current issue |
|---|---|---|
| Shelly (2020) | Primary detection and relative-location reference | Exact window event count, station list, and event-level QC fields must be extracted. |
| Ross et al. (2019) QTM/GrowClust catalog | Secondary structural/relocation reference | Official SCEDC QTM archive is now staged under `catalogs/ROSS2019_SCIENCE/`; mainshock depth is poorly constrained, so do not use it as universal absolute truth. |
| SCSN routine catalog | Baseline | Lower-magnitude coverage is incomplete and must not be treated as high-resolution truth. |

## Calibration checklist

- [ ] Download USGS/Shelly and SCEDC/Ross catalog files.
- [ ] Inspect stable IDs, origin-time precision, location fields, and QC columns.
- [ ] Reconcile the catalog time coverage and spatial region.
- [ ] Subset primary and secondary catalogs to the core and extended windows.
- [ ] Determine active SCSN stations/channels and data gaps.
- [ ] Document shared waveform/template lineage and reference independence.

## Window and data preparation

The inter-mainshock interval is the preferred core because it is compact and scientifically information-rich. The July 4–7 interval should remain an extended condition rather than replacing the core window.

### Frozen v1 benchmark window

| Field | Frozen value |
|---|---|
| Time window | 2019-07-04 00:00:00 to 2019-07-07 00:00:00 UTC (72 hours; includes the two mainshock stages) |
| Spatial/depth rule | 35.45–36.05°N, −117.90 to −117.20°W, depth 0–20 km; exclude 57 Shelly rows outside the depth/space QC envelope |
| Event counts | Shelly Data S1: 7,716 QC-passing events (7,773 raw rows); AWR hypocenter catalog: 5,737 events after the same mask |
| Observed ranges | Shelly QC: lat 35.485–36.013°, lon −117.819 to −117.256°, depth 0.16–19.95 km, M −0.10–7.10; AWR: lat 35.505–36.050°, lon −117.878 to −117.268°, depth 0.69–14.73 km, γ-magnitude 0.056–4.585 |
| Network condition | CI/SCSN continuous waveforms; v1 uses a 39-station, 3-component subset within ~100 km, with station availability recorded per day |
| Waveform volume | Design upper bound: ~28.3 GB for 39 × 3 components × 100 Hz × int32 × 72 hours continuous; actual SCEDC gaps/channel selection reduce this |
| Reference quality and role | Shelly: Q1 detection/relative-location reference; Liu/AWR: Q1–Q2 relocation/structure cross-checks; routine SCSN: Q3 baseline; Ross: structural context/secondary relocation lineage |

## Main risks

1. Primary and secondary references share the SCSN raw-data lineage.
2. Template-derived catalog completeness is not absolute truth.
3. High event rate can cause overlapping events and duplicate matching problems.

## Sources

- `../references/SHELLY2020_0220190309/paper/SHELLY2020_0220190309__paper.pdf` (journal article; former PDF retained as `../references/SHELLY2020_0220190309/context/SHELLY2020_0220190309__poster.pdf`)
- `../references/ROSS2019_SCIENCE/paper/ROSS2019_SCIENCE__paper.pdf`
- Shelly (2020), DOI: https://doi.org/10.1785/0220190309
- Ross et al. (2019), DOI: https://doi.org/10.1126/science.aaz0109
- USGS release, DOI: https://doi.org/10.5066/P9JN6H0N
## Full inventory record (migrated from `Docs/01_Case_details.md`)
### 2019 Ridgecrest Earthquake Sequence

## Literature and catalog gap audit

### Added independent reference — Liu et al. (2020) ML catalog

- Paper: *Rapid Characterization of the July 2019 Ridgecrest, California, Earthquake Sequence From Raw Seismic Data Using Machine-Learning Phase Picker*.
- DOI: https://doi.org/10.1029/2019GL086189
- Coverage: 2019-07-04 to 2019-07-09.
- Product: 15,445-event hypoDD catalog versus 7,743 routine events, constructed from continuous waveforms without using the routine catalog as the event prior.
- Recommended role: **Q2 independent-method secondary reference** for raw-waveform detection, association and end-to-end catalog construction.
- Status: the supporting-information catalog and SI document are locally staged; test overlap with the core and extended windows while retaining its independent-from-routine-catalog provenance.
- Local core table: `../catalogs/LIU2020_GL086189/LIU2020_GL086189__catalog_tableS1.txt`; SI document: `../references/LIU2020_GL086189/supplement/Liu2020_Ridgecrest_SI.docx`.

### Important expansion reference — Atterholt, Wilding & Ross (2025)

- Paper DOI: https://doi.org/10.1093/gji/ggaf001
- Local paper: `../references/AWR2025_CALTECHDATA/paper/AWR2025_CALTECHDATA__paper.pdf`.
- Local catalog release: `../catalogs/AWR2025_CALTECHDATA/` (hypocenter and moment-tensor CSVs), with provenance at https://stp2.gps.caltech.edu/data/alt-2025-atterholt.html and https://doi.org/10.22002/5af05-cah73.
- Catalog DOI: https://doi.org/10.22002/5af05-cah73
- Product: long-term relocated hypocenter and moment-tensor catalogs; current preferred release is Version 2.
- Recommended role: **Q2 methodological/long-term auxiliary**, not the Phase I primary, because it extends beyond the compact window and uses a modern PhaseNO–GaMMA–HypoSVI–GrowClust workflow that may overlap with Agent pipelines.

### Audit conclusion

**Sufficiency verdict:** Conditionally sufficient after adding Liu et al. as the independent secondary catalog. Shelly–Ross–SCSN is sufficient for the core detection/relative-geometry task; it is not sufficient for independent raw-waveform validation or absolute-location claims without Liu and the SCSN anchor. The 2025 long-term catalog remains expansion-only.

#### A. Case information

| Field | Information |
|---|---|
| **Case ID** | RIDGE2019 |
| **Region** | Eastern California / Southern California, USA |
| **Sequence type** | Major foreshock–mainshock–aftershock sequence; complex strike-slip fault system |
| **Key events** | Mw 6.4 on 2019-07-04; Mw 7.1 about 34 h later on 2019-07-06 |
| **Scientific significance** | Exceptionally well recorded sequence with intersecting/orthogonal fault structures and multiple independently produced catalogs. |
| **Full reference span** | Shelly reference: 2019-07-04 to 2019-07-16 |
| **Recommended compact benchmark window** | **Core:** Mw 6.4–Mw 7.1 inter-mainshock interval (~34 h). **Extended:** 2019-07-04 to 2019-07-07 (~3 days). |
| **Network context** | Dense Caltech/USGS Southern California Seismic Network (SCSN; network CI). |
| **Raw waveform access** | Public through SCEDC; SCSN waveform and parametric data are archived at SCEDC. |
| **Routine catalog / picks** | SCSN/SCEDC operational catalog and event phase information available. |
| **Expected benchmark difficulty** | High: intense event rate, overlapping aftershocks, complex fault geometry. |
| **Primary benchmark role** | End-to-end dense catalog reconstruction; detection completeness; association under high event rate; relative relocation/fault geometry. |

##### Key sources

- Shelly (2020), *A High-Resolution Seismic Catalog for the Initial 2019 Ridgecrest Earthquake Sequence: Foreshocks, Aftershocks, and Faulting Complexity*. DOI: <https://doi.org/10.1785/0220190309>
- USGS catalog release. DOI: <https://doi.org/10.5066/P9JN6H0N>
- Ross et al. (2019), *Hierarchical interlocked orthogonal faulting in the 2019 Ridgecrest earthquake sequence*. DOI: <https://doi.org/10.1126/science.aaz0109>
- SCEDC Ridgecrest QTM catalog: <https://scedc.caltech.edu/data/qtm-ridgecrest.html>
- SCSN/SCEDC waveform archive: <https://scedc.caltech.edu/>
- Correlation-derived phase arrivals for Ridgecrest, Maple Creek, and Kīlauea. DOI: <https://doi.org/10.5066/P13JCJ2I>
- Article-associated Data S1 catalog: `../catalogs/SHELLY2020_0220190309/raw_article/SHELLY2020_0220190309__catalog_DataS1.txt`; metadata: `../catalogs/SHELLY2020_0220190309/raw_article/SHELLY2020_0220190309__metadata_DataS1.xml`.
- Local Ridgecrest phase-arrival CSV: `../catalogs/SHELLY2020_0220190309/raw/Ridgecrest_2019_correlation_phase_arrivals.csv` (auxiliary, not the article's Data S1 event catalog).

#### B. Reference catalog candidates

##### B1. Primary reference — Shelly (2020) high-resolution catalog

| Field | Information |
|---|---|
| **Priority** | **Primary** |
| **Reference type** | Detection reference + high-resolution relative-location reference |
| **Reference paper** | Shelly (2020), SRL, DOI 10.1785/0220190309 |
| **Public data release** | USGS DOI 10.5066/P9JN6H0N; public / CC0 |
| **Catalog span** | 2019-07-04 to 2019-07-16 |
| **Routine templates** | 13,525 routinely cataloged events |
| **High-resolution catalog size** | **34,091 detected and precisely located events** |
| **Core processing** | Waveform template matching + precise relative relocation |
| **Station count** | **To verify from the catalog/method metadata before benchmark freeze.** The accessible USGS landing page does not state one definitive station count. |
| **Waveform source** | SCSN/SCEDC continuous data |
| **Initial catalog source** | Routine SCSN catalog |
| **Manual/expert component** | Routine catalog events form the templates; the final enhanced product is waveform based. |
| **Uncertainty / QC** | Precise relative-location workflow; exact event-level uncertainty fields and thresholds should be extracted from the paper/SI before scoring is frozen. |
| **Open access** | Yes — catalog and underlying SCSN waveforms are public. |
| **Provisional reference quality** | **High** |
| **Reference independence** | **Medium** — same raw network data, but high-resolution template/relative-location processing provides a stronger target than the routine catalog. |
| **Best benchmark use** | Event recovery, relative geometry, fine-scale seismicity structure |
| **Main limitation** | Should not be treated as absolute hypocentral ground truth; template-based detection inherits the coverage of the template population. |

##### B2. Secondary reference — Ross et al. (2019) Ridgecrest QTM / relocated catalog

| Field | Information |
|---|---|
| **Priority** | Secondary |
| **Reference type** | Structural + relocation reference |
| **Reference paper** | Ross et al. (2019), *Science*, DOI 10.1126/science.aaz0109 |
| **Catalog access** | Public through SCEDC |
| **Catalog representation** | GrowClust-format relocated catalog |
| **Available QC fields** | Initial and relocated locations; differential-time counts; P/S differential-time RMS; estimated horizontal, vertical, and origin-time errors |
| **Waveform source** | SCSN/SCEDC |
| **Open access** | Yes |
| **Provisional reference quality** | High for structural comparison |
| **Reference independence** | Medium |
| **Best benchmark use** | Fault geometry, relocation consistency, event-level relocation diagnostics |
| **Main limitation** | SCEDC explicitly notes that the Mw 7.1 mainshock depth is poorly constrained in this catalog and recommends the SCSN hypocenter for the mainshock. The catalog should therefore not be used as a universal absolute-location truth set. |
| **Catalog event count** | AWR has 5,737 events after the frozen 3-day space/depth mask; Shelly remains the primary target. |

##### B3. Baseline / auxiliary references

| Product | Role | Important caveat |
|---|---|---|
| **SCSN routine catalog** | Baseline / initial operational catalog | SCEDC notes that the Ridgecrest sequence remains largely unreviewed below M2.5, so it should not be used as the high-resolution target. |
| **USGS 2024 correlation-derived arrivals (P13JCJ2I)** | Phase-arrival auxiliary reference | Valuable for pick-level checks; generated from matched-filter studies and therefore not fully independent of the Shelly workflow. |

#### C. Benchmark suitability

| Field | Assessment |
|---|---|
| **Recommended for core benchmark?** | **Yes — highest priority** |
| **Primary target** | Shelly (2020) |
| **Secondary target** | Ross et al. (2019) |
| **Baseline** | SCSN routine catalog |
| **Suggested Agent input** | Continuous waveform + station metadata; routine catalog/picks can be a separately controlled condition |
| **Recommended window** | 34 h inter-mainshock interval or 3-day July 4–7 window |
| **Short-window target event count** | Shelly 7,716 QC-passing rows; AWR 5,737 events under the same mask |
| **Approximate waveform volume** | ~28.3 GB continuous upper bound for 39 stations × 3C × 100 Hz × int32 × 72 hours |
| **Expected compute cost** | Medium–High |
| **Key benchmark risk** | Target-method leakage if target papers/parameter details are exposed to the Agent; shared waveform/template lineage among references |
| **Overall assessment** | Excellent first benchmark because reference quality, public data, and scientific difficulty are all strong. |

---

---
