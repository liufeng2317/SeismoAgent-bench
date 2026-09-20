# KILAUEA2018 — Case Analysis

> **Source of truth:** This file is the detailed, mutable analysis record for `KILAUEA2018`. The cross-case summary is maintained in [`docs/01_1_Case_details.md`](../../../docs/01_1_Case_details.md).

## Status

- Case ID: `KILAUEA2018`
- Phase: reference calibration and data preparation
- Status: `v1 benchmark window frozen`
- Primary reference: Shelly & Thelen (2019) summit catalog
- Secondary reference: Wei et al. (2022) broader onshore/offshore catalog; HVO remains the Q3 operational baseline
- Frozen v1 summit window: 2018-05-01 to 2018-05-09 UTC
- Catalog processing pilot: [catalog_processing_index.md](./catalog_processing_index.md)

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

Shelly & Thelen report 2,823 template events and 44,188 final high-resolution summit earthquakes. Wei et al. report 375,736 earthquakes from a broader onshore/offshore workflow. In the frozen summit mask, Shelly S1/S2 contribute 1,883/1,877 common-mask rows, while Wei contributes 2,369 rows (1,930 with numeric magnitudes); these are different observation products and require explicit matching.

## Reference evaluation matrix

| Reference | Evaluation role | Time scope | Spatial scope | Quality tier | Network / observation condition |
|---|---|---|---|---|---|
| Shelly & Thelen (2019) | Primary for summit detection and relative location | Full: 2018-04-29–08-06; frozen benchmark: 2018-05-01–05-09 UTC | Frozen summit box 19.30–19.50°N, −155.40 to −155.15°E, depth 0–20 km; S1/S2 common-mask rows 1,883/1,877 | **Q1** relative geometry; **Q2** summit detection/completeness; **Q3** island-wide claims | Article does not state one fixed count; local phase release has 25 unique HV stations; run/network metadata remains separate |
| Wei et al. (2022) | Secondary for broader detection and absolute-location comparison | 2018-03-01–09-30; subset to same week | Broader onshore/offshore island domain; common summit mask gives 2,369 rows, 1,930 with numeric magnitude | **Q2** broad detection/3-D location; not directly equivalent to Shelly | HV, PT, Z1, Z6, 4S and AM; rapidly changing temporary arrays |
| HVO operational catalog | Baseline: routine volcanic monitoring | Same frozen window | Same selected domain | **Q3** operational baseline | HVO operational network |

Kīlauea must be treated as two possible tasks: `summit task` (Shelly primary) or `broader island task` (Wei-centered). The two references cannot be ranked by event count without fixing the spatial domain and network condition.

## Reference products

| Product | Role | Current issue |
|---|---|---|
| Shelly & Thelen (2019) | Primary summit detection and relative-location reference | Paper reading and S1/S2 catalog audit are complete; common-mask counts are S1=1,883 and S2=1,877. Exact run-specific thresholds/station masks remain in the figure SI and are not yet tabulated. |
| Wei et al. (2022) | Secondary broader detection/location reference | Paper reading and 375,736-row S1 audit are complete; common summit mask has 2,369 rows, of which 1,930 have numeric magnitudes. Different spatial domain, networks, and location workflow prevent direct event-count ranking. |
| Matoza et al. (2021) | Island-wide relative-location auxiliary | 347,446-row revised release; 299,966 `nbranch>1`; relocated-coordinate summit mask 1,130/984 (`nbranch>1`), starting-coordinate mask 1,190/1,044. Use for broader spatial role, not a replacement for Shelly. |
| Lengliné et al. (2021) | East Rift Zone/dike auxiliary | 6,327 template-matched events; 6,049 overlap the v1 time interval. Native table has relative x/y only; an assumption-labelled absolute derivative is available, but no observed event-specific depth/magnitude. |
| Matoza et al. (2014) | Historical LP source-type auxiliary | 12,290 LP events from 1986–2009; zero rows in the 2018 window. |
| HVO operational catalog | Baseline | Confirm release and coverage. |

## Calibration checklist

- [x] Obtain and audit the primary and secondary catalog files.
- [x] Freeze the v1 summit region; keep a separate broader-island task for Wei/Matoza.
- [ ] Extract station/network availability for the selected week (Shelly run metadata and Wei temporary-array gaps remain).
- [x] Reconcile event and phase schema differences at the catalog-summary level.
- [ ] Separate high-rate detection evaluation from absolute-location evaluation.
- [ ] Record template-derived and 3-D-location-derived fields separately.

