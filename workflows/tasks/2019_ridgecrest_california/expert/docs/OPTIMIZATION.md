# Bounded catalog-optimization campaign

Objective: produce a demonstrably higher-precision Ridgecrest earthquake catalog, with traceable event/phase identities and retained uncertainties. Maximum **30 executed optimization rounds**, beginning after historical stage 20. Do not equate a report, a successful run, or an improved residual alone with the objective being achieved.

## Evidence and selection policy

- Keep full provisional v1 immutable. Preserve raw waveforms, original picks, reference catalogues and historical results.
- First select candidates on the existing development/transfer sets; acknowledge these sets have informed past work. Each round must implement and evaluate one coherent intervention. A bounded predeclared comparison of several settings counts as one round, not a license for hidden scans.
- `optimization_reserved_events.csv` freezes 300 ordinary v1 events disjoint from the 144 development and 147 transfer events. Selection uses only event IDs, baseline coordinates and periods, with deterministic hash ordering and round-robin spatial/time strata. These events are reserved from adaptive selection in THIS campaign; historical full-catalog comparisons mean they must not be called never-before-examined blind data. Do not inspect their reference outcomes to select candidates.
- Preserve observation holdouts within events when appropriate. Reference coordinates cannot be used as fitting targets for a model that is later scored on those same references. Report event counts, loss of coverage, depth behavior, horizontal and relative structure, and uncertainty alongside timing residuals.
- A candidate must demonstrate balanced gains on the fixed comparisons and then on a still-unused campaign confirmation reserve before full production. The first reserve was consumed in round07 and the second in round13; neither is fresh confirmation for subsequent adaptive changes. If posterior uncertainty changes with the assumed likelihood, explain the dependency; do not equate narrow posterior with truth.
- Produce a versioned full catalog only after a validated improvement, carrying provenance, accepted/review flags, phase associations and magnitude consistency. Run the required whole-product comparisons; a local pilot is insufficient.
- Stop early on a verified satisfactory product. If no defensible improvement is found within 30 rounds, report the exhausted limit and remaining constraints honestly; do not label failure as success or extend the round cap silently.

## Second confirmation reserve

`optimization_reserved_events_v2.csv` freezes 300 additional ordinary v1 events during stage-29 execution, before its complete outcome assessment (only execution counts/failures were inspected): 11 before M6.4, 105 between mainshocks and 184 after M7.1. Selection uses only IDs, baseline times and 10 km XY strata, with deterministic within-stratum hashing and round-robin allocation. It excludes the development/transfer cohorts, the consumed first reserve and reviewed S-window neighboring events. Selection is not population-proportional; historical full-catalog comparisons exist, and event disjointness does not imply spatial/temporal independence.

The matching JSON records source identities, selection rule and exposure limitations; `00_reserve_confirmation.py` reproduces and verifies the frozen CSV. Status: **consumed in round13; confirmation failed coverage and depth-boundary gates**. Its historical reservation no longer provides an unused confirmation set. Subsequent adaptive work on these events is development evidence only.

## Adaptive directions

1. Observation treatment: effective station/phase errors, geometry-preserving station selection, phase-specific robustness and validated waveform-based differential timing.
2. Physical constraints: velocity representation, depth/elevation consistency, justified model calibration with disjoint fitting/validation observations.
3. Location methods: fixed-input absolute location, relative location with adequate graph coverage, and physically consistent integration of absolute anchors and CC differential times.
4. Full production and held-out validation: transfer the chosen method to the entire eligible input set, audit completeness and failures, export a new version only on evidence.

These directions are options, not 30 mandatory stages. Choose the next intervention from actual failures and measured improvements. Do not force station-correction and velocity-induced depth changes to cancel without independent validation.

## Round ledger

