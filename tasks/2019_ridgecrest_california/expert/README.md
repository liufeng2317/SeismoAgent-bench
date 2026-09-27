# Ridgecrest expert result

**The stage 52 delivery candidate is retained; parameter tuning remains closed.** A user-requested stage 53 adds fixed full-cohort native hypoDD CT and CT+CC comparison branches. Neither automatically replaces the candidate. Preserve the original stage 10 baseline, all depth flags and explicit origin-time limitations. This is an expert workflow result, not unique ground truth or a fully validated v2. No unsupported uniform correction or mixing of baseline times with candidate coordinates is applied.

Start with [EXPERT_DELIVERY.md](docs/EXPERT_DELIVERY.md) for the complete inventory, local reproduction commands and limitations.

## Catalog stages and names

**CT** = differential times from picked arrivals; **CC** = differential times from waveform cross-correlation; **Joint DD** = joint fitting of absolute arrivals and CC double differences.

| Order | Catalog / figure label | Position in the workflow |
| --- | --- | --- |
| 01 | [GaMMA initial (ours)](export/01_baseline/03_associate_gamma/full/events.csv) | Association and preliminary location |
| 02 | [NLL baseline (ours)](export/01_baseline/10_validate_catalog/events.csv) | Original absolute-location baseline; stage 10 adds review and magnitude fields |
| 03 | [Absolute-only control (ours)](export/06_full_catalog/52_full_catalog/branch_locations.csv) | Matched stage 52 control, using admitted absolute arrivals; select `branch=absolute_all` |
| 04 | [Joint DD candidate (ours)](export/06_full_catalog/52_full_catalog/working_catalog.csv) | Retained stage 52 candidate: absolute arrivals + CC double differences |
| 05 | [hypoDD CT (ours)](export/06_full_catalog/53_native_double_difference/hypodd_ct/catalog.csv) | Stage 53 native catalog-difference comparison |
| 06 | [hypoDD CT+CC (ours)](export/06_full_catalog/53_native_double_difference/hypodd_cc/catalog.csv) | Stage 53 native catalog + CC difference comparison |

**03–06 are parallel branches initialized from NLL, not successive replacements.**
See [catalog paths, lineage and usage rules](docs/CATALOGS.md) and the
[full-cohort native comparison](export/06_full_catalog/53_native_double_difference/README.md).
Historical `Expert catalog (ours)` labels refer specifically to **Joint DD candidate (ours)**.

## Use these products

| Product | Entry point |
| --- | --- |
| Primary candidate: 6,520 relocated working events | [working_catalog.csv](export/06_full_catalog/52_full_catalog/working_catalog.csv) |
| Complete master: 9,942 IDs; 3,422 non-working locations unchanged | [events.csv](export/06_full_catalog/52_full_catalog/events.csv) |
| Candidate observations and absolute/differential usage | [phases.csv](export/06_full_catalog/52_full_catalog/phases.csv) |
| Per-event support and depth flags | [event_quality.csv](export/06_full_catalog/52_full_catalog/event_quality.csv) |
| Original baseline and original phases | [Stage 10](export/01_baseline/10_validate_catalog/README.md) |
| Quantitative comparisons and catalog figures | [Stage 52 report](export/06_full_catalog/52_full_catalog/README.md) |
| Closing time/depth diagnosis and decision | [Bounded review](export/06_full_catalog/52_full_catalog/diagnostics/time_depth/README.md) |

## Visual results

**`Joint DD candidate (ours)` is our delivered expert candidate; `NLL baseline (ours)` is our preserved baseline. `Reference: Liu`, `Reference: Official` and `Reference: Shelly` are external catalogs, not our output.** Figures below are existing results, linked in place.

| Figure label | Meaning |
| --- | --- |
| `Joint DD candidate (ours)` | Our retained joint-location candidate; limitations and flags remain |
| `NLL baseline (ours)` | Our original NonLinLoc baseline |
| `Absolute-only control (ours)` | Our matched absolute-arrival-only control |
| `hypoDD CT (ours)` | Native relocation using catalog arrival differences |
| `hypoDD CT+CC (ours)` | Native relocation using catalog and waveform-CC arrival differences |
| `Reference: Liu / Official / Shelly / Ross relocated` | External comparison catalogs |

The gallery has two distinct evaluation scopes. The detailed joint-DD figures do **not** evaluate native hypoDD CT or CT+CC.

