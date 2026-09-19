# MAPLE2017 — Case Analysis

> **Source of truth:** This file is the detailed, mutable analysis record for `MAPLE2017`. The cross-case summary is maintained in [`Docs/01_Case_details.md`](../../../Docs/01_Case_details.md).

## Status

- Case ID: `MAPLE2017`
- Phase: reference calibration and data preparation
- Status: `v1 benchmark window frozen`
- Primary reference: Shelly & Hardebeck (2019)
- Frozen v1 core window: 2017-06-11 to 2017-06-19 UTC

## Scientific role

Prolific Yellowstone earthquake swarm, useful for testing event recovery, swarm structure, waveform-similarity detection, and relative relocation outside a mainshock-aftershock setting.

## Case information from v0.2 inventory

| Field | Information |
|---|---|
| Region | Yellowstone region, Wyoming/Montana, USA |
| Sequence type | Earthquake swarm |
| Largest event | Mw 4.4 on 2017-06-16 |
| Scientific significance | One of the most prolific and best-recorded Yellowstone swarms after network upgrades |
| Recommended window | 2017-06-11 to 2017-06-18 |
| Network | Published 27-station setup; EarthScope/IRIS Yellowstone data |
| Expected difficulty | Medium–High |
| Primary role | Swarm detection and relative relocation |

The Shelly & Hardebeck reference contains 15,912 well-located events and a large differential-time set processed with template matching and hypoDD.

## Reference evaluation matrix

| Reference | Evaluation role | Time scope | Spatial scope | Quality tier | Network / observation condition |
|---|---|---|---|---|---|
| Shelly & Hardebeck (2019) | Primary: swarm event recovery, relative relocation and cluster geometry | Published swarm study; frozen benchmark: 2017-06-11–06-19 UTC | Frozen Maple Creek input box; exact event polygon unavailable in phase-only release | **Q1** relative location; **Q2** template-enhanced detection; **Q3** absolute location | Published 27-station Yellowstone setup; EarthScope/IRIS data |
| Routine Yellowstone catalog | Baseline: operational detection and catalog expansion | Same frozen window | Same swarm region | **Q3** operational baseline | Routine Yellowstone network/catalog |
| Published phase/differential-time products | Auxiliary: phase/relative-location diagnostics | Match primary window only | Same event clusters | **Q4** auxiliary unless independent provenance is demonstrated | Correlation/template-derived products unless proven otherwise |

The primary catalog is suitable for a template-enhanced swarm benchmark, but reference independence is `Low–Medium` against a similar template/correlation Agent. It should not be used as an absolute-location truth set.

## Reference products

| Product | Role | Current issue |
|---|---|---|
| Shelly & Hardebeck (2019) | Primary detection and relative-location reference | Template/differential-time lineage and exact window subset require documentation. |
| Routine Yellowstone catalog | Baseline | Identify exact release and event IDs. |
| Published phase/differential-time products | Auxiliary | Determine whether they are independently usable or inherit the same template lineage. |

## Calibration checklist

- [ ] Parse the main catalog and supplementary files.
- [ ] Confirm event, phase, and uncertainty fields.
- [ ] Determine the station/channel set active during 2017-06-11 to 2017-06-18.
- [ ] Quantify catalog overlap with the routine baseline.
- [ ] Mark template-derived versus independently reviewed information.
- [ ] Freeze the spatial region and event inclusion rules.

## Window and data preparation

### Frozen v1 benchmark window

