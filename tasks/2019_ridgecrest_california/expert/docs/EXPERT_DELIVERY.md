# Ridgecrest expert delivery

## Decision and scope

The expert deliverable is the **stage 52 spatially improved joint DD candidate, accompanied by the stage 10 baseline and explicit limitations**. Parameter tuning remains closed. A subsequent user request adds the fixed full-cohort stage 53 native hypoDD CT and CT+CC comparisons; these do not automatically replace the delivery candidate. [CATALOGS.md](CATALOGS.md) defines names, paths and lineage for every main catalog product.

This is a reproducible expert workflow result, not unique ground truth, an exact reproduction of a published catalog, or a fully validated v2. The failed stage 51 depth safeguard remains part of its evidence. Retain all events and flags; apply no unsupported uniform correction and do not combine baseline origin times with candidate coordinates.

The waveform window is **2019-07-04 00:00:00 to 2019-07-07 00:00:00 UTC**, end exclusive. The master contains 9,942 original event IDs. Only the 6,520 ordinary working events were relocated in the full-scale application; the remaining 3,422 records retain baseline locations. This is not a new detection/completeness result. Figures can use narrower documented common-reference windows.

## Delivery inventory

Paths below are relative to the expert root. Files remain in place; this document is the delivery index, not a second data package.

| Deliverable | File or directory | Interpretation |
| --- | --- | --- |
| Primary spatial candidate | [working_catalog.csv](../export/06_full_catalog/52_full_catalog/working_catalog.csv) | 6,520 working events, locations, inherited magnitudes, coverage and flags |
| Complete master | [events.csv](../export/06_full_catalog/52_full_catalog/events.csv) | All 9,942 IDs, including unchanged non-working events |
| Candidate observations | [phases.csv](../export/06_full_catalog/52_full_catalog/phases.csv) | Working-event arrivals, residuals and `absolute_used`; not the full original phase master |
| Per-event quality | [event_quality.csv](../export/06_full_catalog/52_full_catalog/event_quality.csv) | CC support, observation counts, location changes and depth flags |
| Preserved baseline | [Stage 10](../export/01_baseline/10_validate_catalog/README.md) | `events.csv` and original `phases.csv` (288,431 associated observations) |
| Performance and figures | [Stage 52 report](../export/06_full_catalog/52_full_catalog/README.md) | Reference statistics, held-instrument metrics and six PNG/PDF figure sets |
| Closing diagnosis | [Time/depth review](../export/06_full_catalog/52_full_catalog/diagnostics/time_depth/README.md) | Final interpretation, support-stratified tables and diagnostic figure |
| Method provenance | Stage 52 `design.json`, `execution.json`, `comparison_audit.json`, `cc_processing/checks.json` | Existing source identities, report correction and CC reproduction evidence |

Use `event_id` and `pick_id` to join records, never row order. `v1_` fields in the master are original diagnostics, not new uncertainties. Inspect `absolute_used` before interpreting residuals: a relative-only observation is not an absolute fitting constraint. Model `depth_km` is relative to the +0.7 km elevation datum; `depth_below_sea_level_km = depth_km - 0.7`. Do not compare incompatible depth conventions silently.

## Visual preview

![Direct comparison of spatial and timing discrepancies](../export/06_full_catalog/52_full_catalog/figures/05_delivery_metric_changes.png)

