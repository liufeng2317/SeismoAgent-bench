# KILAUEA2018 — Case Analysis

> **Source of truth:** This file is the detailed, mutable analysis record for `KILAUEA2018`. The cross-case summary is maintained in [`docs/01_Case_details.md`](../../../docs/01_Case_details.md).

## Status

- Case ID: `KILAUEA2018`
- Phase: reference calibration and data preparation
- Status: `v1 benchmark window frozen`
- Primary reference: Shelly & Thelen (2019) summit catalog
- Secondary reference: Wei et al. (2022) broader onshore/offshore catalog
- Frozen v1 summit window: 2018-05-01 to 2018-05-09 UTC

## Scientific role

High-rate volcanic seismicity associated with eruption and caldera-collapse processes. The case tests non-stationary monitoring, dense event rates, and domain shift from tectonic sequences.

## Case information from v0.2 inventory

| Field | Information |
|---|---|
| Region | Kīlauea Volcano, Hawaiʻi, USA |
| Sequence type | Volcanic seismicity associated with eruption, summit collapse and repeated Mw~5 collapse events |
| Major events | Mw 6.9 south-flank earthquake on 2018-05-04; summit-collapse sequence intensified later |
| Primary study span | 2018-04-29 to 2018-08-06 |
| Frozen v1 window | 2018-05-01 00:00:00 to 2018-05-09 00:00:00 UTC |
| Networks | HVO and public onshore/offshore networks; Wei lists HV, PT, Z1, Z6, 4S and AM |
| Expected difficulty | High |
| Primary role | Volcanic high-rate monitoring and event recovery |

Shelly & Thelen report 2,823 template events and 44,188 final high-resolution summit earthquakes. Wei et al. report 375,736 earthquakes from a broader onshore/offshore workflow; the two products require explicit spatial matching.

## Reference evaluation matrix

| Reference | Evaluation role | Time scope | Spatial scope | Quality tier | Network / observation condition |
|---|---|---|---|---|---|
| Shelly & Thelen (2019) | Primary for summit detection and relative location | Full: 2018-04-29–08-06; frozen benchmark: 2018-05-01–05-09 UTC | Frozen summit box 19.30–19.50°N, −155.40 to −155.15°E, depth 0–20 km | **Q1** relative geometry; **Q2** summit detection/completeness; **Q3** island-wide claims | HVO summit network and correlation-derived phases |
| Wei et al. (2022) | Secondary for broader detection and absolute-location comparison | Approximately half-year eruption interval; subset to same week | Broader onshore/offshore island domain; must be spatially filtered | **Q2** broad detection/3-D location; not directly equivalent to Shelly | HV, PT, Z1, Z6, 4S and AM onshore/offshore networks |
| HVO operational catalog | Baseline: routine volcanic monitoring | Same frozen window | Same selected domain | **Q3** operational baseline | HVO operational network |

Kīlauea must be treated as two possible tasks: `summit task` (Shelly primary) or `broader island task` (Wei-centered). The two references cannot be ranked by event count without fixing the spatial domain and network condition.

## Reference products

| Product | Role | Current issue |
|---|---|---|
| Shelly & Thelen (2019) | Primary summit detection and relative-location reference | Summit-only scope; station count and exact QC fields require SI extraction. |
| Wei et al. (2022) | Secondary broader detection/location reference | Different spatial domain, networks, and location workflow; cannot be treated as a directly equivalent target. |
| HVO operational catalog | Baseline | Confirm release and coverage. |

## Calibration checklist

- [ ] Obtain the primary and secondary catalog files.
- [ ] Freeze whether the benchmark region is summit-only or broader island/flank.
- [ ] Extract station/network availability for the selected week.
- [ ] Reconcile event and phase schema differences.
- [ ] Separate high-rate detection evaluation from absolute-location evaluation.
- [ ] Record template-derived and 3-D-location-derived fields separately.

