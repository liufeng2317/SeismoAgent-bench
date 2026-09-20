# PRAGUE2011 — Case Analysis

> **Source of truth:** This file is the detailed, mutable analysis record for `PRAGUE2011`. The cross-case summary is maintained in [`docs/01_1_Case_details.md`](../../../docs/01_1_Case_details.md).

## Status

- Case ID: `PRAGUE2011`
- Phase: reference calibration and data preparation
- Status: `v1 benchmark window frozen`
- Information extraction: Cochran paper and catalog audit completed; remaining
  references are pending the same structured extraction.
- Primary reference: Cochran et al. (2020) enhanced catalog
- Frozen v1 core window: 2011-11-11 to 2011-11-19 UTC
- Catalog processing pilot: [catalog_processing_index.md](./catalog_processing_index.md)
- Optional stress window: 2011-11-04 to 2011-11-11

## Scientific role

Induced/triggered aftershock sequence with a changing temporary/permanent network. The case is intended to test high-sensitivity detection, association, location quality control, and robustness to network evolution.

## Case information from v0.2 inventory

| Field | Information |
|---|---|
| Region | Prague, Oklahoma, USA |
| Sequence type | Mw 4.8 foreshock – Mw 5.7 mainshock – prolific aftershock sequence |
| Key event | Mw 5.7 mainshock on 2011-11-06 |
| Published study span | 2011-11-04 to 2011-12-05 |
| Network | Oklahoma RAMP + USArray Transportable Array + Oklahoma Seismic Network; 31 stations in subspace workflow |
| Raw waveform access | EarthScope/IRIS, open PASSCAL ZQ, and a USGS NEIC subset |
| Expected difficulty | Medium–High |
| Primary role | Detection, association, location QC and network-deployment robustness |

The reference workflow used S-phase subspace detection, arrival-time association and Bayesloc. It reports 577,040 S arrivals, 191,100 arrivals associated into 20,788 events, and 21,786 located events before final filtering.

## Reference evaluation matrix

| Reference | Evaluation role | Time scope | Spatial scope | Quality tier | Network / observation condition |
|---|---|---|---|---|---|
| Cochran et al. (2020) local catalog | Primary: enhanced detection and event-support recovery | Frozen core: 2011-11-11–11-19 UTC | Prague sequence region; frozen event envelope below | **Q2** enhanced detection and release-level QC | Oklahoma regional/temporary network; preserve the published station lineage |
| McMahon et al. (2017) | Secondary: independent subspace detection and relocation comparison | Published 2011-11-04–12-05; local USGS 5,446-event release staged separately | Same region | **Q2** independent detection/relocation secondary | Heterogeneous RAMP/USArray/Oklahoma network |
| 998-event reviewed seed set | Secondary expert anchor: clear event existence and location | Subset of study interval; exact span to extract | Same region | **Q1** expert event/location anchor; low completeness | Initial catalog used to construct detectors |
| Regional/operational catalog | Baseline | Same frozen window | Same region | **Q3** operational baseline | Operational/regional network |

The 5,446-event release and 5,262-event paper-filtered set must remain separate reference layers. The core window is preferred because temporary stations were fully operational from 2011-11-11; the earlier window is a separate changing-network stress condition.

## Reference products

| Product | Role | Current issue |
|---|---|---|
| Cochran et al. (2020) local catalog | Primary detection and location reference | 8,811 event rows; time-only frozen window gives 2,078 events; the rounded spatial/depth mask gives 2,076. Magnitude range is −1.36–4.99 overall and its type is unresolved. |
| McMahon et al. (2017) / 998-event reviewed seed | Secondary workflow and expert anchor | McMahon's 5,262/5,446 counts are not the local Cochran file and should not be mixed without an explicit crosswalk. |
| Isken & Mooney (2017) Table S3 | Sparse structural/location anchor | 13 manually picked M>3 events; 7 fall in the canonical core window; not a completeness catalog. |
| Regional/operational catalog | Baseline | Identify exact release and coverage. |

The detailed first-pass extraction is maintained beside the source products:

- [Cochran paper reading](../references/COCHRAN2020_GJIGGAA153/parsed/paper/COCHRAN2020_GJIGGAA153__paper_reading.md)
- [Cochran catalog summary](../catalogs/COCHRAN2020_GJIGGAA153/COCHRAN2020_GJIGGAA153__catalog_summary.md)
- [McMahon paper reading](../references/MCMAHON2017_GL072944/parsed/paper/MCMAHON2017_GL072944__paper_reading.md)
- [McMahon catalog summary](../catalogs/MCMAHON2017_GL072944/MCMAHON2017_GL072944__catalog_summary.md)
- [Isken paper reading](../references/ISKEN2017_BSSA0120160150/parsed/paper/ISKEN2017_BSSA0120160150__paper_reading.md)
- [Isken catalog summary](../catalogs/ISKEN2017_BSSA0120160150/ISKEN2017_BSSA0120160150__catalog_summary.md)

These files distinguish article-reported values from local-file audit values;
the case-level tables above remain the benchmark decision record.

## Calibration checklist

- [x] Download and locally validate the Cochran catalog release.
- [x] Inspect event schema, time standard, coordinates, depth, and magnitude fields.
- [x] Preserve the McMahon 5,446-event release separately; reconcile the paper's 5,262 filtered subset only through an explicit event/quality crosswalk.
- [x] Extract McMahon paper/catalog construction and local E/P schema.
- [x] Extract Isken Table S3 paper/catalog construction and sparse-anchor role.
- [ ] Confirm the station list and deployment dates from McMahon Table S1 and Isken Table S1.
- [ ] Identify archive provenance for ZQ and NEIC waveform subsets.
- [ ] Subset all references to the same time and spatial window.
- [ ] Record the primary reference's inclusion and uncertainty filters.
- [ ] Acquire McMahon SI/Table S1–S2 and resolve P-record timestamp semantics.

## Window and data preparation

The stable-network window is preferred for the core benchmark because the last temporary stations became fully operational on 2011-11-11. The earlier window should remain a separate stress test rather than being mixed into the core result.

### Frozen v1 benchmark window

| Field | Frozen value |
|---|---|
| Time window | 2011-11-11 00:00:00 to 2011-11-19 00:00:00 UTC (half-open; 8 days) |
| Primary event count | 2,078 Cochran events in the local catalog |
| Spatial rule | Descriptive extrema of the canonical time-only window: 35.45231–35.55757°N, −96.87233–−96.73343°E. Rounded bounds are retained only for the 2,076-event sensitivity audit. |
| Depth range | Time-only window: 1.016–9.618 km; rounded displayed mask: 1.02–9.62 km. |
| Magnitude range | −0.96–3.22 in the time-only window; magnitude type is unresolved, so do not label it ML. |
| Network condition | 31-station heterogeneous RAMP/USArray/Oklahoma network; use only channels available during the full window and retain deployment masks |
| Waveform volume | Design upper bound: 25.71264 GB decimal (23.95 GiB) for 31 × 3 components × 100 Hz × int32 × 8 days continuous; actual volume is lower after gaps/channel filtering. |
| Reference quality and role | Cochran: Q2 enhanced detection/location reference; McMahon filtered set: Q1 location/QC subset; Isken Table S3: Q1 local structural anchor, 13 events only |

## Main risks

1. Network geometry changes during the sequence.
2. Publication and release counts do not currently agree.
3. Waveforms originate from more than one archive.

## Sources

- `../references/MCMAHON2017_GL072944/paper/MCMAHON2017_GL072944__paper.pdf`
- `../references/MCMAHON2017_DISSERTATION/paper/MCMAHON2017_DISSERTATION__paper.pdf`
- McMahon et al. (2017), DOI: https://doi.org/10.1002/2017GL072944
- USGS release, DOI: https://doi.org/10.5066/F7FJ2FNT
## Full inventory record (migrated from `docs/01_1_Case_details.md`)
### 2011 Prague, Oklahoma Earthquake Sequence

## Literature and catalog gap audit

### Catalog lineage audit — Cochran et al. (2020) extended template-matched catalog

