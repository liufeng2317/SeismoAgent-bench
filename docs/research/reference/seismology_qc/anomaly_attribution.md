# Anomaly attribution in earthquake-catalog workflows

**Question.** Can anomalies in an earthquake-catalog workflow be traced to their cause reliably, and how do seismologists do this in practice? This note deals with attribution and diagnosis themselves. Per-stage QC criteria are covered in sibling notes.

**Scope.** It covers documented catalog artefacts and how each was traced to a cause (§1), diagnosis methods (§2), basic ambiguities that no amount of checking removes (§3), automated and agent approaches (§4), and what this means for the SeismoAgentBench checker and its symptom→cause knowledge (§5).

**Date.** 2026-10-31. Literature review by a Claude subagent. Downloads are in the session scratchpad (`lit_qc/attribution/`) and are not in the repository.

**How much of each source was read.** Each source is tagged with one of four read levels:
- **[F]**: full text read.
- **[F-part]**: full text, with only the relevant sections read.
- **[A]**: abstract or repository landing page only.
- **[S]**: secondary. Known only through a source read in full (named in the row) or through a search snippet.

Read in full: the CORSSA articles by Gulia, Wiemer & Wyss (2012) and Husen & Hardebeck (2010), plus Vorobieva et al. (2022). Read in part: the CORSSA articles by Woessner, Hardebeck & Hauksson (2010) and Mignan & Woessner (2012), and TRACE v4 (arXiv 2603.21152). Everything else is [A] or [S]. Claims tagged [A] or [S] should be checked against the original before they are cited in the paper (see §7).

**Our evidence, which this note relates to but does not re-derive:**
- (a) Agent magnitude errors were unit or response bugs that gave near-constant offsets. They were attributable by recomputing the magnitudes independently.
- (b) Depth pile-ups at a layer interface were an artefact of the step velocity model. They were attributable by relocating the piled events with a linear-gradient model on a finer travel-time grid.
- (c) Systematic depth and time biases from velocity models were often not detectable without a reference, and the lowest travel-time RMS did not pick the least-biased model.
- (d) Comparing two candidate catalogs is easier than judging one on its own, but the result is often "mixed".

## 1. Documented artefacts and how they were traced to a cause