## Window and data preparation

### Frozen v1 benchmark window — summit task

| Field | Frozen value |
|---|---|
| Time window | 2018-05-01 00:00:00 to 2018-05-09 00:00:00 UTC (8 days) |
| Spatial rule | Summit box 19.30–19.50°N, −155.40 to −155.15°E, depth 0–20 km |
| Event counts | Shelly S1: 1,902 events; Wei S1 after the same summit/depth mask: 1,930 events |
| Observed ranges | Shelly: lat 19.329–19.470°, lon −155.366 to −155.194°, depth −0.69–15.10 km, M −0.72–4.80; Wei masked: lat 19.300–19.499°, lon −155.397 to −155.150°, depth 0.02–19.46 km, M −0.79–5.82 |
| Network condition | 66 HVO stations, 3-component channels where available; keep summit HVO channels separate from Wei's broader HV/PT/Z1/Z6/4S/AM network |
| Waveform volume | Design upper bound: ~47.9 GB for 66 × 3 components × 100 Hz × int32 × 8 days continuous; actual HVO gaps and channel selection reduce this |
| Reference quality and role | Shelly: Q1 relative summit geometry/Q2 high-rate summit detection; Wei: Q2 broader detection/3-D location cross-check; HVO routine: Q3 baseline; QuakeFlow: methodological context, catalog missing |

## Main risks

1. Primary and secondary catalogs cover different spatial domains.
2. The sequence and network are strongly time-dependent.
3. Template-based summit completeness is not island-wide ground truth.

## Sources

- `../references/USGS2019_SCIENCE_OVERVIEW/paper/USGS2019_SCIENCE_OVERVIEW__paper.pdf`
- Shelly & Thelen (2019), DOI: https://doi.org/10.1029/2019GL085636
- Wei et al. (2022), DOI: https://doi.org/10.1029/2021EA001979
## Full inventory record (migrated from `docs/01_Case_details.md`)
### 2018 Kīlauea Eruption / Caldera-Collapse Seismicity

## Literature and catalog gap audit

### Core products already selected

- Shelly & Thelen summit catalog: USGS DOI https://doi.org/10.5066/P9DMIFMW.
- Wei et al. broad onshore/offshore catalog: Dryad DOI https://doi.org/10.5061/dryad.np5hqbzw9.

### Important omitted catalogs/articles