- Paper: *Activation of optimally and unfavourably oriented faults in a uniform local stress field during the 2011 Prague, Oklahoma, sequence*.
- DOI: https://doi.org/10.1093/gji/ggaa153
- Product: 8,811 events (900 template events + 7,911 relocated detections); reported median relative uncertainties are approximately 112 m horizontal and 133 m vertical for the relocated detection population.
- Coverage: approximately three months; the input 900-event catalog begins on 2011-11-07.
- Recommended role: **Q2 enhanced-detection/relative-location reference**, with a metric-specific Q1 structural auxiliary role for differential geometry; it is an important cross-check against McMahon's subspace/Bayesloc catalog.
- Status: the full extended catalog is locally staged; the frozen-window counts are computed by an analysis mask and the source file remains immutable. Keep its template-derived lineage explicit when evaluating independence.

### Important supporting catalogs

- Isken & Mooney (2017), *Relocated Hypocenters and Structural Analysis from Waveform Modeling of Aftershocks...*, DOI https://doi.org/10.1785/0120160150. The official BSSA supplement Table S3 is now archived at `../catalogs/ISKEN2017_BSSA0120160150/ISKEN2017_BSSA0120160150__catalog_relocated_tableS3.csv`; it contains 13 high-quality relocated aftershocks and is a **Q2 structural/location auxiliary**, not a complete catalog.
- Cochran source bundle: `../references/COCHRAN2020_GJIGGAA153/`; core catalog: `../catalogs/COCHRAN2020_GJIGGAA153/COCHRAN2020_GJIGGAA153__catalog_primary.txt`.
- McNamara et al. (2015), DOI https://doi.org/10.1002/2014GL062730. Contains a broader 3,639-event central Oklahoma HD-relocation catalog and is useful as a regional structural anchor, but not as the principal compact-window completeness target.
- Keranen et al. (2013), DOI https://doi.org/10.1130/G34045.1. Important scientific-context and early-aftershock reference, but not a replacement for the enhanced catalogs.

### Audit conclusion

**Sufficiency verdict:** Sufficient for Phase I after staging both Cochran and McMahon as separate detection/relocation references, with Isken as a small structural anchor and an operational catalog as optional baseline. Do not merge Cochran and McMahon event rows.

#### A. Case information

| Field | Information |
|---|---|
| **Case ID** | PRAGUE2011 |
| **Region** | Prague, Oklahoma, USA |
| **Sequence type** | Mw 4.8 foreshock – Mw 5.7 mainshock – prolific aftershock sequence; induced/triggered seismicity context |
| **Key event** | Mw 5.7 mainshock on 2011-11-06 |
| **Scientific significance** | Dense temporary/permanent observations; subspace-detection study substantially expanded and precisely located the aftershock population. |
| **Published study span** | 2011-11-04 to 2011-12-05 |
| **Network timing** | The last temporary stations became fully operational on **2011-11-11**. |
| **Recommended compact benchmark window** | **Canonical v1 core:** 2011-11-11 00:00 to 2011-11-19 00:00 UTC (8 days). **Optional hard window:** 2011-11-04 to 2011-11-11, where network availability evolves; do not mix it into the core score. |
| **Network context** | Temporary Oklahoma RAMP + USArray Transportable Array + Oklahoma Seismic Network; 31 stations used in the subspace workflow. |
| **Raw waveform access** | Most data were obtained from the IRIS DMC / current EarthScope archive; ZQ Oklahoma RAMP data are archived as an open PASSCAL network. The paper notes LC01–LC08 data came from USGS NEIC archives. |
| **Expected benchmark difficulty** | Medium–High |
| **Primary benchmark role** | High-sensitivity detection, heterogeneous network handling, event association, location with explicit uncertainty thresholds. |

##### Key sources

- McMahon et al. (2017), *Spatio-temporal evolution of the 2011 Prague, Oklahoma aftershock sequence revealed using subspace detection and relocation*. DOI: <https://doi.org/10.1002/2017GL072944>
- USGS catalog release. DOI: <https://doi.org/10.5066/F7FJ2FNT>
- EarthScope/IRIS Oklahoma RAMP network ZQ (2011–2012): network DOI <https://doi.org/10.7914/SN/ZQ_2011>

