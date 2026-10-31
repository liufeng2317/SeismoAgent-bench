# How seismologists judge each stage, and whether anomalies can be attributed (synthesis, 2026-11-01)

Five literature reviews, written from full texts where they could be obtained (claims from abstracts or second-hand sources are tagged [abs], [A], [S] or [via X] in each file):

| File | Stage | Read in full or in relevant sections |
|---|---|---|
| [`data_and_picking.md`](data_and_picking.md) | data, preprocessing, phase picking | NMSOP-2 Ch. 16, Münchmeyer et al. 2022, Stehly et al. 2007, MUSTANG/ISPAQ code, Lin et al. 2008, Hutton et al. 2010 and 8 more |
| [`association_and_detection.md`](association_and_detection.md) | association, detection, template matching | GaMMA, PyOcto, Puente et al. 2025, PhaseLink, Ross et al. 2019 (with supplement), Muir 2023, Tan et al. 2021, Hainzl 2016, Herrmann & Marzocchi 2021 and 9 more |
| [`location_and_relocation.md`](location_and_relocation.md) | absolute location, velocity model, relative relocation | Husen & Hardebeck 2010, Gomberg et al. 1990, Waldhauser & Ellsworth 2000, hypoDD manual, Trugman & Shearer 2017, Lin & Shearer 2005, Yu et al. 2025, NonLinLoc and Hypoinverse documentation |
| [`magnitude_and_catalog.md`](magnitude_and_catalog.md) | magnitude, completeness, catalog consistency | Hutton et al. 2010, CORSSA (Mignan & Woessner, Gulia et al.), Herrmann & Marzocchi 2021, Hainzl 2016 and others |
| [`anomaly_attribution.md`](anomaly_attribution.md) | attribution across stages | Gulia et al. 2012, Husen & Hardebeck 2010, Vorobieva 2022, TRACE (relevant sections) |

## 1. How correctness is judged in practice

Across the stages, practitioners rely on five kinds of evidence. Only the first three are available to an Agent without a reference catalog.

1. **Redundancy inside the data.** Independent observables of the same quantity: Wadati diagrams and S−P times (independent of the velocity model), P and S residuals of the same station, neighbouring stations, the two sides of an ambient-noise correlation, an independent recomputation of a quantity (station magnitudes, amplitudes). This is where reference-free checks come from.
2. **Controlled reprocessing.** Change one factor and reprocess: two magnitude calibrations over the same year (Tormann et al. 2010), repicking the same data (Diehl et al. 2009), leave-one-phase-out relocation, bootstrap and jackknife of relocations, different starting locations, different locators, step vs gradient velocity models. This is the standard way to attribute a symptom.
3. **Geometry and physics rules.** GT5-like network criteria (≥ 10 stations, gap < 110°, secondary gap < 160°, nearest station < 30 km; Bondár et al. 2004 via Husen & Hardebeck), a correctly timed S within ≈ 1.4 focal depths for a depth good to ≈ ±1.5 km (Gomberg et al. 1990), short-term aftershock incompleteness Mc(M, t) = M − 4.5 − 0.75 log10 t (Helmstetter et al. 2006), noise models (NLNM/NHNM), SCSN magnitude rules (station median with Chauvenet rejection, SNR ≥ 8, distance cut-off). These give expected ranges per event or per station.
4. **Comparison with routine catalogs or ground truth.** Recall of the routine catalog (GaMMA, EQTransformer), explosions and GT events, agency-to-agency comparison. Most published ML catalogs validated themselves this way. Not available to the Agent; it is what our scorer does.
5. **Human inspection of samples.** Visual review of random detections to set thresholds (Ross et al. 2019: 9.5 × MAD ≈ 5 % false; 12 × MAD < 1 % false but half the catalog), analyst pick review. Network operators (ANSS, SCSN, NCSN, ISC, GEOFON, EMSC) publish no symptom → cause decision table; ComCat runs four semi-automatic QC classes only.