| Evaluation | Question | Event population |
| --- | --- | --- |
| [Parallel branches (stage 53)](#parallel-location-branches-stage-53) | How do joint DD, hypoDD CT and hypoDD CT+CC compare with the original NLL baseline? | 5,938 events retained by all four catalogs; fixed reference subsets within this cohort |
| [Joint DD evaluation (stage 52)](#joint-dd-evaluation-against-nll-stage-52) | What changed from NLL to the retained joint DD candidate? | All 6,520 working events for catalog views; reference-specific matched subsets for reference comparisons |

### Parallel location branches (stage 53)

All three relocation branches start from the original NLL working locations; they are not successive refinements of one another. Joint DD uses the case-local solver, while CT and CT+CC use native hypoDD. Their velocity representation and receiver-elevation treatment also differ, so this is a comparison of the executed workflows, not a controlled solver-only test.

#### Four location catalogs: the same earthquakes

![Maps and depth projections of NLL, joint DD, hypoDD CT and hypoDD CT+CC](export/06_full_catalog/53_native_double_difference/figures/01_same_event_locations.png)

**Left to right:** NLL baseline, retained joint DD candidate, native hypoDD CT, native hypoDD CT+CC. **Top:** map view. **Bottom:** east–depth projection. Every panel shows the same **5,938 event IDs**, with common map limits and common depth-projection limits. Depth uses the +0.7 km model datum. The bottom row projects the entire common population, not a narrow fault-normal section.

These are the common retained events, not each method's complete output: NLL and joint DD contain 6,520 working events, native CT 5,960 and native CT+CC 5,997. Read spatial concentration together with the [retention and reference-discrepancy table below](#full-cohort-native-double-difference-comparison). [PDF](export/06_full_catalog/53_native_double_difference/figures/01_same_event_locations.pdf).

#### Full-cohort native double-difference comparison

Both native branches have completed. **Retain Joint DD candidate (ours) as the delivery; keep the two native products as independent comparisons.** All location metrics below use the same **5,938 common events** and frozen reference pairs (Liu 4,396; Official 3,864; Shelly 4,293 horizontal/time and 4,269 depth pairs). All differences below are **median absolute discrepancies**, not actual event depths or times. Retained counts describe each full output, not just the matched subset.

| Catalog | Retained / 6,520 | Horizontal difference: Liu km | Horizontal difference: Official km | Horizontal difference: Shelly km | Depth difference: Shelly km | Time difference: Shelly s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| NLL baseline (ours) | 6,520 | 0.927 | 0.845 | 0.918 | 1.847 | 0.196 |
| Joint DD candidate (ours) | 6,520 | 0.754 | 0.741 | 0.593 | 0.791 | 0.253 |
| hypoDD CT (ours) | 5,960 | 1.237 | 1.293 | 1.250 | 0.928 | 0.190 |
| hypoDD CT+CC (ours) | 5,997 | 1.043 | 1.061 | 1.024 | 0.839 | 0.180 |

CC improves the native branch, but the retained joint candidate has smaller horizontal medians and P90 discrepancies against all three references on this cohort. Native CT+CC has better origin-time agreement here; it does not replace the joint solution or supply replacement times. Native CT / CT+CC exclude 327 / 290 negative-depth events, respectively; both also lack differential support for 229 input events and exclude four others. Fewer remaining depth-range flags therefore do not establish better overall quality. Constant-layer/elevation differences remain part of this comparison; references are not ground truth.

[Same-event maps and depth sections](export/06_full_catalog/53_native_double_difference/figures/01_same_event_locations.png) · [Full native report and figures](export/06_full_catalog/53_native_double_difference/README.md) · [Event membership and exclusion reasons](export/06_full_catalog/53_native_double_difference/event_membership.csv).

### Joint DD evaluation against NLL (stage 52)

**Every figure in this section concerns the retained Joint DD candidate (ours), the NLL baseline, and the stated reference/control catalogs. Native hypoDD CT and CT+CC are absent.** Here, “improved” means the measured change from NLL to joint DD, including the admitted observation additions and joint fit; it does not isolate the effect of the DD term alone.

This section uses the full 6,520-event working cohort and its fixed reference matches. Its reference statistics therefore differ slightly from the 5,938-common-event comparison above; compare methods within each table/figure, not across the two populations.

#### Joint DD vs NLL: what improved, and what did not?

![Direct comparison of horizontal, depth and origin-time discrepancies](export/06_full_catalog/52_full_catalog/figures/05_delivery_metric_changes.png)

Gray = original NLL; blue = our joint candidate. **Leftward is a smaller reference discrepancy in every panel.** Horizontal medians improve against all three references; Shelly nominal depth median/P90 also improve. Origin-time medians move right and worsen. Numbers are unchanged from the frozen comparison tables; the panels have different units/scales. Reference consistency is not ground-truth accuracy. [PDF](export/06_full_catalog/52_full_catalog/figures/05_delivery_metric_changes.pdf).

#### Joint DD vs NLL: same-event spatial and depth comparison

![NLL baseline (ours) and joint candidate: maps and depth projections](export/06_full_catalog/52_full_catalog/figures/02_depth_sections.png)

Top: original NLL; bottom: joint candidate. All panels retain the same 6,520 working event IDs. Columns show the map and east–depth/north–depth projections of the full population, not narrow fault-normal sections. Orange rings track the same 63 candidate depth-boundary flags in both rows. Depth is relative to the +0.7 km model datum. [PDF](export/06_full_catalog/52_full_catalog/figures/02_depth_sections.pdf).

#### Joint DD vs NLL: local structure alongside Shelly

![Local views of baseline, Shelly reference and joint candidate](export/06_full_catalog/52_full_catalog/figures/06_local_reference_comparison.png)

Left = original NLL; middle = Shelly reference; right = our candidate. The northern and central views contain **819 and 1,253 identical matched event IDs**, respectively. Selection uses original NLL coordinates in 10×10 km squares centered at (−15,20) and (0,0) km. Each row has identical axes expanded to retain every selected event at all three positions; no outliers are hidden or events rematched. These are geographic illustrations, not representative performance samples.

Look at the central oblique band: the candidate shows more concentrated segments than the original broad distribution, while Shelly still has more sharply defined structure. The original regularly spaced coordinates also become less apparent with the continuous joint fit; visual sharpening alone does not prove improved physical resolution. [PDF](export/06_full_catalog/52_full_catalog/figures/06_local_reference_comparison.pdf) · [Selected event IDs](export/06_full_catalog/52_full_catalog/figures/06_local_comparison_events.csv).

#### NLL and joint DD overlaid on reference catalogs

![Paired overlays of NLL and joint DD on the same reference events](export/06_full_catalog/52_full_catalog/figures/04_matched_reference_maps.png)

**Purpose:** compare spatial offsets from the same reference events before and after joint DD. **Rows:** Liu, Official and Shelly. **Left:** NLL baseline (ours) overlaid on the reference. **Right:** Joint DD candidate (ours) overlaid on the same reference. Orange crosses are reference locations; blue dots are ours in both columns. Look for separation between orange and blue structures, then compare the paired median horizontal discrepancy (ΔH); a visually denser cloud alone does not establish better accuracy.

Both panels in each row use identical matched event IDs, reference coordinates and map limits: **4,497 Liu**, **3,961 Official** and **4,401 Shelly** matches. All selected events are shown, without thinning or new matching. These are fixed event pairs from the original time/location matching, not simply all earthquakes in an overlapping time interval. The map assesses spatial agreement; it does not show origin-time agreement or identify individual pairs in crowded regions. The event populations differ between rows and from the four-method common cohort above. [PDF](export/06_full_catalog/52_full_catalog/figures/04_matched_reference_maps.pdf).

<details>
<summary>Show joint DD, NLL and absolute-only control discrepancy distributions</summary>

![Fixed-reference horizontal and nominal depth discrepancy distributions](export/06_full_catalog/52_full_catalog/figures/03_reference_discrepancies.png)

Blue = joint candidate; gray = original NLL; orange = matched absolute-only control. The orange control uses the case-local joint solver with only absolute-arrival constraints; it is not hypoDD CT. At the same cumulative fraction, a smaller horizontal-axis value means a smaller reference discrepancy. References are not truth. Shelly depth uses 4,377 eligible pairs under the existing depth convention. [PDF](export/06_full_catalog/52_full_catalog/figures/03_reference_discrepancies.pdf).

</details>

Additional views: [NLL, joint DD and reference catalog populations, including Ross](export/06_full_catalog/52_full_catalog/figures/01_catalog_maps.png) and [time/depth changes by CC support](export/06_full_catalog/52_full_catalog/diagnostics/time_depth/time_depth_support.png). Spatial gains do not imply uniform improvement: reference origin-time agreement worsens and all 63 depth-boundary flags remain. See the [quantitative report](export/06_full_catalog/52_full_catalog/README.md) and [closing diagnosis](export/06_full_catalog/52_full_catalog/diagnostics/time_depth/README.md).

## Earthquake monitoring workflow and executed parameters

This table describes the executed **offline earthquake catalog construction** for July 4–7. It separates production steps from the historical experiments used to select settings. Parameter scans, alternative-model trials, absolute-only controls and held-instrument tests are evaluation history, not additional monitoring steps.

**Common conventions:** UTC interval `[2019-07-04, 2019-07-07)`; AEQD centered at longitude −117.55°, latitude 35.75°; `depth_below_sea_level_km = depth_km - 0.7`. Preserve real waveform gaps, instrument identities and event/pick IDs.

| Step | Program | Key executed settings | Product |
| --- | --- | --- | --- |
| **1. Prepare waveforms and stations** | [01_prepare_inputs.py](01_pipeline/01_prepare_inputs.py) | Three days; 37 baseline three-component HH/EH instruments; metadata epoch/sample-grid checks; rotate to ZNE using StationXML orientation; no gap filling | Waveform and station input tables |
| **2. Pick P/S arrivals** | **PhaseNet**, [02_pick_phasenet.py](01_pipeline/02_pick_phasenet.py) | `original` v2; P/S thresholds **0.3/0.3**; 100 Hz raw counts; 6 h blocks + 60 s buffers; 16 CPU workers, batch 32 | **411,891 picks** |
| **3. Associate events** | **GaMMA BGMM**, [03_associate_gamma.py](01_pipeline/03_associate_gamma.py) | 1 h blocks + 120 s buffers; DBSCAN `eps=10 s`, `min_samples=3`; minimum **10 picks / 4 P / 3 S / 6 stations**; linear 1D model, depth 0–25 km; no amplitude input | **9,942 initial events**, 288,431 associated picks |
| **4. Locate and review the baseline** | **NonLinLoc 7**, [04_locate_nonlinloc.py](01_pipeline/04_locate_nonlinloc.py); [05_review_catalog.py](02_diagnostics/05_review_catalog.py), [10_validate_catalog.py](01_pipeline/10_validate_catalog.py) | Linear 1D grids, receiver elevations, 0.25 km spacing; search depth 0–25 km; `GAU_ANALYTIC`; P/S errors **0.10/0.20 s**, model error **0.30 s**. Flag residual, geometry and depth concerns; select ordinary regional working events, excluding the two mainshocks | Preserved **NLL baseline** and **6,520-event working set**; other master events remain available |
| **5. Estimate provisional magnitude** | **ObsPy**, [09_estimate_magnitude.py](01_pipeline/09_estimate_magnitude.py) | Horizontal response removal + Wood–Anderson; ≤100 km epicentral distance, SNR ≥3, ≥3 stations, station MAD ≤0.5 | Baseline-geometry ML and support flags; **inherited by the joint candidate, not recomputed after relocation** |
| **6a. A. Joint DD** | Case-local **SciPy least_squares**, [52_run_full_catalog.py](01_pipeline/52_run_full_catalog.py) | **Absolute arrivals + waveform CC differential times**. Linear 1D grids with receiver elevations; absolute P/S sigma **0.316/0.361 s**; CC sigma **0.05 s**, Huber **δ=1.345** on CC only; depth 0–25 km; `tr_solver=lsmr`, `max_nfev=250` | **Joint DD candidate (ours): 6,520 events**; retained delivery candidate; absolute constraints retain events without CC support |
| **6b. B. hypoDD CT** | Native **hypoDD**, [53_native_double_difference.py](01_pipeline/53_native_double_difference.py), `--branch hypodd_ct` | **Catalog arrival differences only**. LSQR **4+8 iterations**, damping **80/40**, CT P/S weights **1/0.5**; constant Shelly layers, Vp/Vs **1.73**, no receiver-elevation correction; no waveform CC constraints | **hypoDD CT (ours): 5,960 events**; independent alternative |
| **6c. C. hypoDD CT+CC** | Native **hypoDD**, [53_native_double_difference.py](01_pipeline/53_native_double_difference.py), `--branch hypodd_cc` | **Catalog + waveform CC arrival differences**. LSQR **4+8 iterations**, damping **80/40**, CT P/S weights **1/0.5**, CC P/S weights **3/1.5**, CC quality **CC²**; constant Shelly layers, Vp/Vs **1.73**, no receiver-elevation correction | **hypoDD CT+CC (ours): 5,997 events**; independent alternative |
| **7. Export and assess catalogs** | [52_compare_full_catalog.py](04_comparison/52_compare_full_catalog.py), [53_native_double_difference.py](01_pipeline/53_native_double_difference.py) | Preserve event identities, membership/exclusions, depth and coverage flags; use fixed reference matches for comparisons | Named catalogs, observation/quality tables, figures and reference metrics; joint working catalog plus **9,942-event master** |

**6a / 6b / 6c are parallel alternatives**, each starting from the same original **6,520 NLL working locations** and shared event-pair graph. They are not successive refinements. The magnitude step uses baseline geometry and does not feed the relocation objectives.

**Differential-time inputs within relocation:** [52_prepare_full_catalog.py](01_pipeline/52_prepare_full_catalog.py) prepares the pair graph (distance screen **3 km**, ≥6 shared phase/instrument keys at ≥4 instruments); [53_native_double_difference.py](01_pipeline/53_native_double_difference.py) exports CT for **6b/6c**. [52_measure_full_catalog.py](01_pipeline/52_measure_full_catalog.py) measures CC for **6a/6c**: bands **2–8 / 2–12 Hz**, P window **[−0.2,1.0] s**, S **[−0.3,1.5] s**, CC ≥0.75, SNR ≥2, inter-band lag agreement ≤0.02 s; P uses Z and S uses joint horizontal correlation. The retained input contains **294,943 CC observations**. These are internal preparation operations for the relevant relocation branches, not a separate numbered monitoring stage.

The native branches use the same initial 6,520 IDs, but lose events through missing differential support or relocation exclusions. Joint DD and native hypoDD differ in velocity representation and elevation treatment as well as objective function. Compare the **5,938 common retained events** using the [parallel-branch results](#parallel-location-branches-stage-53); do not interpret this as a solver-only ablation.

**Case-specific observations:** the retained run also reuses qualified missing-P, LB.DAC and extra-S observations from earlier experiments. They are inputs to relocation branches 6a–6c, subject to each branch’s constraint rules, not another mandatory monitoring stage. Added EQTransformer S is differential-only and excluded from absolute arrivals and native CT. [Admission settings](#retained-observation-additions) and [detailed executed settings](docs/EXPERT_DELIVERY.md#archived-execution-settings) preserve the reproduction details.

**Provisional ML:** `ML_station = log10(A_WA_mm) + 1.11 log10(R/100) + 0.00189(R−100) + 3`, with hypocentral distance `R` in km and `A_WA_mm` the geometric mean of the N/E maximum absolute Wood–Anderson amplitudes in mm. Response, continuity and raw-extreme-plateau checks must also pass. Event ML is the median of accepted station estimates. Stage 52 does not recompute magnitudes at new locations; magnitude processing is the response-removal branch, not an upstream requirement for PhaseNet.

**Retained velocity profile:** depth nodes `[0,1,2,3,4,5,6,7,8,30]` km; Vp `[4.74,5.01,5.35,5.71,6.07,6.17,6.27,6.34,6.39,7.80]` km/s; `Vs = Vp / 1.73`. The implemented baseline linearly interpolates between these nodes, including 8–30 km. The values and baseline settings are frozen in [stage 04 inputs.json](export/01_baseline/04_locate_nonlinloc/inputs.json); use the archived receiver-specific grids for final numerical reproduction. Receiver model depth is `0.7 − (elevation_m − sensor_depth_m)/1000` km.

### Retained observation additions

These are case-specific input provenance, not additional steps in the main workflow. Expand only when reproducing the qualified observation additions.

<details>
<summary>Observation sources and admission settings</summary>


| Source / program | Key admission settings | Final use |
| --- | --- | --- |
| [42_vertical_p.py](03_experiments/08_vertical_observations/42_vertical_p.py) and [44_extract_missing_p.py](03_experiments/08_vertical_observations/44_extract_missing_p.py) | DPP first crossing >0.5; pre-step score ≤0.2, post-step ≥0.8; SNR ≥2; two shifted windows agree within 0.100001 s; predicted P gate ±1 s. Stage 44 targets missing P where an original graph neighbor has PhaseNet P probability ≥0.7. Retain qualification and ambiguity/collision checks in the scripts. | Qualified P enters absolute and differential data; pick error 0.2 s plus model error 0.3 s. |
| [45_pick_station.py](03_experiments/10_added_station/45_pick_station.py), [45_associate_station.py](03_experiments/10_added_station/45_associate_station.py) | LB.DAC real three components; in-memory polyphase resampling factor 2/5, Kaiser 8.6, then baseline PhaseNet. Association probability ≥0.7; P gate ±1 s, S gate ±1.2 s; closest-event margin ≥0.2 s; reject different-event onset collisions within 0.100001 s and S≤P. | New station P/S enters the same original absolute error model and CC rules. This special resampling is not applied to baseline picking. |
| [46_qualify_eqtransformer.py](03_experiments/11_alternative_picker/46_qualify_eqtransformer.py), [47_extract_s.py](03_experiments/11_alternative_picker/47_extract_s.py) | Qualified **S-only** branch; native 100 Hz, metadata-defined 1–45 Hz bandpass; two 90 s contexts centered ±5 s around predicted arrival. S score and detection score ≥0.3, S gate ±1.2 s, context agreement ≤0.2 s; closest-event margin ≥0.2 s; collision/noncausal checks retained. Combined P/S qualification did not pass. | Added S is **relative-only** (`absolute_used=False`); its old 0.3 s pick-error metadata is not an active absolute constraint in the final solve. |

</details>

### Parameter interpretation and reproduction

<details>
<summary>Execution conventions, evaluation controls and reproduction notes</summary>

- The final velocity implementation is the archived linear 1D model, not `pending_selection` from the early general config, a regional 3D alternative, or an exact constant-layer reproduction of Shelly's table. Station-specific grid files are the operative numerical input. Grid spacing, conditional posterior samples and CC working sigma do not establish catalog accuracy.
- Full PhaseNet used **16** workers and 6 h chunks as recorded in [the completed run](export/01_baseline/02_pick_phasenet/full/run.yaml); the generic config's four-worker default describes the pilot. For frozen execution values, use the actual entry point, its run record and matching input identities together.
- Final S CC uses one joint horizontal lag. The old scalar helper's separate-horizontal lag-consistency threshold **0.03 s is not applied** by `52_measure_full_catalog.py`.
- The four stage-52 branches are absolute-only/joint × primary/withheld. The six held instruments are `CI.WBM..HH`, `CI.WHF..HH`, `CI.WMF..HH`, `CI.WOR..HH`, `NN.GWY..HH`, `NN.QSM..HH`. Withheld eligibility requires ≥10 original non-held arrivals including ≥3 S; 6,351 events qualify. Primary output retains all 6,520 events. Withheld observations assess prediction; references are never fitted.
- Current-host entry point: `bash 01_pipeline/run_52_full_catalog.sh` from the expert root. It reuses frozen upstream observations/grids and completed fits, then regenerates exports; it is not a clean-room rebuild or a read-only check. Use `python 01_pipeline/check_export_layout.py --full` for read-only verification. Commands, dependencies and grid-restoration requirements are in [EXPERT_DELIVERY.md](docs/EXPERT_DELIVERY.md) and [CLEANUP.md](docs/CLEANUP.md).

</details>

## Result and limitations

Median horizontal discrepancies decrease against Liu 0.939→0.761 km, Official 0.856→0.747 km and Shelly 0.929→0.599 km. Nominal Shelly depth discrepancy decreases 1.847→0.797 km on eligible fixed pairs. Reference catalogs are not truth.

Origin-time agreement worsens; held absolute-arrival RMS rises 0.40297→0.41073 s despite held CC RMS improving 0.14965→0.07094 s against the matched absolute-only control. Retain all 63 depth-boundary flags, heterogeneous CC support and unresolved mainshock limitations. Magnitudes are inherited at original geometry. The failed stage 51 depth safeguard remains; no independent validation or calibrated posterior is implied.

## Navigation and maintenance

Reusable professional implementations are copied into [project seismotools](../../../seismotools/README.md). Historical case scripts still resolve their recorded original tool paths; using the new snapshots in a future run requires an explicit path configuration and a new run record.


- [Delivery and reproduction](docs/EXPERT_DELIVERY.md): use this for the supported current workflow.
- [Output index](export/README.md): six purpose-based groups; stage directories are retained dependencies/evidence, not 52 active tasks.
- [Evolution and historical diagrams](docs/EVOLUTION.md): scientific decisions and branches.
- [Optimization ledger](docs/OPTIMIZATION.md) and [historical runbook](docs/RUNBOOK.md): consult only when tracing a particular experiment.

Code stays in `00_config/`, `01_pipeline/`, `02_diagnostics/`, `03_experiments/` and `04_comparison/`. `docs/` and `export/` remain unnumbered. Existing flat export aliases preserve frozen paths; no second result tree is created. Read-only delivery check: `python 01_pipeline/check_export_layout.py --full`.

Verified duplicate cleanup: [removed artifacts, storage reduction and restoration notes](docs/CLEANUP.md).