#### B. Reference catalog candidates

##### B1. Primary reference — McMahon et al. (2017) subspace-detection / relocated catalog

| Field | Information |
|---|---|
| **Priority** | **Primary** |
| **Reference type** | Detection + location-quality reference |
| **Public data release** | USGS DOI 10.5066/F7FJ2FNT; public |
| **Catalog span** | 2011-11-04 to 2011-12-05 |
| **Distributed catalog size** | **5,446 events + associated phase arrivals** in the USGS release |
| **Paper-reported final quality-filtered count** | **5,262 events** after the stated location-uncertainty filtering |
| **Count discrepancy** | The paper and the distributed data release report different final counts (5,262 vs 5,446). This must be reconciled by inspecting the release files before benchmark scoring is frozen. |
| **Stations used** | **31 seismic stations** |
| **Initial expert catalog** | 998 events were identified, located, and manually reviewed in the initial catalog used to construct detectors. |
| **Detection method** | S-phase subspace detection |
| **Association** | Arrival-time associator; events required observations at ≥5 stations for the main associated set |
| **Location method** | Bayesloc using the McNamara et al. velocity model |
| **Detection scale before quality filtering** | 577,040 S arrivals; 191,100 associated into 20,788 events; 21,786 events located |
| **High-quality criterion reported in paper** | 5,176 events had estimated epicentral uncertainty <500 m and depth uncertainty <1 km before the final catalog merge/filter accounting described by the paper |
| **Open access** | Catalog public; most waveform data through EarthScope/IRIS; one subset is described as coming from USGS NEIC archives |
| **Provisional reference quality** | **High** |
| **Reference independence** | **Medium–High** relative to a modern PhaseNet/GaMMA-style Agent because the reference uses subspace detection + Bayesloc and a manually reviewed seed catalog |
| **Best benchmark use** | Detection, event support, location uncertainty, network-deployment robustness |
| **Main limitation** | High-quality final set is strongly filtered by uncertainty; subspace detection is less sensitive to larger events and is supplemented with original catalog phases. |

##### B2. Secondary reference — manually reviewed seed catalog

| Field | Information |
|---|---|
| **Priority** | Secondary / expert anchor |
| **Reference type** | Expert-reviewed event/pick anchor |
| **Size** | **998 events** |
| **Construction** | Identified, located, and manually reviewed in the catalog used for subspace-detector construction |
| **Best benchmark use** | Larger/clearer event validation; expert-reviewed anchor for event existence and location comparison |
| **Main limitation** | Less complete than the enhanced catalog; not a separate high-resolution public benchmark product in the same sense as the USGS release. |

##### B3. Baseline

| Product | Role |
|---|---|
| Original operational/regional catalog(s) used by McMahon et al. | Baseline for catalog enhancement |
| Temporary/permanent station metadata | Required to interpret the changing network geometry during the first week |

#### C. Benchmark suitability

| Field | Assessment |
|---|---|
| **Recommended for core benchmark?** | **Yes** |
| **Primary target** | USGS McMahon catalog |
| **Secondary target** | 998-event manually reviewed seed set |
| **Recommended core window** | 2011-11-11 00:00 to 2011-11-19 00:00 UTC (8 days); an earlier 7-day window is retained only as a sensitivity comparison |
| **Optional stress-test window** | 2011-11-04 to 2011-11-11 |
| **Suggested Agent input** | Continuous waveform + station metadata; optional baseline catalog condition |
| **Short-window target event count** | 2,078 Cochran events in the frozen 8-day window |
| **Approximate waveform volume** | 25.71264 GB decimal (23.95 GiB) continuous upper bound for 31 stations × 3C × 100 Hz × int32 × 8 days |
| **Expected compute cost** | Medium |
| **Key benchmark risk** | The network evolves strongly before Nov. 11; some source data came from different archives; paper vs release event-count discrepancy must be reconciled |
| **Overall assessment** | Very strong benchmark for failure handling and network/data heterogeneity, not just catalog reproduction. |

---