| Round | Historical stage | Intervention | Evidence / decision |
|---|---|---|---|
| 01 | 21 | Development-only effective station/phase errors; fixed picks/model | Completed: withheld RMS -7.3%; horizontal reference medians -13.1% to -26.4%; median depth change -0.781 km; Shelly absolute-depth median +18.0%. Fails reference gate; do not promote. 294 new fits +294 verified controls. |
| 02 | 22 | Native EDT likelihood; original errors/model/picks | Completed 294 new fits +294 verified controls. Horizontal medians -12.8% to -24.1%, Shelly depth median -16.2%; withheld RMS +0.85%, posterior depth width +51.5%. Do not promote; preserve as candidate. |
| 03 | 23 | Analytic fit-only origins at fixed EDT xyz; matched six-station omission | Completed: withheld RMS 0.4037→0.3955 s (baseline 0.4003); horizontal omission median +14.5%, depth omission P90 +18.2%. Do not promote. |
| 04 | 24 | Native EDT_OT_WT_ML, original picks/errors/model | Completed 294 fits: withheld RMS 0.4061 s (baseline 0.4003, EDT 0.4037); omission depth P90 1.0469 km versus EDT 1.0156. Fails prediction, posterior and stability gates; close variant search. |
| 05 | 25 | Development mean-depth-gauge-constrained station corrections | Completed: heldout RMS -26.0%, horizontal reference medians -17.9% to -31.6%, omission medians -50%; depth shift -1.172 km and Shelly depth discrepancy +32.9%. Do not promote or tune projection weights. |
| 06 | 26 | Original P corrections only; S corrections zero, all phases retained | Completed: all gates pass. Heldout RMS -5.14%; horizontal reference medians -8.4% to -10.6%; Shelly depth discrepancy -10.6%; median depth shift -0.078 km. Freeze candidate for reserved validation. |
| 07 | 27 | Confirmation on frozen 300 reserved events | Completed 1,134 valid fits: 300 primary pairs, 267 auxiliary pairs. Heldout RMS -0.44%; primary near-boundary count 0→13. Confirmation fails; do not promote. 33 auxiliary-ineligible events retained. |
| 08 | 28 | Fixed 80-km station selection, zero corrections | Completed 290 fits: heldout RMS +11.4%, loss of one primary/three auxiliary fits, worse depth omission response. Some reference medians improve, but no promotion; close radius trial. |
| 09 | 29 | Fixed regional 3D hybrid, matched 3D and original fine 2D controls | Completed 588 new fits, zero failures; numerical/identity/timing checks pass. Against original: held-out RMS -13.5%; horizontal reference medians -36.4% to -56.4%; omission stability improves. Shelly depth discrepancy +67.6% fails the sole remaining gate. Do not promote; retain as a promising horizontal-location candidate. |
| 10 | 30 | Local 1D background with fixed regional fractional lateral variations | Completed 294 new fits +294 verified reused controls, no failures. Against original: held-out RMS +9.7%, Shelly depth discrepancy +149.6%; horizontal medians improve 22.8–40.2%. Prediction, reference-depth, posterior and omission-stability gates fail. Do not promote. |
| 11 | 31 | Development nearest-station S-P selection among two endpoints and one fixed physical midpoint | Completed 552 fits on 138 eligible development events. Held-out S-P RMS: original 0.29325 s, local background 0.31691 s, raw regional 0.28140 s, midpoint 0.30971 s. Midpoint fails both selection criteria; close background-weight trials. No confirmation or adoption. |
| 12 | 33 | Joint absolute arrivals and waveform CC differences with consistent elevated 1D travel times | Completed 16 solves (147 events each). Held-out CC RMS 0.11719→0.04628 s; absolute RMS 0.40064→0.39650 s. Reference and anchor gates pass; no boundary events. Freeze candidate for broader confirmation, not full adoption. |
| 13 | 34 | Frozen joint solver on 300 reserve targets with 1,970 geometry-selected supports | Completed 16 solves +290 native controls. Held CC RMS 0.13884→0.07169 s; absolute RMS 0.43804→0.43269 s. Reference/anchor gates pass. Training CC supports 181/300 (required 210), near-depth-boundary count 0→7 (allowed +3); confirmation fails. |

| 14 | 35 | Remove only absolute-model residual filtering of CC candidates | Completed 8 new joint solves +8 verified reused controls. Old-common held CC RMS 0.07169→0.06415 s; training CC support 181→190/300. Coverage still fails; near-depth-boundary count worsens 7→9. No promotion. |

