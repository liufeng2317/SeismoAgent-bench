# Candidate case pool

Candidate earthquake sequences and swarms for the benchmark, grouped by priority: Tier A is the Phase I set now in use, Tiers B and C are expansion and watchlist candidates. The priority tiers here are about readiness and value as a case; the difficulty tiers of the Phase I cases are defined in the [research plan](../research/00_Research_Plan_Benchmark.md) §2. Source verification: 2026-09-18 (moved from the research plan v0.2, Part II, on 2026-10-29).

## 1. Purpose of the candidate pool

The candidate pool is intentionally broader than the first implementation set.

It serves four purposes:

1. preserve multiple options before waveform-access and compute tests are completed;
2. cover distinct monitoring regimes;
3. identify cases with multiple high-quality reference catalogs;
4. provide a path for expanding the benchmark after the first six cases are operational.

Cases are selected because they combine, to varying degrees:

- a high-quality published reference catalog;
- continuous or event waveform availability;
- transparent processing methods;
- a short sequence or a scientifically meaningful short-window subset;
- complementary scientific difficulty.

The table below is a **research candidate pool**, not a final ranking. Cases marked as long-duration studies would only be used through compact subsets.

## 2. Tier A — Phase I highest-priority cases

The six Tier A cases became the Phase I set. Their current primary references, windows and tiers are in [`00_Case_Registry.md`](00_Case_Registry.md); the table below is the selection record of 2026-09-18 and names the primaries proposed then (since changed for Prague, Maple Creek and Kaikōura).

| Case | Sequence / regime | Candidate primary reference(s) | Reference methods | Waveform / data access | Why selected | Main concern |
|---|---|---|---|---|---|---|
| **2019 Ridgecrest, California** | Dense foreshock–mainshock–aftershock sequence | Shelly (2020), 34,091 events; Ross et al. (2019) secondary | Template matching, waveform correlation, precise relative relocation / GrowClust-style structural catalog | SCEDC/SCSN public | Excellent public data, widely accepted high-resolution target, extreme association density, existing TRACE baseline | Shared raw-data lineage among references; target-method leakage must be controlled |
| **2020 Magna, Utah** | Moderate mainshock–aftershock sequence | Pang et al. (2020); Baker et al. ML/nodal catalog secondary | Matched filtering, cross-correlation, high-precision relocation; independent ML/nodal workflow | EarthScope/IRIS + COSMOS; UU data public | Two complementary enhanced catalogs; manageable scale; explicit robustness tests in reference work | Reference catalogs use different station configurations |
| **2017 Maple Creek, Yellowstone** | Earthquake swarm | Shelly & Hardebeck (2019), 15,912 well-located events | Template matching, large differential-time set, hypoDD | EarthScope/IRIS + public supporting data | Strong swarm benchmark; 27-station published setup; clear routine-to-enhanced gap | Main phase-arrival auxiliary data share the same matched-filter lineage |
| **2011 Prague, Oklahoma** | Induced/triggered aftershock sequence | McMahon et al. (2017), 5,446-event public release | Subspace detection, associator, Bayesloc, manually reviewed seed catalog | EarthScope/IRIS + USGS release | Different methodology from common PhaseNet/GaMMA pipelines; 31-station mixed network; explicit uncertainty filtering | Network deployment changes during early sequence; paper/release count discrepancy |
| **2018 Kīlauea, Hawaiʻi** | Volcanic / caldera-collapse seismicity | Shelly & Thelen (2019); Wei et al. (2022) secondary | Template matching + hypoDD; independent broader NonLinLoc/3-D workflow | HVO/EarthScope public; public USGS release | Strong domain shift from tectonic sequences; very high event rate; multiple catalogs | Primary and secondary catalogs cover different spatial domains and networks |
| **2016 Kaikōura, New Zealand** | Complex multi-fault aftershock sequence | Lanza et al. (2019); Tan et al. (2024) SUGAR secondary | 3-D relocation, waveform CC, hypoDD, bootstrap; CV-based detection + GrowClust | GeoNet public + temporary deployment details | Hard benchmark for complex geometry, uncertainty, and changing network conditions | Different targets optimize different event populations; temporary-network availability must be matched |

## 3. Tier B — Strong expansion candidates