## Window and data preparation

### Frozen v1 benchmark window — summit task

| Field | Frozen value |
|---|---|
| Time window | 2018-05-01 00:00:00 to 2018-05-09 00:00:00 UTC (8 days) |
| Spatial rule | Summit box 19.30–19.50°N, −155.40 to −155.15°E, depth 0–20 km |
| Event counts | Shelly S1: 1,902 time-only / **1,883 common-mask** events; Shelly S2: 1,896 time-only / **1,877 common-mask** events; Wei: 2,369 common-mask rows, of which 1,930 have numeric magnitudes; Matoza 2021 relocated-coordinate mask 1,130/984 (`nbranch>1`) and starting-coordinate mask 1,190/1,044 |
| Observed ranges | Shelly S1 common mask: lat 19.329–19.470°, lon −155.366 to −155.194°, depth 0.010–15.103 km, M −0.72–4.80; Wei mask: lat 19.300–19.499°, lon −155.397 to −155.150°, depth 0.017–19.902 km, M −0.79–5.82 when present; Matoza relocated-coordinate mask: lat 19.300520–19.495500°, lon −155.396330–−155.150200°, depth 0.007–19.237 km, M 0.00–4.66; starting-coordinate mask: lat 19.300330–19.491170°, lon −155.396330–−155.150160°, depth 0.000–18.640 km, M 0.00–4.66 |
| Network condition | Shelly: article has no fixed station count; local phase release has 25 HV station codes. Wei: HV/PT/Z1/Z6/4S/AM with changing temporary-array coverage; preserve network/deployment flags separately |
| Waveform volume | Not frozen from the current catalogs: derive from an explicit station/channel/day manifest. The prior 66-station/47.9-GB estimate is provisional and not supported by the local Shelly phase release |
| Reference quality and role | Shelly S1/S2: Q1 relative summit geometry/Q2 high-rate summit detection; Wei: Q2 broad detection/3-D location cross-check (2,369 rows, 1,930 numeric-M); HVO routine: Q3 baseline; QuakeFlow: methodological context, catalog missing |

## Main risks

1. Primary and secondary catalogs cover different spatial domains.
2. The sequence and network are strongly time-dependent.
3. Template-based summit completeness is not island-wide ground truth.
4. Shelly S1/S2 time-only and common-mask counts differ; Wei rows without numeric magnitude must not be silently discarded.
5. The local Shelly phase CSV measures 25 HV station codes, not a complete station-day inventory.

## Sources

- `../references/USGS2019_SCIENCE_OVERVIEW/paper/USGS2019_SCIENCE_OVERVIEW__paper.pdf`
- `../references/SHELLY2019_GL085636/parsed/paper/SHELLY2019_GL085636__paper_reading.md`
- `../catalogs/SHELLY2019_GL085636/SHELLY2019_GL085636__catalog_summary.md`
- `../references/WEI2022_EA001979/parsed/paper/WEI2022_EA001979__paper_reading.md`
- `../catalogs/WEI2022_EA001979/WEI2022_EA001979__catalog_summary.md`
- `../references/MATOZA2021_EA001253/parsed/paper/MATOZA2021_EA001253__paper_reading.md`
- `../catalogs/MATOZA2021_EA001253/MATOZA2021_EA001253__catalog_summary.md`
- `../references/MATOZA2014_GL059819/parsed/paper/MATOZA2014_GL059819__paper_reading.md`
- `../catalogs/MATOZA2014_GL059819/MATOZA2014_GL059819__catalog_summary.md`
- `../references/LENGLINE2021_EPSL116653/parsed/paper/LENGLINE2021_EPSL116653__paper_reading.md`
- `../catalogs/LENGLINE2021_EPSL116653/LENGLINE2021_EPSL116653__catalog_summary.md`
- Shelly & Thelen (2019), DOI: https://doi.org/10.1029/2019GL085636
- Wei et al. (2022), DOI: https://doi.org/10.1029/2021EA001979
## Full inventory record (migrated from `docs/01_1_Case_details.md`)
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
- Local Lengliné product: `../catalogs/LENGLINE2021_EPSL116653/raw/loc_events.txt`; the native relative file is kept separate from the Shelly summit S1/S2 products. An approximate absolute derivative and transform specification are under `../catalogs/LENGLINE2021_EPSL116653/analysis/derived/relative_events/`.
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
| **Recommended compact benchmark window** | **2018-05-01T00:00:00Z <= t < 2018-05-09T00:00:00Z (8 days; display dates May 1–8)** for eruption-onset/high-rate monitoring. A later 3–7 day summit-collapse window can be added after checking target density and station availability. |
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
| **Final high-resolution catalog** | **44,188 summit earthquakes** with at least 10 P and 10 S correlation-derived differential times after hypoDD inversion; common-mask v1 count 1,883 |
| **Core processing** | Waveform-based detection + correlation-derived differential times + hypoDD |
| **Template quality policy** | During May, automatic + analyst-refined events were used; later processing switched to analyst-refined templates because of their higher quality |
| **Station count** | The article depicts a full HVO network but does not state one fixed count; the local phase CSV contains 25 unique HV stations. Do not use the old 66-station estimate without a station inventory. |
| **Open access** | Public catalog; HVO waveform data are openly archived through EarthScope/IRIS |
| **Provisional reference quality** | **High** |
| **Reference independence** | Medium |
| **Best benchmark use** | Dense summit event recovery, relative relocation, high-rate monitoring |
| **Main limitation** | Summit-focused, template-dependent reference; magnitudes are approximate and depth is summit-referenced; not a complete island-wide or offshore ground truth. |