| 15 | 36 | Fixed differential-model sensitivity envelope added to CC error | Completed 8 new joint solves +8 controls. Same 575 held CC RMS 0.069497→0.069957 s; near-boundary count 9→8, problematic depth still 0.032 km. Coverage unchanged at 190/300. No promotion; no envelope multiplier scan. |

| 16 | 37 | Fixed CC-only Huber loss; absolute objective unchanged | Completed 8 new joint solves +8 controls. Same held CC RMS 0.069497→0.068746 s; coverage 190/300 and near-depth-boundary count 9 still fail. The single-edge target remains at about 0 km. No promotion or loss-threshold scan. |

| 17 | 38 | Noise-normalized joint-horizontal S correlation; P and Huber locator unchanged | Completed: S acceptance 978→1601, support 190→194/300. All old 575 held CC RMS 0.068746→0.066901 s; near-boundary count 9→8. Both coverage and boundary gates still fail. No promotion. |

| 18 | 39 | Support-aware neighbor augmentation; old graph and waveform/locator rules retained | Completed 16 matched solves. Coverage 194→206/300; identical old held CC RMS 0.066901→0.062501 s; near-boundary count 8→6. Coverage and boundary still fail; no promotion or graph-parameter scan. |

| 19 | 40 | Consistent archived regional 3D TIME fields for absolute and CC terms, matched 3D-background controls | Completed 20 solves. Old held CC RMS 0.062501→0.058004 s; held absolute 0.429886→0.381343 s; near-boundary 6→0. Median depth shifts +2.505 km, Shelly depth discrepancy 1.848→2.083 km. Coverage and reference-depth gates fail; no promotion. |

| 20 | 41 | P-only empirical receiver corrections calibrated on 147 disjoint regional-model events; zero calibration-weighted P mean | Completed 16 solves. Held absolute RMS 0.381343→0.367297 s; depths +0.204 km, Shelly depth discrepancy 2.083→2.315 km. Coverage/reference-depth fail; no promotion or correction-strength scan. |

| 21 | 42 | Actual vertical-only P observations at WNM, WRV2 and WVP2; original joint model and fixed old held observations | Completed 16 matched solves. Add 3,866 P picks and 429 CC edges; held 1,408-CC RMS 0.069485→0.066867 s, held absolute 0.429886→0.425338 s. Coverage 206→207/300 and near-boundary 6→7 still fail. References worsen slightly; no promotion. |

| 22 | 43 | Waveform-template recovery of hidden P arrivals before missing-observation use | Completed qualification on 561 disjoint calibration pairs: 75 accepted (13.37%), median timing difference 0.01994 s but P90 0.49249 s; off-time acceptance 2/561. Coverage and timing fail; no target pick/location changes and no threshold retuning. |

| 23 | 44 | Unchanged qualified direct DPP P picking for missing P at existing training receivers | Completed 16 matched solves. 9,412 queries yield237 admitted P picks and35 new CC edges; held absolute0.425338→0.424065s, held1408-CC0.066867→0.066831s. Coverage207/300 and near-boundary7 unchanged; no promotion. |

| 24 | 45 | Added LB.DAC real three-component P/S observations with unchanged old data and solver | Completed 16 matched solves. Add 1,289 picks and 78 CC edges; fixed 1,408-CC RMS 0.066831→0.065971 s, held absolute 0.424065→0.426001 s. Shelly depth difference 1.913→1.824 km; coverage 207/300 unchanged and near-boundary 7→6. Both gates still fail; no promotion. |

| 25 | 46 | Independent EQTransformer P/S compatibility qualification on disjoint old transfer events | Completed 1,186 examples. P acceptance 37.19% fails the fixed50% gate; S acceptance90.11%, median/P90 difference0.05/0.09s passes. Joint candidate rejected; no target data or location changes. |

| 26 | 47 | Separately counted S-only missing-observation augmentation using unchanged qualified S rules | Completed 16 matched solves. Add 4,557 S picks and162 CC edges. Held absolute0.426001→0.428505s; fixed1408-CC0.065971→0.066891s; old575-CC improves0.061894→0.060005s. Horizontal medians improve, but depths shift-0.239km, coverage207/300 and near-boundary6→12 fail. No promotion. |