| Artefact | Symptom | Cause | Diagnostic evidence used | Source (read level) |
|---|---|---|---|---|
| Artificial seismicity-rate changes ("phantom" quiescence or activation) | Rate steps of up to about 40 % that look like precursors or quiescence | Changes in detection, reporting or magnitude after network, hardware, software or procedure changes | Compare the frequency–magnitude distribution (FMD) before and after the change. The "magnitude signature" (rate change as a function of magnitude band) separates a detection change (affects only small M), a magnitude shift (all bands, in a characteristic pattern) and a real rate change (all bands, uniformly). The timing is matched against the network history | Habermann 1987, 1991 [S via Gulia 2012]. Zúñiga & Wiemer 1999 [S via Gulia 2012] |
| Magnitude shift or stretch (Guerrero, Mexico) | Apparent rate decrease after 1993 | Change in operating procedures | Cumulative and non-cumulative FMDs compared across two periods. A linear transform (M_new = 0.8·M_old + 1.07 in one period) restores the match. z-value maps of the rate change before and after the correction | Zúñiga & Wyss 1995. Zúñiga & Wiemer 1999 [both S via Gulia 2012] |
| Inadvertent magnitude-scale change (central Italy, 1981–1989) | b-value changes at the same time as Mc steps | Scale changed during the network upgrade | Coincidence argued on plausibility: a simultaneous region-wide natural b change that coincides with the Mc step is "not attractive". Utsu test of b across periods. The correcting transform (shift plus compression) is explicitly **non-unique** because the Mc change happened at the same time | Gulia, Wiemer & Wyss 2012 [F] |
| New ML calibration in southern California (2008) | Rate of M ≥ 1.8 down 32 %. Mc apparently down by 0.3. b falls from about 1.1 to about 0.95 | Recalibration of ML (new attenuation and station terms) | **Controlled overlap experiment.** The year 2007 was processed with both the old and the new calibration. Per-event differences ranged from +1.5 to −2.3 (mean −0.13). Poisson significance of the rate change at each magnitude cutoff. b-stability plateau used as a goodness-of-scaling criterion | Tormann, Wiemer & Hauksson 2010 [S via Gulia 2012, figures described in detail] |
| Apparent post-1952 decline in southern California seismicity | Higher rate in the 1930s–40s | Magnitudes not determined consistently over 1932–1990 | Re-determination and homogenisation of magnitudes against the network history | Hutton & Jones 1993 [S snippet]. Hutton, Woessner & Hauksson 2010 [A] |
| Wood-Anderson gain constant | ML from synthetic Wood-Anderson records is too high by about 0.13 on average | Static magnification 2800 assumed, while the measured value is 2080 ± 60 | Physical re-measurement of instrument constants. The offset is constant (log10 2800/2080 ≈ 0.13) and depends on the amplitude in some datasets | Uhrhammer & Collins 1990 [A/S]. Later reviews [S] |
| Coda-duration magnitude bias | Md too large during aftershock sequences | Overlapping later events lengthen the coda | Mechanism argument. Compare against amplitude magnitudes | Woessner, Hardebeck & Hauksson 2010 [F-part] |
| Long-period gain errors at GSN stations | Station amplitudes drift relative to synthetics | Time-dependent, frequency-dependent STS-1 gain loss, sometimes by more than a factor of 2 | Observed versus synthetic waveforms for many Mw ≥ 6.5 CMT events, with annual median and quartile statistics. A single event cannot resolve small gain errors | Ekström, Dalton & Nettles 2006 [S]. LDEO Waveform Quality Center reports [S] |
| Sensor misorientation | Rotated horizontal components | Compass and declination errors at installation | Rotate horizontals to maximise correlation with synthetic 40–250 s surface waves. Median and interquartile range over at least 5 events. Anomalies of 5° or more are "unlikely" to come from propagation | Ekström & Busby 2008 [S] |
| Gain and orientation errors across a dense network | Network-wide station anomalies | Metadata errors | Automated comparison of observed and synthetic teleseismic amplitudes and polarisations (AutoStatsQ, more than 750 AlpArray stations) | Petersen et al. 2019 [A] |
| Polarity reversals | First motions that consistently disagree with mechanisms at one station. Anti-correlated waveforms of similar events | Cable miswiring, orientation, digitiser sign, negative sensitivity in metadata | Consensus polarity across event pairs. Comparison against a reference station. Per-station misfit with mechanisms over time | Search-level summaries only [S]. No canonical paper read |
| Station clock errors | Step or drift in arrival residuals | GPS loss, missing samples, drift (ocean-bottom seismometers, OBS) | Daily noise cross-correlations compared with a reference correlation (precision about 20 ms). Clock jumps of up to 6 min (land) and about 1 s (OBS, missing samples) were found. **A constant offset present from deployment cannot be seen by stability methods.** The time symmetry of the noise correlation is needed instead | Hable et al. 2018 [S]. Naranjo et al. 2024 (Seismica) [S]. Stehly et al. 2007 and Sens-Schönfelder 2008 [S] |
| Wrong station coordinates | Epicentre bias of several km. Depth bias that is non-linear in the coordinate error | Metadata error | Station-delay and residual distributions in a minimum 1-D (joint hypocentre–velocity–station-delay) inversion. Station delays compared with local geology | Maurer et al. 2010 [S via Husen & Hardebeck 2010] |
| Phase misidentification (Pg/PmP labelled as Pn; S confused with converted phases) | Epicentre shifts of up to 30 km (Alps). One misidentified Pn moved an ML 3.4 event 4 km shallower **without changing the formal uncertainty** | Picks beyond the crossover distance; converted phases | Reduced record sections against theoretical branches. Repicking the same data consistently (controlled). Relocation with and without the suspect phase | Diehl et al. 2009 [A]. Husen & Hardebeck 2010 [F] |
| Default or fixed depth streaks | Horizontal streaks at 5, 10 or 33 km in cross-sections | Depth poorly constrained (no depth phases, no near station), so depth fixed to a default | Provenance flag on the depth type. The ISC/iLoc depth-type codes separate free depth, depth from depth phases, default-grid depth (5) and median fallback (6) | Husen & Hardebeck 2010 [F]. SeisComP iLoc documentation [S] |
| Depths stuck at layer boundaries | Events cluster at the interfaces of a step 1-D model | Layered (step) model in single-event or double-difference location | Synthetic test: data generated with a gradient model and inverted with a layered model. Remedy: thinner layers, a gradient model, or a 3-D model (tomoDD) | Michelini & Lomax 2004 [A]. Husen & Hardebeck 2010 [F]. **Matches our (b)** |
| Distortion of double-difference relative locations | Artificial offsets between nearby clusters | Wrong large-scale velocity model combined with an unbalanced source–receiver distribution | Synthetic tests with known truth | Michelini & Lomax 2004 [A] |
| Lateral velocity contrast across a fault | A vertical fault appears to dip; events shift towards the fast side, more so with depth | Unmodelled 2-D/3-D structure in a 1-D location | Forward reasoning plus relocation with separate 1-D models per side of the fault or with a 3-D model | Thurber 1992 [S via Husen & Hardebeck 2010] |
| Magnitude-dependent location offset | Large events offset from small events | Large events are recorded at greater distances and sample the deeper model | Mechanism argument (no specific test cited) | Husen & Hardebeck 2010 [F] |
| Systematic subduction-zone bias | Epicentres pulled towards the Pacific; shifts of up to 25 km | 1-D model that ignores the fast slab | Relocation with 3-D corrections compared with relocation without | Syracuse & Abers 2009 [S via Husen & Hardebeck 2010] |
| 3-D model not more accurate | Tunnel explosion located 2 km too deep with the regional 3-D model; 200 m off with velocities derived from the explosion itself | Upper-crustal velocities about 20 % slower than the model, with up to 10 % variation between stations | Ground-truth (GT) explosion | Husen & Hardebeck 2010 [F] (Husen et al. 2003) |
| Catalog location and depth biases at global scale | Epicentres off by about 10 km (ISC/EHB) and about 21 km (GCMT) relative to InSAR. EHB depths about 5 km deeper than InSAR | Earth-model and method bias. Part of the difference is physical (centroid versus hypocentre; upward rupture) | Independent geodetic observable (InSAR) for more than 50 events. The size of the bias depends on the Earth model assumed in the InSAR inversion | Weston, Ferreira & Funning 2011, 2012 [A] |
| Short-term aftershock incompleteness | Early aftershock rate too low. Omori c grows with mainshock magnitude. b varies in time | Detector "blind time" after large events | Rate-dependent Mc model reproduces the observed c-scaling. The a-positive estimator gives c that cannot be distinguished from 0. Short-term incompleteness also produces apparent b variations | Hainzl 2016 [A]. van der Elst & Page 2023 [S]. Ben-Zion & Zaliapin 2015 [A] |
| Location errors corrupting cluster statistics | Larger parent–offspring distances, weaker clustering, higher background rate | Absolute and relative location errors (m < 3.5) | Same analysis repeated on four catalogs of different quality. The size of the artefact scales with catalog quality, so the artefact is not tied to any one relocation method | Ben-Zion & Zaliapin 2015 [A] |
| Quarry and mine blasts | Excess events in daytime and on working days; lunch-break dip; spatial clusters | Industrial explosions | Mapped day/night ratio Rq (Rq ≥ 1.5, Monte-Carlo significance), checked against known quarries. Aftershock guard: at most 20 % of daytime events may fall on one day. The daytime excess disappears above about M 2.5 (Romania). About 20 % of the Swiss catalog was removed | Wiemer & Baer 2000 [S]. Gulia 2010 [S]. Both via Gulia 2012 [F] |
| Duplicates across networks | Pairs of events close in time and space with different magnitude scales | Several agencies report the same event; incorrect association | Error-normalised space–time distance. Duplicates show **symmetric** (signed) time differences with no causal ordering, unlike aftershocks. Reliability above 97 %, falling to about 96 % on day 1 after Tohoku. Window methods flag aftershocks as false duplicates | Vorobieva et al. 2022 [F]. USGS ComCat QC (Fee & Martinez; Earle) [S] |
| Non-double-couple artefacts | Routine non-DC components | Noise and modelling errors | Comparison between catalogs (CMT versus USGS MT) | Kagan 2003 [A] |
| Label errors in ML training sets | 3.9 % of 8.6 M waveforms mislabelled (0–8 % per dataset) | Unlabelled events, events in "noise" samples, wrong arrival times | Disagreement with an ensemble of two pickers (PhaseNet + EQTransformer) | Aguilar Suarez & Beroza 2025 [A] |