##### B2. Secondary reference — Wei et al. (2022) onshore + offshore catalog

| Field | Information |
|---|---|
| **Priority** | Secondary |
| **Reference type** | Broader detection/association/absolute-location reference |
| **Paper** | Earth and Space Science, DOI 10.1029/2021EA001979; open access |
| **Catalog span** | Approximately half a year during the 2018 eruption |
| **Catalog size** | **375,736 rows**; common summit mask 2,369 rows, 1,930 with numeric magnitudes |
| **Detection** | STA/LTA candidate detection |
| **Association/picking** | Detections associated into events; automatic P/S picking |
| **Location** | NonLinLoc with a 3-D velocity model and topographic constraints |
| **Magnitude** | Coda/duration magnitude |
| **Networks** | Most publicly available onshore/offshore data; paper lists HV, PT, Z1, Z6, 4S and Raspberry Shake AM |
| **Open access** | Source waveforms public; resulting catalog available in article supplement / Dryad |
| **Provisional reference quality** | Medium–High |
| **Reference independence** | Medium–High relative to Shelly because detection/location workflow and network coverage differ substantially |
| **Best benchmark use** | Cross-method comparison; broader flank/offshore completeness; sensitivity to network coverage |
| **Main limitation** | Much larger temporal/spatial scope and changing observation set than the summit catalog; 67,719 rows have no magnitude, so use the all-row count for detection and a separate numeric-M sensitivity for magnitude metrics. |

##### B3. Baseline / auxiliary references

| Product | Role |
|---|---|
| HVO operational catalog | Routine baseline |
| USGS correlation-derived arrival release (P13JCJ2I) | Pick-level auxiliary reference; shares methodology with Shelly study |
| Matoza et al. (2021) | Island-wide Q1-relative/Q2-broad auxiliary; local revised release has 984 relocated-coordinate rows (or 1,044 starting-coordinate rows) in the common summit mask |
| Lengliné et al. (2021) | East Rift Zone dike auxiliary; native table has no absolute depth/magnitude; derived lat/lon are assumption-labelled only |
| Matoza et al. (2014) | Historical LP auxiliary; no 2018 temporal overlap |
| ComCat | Large-event / operational cross-check |

#### C. Benchmark suitability

| Field | Assessment |
|---|---|
| **Recommended for core benchmark?** | **Yes, but scope must be tightly defined** |
| **Primary target** | Shelly & Thelen summit catalog |
| **Secondary target** | Wei et al. short-window/region subset |
| **Recommended window** | 2018-05-01T00:00:00Z <= t < 2018-05-09T00:00:00Z (display dates May 1–8) for v1 |
| **Short-window target event count** | Shelly S1 1,883 and S2 1,877 after the common mask (time-only 1,902/1,896); Wei 2,369 rows, with 1,930 numeric-magnitude rows |
| **Station count** | Shelly local phase release: 25 HV codes; complete run/station-day inventory pending. Wei network labels and deployments retained separately |
| **Approximate waveform volume** | Not frozen; derive from the station/channel/day manifest before waveform acquisition |
| **Expected compute cost** | Medium–High |
| **Key benchmark risk** | Different catalogs target different spatial domains and use different station sets; comparison is invalid unless space/time/network conditions are explicitly matched |
| **Overall assessment** | Scientifically valuable because it tests a regime very different from tectonic aftershock sequences. |

---