| Field | Frozen value |
|---|---|
| Time window | 2017-06-11 00:00:00 to 2017-06-19 00:00:00 UTC (8 days) |
| Event count | The phase release contains 1,536,742 phase rows and 22,858 unique `match_id` values in this window; this is a phase-associated ID count, not a validated event-catalog count. The published Shelly catalog total is 15,912 well-located events for the study. |
| Spatial rule | Maple Creek swarm envelope, approximately 44.45–44.75°N, 110.55–110.15°W; this is the frozen input box because the local product is phase-only |
| Depth/magnitude rule | Retain 0–15 km depth and all reported magnitudes when the event catalog is obtained; observed depth/magnitude ranges cannot be computed from the phase-only release |
| Network condition | Published 27-station Yellowstone/EarthScope–IRIS setup; preserve station availability and template/match lineage |
| Waveform volume | Design upper bound: ~19.6 GB for 27 × 3 components × 100 Hz × int32 × 8 days continuous; actual volume depends strongly on channel gaps |
| Reference quality and role | Shelly: Q1 relative geometry/Q2 template-enhanced detection; routine Yellowstone catalog: Q3 baseline; phase release: Q4 auxiliary, not independent event truth; Pang: context only until its 3,345-event table is obtained |

## Main risks

1. The primary reference is strongly template-based.
2. Template lineage may reduce reference independence.
3. Swarm completeness should not be inferred from a single catalog.

## Sources

- `../references/SHELLY2019_GL081607/`
- `../references/PANG2019_GL082376/`
- `../references/MAPLE_RELATED_OPEN/paper/MAPLE_RELATED_OPEN__paper.pdf`
- Shelly & Hardebeck (2019), DOI: https://doi.org/10.1029/2018GL081607
## Full inventory record (migrated from `Docs/01_Case_details.md`)
### 2017 Maple Creek Earthquake Swarm, Yellowstone

## Literature and catalog gap audit

### Core omission — Pang et al. (2019) independent relocation catalog