## 2. Diagnosis methods

| Method | What it separates | Cost | Limits | Source |
|---|---|---|---|---|
| Matching the symptom's onset in time against the change log (network history, software or calibration changes) | Man-made versus natural rate, Mc or b changes | Low, if a log exists | Plausibility argument, not proof. Fails when a change coincides with a real event (for example the 1997 Umbria-Marche aftershocks during an upgrade) | Gulia 2012 [F]. Habermann 1987 [S]. Hutton et al. 2010 [A] |
| Habermann "magnitude signature" (rate change by magnitude band); FMD comparison between periods | Detection change versus magnitude shift or stretch versus real rate change | Low | Needs two long homogeneous periods. A shift and an Mc change at the same time cannot be uniquely resolved | Habermann 1987 [S]. Zúñiga & Wyss 1995 [S]. Gulia 2012 [F] |
| Controlled overlap or reprocessing (same data, one factor changed) | Effect of a single factor: a calibration (Tormann 2010), a pick set (Diehl 2009), a velocity model (Husen et al. 2003), a single phase (Husen & Hardebeck Fig. 5) | Medium (reprocessing) | Measures **sensitivity** to the factor, not which variant is correct | Tormann 2010 [S]. Diehl 2009 [A]. Husen & Hardebeck 2010 [F] |
| Synthetic tests with known truth | Whether a method or model *can* produce the symptom (layer sticking, double-difference distortion, resolution) | Medium | Only covers the error mechanisms that are put into the simulation. The model-error distribution is unknown (Pavlis 1986) | Michelini & Lomax 2004 [A]. Kissling et al. 1994 [A]. Mignan & Woessner 2012 §6.7 [F-part] |
| Bootstrap or jackknife over data | Precision (random error), e.g. Mc ± σ from 200 bootstraps. Drop-one-station relocation exposes a single bad station or phase | Low to medium | **Blind to systematic bias.** Formal errors do not change when one misidentified phase moves a hypocentre by 4 km | Woessner & Wiemer 2005 via Mignan & Woessner [F-part]. Husen & Hardebeck 2010 [F] |
| Minimum 1-D model (joint inversion of hypocentres, velocities and station delays) with residual analysis per station, distance and time | Station problems (coordinates, timing, mislabelled phases) versus average structure. Its final RMS gives the noise floor | Medium | Station delays absorb the near-surface structure and also part of the hypocentre shift (trade-off). Many runs and starting models are needed ("a single or even a few VELEST runs are useless") | Kissling 1988, 1994 [S/A]. Maurer et al. 2010 [S]. Husen et al. 2011 [S] |
| Comparing independent methods or catalogs | Whether a feature is method-specific or robust | Low | A disagreement says that *something* differs, not which catalog is right. Few events match across catalogs (Kagan 2002: "several tens"). Composite catalogs have discontinuities at boundaries between authoritative regions | Kagan 2003 [A]. Ben-Zion & Zaliapin 2015 [A]. Husen & Hardebeck 2010 [F] |
| Ground-truth events (explosions, quarry blasts, GT0–GT5) | Absolute bias of model and locator | High (needs GT events in the region) | Rare. Usually shallow, so depth bias is poorly sampled. Bondár et al. give local-network criteria (≥ 10 stations, gap < 110°, nearest station < 30 km, secondary gap < 160° for 5 km at 95 %) for the **epicentre only**, not depth | Bondár et al. 2004 [S via Husen & Hardebeck]. Husen & Hardebeck 2010 [F] |
| Independent observables: S near the source (within 1.4 × depth), depth phases, waveform-modelled depth, InSAR or geodesy, fault geometry | Depth versus origin time; absolute location | Medium to high | S picks can carry bias from converted phases while the formal error goes **down**. InSAR has its own model dependence. Centroid and hypocentre differ physically | Gomberg et al. 1990 [S]. Husen & Hardebeck 2010 [F]. Weston et al. 2011 [A] |
| Station-level comparison of waveforms with synthetics or neighbours (gain, orientation, polarity, timing) | Hardware or metadata faults versus earthquake or path effects | Medium (needs many events) | Single events cannot resolve small gain errors. Site effects and attenuation curves mimic gain errors in magnitude residuals | Ekström et al. 2006 [S]. Ekström & Busby 2008 [S]. Petersen 2019 [A]. Casey et al. 2018 (MUSTANG) [A] |
| Statistical signature mapping (day/night Rq, Mc maps, b maps) | Blasts versus earthquakes; spatial completeness | Low | Confounded by aftershocks (handled by the 20 % rule) and by quarries inside active zones (e.g. Turkey) | Wiemer & Baer 2000 [S]. Gulia 2012 [F] |