| 27 | 48 | Differential-only use of added EQ S, with a fixed-graph attribution control and unchanged-rule graph refresh | Completed32 fits. Add918 accepted CC edges; fixed1408 RMS0.065971→0.064456s; aggregate shallowing removed. Coverage208/300 and near-boundary6 still fail; no promotion. |

| 28 | 49 | Disjoint event-centered Vp/Vs calibration, then fixed-data matched relocation | Completed16 matched fits after calibration passed. Ratio1.698836 gives joint depth shift-1.560km, boundary6→79, fixed1524 CC RMS0.074758→0.082126s and Shelly depth discrepancy1.709→3.733km. Reject this1D substitution; no promotion. |

| 29 | 50 | Candidate pairing using original posterior depth moment envelopes, with fixed horizontal geometry and waveform/locator rules | Completed16 fits. Add1,854 accepted CC edges; coverage208→222/300, boundary6→3, fixed1524 RMS0.074758→0.072912s. Every gate passes; freeze for round30 confirmation, not adoption. |
| 30 | 51 | Frozen stage50 recipe on all300 third-reserve targets | Completed16 fits and282 native controls. Held CC0.162089→0.108425s; held absolute0.433326→0.419967s; coverage234/300 and reference/stability gates pass. Boundary0→6 exceeds3: confirmation fails. No promotion, no further rounds authorized. |

## Third confirmation reserve (consumed in round30)

`optimization_reserved_events_v3.csv` freezes 300 events before stage42 location results. Selection reads only original v1 IDs, times and XY coordinates and excludes 3,475 unique prior experiment/review IDs, including all current targets and supports. The eligible v1 pool has 3,047 events. The same deterministic period/10-km-stratum round robin selects 126 events between the mainshocks and 174 after M7.1. No unused pre-M6.4 events remain in this selection pool; this reserve cannot independently confirm that early period. Historical full-catalog comparisons and proximity to training events also limit independence.

At the original freeze these IDs were excluded from development/support use. They were opened only after the complete stage50 candidate passed all development gates and was frozen. Round30 used the reserve and failed the depth-boundary safeguard; it is no longer available as fresh confirmation. The earlier administrative freeze did not consume an optimization round.

## Campaign closing decision (before the subsequent full-scale authorization)

All30 rounds are complete. Stage50 passed development, but the unchanged candidate failed round30 confirmation: six near-depth-boundary targets versus the allowed three. All other confirmation gates pass. Held differential RMS improves33.1% and held absolute RMS improves3.1% against matched absolute-only; all three horizontal reference medians and Shelly nominal depth median improve against original NLL. These aggregate improvements do not remove the local depth failure.

The requested validated higher-precision full catalog has **not** been achieved. Keep the frozen gate, all300 targets and all six uncertainty flags. Do not start full production, select only favorable events or silently add round31. V1 remains the sole full product. The third reserve is consumed. Any further optimization requires a new explicit scope/budget; the current campaign stops here. [Final confirmation and bounded depth review](../export/05_confirmation/51_confirmation/README.md).

**Subsequent user authorization:** stage52 applies the selected method to the full working catalog and compares it with references. This explicitly permits full-scale candidate generation despite the failed safeguard; it does not erase the failure, authorize new parameter optimization, or imply adoption as a validated v2. See the [full-scale application](../export/06_full_catalog/52_full_catalog/README.md).

### Historical round13–14 decision

The joint absolute/CC method improves held-out differential timing and reference agreement, but broader confirmation fails CC coverage (181/300) and near-depth-boundary behavior (0→7). Keep that failure; do not change the gates retroactively. Round14 tested one observation-selection change on the exposed stage34 cohort: remove the old absolute-model residual prefilter while retaining probability, waveform checks, neighbor geometry and all location weights. It improves common held CC but fails coverage and depth-boundary gates. Its results are development evidence only. No qualifying candidate exists yet.