**This preview evaluates stage 52 joint DD against NLL; it does not show native hypoDD results.** Gray is the original NLL baseline; blue is the delivered joint candidate. Smaller values indicate closer reference agreement: spatial differences decrease, but origin-time differences increase. The [README visual gallery](../README.md#visual-results) separates the stage 53 parallel-branch comparison (5,938 common events) from the detailed stage 52 joint-DD evaluation (6,520 working events and reference-specific subsets), including local structure, depth projections and PDFs. `Official` identifies an external reference, not the expert output.

## Effective scientific chain

The [main workflow table](../README.md#earthquake-monitoring-workflow-and-executed-parameters) is the authoritative concise overview: waveform/station preparation → PhaseNet picking → GaMMA association → NLL location and review → provisional magnitude → **6a Joint DD / 6b hypoDD CT / 6c hypoDD CT+CC (parallel)** → catalog delivery. Differential-time preparation is internal to the applicable relocation branches, not a separate numbered stage.

- **Joint DD:** case-local absolute-arrival + CC differential fit; retained primary candidate.
- **hypoDD CT:** native catalog-differential relocation from the original NLL locations.
- **hypoDD CT+CC:** native catalog + waveform-differential relocation, also from the original NLL locations.

These branches are not serial. Provisional magnitudes were computed on the baseline and inherited. Qualified observation additions are case-specific inputs; parameter trials, absolute-only controls and held-instrument tests belong to evaluation history. Their retained files remain reproduction dependencies, not additional mandatory monitoring stages.

## Reproduction on the current host

Run commands from the expert root:

```bash
cd /liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/tasks/2019_ridgecrest_california/expert
```

Environment: existing `seismoagent`, CPU only. The shell entry point explicitly uses `/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python`; selecting another active conda environment does not override it. Full-stage extraction/correlation uses 12 CPU processes and fitting uses four, with BLAS/OpenMP threads limited to one by the wrapper.

The waveform/StationXML entry point is `benchmark_source/2019_ridgecrest_california/data/waveforms` relative to the repository root; it resolves to `/ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/data/2019_ridgecrest_california/waveforms`. Baseline reconstruction also needs the local TRACE-1.1 library and picker weights, NonLinLoc binaries configured in `00_config/nonlinloc.yaml`, and the reference/model assets. Configuration paths are relative to the expert root where documented.

### A. Verify the delivered state without changing results

```bash
/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python 01_pipeline/check_export_layout.py --full
```

This checks 52 physical stage directories and their compatibility aliases, 729 original symlinks, 177 recorded stage-52 source dependencies and four fitted-result hashes. It does not rerun a solver or prove scientific accuracy. Existing legacy `export/<stage>/` aliases are required by frozen paths; VS Code hides them but they must remain. Migration details are in `export/_provenance/export_layout.json`.

### B. Replay the existing full-scale application when needed

```bash
bash 01_pipeline/run_52_full_catalog.sh
```

The wrapper skips preparation when `design.json` exists and measurement when `cc_measurements.csv` exists. Fits are reused after source checks; export/comparison processing runs again and can rewrite reports, tables and figures. Logs go to `01_pipeline/logs/52_full_catalog/`. This is a write operation, not a verification command; do not run duplicate writers or invoke it merely to inspect delivery. This documentation task did not execute it.

The frozen full-stage input/fit hashes remain authoritative for this implementation. If a source check fails, investigate the difference instead of rewriting hashes or deleting outputs to force execution. Preserve this delivery when rebuilding in a separate environment.

### C. Regenerate only the closing diagnostic tables and figure

```bash
/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python 02_diagnostics/52_review_time_depth.py
```

This reads existing catalogs and observations, writes only `export/06_full_catalog/52_full_catalog/diagnostics/time_depth/`, and runs no locator. Its README records the interpretation separately.

### Boundary of the reproduction claim

The delivered workflow supports current-host artifact verification and replay using retained inputs/caches. It is **not yet a self-contained, portable raw-waveform-to-final-catalog package**: historical absolute paths, local binaries/weights, selected observation products and shared helper modules remain dependencies. For baseline commands and historical dependency details, see [RUNBOOK.md](RUNBOOK.md); do not run every historical experiment in order. No clean-room rebuild or new scientific fit was executed for this handoff. The raw-data pipeline and original frozen provenance must be preserved when planning any future independent rebuild.

## Measured level and limitations

| Fixed comparison | Baseline | Candidate |
| --- | ---: | ---: |
| Median horizontal difference to Liu, 4,497 pairs | 0.939 km | 0.761 km |
| Median horizontal difference to Official, 3,961 pairs | 0.856 km | 0.747 km |
| Median horizontal difference to Shelly, 4,401 pairs | 0.929 km | 0.599 km |
| Median nominal depth difference to Shelly, 4,377 eligible pairs | 1.847 km | 0.797 km |
| Held CC RMS, matched absolute-only vs joint controls | 0.14965 s | 0.07094 s |
| Held absolute-arrival RMS, same controls | 0.40297 s | 0.41073 s |

Reference identities are fixed; references are not truth. Shelly depth scoring retains the existing 0–40 km eligibility convention; 24 out-of-range reference depths remain in horizontal/time comparisons. Ross provides spatial context, not a frozen paired score.

- Origin-time absolute differences worsen against Liu (0.287 -> 0.377 s), Official (0.190 -> 0.267 s) and Shelly (0.197 -> 0.252 s), despite spatial gains.
- 5,780 of 6,520 events have accepted CC; 740 do not. 905 have CC at only 1–2 instruments. Additional-pick coverage is heterogeneous.
- All 63 depth-boundary flags remain, including well-supported and weakly supported events. They are safeguards, not manual error labels. No newly calibrated location posterior is claimed.
- Magnitudes retain the original geometry/estimation limitations; they were not recomputed at candidate locations. Mainshock uncertainties remain unresolved.
- Stage 51 failed the depth gate. Stage 52 and the closing diagnosis are exposed full-scale evaluation, not fresh independent confirmation. No threshold was relaxed to declare success.

## Use as the expert benchmark result

Use the candidate, baseline, observation identities and caveats together as the expert result. Keep this directory, reference comparisons and historical outcomes on the evaluation side rather than exposing them as raw task inputs to an agent. An agent need not reproduce the exploratory history or match expert coordinates exactly to be scientifically successful. Future evaluation should distinguish event coverage, absolute prediction, differential prediction, reference agreement and uncertainty reporting.

The stage 52 handoff remains the retained local expert result. Stage 53 supplements it with fixed native double-difference comparisons. Picking, parameter scanning and uniform corrections are outside this extension.

## Storage maintenance after handoff

Verified duplicate cleanup removed 112,418 redundant native convenience files and replaced 33 identical model buffers with relative links, preserving the delivered scientific contents. See [CLEANUP.md](CLEANUP.md) for the audit and the required restoration of independent model outputs before deliberately rerunning historical grid generators. Current frozen replay reads the retained files and remains supported.

## Native double-difference completion (stage 53)

This is an independent, fixed comparison extension, not a new tuning campaign.
Run from the expert root:

```bash
bash 01_pipeline/run_53_native_double_difference.sh
```

The two independent native branches run concurrently, one CPU process each.
Stages can be replayed separately with `--stage prepare`, `--stage locate`, or
`--stage report`. Inputs reuse stage 52 picks, pair identities and measured CC.
The two native branches start from original NLL coordinates and use unchanged
historical control files. Native array capacities are rebuilt for the full cohort;
no scientific Fortran routines are changed. Input fingerprints and capacities are
recorded in stage 53 `design.json` and `native/build.json`.

Wrapper logs are in `01_pipeline/logs/53_native_double_difference/`. Native solver
logs remain beside their native inputs and outputs within each branch. See the
[stage 53 report](../export/06_full_catalog/53_native_double_difference/README.md)
for event retention, same-event reference metrics and comparison figures. Raw
native magnitudes are placeholders and are omitted from the exported catalogs.
The retained joint DD candidate and baseline are unchanged.

Completed stage 53: native CT retains **5,960** events and CT+CC **5,997**, with **5,938** common IDs across NLL, joint DD and both native catalogs. The joint DD candidate retains better horizontal reference agreement and full working-event coverage; native CT+CC improves origin-time agreement on these matches. Preserve both methods and their limitations rather than mixing their coordinates and times. Quantitative values and figures are in the stage 53 report linked above.

## Archived execution settings

The detailed table below preserves the executed settings previously expanded in the root README. It is a reproduction record, **not the production step sequence**: observation additions and controls describe case-specific development, and the two native methods are parallel alternatives to joint DD. For the consolidated workflow and separate CT/CT+CC branches, use the [main workflow table](../README.md#earthquake-monitoring-workflow-and-executed-parameters).

| Step | Program / entry point | Key executed settings | Input → output |
| --- | --- | --- | --- |
| **1. Input preparation** | [01_prepare_inputs.py](../01_pipeline/01_prepare_inputs.py); [config.yaml](../00_config/config.yaml) | Full three-day scope; original baseline uses 37 simultaneous three-component HH/EH instruments. Check metadata epochs, sample-grid and component compatibility; rotate to ZNE with StationXML orientation. No invented components or gap filling. | Archived waveform files + StationXML → full waveform/station input tables in stage 01 |
| **2a. Phase picking** | **PhaseNet**, local TRACE-1.1/SeisBench implementation; [02_pick_phasenet.py](../01_pipeline/02_pick_phasenet.py) | `original` v2 weights; P/S thresholds **0.3/0.3**; actual 100 Hz input; model-provided normalization/overlap/blinding. **6 h blocks, 60 s buffers, 16 CPU processes × 1 thread**, batch size 32. Raw counts: no response removal, extra filter or baseline resampling. | Real ZNE components → **411,891 picks** (192,900 P; 218,991 S), stage 02/full |
| **2b. Event association** | **GaMMA BGMM**; [03_associate_gamma.py](../01_pipeline/03_associate_gamma.py); [association.yaml](../00_config/association.yaml) | **1 h blocks + 120 s buffers; 32 processes**. No amplitude input. DBSCAN `eps=10 s`, `min_samples=3`; oversampling 5; covariance prior `[3]`; `max_sigma11=1.5`. Minimum **10 picks, 4 P, 3 S, 6 stations**. Linear Shelly-derived model, 0.5 km eikonal grid; lon [−118.15, −116.95], lat [35.20, 36.30], depth [0,25] km. | Picks + stations → **9,942 initial events and 288,431 associated picks**, stage 03/full; unassociated picks retained separately |
| **3a. Absolute location** | **NonLinLoc 7**, `Vel2Grid`, `Grid2Time`, `NLLoc`; [04_locate_nonlinloc.py](../01_pipeline/04_locate_nonlinloc.py); [nonlinloc.yaml](../00_config/nonlinloc.yaml) | Retained **linear 1D** velocity fields with receiver elevation/burial; grid spacing **0.25 km**, vertical extent −3 to 35 km; event search depth 0–25 km. `GAU_ANALYTIC`; oct-tree minimum node 0.1 km, maximum 50,000 nodes; 2,000 posterior samples. Pick errors **P 0.10 s / S 0.20 s**, model error **0.30 s**; 32 processes, 180 s/event timeout. | Associated events/picks → original NLL locations, residuals and conditional uncertainty diagnostics, stage 04 |
| **3b. Review and baseline selection** | [05_review_catalog.py](../02_diagnostics/05_review_catalog.py), [10_validate_catalog.py](../01_pipeline/10_validate_catalog.py); [validation.yaml](../00_config/validation.yaml) | Require NLL `LOCATED`; review flags: depth <0.5 or >24.5 km; azimuth gap >180°; conditional depth sigma >3 km; horizontal locator shift >2 km; unweighted RMS >0.6 s. Association review when residual outliers >1 s number ≥3 **and** fraction ≥20%. Working set: provisionally usable, inside lon [−117.90,−117.20]/lat [35.45,36.05], excluding the two mainshocks. These are descriptive safeguards, not truth labels. | NLL output → complete baseline master and **6,520-event working selection**; no discarded master IDs |
| **3c. Provisional local magnitude** | **ObsPy** response removal + Wood–Anderson simulation; [09_estimate_magnitude.py](../01_pipeline/09_estimate_magnitude.py) | Horizontal components; remove response to velocity, prefilter **[0.1,0.2,20,25] Hz**, `water_level=None`; WA magnification **2080**. Window P−0.5 s to P−0.5+2(S−P); S−P **0.5–30 s**, epicentral distance ≤100 km, hypocentral distance ≥10 km, paired phase residuals ≤0.5 s. SNR ≥3; accept event ML with ≥3 station estimates and station MAD ≤0.5; 6 workers. Formula and aggregation below. | Baseline events + raw waveforms + responses → provisional ML and support flags, stages 09/10; candidate inherits these values |
| **4. Qualified observation additions** | **DPP SCEDC vertical-P**, added-station **PhaseNet**, S-only **EQTransformer original_nonconservative v1**; [retained settings below](../README.md#retained-observation-additions) | Reuse already-admitted observations from stages 42, 44–48 and 50/51. Preserve original picks/associations. Added EQTransformer S is **differential-only**, never an absolute constraint in the final fit. Coverage is heterogeneous; no full-scale repicking in stage 52. | Original phases + qualified missing P, LB.DAC picks and extra S → stage 52 `inputs/all_phases.csv` |
| **5a. Event-pair graph** | [52_prepare_full_catalog.py](../01_pipeline/52_prepare_full_catalog.py), [_confirmation.py](../03_experiments/15_confirmation/_confirmation.py) | Union nearest-neighbor, original/augmented shared-support and depth-envelope proposals, plus existing stage 50/51 pairs. **3 km** distance screen; up to **12 neighbors per event per proposal rule**, not a global degree cap. Depth-envelope rule uses original mean ±2 conditional sigma, clipped to 0–25 km, plus horizontal distance. Edge eligibility: ≥6 shared phase/instrument keys at ≥4 instruments; original CC candidate probability ≥0.5, qualified additions admitted separately. | 6,520 original working IDs + original coordinates/uncertainties + phases → **139,343 pairs / 3,562,868 candidate edges** |
| **5b. Waveform differential timing** | [52_measure_full_catalog.py](../01_pipeline/52_measure_full_catalog.py); scalar extraction helper [13_hypodd_cc_pilot.py](../03_experiments/02_relative_location/13_hypodd_cc_pilot.py) | **100 Hz**, bands **2–8 and 2–12 Hz**, 3-corner zero-phase bandpass after detrend/5% taper. Pick-relative windows: P **[−0.2,1.0] s**, S **[−0.3,1.5] s**. Lag limits P ±0.3 s/S ±0.4 s. Both bands require positive CC ≥0.75, SNR ≥2, peak margin ≥0.08 outside an 0.08 s exclusion neighborhood, lag agreement ≤0.020001 s; reject peaks within one sample of the lag limit. P uses Z; S uses noise-normalized two-horizontal-component **joint** correlation. 12 CPU processes. | Real common waveform windows → **294,943 accepted CC edges**, supporting 5,780 events; arrival difference = pick-time difference − measured lag |
| **6a. Joint double-difference location** | Case-local sparse **SciPy least_squares**, [52_run_full_catalog.py](../01_pipeline/52_run_full_catalog.py) → [48_run.py](../03_experiments/12_differential_augmentation/48_run.py) / [37_robust_cc.py](../03_experiments/07_joint_location/37_robust_cc.py) | Same retained 1D grids for absolute and differential terms. Absolute sigma: P √(0.1²+0.3²)=**0.316 s**, S √(0.2²+0.3²)=**0.361 s**; added DPP P uses **0.361 s**. Quadratic absolute loss; CC sigma **0.05 s**, Huber **δ=1.345** on standardized CC residuals. Depth bounds 0–25 km; origin adjustment ±10 s. `tr_solver=lsmr`, `x_scale=jac`, `max_nfev=250`, `ftol=xtol=1e−8`, `gtol=1e−6`; LSMR `atol=btol=1e−8`, `maxiter=2000`. Four matched branches, four processes. | Original working locations + absolute picks + accepted CC → joint candidate and absolute-only/withheld controls; all working IDs retained |
| **6b. Native double-difference comparison** | Native **hypoDD**, [53_native_double_difference.py](../01_pipeline/53_native_double_difference.py); [run_53_native_double_difference.sh](../01_pipeline/run_53_native_double_difference.sh) | Same 6,520 NLL initial events and stage 52 pair graph; CT excludes relative-only EQ S. All stations used. Fixed historical controls: LSQR **4+8 iterations**, damping **80/40**, CT P/S **1/0.5**, CC P/S **3/1.5**, CC quality **CC²**. Constant Shelly layers, Vp/Vs **1.73**, no native receiver elevation; native time precision **0.01 s**. No parameter search. | Two independent retained-event catalogs, membership/exclusion table and same-event reference comparisons; does not overwrite joint candidate |
| **7. Export, evaluate and close** | [52_compare_full_catalog.py](../04_comparison/52_compare_full_catalog.py); [52_review_time_depth.py](../02_diagnostics/52_review_time_depth.py) | Keep original fixed unambiguous reference matches (primary matching **2 s / 5 km**, no depth gate); no outcome-dependent rematching. Shelly depth scoring restricted to existing 0–40 km reference eligibility. Compare all primary events; held-instrument metrics are separate. Preserve depth/coverage flags, original magnitude geometry and timing limitations. | **6,520-event candidate + 9,942-event master**, phase/quality tables, reference metrics, maps/depth sections and closing diagnosis |