**How network operators trace causes.** No published, formal root-cause checklist was found for ANSS/SCSN/NCSN, ISC, GFZ/GEOFON or EMSC. Their practice is documented piecemeal:
- **Network histories.** The 77-year SCSN history explains catalog changes so that users can understand its limits (Hutton et al. 2010 [A]).
- **Overlap reprocessing.** When a calibration changes, one period is processed both ways (Tormann 2010).
- **Semi-automated ComCat QC.** The USGS ComCat QC targets four error classes: systematic magnitude biases, missing time periods, duplicate postings and incorrectly associated events (Fee & Martinez; Earle, SSA posters [S]). The related USGS tools `qcreport`/`qcmulti` produce statistics for a single catalog and for comparing catalogs (Ambruz 2019 [A]).
- **ISC depth provenance and baseline.** The ISC records how each depth was obtained in iLoc depth-type codes and uses a default depth grid. ISC-GEM and the Bulletin rebuild recompute everything with one locator, one model (ak135) and one magnitude procedure, which turns heterogeneous agency practice into a single traceable baseline (Storchak et al. 2020 [A, download failed]).
- **Station-level waveform QC.** LDEO WQC, EarthScope/IRIS MUSTANG and AutoStatsQ work at the level of station waveforms, not catalogs.

The common pattern is to keep a change log, reprocess one factor at a time, and compare against synthetics or neighbours. Nothing comparable to a published symptom→cause decision table was found. The CORSSA chapters come closest; they describe themselves as "forensic seismicity analysis" tools for a "first order quality analysis".

## 3. Basic ambiguities