Score the same 1,394 held-out absolute arrivals and separately the old 526 held-out CC edges, expanded CC set and new-only set. The shared evaluator exactly reproduces stage34's decision and five CSV products, and its current source is frozen before new outcomes. Historical grids, waveforms, picks and full v1 remain unchanged.

### Completed anchor check (stage32, not an optimization round)

Fourteen fixed hypoDD/hypoDD+CC runs reproduce both archived controls exactly and show strong common-initial-position dependence: 0.95–0.98 km horizontal and 0.60–0.93 km depth response to a 1 km input translation. The next optimization intervention is a joint absolute-arrival/CC-differential solver with consistent physics and a matched absolute-only control. Pure differential results alone cannot establish improved absolute anchoring. Freeze the joint observation/error specification before evaluating outcomes; do not use reference positions in fitting. Keep confirmation v2 unused pending transfer qualification.

### Round12 candidate ready for broader validation

The joint candidate passes its predeclared relative-gain/nondegradation gates. Unlike the earlier absolute-model trials, its explicit target is relative precision with preserved absolute anchoring; CC and absolute RMS are evaluated separately. Horizontal reference medians improve against original NLL (Liu 1.09578→1.02056 km, Official 0.88262→0.83473 km, Shelly 0.93524→0.82325 km); Shelly absolute-depth median improves 1.33747→1.02617 km. All original events remain represented. No posterior precision claim is made from the working CC error or nonzero-gradient solver termination.

Freeze the implementation and 50 ms CC weight. Next prepare a broader validation using the still-unused second event reserve and waveform-derived edges, with network/connectivity eligibility fixed before scoring. Sparse isolated reserved events may require neighboring support events selected by original geometry; keep their roles explicit and score only the fixed reserve, retaining unsupported events and reporting coverage. Do not select neighborhoods using references or new CC outcomes, tune weights, or substitute favorable reserve events. Verify sparse-solver behavior/coverage and uncertainty stability before any full-catalog promotion. The reserve is still unused as of this report.

### Round13 confirmation preparation underway

The candidate is frozen. Stage34 retains all 300 reserve_v2 events and adds 1,970 support events chosen only by original 3D distance (up to 12 neighbors within 3 km per reserve event). Prior development, transfer and consumed-reserve events are excluded from support. There are 2,764 proposed pairs, 31,776 eligible differential observations and 71,847 absolute picks. All disconnected/rejected states remain; no largest-component selection. After the fixed station omission, 290 reserve events meet the >=10-arrival and >=3-S requirements; all 300 remain in primary validation.

The historical CC extractor cannot process one pick at 2019-07-06T23:59:50.328300Z within its 10 s case-boundary padding. The stage34 adapter explicitly records the single unsupported edge, preserves the frozen graph and all absolute observations, and uses the unchanged CC measurement implementation for the rest. It does not assert that archived waveforms are absent. Graph preparation is not confirmation success; reserve location/reference outcomes remain unscored. Do not restart a live waveform job.

Stage34 CC measurements are complete. After auxiliary eligibility, training edges support 181/300 reserve events, below the predeclared 210 minimum; withheld CC covers 104 events with 526 edges. The coverage gate fails before location outcomes. Keep thresholds and the cohort unchanged. Fixed location runs continue for conditional-effect assessment, but this round cannot authorize full promotion. Reserve v2 is now exposed to confirmation coverage; do not describe it as untouched or use its outcomes for further selection while claiming independent validation.

Stage34 coverage attribution retains all 300 targets: 181 supported, 19 without a <=3 km neighbor, 42 without eligible training pick pairs, 48 with candidate pairs but no accepted training CC, and 10 auxiliary-ineligible. Missing waveform windows are rare in the unsupported candidate group. A fixed accounting check (not a new optimization) removes only the historical absolute-residual <=0.5 s prefilter while keeping probability >=0.5 and all original neighbors/pair rules. It restores candidate support for 23 of the 42 pair-deficient events; CC acceptance and location benefit are NOT established by this count. This identifies a model-dependent observation-selection mechanism worth testing after round13 closes, without lowering CC quality thresholds or altering its existing gate/graph.