| Case | Sequence / regime | Candidate reference(s) | Why selected | Data-access / compact-window status | Main concern |
|---|---|---|---|---|---|
| **2010 El Mayor–Cucapah / Yuha Desert, California** | Major aftershock sequence | Kroll et al. (2013), 9,770 relocated events; ~40 m horizontal / ~120 m vertical bootstrap errors | Expert repicking + Hypoinverse + VELEST + hypoDD + waveform cross-correlation gives an unusually strong relocation target | SCSN/SCEDC data; a 3–7 day subset is feasible | Published reference covers ~2 months; short-window target must be recomputed |
| **2014 South Napa, California** | Mw 6.0 aftershock sequence | Hardebeck & Shelly (2016) | Matched-filter detection + precise differential times + double-difference relocation in 3-D model; compact first-week sequence | NCEDC/network data likely practical; short window natural | Smaller target catalog than some other cases; waveform-access workflow needs confirmation |
| **2020 Westmorland, California** | Short swarm / slow-slip related | Sirorattanakul et al. (2022), relocated catalog | Sequence itself spans ~30 Sep–6 Oct; >2,000 events; high-resolution relocated seismicity; data/code deposited at CaltechDATA | SCEDC waveforms and catalog public; naturally compact 7-day task | Reference workflow uses PhaseLink/HypoSVI/GrowClust; overlap with Agent tools must be documented |
| **2010 Madison Plateau, Yellowstone** | Three-week volcanic swarm | Shelly et al. (2013), 8,710 events | Waveform template detection + precise DD relocation; nearly 4× routine catalog | EarthScope/IRIS Yellowstone data; 3–7 day subset possible | Older workflow; public event-product accessibility should be checked |
| **2023 Kahramanmaraş, Türkiye** | Doublet and extreme early aftershock sequence | Ding et al. (2023) PALM catalog; GFZ GaMMA/GENIE/NLLoc/hypoDD catalogs | Multiple independent modern pipelines; PALM gives 29,519 well-located events over Feb.; GFZ provides first-5-day GaMMA 17,550, GENIE 14,805, and 5,215 hypoDD events | GFZ catalogs public; AFAD/KOERI waveform access requires practical verification | Different reference products use different station/data selections; target leakage likely if PALM is supplied as Agent prior |
| **2016–2017 Central Italy** | Multi-mainshock aftershock cascade | Waldhauser et al. 390,334 high-precision relocations; Tan et al. ML catalog; Spallarossa automatic catalog | Exceptionally rich reference hierarchy: manual/operational picks, ML-enhanced events, waveform CC, DD relocation | INGV/EIDA data available; use only a 3–7 day Amatrice or Norcia subset | Full study is very large; benchmark must avoid downloading the full-year waveform archive |
| **2020 Samos, eastern Aegean** | Mw 7.0 aftershock sequence | Fountoulakis et al. high-precision relocated catalog, ISC DOI 10.31905/SK7LCETI | Public relocated catalog tied to a peer-reviewed BSSA study; compact sequence suitable for location benchmark | Catalog public at ISC; waveform/EIDA access should be verified | Need to confirm waveform and phase-pick accessibility for raw-input benchmark |
| **2021 Yangbi, Yunnan** | Foreshock–mainshock–aftershock sequence | Zhou et al. ~7,943–8,000 well-located events; Su et al. independent DL workflow | Particularly attractive foreshock benchmark; multiple high-resolution catalogs; matched filter + AI picker + cross-correlated DD times | Catalog papers/data available; raw regional waveform openness needs confirmation | Some waveforms are from regional agency/temporary stations; public access may be incomplete |
| **2022 Luding, Sichuan** | Mw 6.8 aftershock sequence | Zhao et al. 7,388 relocated events; later LOC-FLOW studies 13k–15k events | Modern DL picking + relocation; waveform package and relocated catalog have Zenodo releases; strong method transparency | Catalog DOI 10.5281/zenodo.7556059; related waveform package DOI 10.5281/zenodo.8112022 | Some studies use longer pre-mainshock windows; benchmark should restrict to first 3–7 days |
| **2024 Hualien, Taiwan** | Mw 7.4 aftershock sequence | Yang et al. (2025) AutoQuake ML-enhanced catalog | Very recent end-to-end automated catalog; 3-D DD relocation; local catalog incompleteness explicitly motivates automation | Reference paper public; raw CWBSN/agency data access needs verification | Target method is itself an automated end-to-end workflow, so independence may be low for similar Agent toolchains |
| **2016 Kumamoto, Japan** | Mw 7.0 foreshock/mainshock sequence | Yue et al. (2017), 36,543 precisely located events | 63,336 template detections followed by GrowClust relocation; excellent dense Japanese sequence | NIED/JMA data available to registered users; short-window subset feasible | Data access less frictionless than SCEDC/EarthScope; reference is template-heavy |
| **2020 Southwestern Puerto Rico — January subset** | Foreshock–Mw 6.4–aftershock sequence | Yoon et al. enhanced catalog | EQTransformer + probabilistic neural/eikonal location + waveform CC relocation; 43 stations in full study | PR network data available; use only late Dec 2019–mid Jan 2020 subset | Published catalog spans 3+ years; benchmark must avoid full-duration download |
| **2020 Monte Cristo Range, Nevada** | Mw 6.5 aftershock sequence + dense nodal deployment | Zhang et al. 2025 enhanced catalog (conference/poster stage) | EQTransformer/SeisBench + association + NonLinLoc on NSL broadband + 48-node LASSO deployment | NSL and deployment waveforms reported available through IRIS/EarthScope | High-resolution target is recent and may not yet have the same archival maturity as peer-reviewed core cases |