| Symptom | Causes that cannot be told apart from the symptom alone | What breaks the degeneracy | Source |
|---|---|---|---|
| Depth shift together with an origin-time shift | Origin time versus depth. When stations sit at similar distances, or when first arrivals come from one refractor, the depth column of the location matrix becomes nearly parallel to the origin-time column | S picks within about 1.4 × focal depth; depth phases (pP, sP; their partial derivatives have the opposite sign); a wide spread of take-off angles; fixing depth (which hides the problem) | Husen & Hardebeck 2010 [F]. Gomberg 1990 [S] |
| Whole cluster shifted, or depth bias, with good RMS | Hypocentres versus velocity model versus station corrections (the coupled problem). A common-mode shift is absorbed by origin times and station delays | Ground-truth events or explosions; independent depth (depth phases, waveform modelling, InSAR); joint inversion only removes the part that the ray geometry resolves | Thurber 1992 [S]. Kissling 1994 [A]. Pavlis 1986 [S]. **Matches our (c)** |
| Lower RMS | Better model, *or* fewer observations, *or* an overfitted model or station terms | RMS is meaningful only relative to a noise floor such as the RMS of a minimum 1-D model. Validate with explosions or shifted-hypocentre tests rather than misfit. A model with more complexity is not more accurate | Husen & Hardebeck 2010 [F]. **Matches our (c)** |
| Small formal error | Precise *and* accurate, or precise but biased (misidentified phase, wrong S, model error) | Formal errors cannot separate these by construction. Only an independent observable or ground truth can | Pavlis 1986 [S]. Husen & Hardebeck 2010 [F] |
| Cluster of depths at a model interface | Step-model artefact versus a real lithological or rheological boundary | Relocate with a gradient model or thin layers (and a finer travel-time grid). Persistence means the cluster is probably real | Michelini & Lomax 2004 [A]. Husen & Hardebeck 2010 [F]. **Our (b)** |
| Constant arrival delay at one station | Clock offset versus near-surface slowness (static) versus coordinate error | Time symmetry of noise correlations (Naranjo 2024 [S]); GPS or clock logs. *Our inference, not taken from a source:* a clock error shifts P and S equally, a slow site delays S by about Vp/Vs × the P delay, and a coordinate error gives a residual pattern that depends on azimuth and distance | Hable 2018 [S]. Maurer 2010 [S] |
| Constant magnitude offset against a reference | Wrong regional −logA0 level versus mean station terms versus a common response or unit error versus a difference in reference scale | Recompute from raw amplitudes plus the response, independently. Check whether the offset is **quantised** at log10 of a known factor (2800/2080 → 0.13; nm↔mm → 6; m↔mm → 3). Use events with an independent Mw | Uhrhammer & Collins 1990 [A]. Tormann 2010 [S]. **Our (a)** |
| Magnitude residual at one station | Gain or metadata error versus site amplification versus a wrong attenuation curve | Step in time (likely hardware or metadata); a stable offset that correlates with geology (likely site); a trend with distance (likely attenuation curve). Confirm with component ratios or polarisation | Search-level summaries [S] (USGS component-ratio paper, CTBTO and Hi-net gain studies) |
| b-value change | Real change versus magnitude shift or stretch versus Mc change versus short-term incompleteness | Coincidence with operational changes; magnitude signature; b-stability plateau. Not unique when the Mc and scale changes happen together | Gulia 2012 [F]. Tormann 2010 [S]. Ben-Zion & Zaliapin 2015 [A] |
| Curved FMD | Spatial or temporal heterogeneity in Mc versus a non-Gutenberg–Richter FMD | Map Mc in space and time and split the catalog. Mc estimators disagree (MAXC underestimates; MBS overestimates) | Mignan & Woessner 2012 [F-part] |
| Large Omori c; early rate deficit | Physical delay (rate-and-state) versus detector blind time | Template or matched-filter detection to fill the gap; a-positive rate estimate; c scaling with mainshock M points to incompleteness | Hainzl 2016 [A]. van der Elst & Page 2023 [S] |
| Diffuse clustering; high background rate | Location error versus real physics | Compare across catalogs of known differing quality; use aggregated statistics, which are more robust | Ben-Zion & Zaliapin 2015 [A] |
| Pair of events close in time and space | Duplicate versus aftershock | Error-normalised distance; symmetry of the signed time difference | Vorobieva 2022 [F] |
| Daytime excess | Blasts versus an aftershock sequence that started in daytime versus a noise-modulated detection threshold (nights record more events) | Day-of-week pattern; known quarry locations; one-day concentration guard; a magnitude ceiling | Gulia 2012 [F]. Mignan & Woessner 2012 §6.6 [F-part] |
| Dipping alignment of seismicity | Real dip versus a vertical fault with a velocity contrast across it | Separate 1-D models per side or a 3-D model; focal mechanisms; surface trace | Thurber 1992 [S] |

The general pattern behind these rows is our synthesis, consistent with the sources. Attribution works when the error has *structure* that the redundancy in the data can expose, for example a single station, a single phase type, a time step, a quantised offset, or a dependence on distance or azimuth. A *common-mode* error is shared by all stations or all events, such as an absolute model bias or a uniform calibration level. Such an error is absorbed by free parameters (origin time, station terms, a-value) and cannot be identified from the data alone. Only external truth breaks it: ground-truth events, independent observables, or a reference catalog.

## 4. Automated and agent approaches

- **Automated station QC** is the most mature form of automated attribution in seismology. It can attribute causes because it compares against an external standard (synthetics or neighbours) and accumulates many events. Examples are MUSTANG metrics (Casey et al. 2018 [A]), LDEO WQC gain and orientation tables (Ekström et al. 2006 and 2008 [S]), AutoStatsQ (Petersen 2019 [A]), noise-correlation clock QC (Hable 2018 [S]), and SeisComP waveform-QC plugins (not reviewed).
- **Automated catalog QC.** Examples are the ZMAP/MapSeis routines (Mc(t), Mc maps, Rq maps, magnitude-shift fitting; Wiemer 2001 [S]), USGS `qcreport`/`qcmulti` and ComCat semi-automated QC [A/S], and duplicate detection (Vorobieva 2022 [F]). All of them report *symptoms* plus a small set of standard causes. A human analyst still makes the final attribution, using the network history.
- **ML-based consistency checks.** Ensemble disagreement between pickers flags label errors (Aguilar Suarez & Beroza 2025 [A]). The work is framed as detection; the four error types it finds were categorised after the fact.
- **LLM agents.** *TRACE* (arXiv 2603.21152 v4, [F-part]) includes a "Result Checking Agent". It checks file validity, numerical ranges, catalog completeness, spatial and temporal consistency, convergence and plausibility of statistics. When a check fails, the agent revises the workflow within allowed operations (a parameter, the code, the data subset, or a different tool). "Persistent differences among valid alternatives are retained as separate evidence branches." Unresolved failures stay in provenance and are not used as evidence. In the Sanriku case, human-supervised QC caught implausible deep-learning S picks, and JMA picks were kept instead. TRACE detects failures and revises; it has no explicit symptom→cause model, and attribution is implicit in the revision choice. *GeoAgent* (arXiv 2610.31096, [A]; reflection processing) reports that agents "invent units", wire the wrong artefact into a step and claim completion without a verifiable product. Its remedy is contracts plus a deterministic check after each stage, which is prevention, not attribution. Its "invented units" failure is the same class as our (a). *TREMORS* (arXiv 2609.01777, [A]) covers data acquisition only.
- **Gap.** No seismology system was found that uses an explicit symptom→cause knowledge base, or that runs discriminating experiments automatically to choose between causes.