### Round13 closed: conditional gains, failed coverage and depth-boundary checks

All 16 solves terminate; native residual equations agree within 0.000065 s. Held-out CC RMS improves 48.4%; held absolute RMS improves 1.2% versus the matched control and also improves against original NLL (0.44040 s). Frozen reference medians and common-start stability pass. Nevertheless, coverage and near-depth-boundary gates fail; **do not promote** and do not tune on reserve_v2 while treating it as independent confirmation.

The seven near-boundary cases are not seven hard-bound hits. Six remain at 0.249–0.487 km; gamma_0007386 moves from original 2.383 km / absolute-only 2.502 km to approximately 0 km with just one CC edge at one station. Other near-boundary events have 1–98 edges at 1–21 stations. This heterogeneity does not establish a universal CC failure. Next inspect the single-edge depth collapse and differential-model/error assumptions before treating broader CC candidate coverage as sufficient. Do not clip or delete problematic events or adjust the failed threshold retroactively. Full v1 remains unchanged; no full improved catalog has passed confirmation.

### Round14 started: CC candidates independent of absolute-model residuals

One intervention is frozen: remove only the original NLL residual <=0.5 s prefilter for CC candidates. Keep probability >=0.5, the exact stage34 neighbor pairs and common-phase/station requirements, all waveform acceptance settings, 50 ms CC error and the absolute/joint solver. The already-exposed stage34 targets are DEVELOPMENT data now, not a fresh confirmation. Candidate edges increase 31,776→40,256; two case-boundary edges are explicitly unsupported. Waveform measurement is running; acceptance, coverage and location benefits are not yet known. Passing the unchanged stage34 gates would authorize only a genuinely fresh confirmation.

The worst depth-boundary target, gamma_0007386, has one accepted CI.SRT P edge (CC about 0.907, lag -0.02 s); its original conditional depth sigma is about 1.576 km. Its full absolute input has 16 picks, and several probability-qualified picks were excluded from CC by the old absolute residual screen. This motivates acquiring additional independently checked observations, not declaring the one CC wrong or assuming more candidates will cure depth bias. No correction, weight change, clipping or threshold relaxation is applied.

Round14 waveform measurement is complete: 3,396 accepted CC edges. Auxiliary training support increases 181→190 targets, still below 210; 575 held edges cover 108 targets. All historical edge acceptances and accepted differential times reproduce. The problematic gamma_0007386 retains only one P edge. Eight independent joint fits now run on four CPU workers with unchanged equations/options; absolute controls are verified and reused. The coverage failure remains, irrespective of the pending location outcomes.

### Round14 closed: extra observations help differential prediction but not depth stability

All eight new joint solves complete; eight immutable absolute-only controls are reused after source/measurement checks. The same 526 held CC edges improve from previous-joint RMS 0.071693 to 0.064152 s. On the expanded 575-edge set, previous joint gives 0.078260 s and expanded joint 0.069497 s; absolute-only gives 0.142148 s. Thus the differential improvement is not merely a changed scoring set.

However, training support is only 190/300 and near-depth-boundary count rises 7→9 (original NLL zero). Reference, initialization and absolute-prediction gates pass, but both failed gates remain. Close residual-cutoff/probability/CC-threshold scanning; do not declare a high-precision full product. Additional reliable differential constraints alone have not resolved absolute depth/model sensitivity. Next intervention should address the physical travel-time model or justified differential-model uncertainty while preserving matched controls and independent prediction checks, not simply add more edges or clip depths.

### Round15 in progress: fixed differential-model sensitivity errors

Use the maximum local-layered/regional-3D differential-time contrast with the original model, evaluated at original positions, as an error envelope added in quadrature to 50 ms. Keep the original mean model and all stage35 observations unchanged. Median working error is 0.05113 s; 72/3,396 edges exceed 0.1 s. No multiplier scan. This is not a calibrated model ensemble, and the 190/300 coverage failure remains. Eight joint fits are executing; eight absolute controls are reused. Source/error identities and weighted derivatives are verified. Independent confirmation is still required for any future complete candidate.

### Round15 closed: model contrast does not resolve the weak-depth case