- Paper: *The 2017–2018 Maple Creek Earthquake Sequence in Yellowstone National Park, USA*.
- DOI: https://doi.org/10.1029/2019GL082376
- Product: 3,345-event catalog with regional 1-D absolute locations and GrowClust relative relocation; the paper reports median horizontal/depth standard errors of approximately 500/730 m for the starting locations.
- Networks: MB, PB, TA, US and WY; waveform data are openly available through IRIS/EarthScope.
- Recommended role: **Q1/Q2 independent location secondary reference**, especially valuable because the present primary is template-matching-heavy.
- Action: retain the article SI and IRIS waveform links; no public 3,345-event machine-readable GrowClust table was identified in the article or its SI. The related [USGS 2025 phase-arrival release](https://doi.org/10.5066/P13JCJ2I) is Shelly & Hardebeck's Maple Creek product and is auxiliary only; it must not be substituted for Pang's catalog without provenance review.

### Existing primary remains valid

Shelly & Hardebeck remains the stronger detection-completeness and dense relative-geometry target (15,912 well-located events; 30,411-event magnitude catalog). Pang provides the missing independent location view rather than replacing Shelly.

### Audit conclusion

**Sufficiency verdict:** Conditionally sufficient at the paper level, but the Pang machine-readable catalog remains an acquisition gap. Shelly & Hardebeck alone is not sufficient for independent validation because of its strong template/correlation lineage; a three-level Shelly–Pang–routine comparison becomes possible only after the Pang event table is obtained or reconstructed with explicit provenance.

#### A. Case information

| Field | Information |
|---|---|
| **Case ID** | MAPLE2017 |
| **Region** | Yellowstone region, Wyoming/Montana, USA |
| **Sequence type** | Earthquake swarm |
| **Largest event** | Mw 4.4 on 2017-06-16 |
| **Scientific significance** | One of the most prolific Yellowstone swarms in recent decades and the best-recorded large Yellowstone swarm following network upgrades. |
| **Routine activity** | Nearly 2,500 routinely detected events during the main June–September phase |
| **Full high-resolution processing span** | Templates: 2017-06-11 to 2017-09-06; continuous scanning through 2017-09-14 |
| **Recommended compact benchmark window** | **2017-06-11 to 2017-06-18 (7 days)**, covering swarm onset and the Mw 4.4 event |
| **Network context** | 27 stations within 70 km; upgraded three-component broadband coverage |
| **Raw waveform access** | Continuous seismic data used with UUSS routine catalog and picks; Yellowstone network data are distributed through EarthScope/IRIS. |
| **Expected benchmark difficulty** | Medium–High |
| **Primary benchmark role** | Swarm monitoring without a classic mainshock–aftershock structure; template-based detection; dense relative relocation; migration/fault-network geometry. |

##### Key sources

- Shelly & Hardebeck (2019), *Illuminating Faulting Complexity of the 2017 Yellowstone Maple Creek Earthquake Swarm*. DOI: <https://doi.org/10.1029/2018GL081607>
- Public supporting datasets are attached to the article.
- USGS correlation-derived phase arrivals for the same study. DOI: <https://doi.org/10.5066/P13JCJ2I>
- Local phase-arrival CSV: `../catalogs/SHELLY2019_GL081607/raw/Yellowstone_2017_correlation_phase_arrivals.csv`
- Yellowstone National Park Seismograph Network (WY) is distributed by EarthScope/IRIS.

#### B. Reference catalog candidates

##### B1. Primary reference — Shelly & Hardebeck (2019) high-resolution catalog

| Field | Information |
|---|---|
| **Priority** | **Primary** |
| **Reference type** | Detection + high-precision relative-location reference |
| **Paper** | GRL DOI 10.1029/2018GL081607 |
| **Catalog/data access** | Supporting data publicly attached to the article |
| **Routine templates** | **2,289 events** from 2017-06-11 to 2017-09-06 |
| **Stations** | **27 stations within 70 km** |
| **Continuous scan** | 2017-06-11 to 2017-09-14 |
| **Detection** | Waveform template matching / correlation-based detection |
| **Differential times** | 34.1 million correlation-derived + 1.3 million catalog-derived differential times |
| **Relocation** | hypoDD double-difference relocation |
| **Well-located events** | **15,912 events** retaining at least 50 P and 50 S correlation observations |
| **Magnitudes** | Magnitudes estimated for >30,000 events |
| **Initial catalog/picks** | Routine catalog + phase picks from University of Utah Seismograph Stations |
| **Provisional reference quality** | **High** |
| **Reference independence** | Medium |
| **Best benchmark use** | Event recovery, dense swarm relative location, fine-scale fault/migration structure |
| **Main limitation** | Template coverage and correlation requirements favor events similar to catalog templates; not absolute-location ground truth. |

##### B2. Auxiliary reference — USGS correlation-derived arrival-time release

| Field | Information |
|---|---|
| **Priority** | Auxiliary |
| **Reference type** | Phase-arrival reference |
| **Data release** | USGS DOI 10.5066/P13JCJ2I |
| **Coverage** | Includes Maple Creek 2017, Kīlauea 2018, Ridgecrest 2019 |
| **Best benchmark use** | Pick timing / phase-arrival consistency for matched events |
| **Independence** | Low relative to the Shelly catalog because the arrivals are derived from the same matched-filter studies |
| **Main limitation** | Not a second independent catalog. |

##### B3. Baseline

| Product | Role |
|---|---|
| UUSS routine catalog + phase picks | Operational baseline / template seed |
| WY network metadata/waveforms | Raw observation source |

#### C. Benchmark suitability

| Field | Assessment |
|---|---|
| **Recommended for core benchmark?** | **Yes** |
| **Primary target** | Shelly & Hardebeck |
| **Secondary independent high-resolution catalog** | None confirmed in this first survey; do not fabricate one merely to reach three references |
| **Auxiliary reference** | USGS correlation-derived arrivals |
| **Recommended window** | 2017-06-11 to 2017-06-18 |
| **Short-window target event count** | 22,858 unique phase-associated match IDs (not a validated event count); published Shelly total is 15,912 well-located events |
| **Stations** | 27 in the published processing |
| **Approximate waveform volume** | ~19.6 GB continuous upper bound for 27 stations × 3C × 100 Hz × int32 × 8 days |
| **Expected compute cost** | Medium |
| **Key benchmark risk** | Primary target and phase-arrival auxiliary product share the same underlying matched-filter methodology |
| **Overall assessment** | Excellent swarm benchmark and strong complement to mainshock–aftershock cases. |

---

---