**Analogues outside seismology (brief).**
- LIGO detector characterisation vetoes a glitch only when it coincides with a "safe" auxiliary channel that cannot record gravitational waves (Hveto, which ranks Poisson coincidence significance). Attribution there rests on independent witness channels plus operator logs (Davis et al. 2021 [A]). The seismic analogues of witness channels are the state-of-health/GPS channels, neighbouring stations, and the P/S split.
- Blind analysis in particle physics (Klein & Roodman 2005; not opened) guards against confirmation bias when choosing among candidate corrections. It is relevant to tuning a model until the result "looks right".
- The common principle is to keep a change log or witness channel, change one factor at a time, and keep competing explanations open. TRACE's evidence branches and the ISC depth-type flags are seismic examples.

## 5. Implications for the SeismoAgentBench checker and its knowledge base

**Tier 1: attributable reliably by an automated checker plus knowledge, without a reference.** In each case the symptom has a unique signature, or a cheap deterministic recomputation settles it:
- **Magnitude offsets from units or responses.** Recompute independently from raw amplitudes and the response. Test whether the offset is quantised at log10 of known factors, and whether it appears network-wide or only at single stations. *Our (a); Uhrhammer & Collins.*
- **Fixed or default depths.** Read the depth-type provenance, or check for depths equal to configured defaults within numerical tolerance. *ISC/iLoc practice.*
- **Duplicates.** Error-normalised distance and symmetric time differences. *Vorobieva 2022.*
- **Single-station faults with temporal structure.** Clock jumps, gain steps, polarity flips, wrong coordinates, and misorientation of 5° or more. Evidence comes from per-station residual time series (P and S together), comparison with neighbours, and relocation with that station dropped. *Hable 2018; Ekström & Busby 2008; Maurer 2010.*
- **Quarry blasts.** The Rq map plus the day-of-week pattern, with the aftershock guard. *Wiemer & Baer 2000.*
- **Mechanical failures that GeoAgent-style contracts catch.** Wrong units, wrong input wiring, and missing products.

**Tier 2: attributable only through a discriminating experiment.** The checker can trigger these experiments but cannot decide from the symptom alone:
- **Interface pile-up.** Relocate the piled events with a gradient model or thin layers and a finer travel-time grid. If the pile-up disappears, it was an artefact. If it persists, it may be real. *Our (b); Michelini & Lomax 2004.*
- **Phase misidentification or a bad single phase.** Jackknife over stations and phases; check against a reduced record section. *Husen & Hardebeck; Diehl 2009.*
- **Magnitude shift versus rate change versus Mc change.** Overlap reprocessing with both variants, plus the magnitude signature. *Tormann 2010; Habermann.*
- **Short-term incompleteness versus physical c or b changes.** Template detection or the a-positive estimate. *Hainzl 2016.*
- **Sensitivity of location or depth to the velocity model.** Relocate with alternative models. The relocation measures how sensitive the result is to the model. It does **not** say which model is right, so the checker should report the spread as an uncertainty, not as a verdict. *Our earlier finding that the spread between locators indicates quality.*
- **Constant offset at one station: clock versus path.** Use the P/S delay ratio, or the time symmetry of the noise correlation (continuous waveforms are available in our setting).

**Tier 3: not attributable without external truth.**
- **Absolute (common-mode) depth or origin-time bias from the velocity model.** This is the coupled hypocentre–velocity problem. RMS cannot rank models; formal errors cannot detect the bias. It needs ground-truth or explosion events, depth phases or waveform-modelled depths, InSAR, or a trusted reference. *Our (c); Thurber 1992; Kissling 1994; Pavlis 1986.*
- **Absolute magnitude calibration level.** The regional −logA0 trades off against the mean station terms. Only an independent Mw or a reference catalog sets the level.
- **Coincident Mc and scale changes.** The correcting transform is non-unique (Gulia 2012).
- **Real structure versus residual model artefact.** If an interface cluster or dipping alignment survives the discriminating experiment, it is "probably real". It is still not proven.
- **Which of two disagreeing catalogs is right.** Without a third independent observable or a ground-truth subset, the comparison can only localise *where* the catalogs differ. *Our (d); Kagan 2003; the ref-to-ref ceiling.*

**Design consequences.**
1. Pair every checker symptom with a provenance diff (what changed since the last good state). This is the agent analogue of the network history log, which is the main attribution evidence in the literature.
2. Encode each knowledge entry as *symptom → candidate causes → discriminating experiment → expected outcome under each cause*, and keep tiers separate in reports.
3. Never use RMS or formal uncertainty as evidence that a model is not biased.
4. When the outcome of an experiment is ambiguous, keep several candidate explanations open (TRACE-style evidence branches) instead of forcing one cause.
5. Report Tier-3 quantities as "unverifiable without a reference", with the sensitivity spread as an uncertainty. This fits the "compare against HIL final only" framing.

## 6. References

Read levels: [F] full text, [F-part] full text with relevant sections read, [A] abstract or landing page, [S] secondary or search snippet.