The fixed contrast-based error treatment gives held CC RMS 0.069957 s on the same 575 observations versus 0.069497 s with fixed 50 ms errors. Held absolute RMS is 0.433388 s (matched absolute-only 0.438039 s). Reference and initial-position stability gates pass, but coverage remains 190/300 and near-depth-boundary count is eight versus original zero. No promotion.

For gamma_0007386, the CC error changes to 0.05962 s and depth changes only 0.00522→0.03239 km. This sensitivity test does not support treating the available model contrasts as a sufficient cure. Do not scan envelope multipliers or hand-limit its depth. The remaining issue is the influence of weakly supported differential constraints under a purely quadratic likelihood; a bounded robust-loss experiment is a possible next algorithmic intervention, alongside the still-unresolved observation-coverage requirement. Preserve the full original objective and both failed gates.

### Round16 in progress: fixed robust CC likelihood

Replace only the CC quadratic loss with Huber(delta=1.345) on residual/0.05 s, retaining quadratic absolute arrivals, the original mean model and all stage35 observations. Exact objective/derivative checks pass. Eight new joint fits run on four CPU workers; absolute controls are reused. No threshold scan and no claim that Huber controls geometric leverage. All existing gates remain, including the known coverage failure. A future complete improvement still requires broader/fresh validation and full production.

### Round16 closed: residual robustness does not repair weak geometric support

The same 575 held CC observations improve slightly, 0.069497→0.068746 s, but nine near-depth-boundary events remain and gamma_0007386 is at 0.000123 km. Coverage is unchanged at 190/300. All fixed gates are retained; no promotion and no Huber threshold/loss-family scan. Restricting residual influence is insufficient to establish stable depth for this weakly supported event.

A bounded input accounting check found 17,774 training S candidate edges in the fixed stage35 graph: 1,427 have two recorded horizontal components but exactly one component accepted, while 798 have both accepted before inter-component lag consistency. This identifies a specific observation-processing hypothesis: evaluate both horizontal traces jointly, retaining two-band/ambiguity/SNR checks, instead of requiring each component independently to pass. These counts do not establish valid extra picks, improved coverage or location gains; any such method must be implemented and independently checked on identical observations without relaxing thresholds or reusing this exposed cohort as confirmation.

### Round17 in progress: joint-horizontal S measurements

Use a single noise-normalized two-component S lag, with the original two-band, polarity, ambiguity and lag tests. P rows and the stage37 robust locator remain unchanged. Synthetic sign/delay/reversal, gain-invariance and zero-component checks pass. All S candidates are treated uniformly; do not choose old or new outcomes per edge. A new predeclared gate scores ALL old 575 held measurements and requires <=1.05 times stage37 RMS, alongside the original gates. This is exposed development; no fresh-confirmation claim. Measurement is currently running on cached windows.

Round17 measurement is complete: S acceptance 978→1,601; all 2,418 accepted P observations and all P rows are unchanged. Auxiliary training coverage is 194/300 (still below 210); held CC has 698 edges covering 120 targets. The weak-depth event gains one independently located CI.DTP S measurement in addition to its original CI.SRT P. New joint solves are running. No depth or accuracy conclusion is inferred from increased counts.

### Round17 closed: better S observations, insufficient graph coverage

All fixed solves and checks complete. On ALL 575 old held measurements, vector-S/Huber locations yield 0.066901 s RMS versus 0.068746 s previously (ratio 0.97316); P and S both improve. On the 698 new held measurements, previous Huber gives 0.075123 s and vector-S Huber 0.072991 s, versus absolute-only 0.146155 s. New observations are not substituted for the old validation set.

Training support reaches only 194/300 and near-depth-boundary count remains eight. gamma_0007386 gains a CI.DTP S observation but still locates at 0.00287 km. Extra observations have helped prediction without resolving all depth/coverage issues; no promotion or threshold scan. The next bounded direction is observation-support-aware event pairing within the original spatial radius, preserving old edges and observations, rather than reducing waveform quality thresholds. Freeze any graph rule before new waveform outcomes; this cohort remains exposed development.