## 4. Tier C — Specialist / watchlist candidates

| Case | Sequence / regime | Candidate reference(s) | Why keep in pool | Current limitation / watch item |
|---|---|---|---|---|
| **2020 Petrinja, Croatia** | Mw 6.4 aftershock sequence | Herak & Herak (2023), ~14,000 located events in first six months | Strong example of location improvement after local-network deployment; velocity-model epistemic uncertainty explicitly studied | Waveform/public-data workflow needs verification; published study is months long, so compact subset must be designed |
| **2023 Noto Peninsula Mj 6.5, Japan** | Large event inside long-running swarm | Kato (2024) precise May 5–22 catalog | 17 permanent stations; PhaseNet + REAL + DD relocation + matched filter; naturally short post-mainshock window | NIED/JMA waveform access may require registration; high overlap with modern Agent pipeline |
| **2016–2019 Cahuilla Swarm, California — short subset only** | Long-lived swarm | Ross et al. (2020), ~22,000-event high-resolution catalog | Excellent 3-D fault-architecture catalog, public SCEDC product, strong scientific acceptance | Full catalog spans years; only include if a compact scientifically meaningful 3–7 day interval is identified |
| **2021 Nippes, Haiti** | Mw 7.2 aftershock sequence | Recent 5,341-event NLL-SSST-coherence relocation; additional high-resolution work ongoing | Valuable sparse/heterogeneous/citizen-network regime and independent nonlinear location methodology | Temporary broadband data were scheduled for public IRIS release in Oct. 2026; not yet ideal for immediate Phase I use |
| **2020–2023 Puerto Rico full sequence** | Multi-year complex fault activation | Yoon et al. ~180,000-event catalog | Excellent long-term generalization/scalability reference | Excluded from compact benchmark unless reduced to a short January 2020 window |
| **2021 Maduo, Qinghai** | Mw 7.4 intraplate sequence | Guan et al. (2024), 78,832 events with LOC-FLOW | Dense portable array; clear modern workflow; useful future reproduction/generalization case | Reference processing spans ~2 years; portable-array waveform access must be verified; use only short subset |
| **2023/2024 Noto long swarm** | Long-lived fluid-related swarm | Amezawa et al. high-resolution relocated swarm catalog + Kato 2024 event-specific catalog | Multiple catalogs and rich fluid-driven swarm physics | Full swarm is multi-year; should only be used through event-centered compact subsets |

## 5. Candidate-pool summary

The candidate pool currently contains **23 case families**.

The current strategy is:

- **Phase I:** deeply verify and operationalize the first six cases;
- **Tier B:** retain scientifically strong alternatives with good reference catalogs;
- **Tier C:** preserve specialized cases that require further access checks, short-window design, or stronger archival targets.

Tiers B and C remain editable. A case moves into the benchmark only after the checks of [`preparation/01_Case_Record_Standard.md`](preparation/01_Case_Record_Standard.md) §3; waveform access and data-release dates noted here (e.g. the Nippes temporary-network release expected for October 2026) are as of 2026-09-18 and must be re-checked first.