- Aguilar Suarez, A. L., & Beroza, G. (2025). Pervasive label errors in seismological machine learning datasets. arXiv:2511.09805. https://arxiv.org/abs/2511.09805 [A]
- Ambruz, N. B. (2019). Quality control tools for seismic catalogs: qcreport and qcmulti. USGS data release. doi:10.5066/P9JO5N3N [A]
- Ben-Zion, Y., & Zaliapin, I. (2015). Artefacts of earthquake location errors and short-term incompleteness on seismicity clusters in southern California. GJI 202(3), 1949–1968. doi:10.1093/gji/ggv259 [A]
- Bondár, I., Myers, S. C., Engdahl, E. R., & Bergman, E. A. (2004). Epicentre accuracy based on seismic network criteria. GJI 156, 483–496. doi:10.1111/j.1365-246X.2004.02070.x [S]
- Casey, R., et al. (2018). Assuring the quality of IRIS data with MUSTANG. SRL 89(2A), 630–639. doi:10.1785/0220170191 [A]
- Davis, D., et al. (2021). LIGO detector characterization in the second and third observing runs. CQG 38, 135014. doi:10.1088/1361-6382/abfd85; arXiv:2101.11673 [A]
- Diehl, T., Kissling, E., Husen, S., & Aldersons, F. (2009). Consistent phase picking for regional tomography models: application to the greater Alpine region. GJI 176(2), 542–554. Open PDF: https://doc.rero.ch/record/299583 [A]
- Ekström, G., Dalton, C. A., & Nettles, M. (2006). Observations of time-dependent errors in long-period instrument gain at global seismic stations. SRL 77(1), 12–22 [S]
- Ekström, G., & Busby, R. W. (2008). Measurements of seismometer orientation at USArray Transportable Array and backbone stations. SRL 79(4). https://ds.iris.edu/hq/files/programs/gsn/gsnqual/Ekstrom_Busby_2008_SRL.pdf [S]
- Fang, Z., et al. (2026). GeoAgent: Contract-constrained LLM agents for seismic data processing. arXiv:2610.31096 [A]
- Fee, J., & Martinez, E.; Earle, P. (n.d.). ComCat semi-automated QC, SSA posters. https://seismosoc.secure-platform.com/a/gallery/rounds/29/details/7994 and https://seismosoc.secure-platform.com/a/gallery/rounds/7/details/4297 [S]
- Gomberg, J. S., Shedlock, K. M., & Roecker, S. W. (1990). The effect of S-wave arrival times on the accuracy of hypocenter estimation. BSSA 80, 1605–1628 [S]
- Gulia, L., Wiemer, S., & Wyss, M. (2012). Catalog artifacts and quality controls. CORSSA. doi:10.5078/corssa-93722864. http://www.corssa.org/export/sites/corssa/.galleries/articles-pdf/gulia_et_al.pdf_2063069299.pdf [F]
- Habermann, R. E. (1987). Man-made changes of seismicity rates. BSSA 77, 141–159. Also Habermann (1991), Tectonophysics 193, 277–289 [S]
- Hable, S., Sigloch, K., Barruol, G., Stähler, S. C., & Hadziioannou, C. (2018). Clock errors in land and ocean bottom seismograms: high-accuracy estimates from multiple-component noise cross-correlations. GJI 214, 2014–2034. Open: https://hal.archives-ouvertes.fr/hal-01834950 [S]
- Hainzl, S. (2016). Apparent triggering function of aftershocks resulting from rate-dependent incompleteness of earthquake catalogs. JGR 121, 6499–6509. Also Rate-dependent incompleteness of earthquake catalogs, SRL 87, 337–344 [A]
- Husen, S., & Hardebeck, J. L. (2010). Earthquake location accuracy. CORSSA. doi:10.5078/corssa-55815573 [F]
- Husen, S., Kissling, E., & Clinton, J. F. (2011). Local and regional minimum 1D models for earthquake location and data quality assessment in complex tectonic regions: application to Switzerland. Swiss J. Geosci. 104. doi:10.1007/s00015-011-0071-3 [S]
- Hutton, L. K., & Jones, L. M. (1993). Local magnitudes and apparent variations in seismicity rates in southern California. BSSA 83 [S]
- Hutton, K., Woessner, J., & Hauksson, E. (2010). Earthquake monitoring in southern California for seventy-seven years (1932–2008). BSSA 100(2), 423–446. doi:10.1785/0120090130 [A]
- Kagan, Y. Y. (2003). Accuracy of modern global earthquake catalogs. PEPI 135, 173–209. doi:10.1016/S0031-9201(02)00214-5 [A]
- Kissling, E., Ellsworth, W. L., Eberhart-Phillips, D., & Kradolfer, U. (1994). Initial reference models in local earthquake tomography. JGR 99, 19635–19646. doi:10.1029/93JB03138 [A]
- Liu, F., et al. (2026). TRACE: A multi-agent system for autonomous physical reasoning for seismology. arXiv:2603.21152 (v4). [F-part: architecture, checking agent, limitations]
- Maurer, V., Kissling, E., Husen, S., & Quintero, R. (2010). Detection of systematic errors in travel-time data using a minimum 1-D model: application to Costa Rica seismic tomography. BSSA 100, 629–639 [S]
- Michelini, A., & Lomax, A. (2004). The effect of velocity structure errors on double-difference earthquake location. GRL 31, L09602. doi:10.1029/2004GL019682 [A]
- Mignan, A., & Woessner, J. (2012). Estimating the magnitude of completeness for earthquake catalogs. CORSSA. doi:10.5078/corssa-00180805 [F-part]
- Naranjo, D., et al. (2024). Ocean bottom seismometer clock correction using ambient seismic noise. Seismica. https://seismica.library.mcgill.ca/article/view/367 [S]
- Pavlis, G. L. (1986). Appraising earthquake hypocenter location errors: a complete, practical approach for single-event locations. BSSA 76, 1699–1717 [S]
- Petersen, G., et al. (2019). Automated quality control for large seismic networks: implementation and application to the AlpArray seismic network. SRL. doi:10.1785/0220180342 [A]
- SeisComP iLoc documentation (depth-type codes, default depth grid after Bondár & Storchak 2011). https://docs.gempa.de/seiscomp/ (global_iloc) [S]
- Storchak, D. A., et al. (2020). Rebuild of the Bulletin of the International Seismological Centre (ISC)—part 2: 1980–2010. Geosci. Lett. 7, 18. doi:10.1186/s40562-020-00164-6 [A]
- Syracuse, E. M., & Abers, G. A. (2009). Systematic biases in subduction zone hypocenters. GRL 36. doi:10.1029/2009GL037487 [S]
- Thurber, C. H. (1992). Hypocenter–velocity structure coupling in local earthquake tomography. PEPI 75, 55–62 [S]
- Tormann, T., Wiemer, S., & Hauksson, E. (2010). Changes of reporting rates in the southern California earthquake catalog, introduced by a new definition of ML. BSSA 100(4), 1733–1742 [S]
- Uhrhammer, R. A., & Collins, E. R. (1990). Synthesis of Wood-Anderson seismograms from broadband digital records. BSSA 80. https://ncedc.org/ftp/outgoing/peggy/ML/Uhrhammer_Collins_1990.pdf [A]
- van der Elst, N., & Page, M. (2023). a-positive: a robust estimator of the earthquake rate in incomplete or saturated catalogs. https://www.usgs.gov/publications/a-positive-a-robust-estimator-earthquake-rate-incomplete-or-saturated-catalogs [S]
- Vorobieva, I. A., et al. (2022). Nearest neighbor method for discriminating aftershocks and duplicates when merging earthquake catalogs. Front. Earth Sci. 10:820277. doi:10.3389/feart.2022.820277 [F]
- Weston, J., Ferreira, A. M. G., & Funning, G. J. (2011). Global compilation of InSAR earthquake source models: 1. Comparisons with seismic catalogs. JGR 116, B08408. Also Weston et al. (2012), Tectonophysics [A]
- Wiemer, S., & Baer, M. (2000). Mapping and removing quarry blast events from seismicity catalogs. BSSA 90, 525–530 [S]
- Woessner, J., Hardebeck, J. L., & Hauksson, E. (2010). What is an instrumental seismicity catalog? CORSSA. doi:10.5078/corssa-38784307 [F-part]
- Zúñiga, F. R., & Wyss, M. (1995). Inadvertent changes in magnitude reported in earthquake catalogs: their evaluation through b-value estimates. BSSA 85, 1858–1866. Also Zúñiga & Wiemer (1999), PAGEOPH 155, 713–726 [S]
- Klein, J. R., & Roodman, A. (2005). Blind analysis in nuclear and particle physics. Annu. Rev. Nucl. Part. Sci. 55, 141–163 [not opened; cited from background knowledge]