- Lengliné, Duputel & Okubo (2021), *Tracking dike propagation leading to the 2018 Kīlauea eruption*, DOI https://doi.org/10.1016/j.epsl.2020.116653. Recommended as an **East Rift Zone/dike-propagation auxiliary**; it fills a spatial role not covered by the summit-only primary.
- Matoza, Okubo & Shearer (2021), *Comprehensive high-precision relocation of seismicity on the Island of Hawaiʻi 1986–2018*, DOI https://doi.org/10.1029/2020EA001253. The downloadable catalog includes starting hypocenters, phase picks and high-precision relocations. Recommended as a **Q1/Q2 absolute/relative-location auxiliary** for the broader-island condition.
- Local author-hosted product: `../catalogs/MATOZA2021_EA001253/MATOZA2021_EA001253__catalog_islandwide.txt` (347,446 starting and 299,966 relocated events; release ZIP and README retained).
- Matoza et al. (2021) paper: `../references/MATOZA2021_EA001253/paper/MATOZA2021_EA001253__paper.pdf`.
- Local LP summit auxiliary: `../catalogs/MATOZA2014_GL059819/MATOZA2014_GL059819__catalog_lp_summit.txt` (12,290 LP events; Matoza et al. 2014).
- Matoza et al. (2014) paper: `../references/MATOZA2014_GL059819/paper/MATOZA2014_GL059819__paper.pdf`.
- Local Lengliné product: `../catalogs/LENGLINE2021_EPSL116653/raw/loc_events.txt`; the file is kept separate from the Shelly summit S1/S2 products.
- QuakeFlow (Zhu et al., GJI, DOI https://doi.org/10.1093/gji/ggac355) is retained as a **modern automated-workflow comparison**, not independent truth. The local paper and evaluation document are under `../references/QUAKEFLOW_GJI_GGAC355/`. The paper identifies HVO/USGS network catalogs as the data sources and archives code (https://doi.org/10.5281/zenodo.7023970), but no stable downloadable Hawaii QuakeFlow-generated event catalog was found. It must remain catalog-missing until an original output or frozen reproducible run is obtained.

### Audit conclusion

**Sufficiency verdict:** Conditionally sufficient, but only after freezing the spatial task. For a summit-only task, Shelly–HVO is sufficient with Wei as cross-check. For a broad-island task, Wei–Matoza–HVO is needed, with Shelly and Lengliné as spatially restricted auxiliaries; the Matoza island-wide and LP products are now locally available. A single undifferentiated Kīlauea target is not sufficient.

#### A. Case information

| Field | Information |
|---|---|
| **Case ID** | KILAUEA2018 |
| **Region** | Kīlauea Volcano, Hawaiʻi, USA |
| **Sequence type** | Volcanic seismicity associated with eruption, summit collapse, and repeated Mw ~5 collapse events |
| **Major regional event** | Mw 6.9 south-flank earthquake on 2018-05-04; summit collapse sequence intensified later |
| **Scientific significance** | Extremely high-rate volcanic monitoring problem with strong temporal evolution, collapse cycles, and changing network/data conditions. |
| **Primary reference span** | 2018-04-29 to 2018-08-06 |
| **Recommended compact benchmark window** | **2018-05-01 to 2018-05-08 (7 days)** for eruption-onset/high-rate monitoring. A later 3–7 day summit-collapse window can be added after checking target density and station availability. |
| **Benchmark region** | The benchmark should explicitly specify whether it targets the **summit catalog** (Shelly & Thelen) or the broader island/flank catalog (Wei et al.). |
| **Raw waveform access** | HVO and other network data are publicly available through EarthScope/IRIS; the broader Wei study used HV, PT, Z1, Z6, 4S and AM networks. |
| **Expected benchmark difficulty** | High |
| **Primary benchmark role** | Volcanic monitoring; high event rate; waveform-similarity detection; robust processing under a rapidly evolving sequence. |

##### Key sources

- Shelly & Thelen (2019), *Anatomy of a Caldera Collapse: Kīlauea 2018 Summit Seismicity Sequence in High Resolution*. DOI: <https://doi.org/10.1029/2019GL085636>
- USGS high-resolution catalog release. DOI: <https://doi.org/10.5066/P9DMIFMW>
- Wei et al. (2022), *An Improved Earthquake Catalog During the 2018 Kīlauea Eruption From Combined Onshore and Offshore Seismic Arrays*. DOI: <https://doi.org/10.1029/2021EA001979>
- USGS correlation-derived phase arrivals. DOI: <https://doi.org/10.5066/P13JCJ2I>
- Local phase-arrival CSV and Shelly location products: `../catalogs/SHELLY2019_GL085636/`
- Shelly Data Set S1/S2: `../catalogs/SHELLY2019_GL085636/SHELLY2019_GL085636__catalog_S1.txt` and `SHELLY2019_GL085636__catalog_S2.txt`; Figure SI: `../references/SHELLY2019_GL085636/supplement/Shelly2019_Kilauea_Figure_SI.pdf`.
- Wei paper/SI: `../references/WEI2022_EA001979/paper/WEI2022_EA001979__paper.pdf` and `../references/WEI2022_EA001979/supplement/Wei2022_Kilauea_SI.pdf`.
- Wei Data Set S1: `../catalogs/WEI2022_EA001979/WEI2022_EA001979__catalog_S1.txt` (375,736 events).

#### B. Reference catalog candidates

##### B1. Primary reference — Shelly & Thelen (2019) summit high-resolution catalog

| Field | Information |
|---|---|
| **Priority** | **Primary** |
| **Reference type** | Summit detection + high-precision relative-location reference |
| **Public release** | USGS DOI 10.5066/P9DMIFMW; public / CC0 |
| **Span** | 2018-04-29 to 2018-08-06 |
| **HVO template events** | **2,823 cataloged earthquakes** |
| **Final high-resolution catalog** | **44,188 summit earthquakes** with at least 10 P and 10 S correlation-derived differential times after hypoDD inversion |
| **Core processing** | Waveform-based detection + correlation-derived differential times + hypoDD |
| **Template quality policy** | During May, automatic + analyst-refined events were used; later processing switched to analyst-refined templates because of their higher quality |
| **Station count** | **66 HVO stations for the frozen summit task; Wei's broader network remains a secondary condition.** |
| **Open access** | Public catalog; HVO waveform data are openly archived through EarthScope/IRIS |
| **Provisional reference quality** | **High** |
| **Reference independence** | Medium |
| **Best benchmark use** | Dense summit event recovery, relative relocation, high-rate monitoring |
| **Main limitation** | Summit-focused, template-dependent reference; not a complete island-wide or offshore ground truth. |

##### B2. Secondary reference — Wei et al. (2022) onshore + offshore catalog

| Field | Information |
|---|---|
| **Priority** | Secondary |
| **Reference type** | Broader detection/association/absolute-location reference |
| **Paper** | Earth and Space Science, DOI 10.1029/2021EA001979; open access |
| **Catalog span** | Approximately half a year during the 2018 eruption |
| **Catalog size** | **375,736 earthquakes** |
| **Detection** | STA/LTA candidate detection |
| **Association/picking** | Detections associated into events; automatic P/S picking |
| **Location** | NonLinLoc with a 3-D velocity model and topographic constraints |
| **Magnitude** | Coda/duration magnitude |
| **Networks** | Most publicly available onshore/offshore data; paper lists HV, PT, Z1, Z6, 4S and Raspberry Shake AM |
| **Open access** | Source waveforms public; resulting catalog available in article supplement / Dryad |
| **Provisional reference quality** | Medium–High |
| **Reference independence** | Medium–High relative to Shelly because detection/location workflow and network coverage differ substantially |
| **Best benchmark use** | Cross-method comparison; broader flank/offshore completeness; sensitivity to network coverage |
| **Main limitation** | Much larger temporal/spatial scope and observation set than the summit catalog; use only a carefully matched short-window/region subset for benchmark comparison. |

##### B3. Baseline / auxiliary references

| Product | Role |
|---|---|
| HVO operational catalog | Routine baseline |
| USGS correlation-derived arrival release (P13JCJ2I) | Pick-level auxiliary reference; shares methodology with Shelly study |
| ComCat | Large-event / operational cross-check |

#### C. Benchmark suitability

| Field | Assessment |
|---|---|
| **Recommended for core benchmark?** | **Yes, but scope must be tightly defined** |
| **Primary target** | Shelly & Thelen summit catalog |
| **Secondary target** | Wei et al. short-window/region subset |
| **Recommended window** | 2018-05-01 to 2018-05-08 for v1 |
| **Short-window target event count** | Shelly 1,902; Wei summit/depth-matched 1,930 |
| **Station count** | 66 HVO stations for primary; Wei network labels retained separately |
| **Approximate waveform volume** | ~47.9 GB continuous upper bound for 66 stations × 3C × 100 Hz × int32 × 8 days |
| **Expected compute cost** | Medium–High |
| **Key benchmark risk** | Different catalogs target different spatial domains and use different station sets; comparison is invalid unless space/time/network conditions are explicitly matched |
| **Overall assessment** | Scientifically valuable because it tests a regime very different from tectonic aftershock sequences. |

---