Two common yardsticks are **not** measures of correctness: formal errors (true locations fall inside the reported 95 % region for 13 % of events with Hypoinverse and 85 % with NonLinLoc on a synthetic sequence, Yu et al. 2025; hypoDD's LSQR errors are "grossly under estimated") and travel-time RMS (it falls when fewer picks are used; P-only locations had 3× lower RMS and were worse). A misidentified phase can move a depth by kilometres while the formal error shrinks.

## 2. Can anomalies be attributed?

The reviews converge on one principle (anomaly_attribution §3, supported in every stage): **an error with structure can be attributed by the redundancy of the data; an error common to all stations or events is absorbed by a free parameter and needs external truth.** Structure means: one station, one phase, a step in time, a quantised offset, a dependence on distance, azimuth or magnitude. Common-mode errors are absorbed by origin times, station terms or the magnitude constant.

| Tier | Anomalies | How |
|---|---|---|
| **A. Reliable without a reference** | magnitude offsets from units or response (quantised: 0.13, 2.68, 3, 6, log10 2πf); fixed, trial, grid-node or grid-bound depths (exact repeated values, matched against the run configuration); datum mismatch (constant offset of the order of station elevations); duplicates from a pipeline (shared picks); single-station faults with time structure (clock steps, gain steps, polarity reversal, misorientation); dead channels and spikes (noise models, MUSTANG rules); blasts (day/night ratio Rq ≥ 1.5, weekday pattern, spectral ratio); large events missed in the coda well above Mc(M, t); clipping and short windows of large events (recompute on far, unclipped records) | a cheap deterministic check or recomputation; the checker can state the evidence |
| **B. Only with a discriminating experiment** | depth pile-up at a layer interface vs a wrong model (shift the interface, gradient model, finer grid: an artefact moves with the representation); misidentified phases (jackknife by station and phase); magnitude shift vs real rate change vs Mc change (overlapping reprocessing, magnitude signature à la Habermann); incompleteness vs physical b-value (b-positive, later time windows, Mc(t)); constant station delay: clock vs path (δS/δP ratio: equal for a clock or instrument, ≈ Vp/Vs for structure; symmetry of noise correlations); real streaks vs relocation artefacts (bootstrap ellipses, catalogue-only vs CC-only vs combined); velocity-model sensitivity (relocate with other models: measures sensitivity, not which is right) | the checker can trigger the experiment; the knowledge says which experiment and what each cause predicts |
| **C. Not without external truth** | a common-mode depth or origin-time bias from the velocity model (coupled hypocentre–velocity problem; sign depends on geometry: a too-fast model with distant stations pushes events deeper, a too-fast near-surface layer pushes them shallower); the absolute level of a regional magnitude calibration (−log A0 vs mean station term; 0.1–0.3 offsets); a magnitude shift that coincides with an Mc change; constant clock offset vs site delay at one station; a timing error common to all stations; ghost detections vs real early aftershocks in mainshock coda; which of two disagreeing catalogs is right | report "consistent with X or Y", state what evidence would settle it (ground truth, explosions, depth phases, InSAR, a co-located sensor, Mw for some events) |

Our own results fall into these tiers: the unit and response bugs in run magnitudes are tier A; the step-interface pile-up (Prague) is tier B and was resolved by exactly the experiment the literature uses (Michelini & Lomax 2004 report events trapped at layer interfaces); the depth and time biases of velocity models that the checker cannot see (Prague 1.10 km, Maple, Kīlauea origin times) are tier C. That is why checker + knowledge reaches part of the human-in-loop gain and not all of it, and why the regional-model knowledge swap helped where the checker could not.

## 3. Consequences for the checker

**Reporting.** Each symptom should name its tier: attributable now (with the evidence), needs experiment E (named), or not verifiable reference-free (with the evidence that would settle it). Checks that cannot see a class of error should say so ("timing not verifiable: pick and onset come from the same record") instead of passing silently. For tier B and C symptoms the text says "consistent with X or Y", never a single cause.

**Missing checks, in priority order** (status 2026-11-01: items 1, 2, 4, 6, 7, 11 and 12 and the δS/δP part of 3 are implemented as report-only diagnostics, validated in `04_Checker_Design.md` §10.3 (6 needs ≥ 14 days of events, so it does not apply to the benchmark windows); 5, 8, 9 and 10 are open) (all reference-free; stage files give methods and sources):

1. Per-event depth-constraint class (correct S within 1.4 z, nearest station, gap, secondary gap) and every depth check split by it (location §L2–L3).
2. Pile-up values matched against the run's trial depth, grid nodes and bounds, datum and model interfaces (location; attribution tier A).
3. Station residuals split into δP, δS and δS/δP, binned in time (steps) and by azimuth (data_and_picking; Lin et al. 2008).
4. Station magnitude residuals by station and by distance bin, from the amplitudes `magnitude_recompute` already measures; number and spread of station MLs per event (magnitude; Hutton et al. 2010).
5. Large events in the coda: events above Mc(M, t) missing after the largest events, using a high-threshold scan on far, unclipped stations (magnitude C3/G; association).
6. Day/night ratio Rq and weekday pattern, above and below Mc (association, magnitude; Tan et al. 2021, Skoumal et al. 2015).
7. Duplicate events with pick overlap (pipeline duplicate vs true doublet) (association).
8. Template matching: null test (time-reversed or shifted data) next to the CC/MAD distribution, detections per template with their hour of day, decoy templates, detections larger than their template (association).
9. Waveform-level data QC: noise level against NLNM/NHNM and the network median, spikes, DC offsets, clipping, miniSEED timing flags (data_and_picking; MUSTANG rules).
10. Relocation health: cluster connectivity, residual reduction per data type, centroid shift against the initial location error, bootstrap on a subset (location R-rows).
11. Wadati diagram per event (robust slope, outlier S picks) (data_and_picking; NMSOP-2 Ch. 16).
12. b-positive next to the standard b-value, and the frequency–magnitude distribution split by magnitude type or detection method (magnitude).

**Thresholds to revisit:** `pick_onset_offset` 0.2 s on the median is loose (in-domain ML picks centre on zero; ≈ 0.05 s plus the share of picks > 0.45 s, and judge S); `processing_time_shift` 0.1 s against a 10 ms timing goal (1–2 samples); `s_to_p_ratio` has no upper bound (ML pickers on ocean-bottom data give ≈ 1.7); `associated_share_min` 0.2 flags published studies that associated 12–19 % (keep report-only unless extreme); `events_with_few_picks` < 4 P is looser than common practice (≥ 4 P and ≥ 7 picks; ≥ 4 stations with P and S); `relocation_shift` 1.5 km should be relative to the initial location error; `relocated_share` should count events above Mc only; `rate_after_largest` should use Mc(M, t). `magnitude_recompute` 0.5 and `sp_depth_offset` 1.5 km agree with the literature.

## 4. Consequences for the knowledge skill

- Entries follow the form "symptom → candidate causes → discriminating experiment → expected result under each cause" (attribution §5), which is the form `playbooks/decide_between_candidates.md` already uses for the step-interface pile-up.
- Each symptom should carry its provenance: what changed since the last product that passed (attribution §5). Most documented attributions in the literature came from matching a symptom's onset to a change log.
- Tier C needs knowledge, not checks: where to find a regional model and how to use it, regional magnitude calibrations (`data/agent_resource/magnitude/calibrations.json`), and the rule that among models that fit equally well the choice cannot be made from residuals.

## 5. Papers to download (merged, deduplicated)

Priority 1 (needed to cite claims now resting on abstracts or second-hand sources):
- Bondár, Myers, Engdahl & Bergman 2004, GJI 156, doi:10.1111/j.1365-246X.2004.02070.x
- Michelini & Lomax 2004, GRL 31, L09602, doi:10.1029/2004GL019682, with the Thurber & Zhang comment and reply (doi:10.1029/2004GL020731)
- Kissling, Ellsworth, Eberhart-Phillips & Kradolfer 1994, JGR 99, doi:10.1029/93JB03138; Kissling, Kradolfer & Maurer 1995, VELEST user's guide
- Thurber 1992, PEPI 75, 55–62
- Habermann 1987, BSSA 77, 141–159; Habermann 1991, Tectonophysics 193; Habermann & Craig 1988, BSSA 78
- Tormann, Wiemer & Hauksson 2010, BSSA 100, doi:10.1785/0120090124
- Woessner & Wiemer 2005, BSSA 95, doi:10.1785/0120040007
- Helmstetter, Kagan & Jackson 2006, BSSA 96, doi:10.1785/0120050067; Kagan 2004, BSSA 94, doi:10.1785/012003098
- van der Elst 2021, JGR, doi:10.1029/2020JB021027 (b-positive)
- Diehl, Kissling, Husen & Aldersons 2009, GJI 176 (open on doc.rero.ch); Diehl et al. 2009, BSSA 99(3)
- Husen, Kissling & Clinton 2011, Swiss J. Geosci. 104, doi:10.1007/s00015-011-0071-3 (open, blocked here)
- Pavlis 1986, BSSA 76

Priority 2:
- Zúñiga & Wyss 1995, BSSA 85; Wiemer & Baer 2000, BSSA 90, doi:10.1785/0119990104; Deichmann 2017, BSSA, doi:10.1785/0120160318; Munafò et al. 2016, doi:10.1785/0120160130; Castellaro et al. 2006, GJI; Marzocchi et al. 2020, GJI, doi:10.1093/gji/ggz541; Kanamori 1983; Koper et al. 2016, GRL, doi:10.1002/2016GL070742
- McNamara & Buland 2004, BSSA 94(4); Peterson 1993 (scan, needs OCR or tabulated models); Casey et al. 2018, SRL; Ringler et al. 2015, 2021; Yang, Song & Ringler 2022 with comment and reply; Ekström & Busby 2008; Ekström & Nettles 2018; Davis, Ishii & Masters 2005; Davis & Berger 2007, 2012; Pita-Sllim et al. 2023; Sens-Schönfelder 2008; Zeiler & Velasco 2009 (details unverified); NMSOP-2 IS 11.4 and IS 11.5
- Menke & Schaff 2004, BSSA 94; Waldhauser & Schaff 2008, doi:10.1029/2007JB005479; Schaff et al. 2004, doi:10.1785/0120020238; Schaff & Waldhauser 2010, doi:10.1785/0120100042; Lomax & Savvaidis 2022, doi:10.1029/2021JB023190; Husen et al. 1999, GJI 138; Richards-Dinger & Shearer 2000, JGR 105; Wolfe 2002, BSSA 92; Hutton et al. 2010 (doi:10.1785/0120090130); Hutton & Jones 1993; Uhrhammer & Collins 1990
- Peng & Zhao 2009, Nat. Geosci., doi:10.1038/ngeo697 (with SI); Renouard et al. 2021, SRL, doi:10.1785/0220200305; Linville et al. 2019, GRL, doi:10.1029/2018GL081119; Gibbons & Ringdal 2006, GJI (DOI unverified); Park et al. 2020, GRL, doi:10.1029/2020GL087032; Weston et al. 2011; Storchak et al. 2017, 2020; Bondár & Storchak 2011; Hable et al. 2018; Hainzl 2016 (open on GFZpublic); Ben-Zion & Zaliapin 2015; Kagan 2003; Petersen et al. 2019; Kisslinger & Engdahl 1973; Leonard 2000

Case-related (useful for interpreting our cases; target papers stay blocked for Agents and must not enter Agent-facing knowledge): Shelly 2020, SRL, doi:10.1785/0220190309; Liu et al. 2020, GRL, doi:10.1029/2019GL086189; Lomax 2020 (Ridgecrest absolute locations); Matoza et al. 2013, doi:10.1002/jgrb.50189, and 2020.