## 7. Needs user download (paywalled, or the download failed here)

Priority 1: these are central to the attribution claims in §3 and §5.
- Michelini & Lomax 2004, GRL, doi:10.1029/2004GL019682. Needed for the layer-sticking test details that support our (b).
- Thurber 1992, PEPI 75, 55–62. The coupled-problem statement.
- Kissling et al. 1994, JGR, doi:10.1029/93JB03138. Minimum 1-D model and stability tests.
- Maurer et al. 2010, BSSA 100, 629–639. Systematic travel-time errors found through minimum 1-D residuals.
- Tormann, Wiemer & Hauksson 2010, BSSA 100(4), 1733–1742. The overlap experiment.
- Habermann 1987, BSSA 77, 141–159.
- Zúñiga & Wyss 1995, BSSA 85, 1858–1866.
- Husen, Kissling & Clinton 2011, Swiss J. Geosci., doi:10.1007/s00015-011-0071-3. Open access, but Springer blocked the download.

Priority 2:
- Pavlis 1986, BSSA 76, 1699–1717.
- Hutton, Woessner & Hauksson 2010, BSSA, doi:10.1785/0120090130.
- Hutton & Jones 1993, BSSA 83.
- Uhrhammer & Collins 1990, BSSA 80. The NCEDC PDF came back empty.
- Ekström, Dalton & Nettles 2006, SRL 77.
- Ekström & Busby 2008, SRL 79. The IRIS link returned HTML.
- Weston et al. 2011, JGR 116 B08408. The open UCR PDF downloaded but text extraction failed.
- Storchak et al. 2020, Geosci. Lett. 7:18. Open access; Springer blocked the download.
- Hable et al. 2018, GJI 214. Open on HAL; the download returned HTML.
- Hainzl 2016, JGR 121. Open copy on GFZpublic.
- Ben-Zion & Zaliapin 2015, GJI 202.
- Kagan 2003, PEPI 135.
- Petersen et al. 2019, SRL.
- Diehl et al. 2009, GJI 176. Open at doc.rero.ch; not fetched.
