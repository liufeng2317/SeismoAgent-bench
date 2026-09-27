# Ridgecrest expert runbook

Historical execution details and stage outcomes through stage 16. Run all commands from the expert root, not from this docs directory. For current decisions and product status, use [the workflow overview](../README.md) and [the evolution and organization plan](EVOLUTION.md). Stage numbering records execution history, not a catalog version sequence.

Entry points now live in the numbered responsibility directories; all commands below run from the expert root. Outputs now live under the [grouped export layout](../export/README.md). Historical `export/<step>/` paths remain compatibility symlinks; existing entry points and frozen manifests continue to work. Logs remain beside the scripts. Keep these outputs locally until explicitly cleaned up; no automatic cleanup is performed. Raw observations are read from the configured source archive without copying or rewriting them.

For the completed deliverable and the short supported replay path, start with [EXPERT_DELIVERY.md](EXPERT_DELIVERY.md). The detailed commands below include historical development and are not a mandatory execution sequence.

## Baseline and stage layout

| Script | Output directory | Responsibility | Status |
| --- | --- | --- | --- |
| `01_pipeline/01_prepare_inputs.py` | `export/01_baseline/01_prepare_inputs/` | Index pilot/full waveform files, channels and metadata | Implemented and run |
| `01_pipeline/02_pick_phasenet.py` | `export/01_baseline/02_pick_phasenet/` | Component preparation, PhaseNet inference, picks and a few diagnostic plots | Implemented; pilot and full three-day picking completed |
| `01_pipeline/03_associate_gamma.py` | `export/01_baseline/03_associate_gamma/` | Arrival-time association and initial event locations | Implemented; pilot and full three-day association completed |
| `01_pipeline/04_locate_nonlinloc.py` | `export/01_baseline/04_locate_nonlinloc/` | Travel-time grids, absolute locations and location uncertainty | Implemented; pilot and full three-day absolute locations completed |
| `02_diagnostics/05_review_catalog.py` | `export/01_baseline/05_review_catalog/` | Fixed reference pairs, eight waveform examples and provisional quality flags | Implemented and run |
| `02_diagnostics/06_diagnose_depth.py` | `export/01_baseline/06_diagnose_depth/` | Common-objective depth profiles and one velocity-representation sensitivity test | Implemented; 8 diagnostic and 100 validation events completed |
| `02_diagnostics/07_audit_mainshocks.py` | `export/01_baseline/07_audit_mainshocks/` | Original layer semantics, official arrival comparison and mainshock onset review | Implemented; two events, 28 controlled fits |
| `03_experiments/01_strong_motion/08_check_strong_motion.py` | `export/01_baseline/08_check_strong_motion/` | Six-station HN response processing, S-pick stability and bounded location check | Implemented; no HN pick admitted |
| `01_pipeline/09_estimate_magnitude.py` | `export/01_baseline/09_estimate_magnitude/` | Ordinary-event working catalog, response-corrected amplitudes and provisional ML | Implemented; 6,628 ordinary events attempted, 2,086 provisional ML |
| `01_pipeline/10_validate_catalog.py` | `export/01_baseline/10_validate_catalog/` | Frozen-scope reference comparisons, four waveform cases and provisional v1 export | Implemented and run |

Only implemented scripts are created. Later absolute-location methods can consume the same associated-pick table in separate stages; do not overwrite the NonLinLoc result. Each event must retain stable links to its contributing picks.

## Method choice

There is no single universal expert picker. Use **PhaseNet → GaMMA → NonLinLoc** as the first reproducible baseline, rather than implementing several competing pipelines at once.

- **PhaseNet:** a suitable starting point given its documented Ridgecrest application and existing local weights. The proposed first weight set is the SeisBench-converted `original`, version 2; its metadata specifies three ENZ components, 100 Hz, and standard-deviation normalization. Strict weight loading and a short-window inference test have passed; this does not establish exact numerical equivalence to the original TensorFlow implementation. Other local weights (e.g. SCEDC, STEAD or offshore SNet) are distinct models and must not be substituted silently. Do not claim exact reproduction of Liu's published configuration.
- **GaMMA:** associate picks and estimate initial locations. Initially disable amplitude information so uncalibrated HH/EH/HN counts do not enter a shared physical-amplitude model.
- **NonLinLoc:** perform a separate absolute-location stage on the associated picks, with explicit velocity model, travel-time grids, phase errors, coordinates and depth datum. It does not replace phase association. Treat GaMMA and NonLinLoc locations as successive, separately preserved products.
- Other pickers or absolute locators may be compared after this baseline works. Relative relocation is optional later work.

Primary references: [PhaseNet](https://github.com/AI4EPS/PhaseNet), [GaMMA](https://github.com/AI4EPS/GaMMA), [NonLinLoc](https://github.com/ut-beg-texnet/NonLinLoc).

## Current local readiness

The PhaseNet step uses the existing **seismoagent** conda environment: PyTorch 2.8.0, SeisBench 0.9.0 and ObsPy 1.4.2. It imports the PhaseNet class from the configured **TRACE-1.1** library, loads local `original.pt.v2` weights with strict key matching, and applies the accompanying metadata/default arguments. No package installation or model download is required. The reference example's unconditional NPU import is not copied into this CPU-only runner.

GaMMA's local source checkout declares version 1.2.17 and its association function imports successfully when that checkout is added to the Python path. It is not installed as `gamma` in the default environment. The local NonLinLoc 7.00 `NLLoc`, `Vel2Grid` and `Grid2Time` executables have now passed the stage-04 pilot and numerical checks. No environment packages were changed. Executable/model paths and fingerprints are recorded in the corresponding stage outputs.

## First pilot

From this directory, using the `seismoagent` environment:

```bash
python -B 01_pipeline/01_prepare_inputs.py
```

The current pilot is 2019-07-04 16:00–16:10 UTC, within the three-day candidate window. Step 01 indexes all 117 channel-file entries at 41 stations. The first three-component baseline has 37 HH/EH instruments. CI.APL (HN acceleration) and CI.WNM/WRV2/WVP2 (vertical-only EH) remain visible in the tables but are deferred to explicit later input conditions; this is not a declaration of bad data. Use StationXML to rotate numbered horizontal components; never copy vertical data into missing horizontals. Confirm simultaneous component coverage during stage 02.

The stage reuses existing metadata and checks file existence/size, response presence, and epoch/rate compatibility. It does not repeat full waveform QC, preprocess samples, use reference event catalogs, or freeze benchmark inputs. Step 02 consumes these tables and writes picks, probabilities, prepared waveforms and an overlay in its own export directory.

`export/` is ignored by Git because intermediate waveforms and model outputs may be large. Keep this entire expert directory outside agent-visible task inputs.

## Run the CPU PhaseNet pilot

```bash
conda activate seismoagent
python -B 01_pipeline/01_prepare_inputs.py
python -u -B 01_pipeline/02_pick_phasenet.py > export/01_baseline/02_pick_phasenet/run.log 2>&1
```

Create `export/01_baseline/02_pick_phasenet/` before shell log redirection if it does not yet exist (`mkdir -p export/01_baseline/02_pick_phasenet`). All stage outputs stay in this folder. The runner uses a persistent process pool: **4 station workers × 1 compute thread**, configured by `picking.cpu_workers` and `picking.cpu_threads`. Each worker loads one model once; OpenMP/BLAS and PyTorch thread counts are bounded to avoid oversubscription. Execution order can differ, but final picks are sorted deterministically. No CUDA or NPU path is used. Startup and file I/O may dominate this short pilot; no speedup factor is assumed.

Thresholds start at 0.3 for P and S, with weight-specified overlapping windows and edge blinding. The input buffer is 60 seconds on each side; only picks inside the configured target window are exported. Three real components are intersected on the same 100 Hz grid and rotated using metadata. No gap filling, synthetic components, extra filtering, response removal or reference catalog input is applied. Non-matching sample grids fail explicitly. Probabilities and picks are obtained from one annotation pass followed by the model's classification aggregation.

The initial serial attempt's outputs and error log are retained under `export/01_baseline/02_pick_phasenet/serial_attempt/` for numerical comparison. Its inference completed but metadata serialization failed; the parallel runner fixes that serialization. This is temporary local evidence, not a second official result.

### Pilot outcome

The 2019-07-04 16:00–16:10 UTC pilot completed for all 37 selected instruments: **34 picks (14 P, 20 S)**. Serial and four-worker runs produced identical station/phase/arrival-time identities; the maximum probability difference was approximately 1.2e-7. The saved overlay shows three stations around a common picked signal. These checks verify execution consistency, not catalog completeness or pick accuracy. This pilot is a picking-only product. Main outputs: `export/01_baseline/02_pick_phasenet/picks.csv`, `pick_example.png`, and `run.yaml`.

## Full three-day picking

```bash
conda activate seismoagent
python -B 01_pipeline/01_prepare_inputs.py --scope full
mkdir -p export/01_baseline/02_pick_phasenet/full
python -u -B 01_pipeline/02_pick_phasenet.py --scope full --workers 16 --chunk-hours 6 > export/01_baseline/02_pick_phasenet/full/run.log 2>&1
```

Full scope is `[2019-07-04, 2019-07-07)` UTC: the same 37 three-component HH/EH instruments, 444 instrument/time blocks, with 60-second buffers. Input tables are in `export/01_baseline/01_prepare_inputs/full/`; merged picks, summaries, restart records and logs are in `export/01_baseline/02_pick_phasenet/full/`. Full inference exports picks only, preserving the pilot waveforms/probabilities in their original directory. Repeating the same command resumes verified completed blocks; changed data, code, configuration or weights require a separate export root. Do not run two writers in the same output directory.

For association, use `export/01_baseline/02_pick_phasenet/full/picks.csv` and the corresponding station metadata table. A successful `run.yaml` must report all expected blocks completed. Picks remain unassociated arrivals; gaps, blinded edges and excluded input conditions prevent interpreting this output as complete seismicity.

### Full-run outcome

Completed all 444 blocks at 37 instruments with 16 CPU workers in 315.84 seconds (inference, merging and checks). Produced **411,891 picks: 192,900 P and 218,991 S**. All IDs and station/location/family/phase/time identities are unique; times are sorted and inside the candidate interval, and probabilities satisfy the configured thresholds. No exact duplicate picks or <=0.1 s same-phase pairs across block boundaries were found. No picks fall inside the known CI.WRC2 three-component coverage gap. These are consistency checks, not pick-accuracy validation.

Daily pick totals (UTC): 2019-07-04: 52,419, 2019-07-05: 156,764, 2019-07-06: 202,708. The four deferred stations remain outside this baseline. Next stage: GaMMA arrival-time association.

## GaMMA association

Stage 03 reads the full PhaseNet pick table and the matching station metadata. Settings are isolated in `association.yaml` so the frozen picking configuration is unchanged.

```bash
conda activate seismoagent
mkdir -p export/01_baseline/03_associate_gamma/pilot export/01_baseline/03_associate_gamma/full
python -u -B 01_pipeline/03_associate_gamma.py --scope pilot > export/01_baseline/03_associate_gamma/pilot/run.log 2>&1
python -u -B 01_pipeline/03_associate_gamma.py --scope full > export/01_baseline/03_associate_gamma/full/run.log 2>&1
```

The pilot covers a quiet window and windows near both mainshocks. Full processing uses one-hour origin-time blocks, 120-second pick buffers and 32 CPU processes. Completed blocks are reusable only with identical input/code/settings fingerprints. Outputs include `events.csv`, the complete phase table `picks.csv` with event links/status/residuals, `stations.csv`, overlap-reconciliation records, and `run.yaml`. Published event catalogs are not association inputs.

The initial travel-time model uses the Shelly numeric profile with GaMMA's linear interpolation and approximate station-elevation treatment; these conventions and the 0.7-km reference elevation are documented in the result README. Minimum support is 10 picks (at least 4 P, 3 S), from 6 stations. This produces an initial catalog for NonLinLoc, not final locations or magnitudes. The library's assignment scores are omitted due to an indexing problem in the local implementation; original PhaseNet probabilities remain available.

### Association pilot outcome

After including sensor burial depth, the quiet/M6.4/M7.1 windows contain 1/30/44 initial events, respectively (75 total, 2,231 assigned picks). Median event RMS is 0.351 s and median station count is 17. Twenty events are within 0.5 km of a depth bound and remain explicitly flagged. No duplicate event/instrument/phase assignments were found. Pilot unassociated totals include picks outside the development windows and must not be interpreted as a detection rate. Earlier attempts using site elevation without sensor burial depth are retained under `export/01_baseline/03_associate_gamma/*_before_sensor_depth/`; they are not current results.

### Full association outcome

All 72 hourly blocks completed with 32 CPU workers in **2,703.56 seconds (45.1 minutes)**, including merging and built-in checks. The initial catalog contains **9,942 events** with **288,431 associated picks**; **123,460 picks** remain explicitly unassociated. No shared-pick duplicate candidates or conflicting pick assignments were found. Median event RMS is **0.357 s**, with a median of **16 stations** per event.

Independent checks verified all 411,891 pick IDs, unique event/instrument/phase assignments, event support counts, UTC bounds, finite residuals and the depth-datum conversion. All 72 checkpoints were readable and block logs contained no ConvergenceWarning messages. These are execution/consistency checks, not accuracy validation. **2,414 events are within 0.5 km of a depth bound** and remain flagged for NonLinLoc review; the GaMMA catalog is an initial association product, not the final expert catalog. No magnitudes have been estimated. Current products are `export/01_baseline/03_associate_gamma/full/events.csv`, `picks.csv`, `stations.csv`, `run.yaml`, and the result README.

## Visual inspection of the initial association

Run `python 04_comparison/03_plot_association.py` in the seismoagent environment. It writes three PNG/PDF figures under `export/01_baseline/03_associate_gamma/full/figures/`: whole-catalog spatial/depth/time distributions, aggregate association diagnostics, and three reproducibly selected event moveout/station-geometry examples. Selection rules, depth conventions, interpretation limits and example IDs are documented alongside the figures. The shallow-bound concentration (2,327 events within 0.5 km of the adopted reference surface) requires review; good residuals alone do not validate depth or association accuracy.

## NonLinLoc absolute locations

Stage 04 preserves the full GaMMA event/pick associations and uses `nonlinloc.yaml`. It builds receiver-specific P/S travel-time grids, including sensor burial, then runs independent CPU-parallel absolute locations. It does not perform double-difference relocation or assign new picks.

```bash
conda activate seismoagent
python -u 01_pipeline/04_locate_nonlinloc.py --scope pilot
mkdir -p export/01_baseline/04_locate_nonlinloc/full
python -u 01_pipeline/04_locate_nonlinloc.py --scope full > export/01_baseline/04_locate_nonlinloc/full/run.log 2>&1
python 04_comparison/04_plot_nonlinloc.py
```

Outputs are in `export/01_baseline/04_locate_nonlinloc/`: `full/events.csv`, `full/picks.csv`, per-event native products, travel-time grids, execution records and paired comparison figures. The output README documents coordinates, depth datum, phase/model errors, status flags and the limitations of posterior uncertainties. Use CSV longitude/latitude: native `TRANS NONE` geographic fields contain projected coordinates. This remains an intermediate location catalog; neither `LOCATED` nor a smaller residual certifies event accuracy.

### Absolute-location outcome

Processed all **9,942 events and the same 288,431 associated picks**: 9,879 `LOCATED`, 63 boundary `REJECTED`, zero execution failures. Rejected solutions remain explicit and are not accepted catalog entries. Median horizontal change from GaMMA is 0.444 km; median absolute depth change is 0.459 km.

Events shallower than 0.5 km decrease from 2,327 to 2,042, but the boundary concentration remains. Median **unweighted** event RMS changes from 0.357 s (GaMMA) to 0.367 s (NonLinLoc); the results do not establish improved accuracy. Conditional posterior depth standard deviation has median 1.40 km and excludes velocity-model/association uncertainty. See `export/01_baseline/04_locate_nonlinloc/full/figures/01_location_comparison.png` (also PDF) and `full/comparison.yaml` for the complete comparison. All event/pick links, positive phase weights, finite outputs and depth bounds passed verification; a noiseless synthetic check recovered location within 0.05 km horizontally and 0.01 km vertically.

## Initial reference and waveform review

Run `python -u 02_diagnostics/05_review_catalog.py` in `seismoagent`; settings are in `validation.yaml`, outputs in `export/01_baseline/05_review_catalog/`. The primary comparison uses fixed one-to-one reference identities for both locators, explicit candidate ambiguity, and a shared time/geographic slice without a depth-matching gate. Tighter/wider gates are reported separately. Native depth-datum limitations are preserved.

All 9,942 events receive **provisional numerical flags**: 6,628 provisionally usable, 3,120 location review and 194 association review, with native rejection status retained separately. Eight purpose-selected waveform examples were inspected, including both mainshocks. Neither unmatched events nor shallow events are automatically deleted. These are not ground-truth labels.

The current NonLinLoc run has larger median horizontal differences from all three references than GaMMA; both mainshock candidates remain at the shallow depth bound. Retain both products, and avoid adopting NonLinLoc globally as final locations. See the [review report](../export/01_baseline/05_review_catalog/README.md), [quality table](../export/01_baseline/05_review_catalog/event_quality.csv) and [comparison](../export/01_baseline/05_review_catalog/figures/01_reference_and_quality.png). Response-based magnitude estimation remains separate; no response correction or catalog alteration was performed during this review.

## Controlled depth diagnostic

Stage 06 uses `depth_diagnostic.yaml`, unchanged associated picks, receiver-specific travel times and common phase/model errors. Run the following in `seismoagent` from this directory:

```bash
python -u 02_diagnostics/06_diagnose_depth.py --stage diagnose
python -u 02_diagnostics/06_diagnose_depth.py --stage control
python -u 02_diagnostics/06_diagnose_depth.py --stage validate
python -u 02_diagnostics/06_report_depth.py
```

The report companion performs numerical consistency checks and compares existing, unambiguous reference pairs without rematching. Eight diagnostic events have 0–25 km depth profiles; 100 additional events form a frozen, equally stratified validation sample. Eight CPU workers are used. Published reference locations do not enter fitting. This is not a new full-catalog location product.

Multistart refinement reproduces the original travel times and leaves both mainshocks at the shallow bound under the linear model. Changing only the velocity representation to piecewise constant moves M6.4 to 16.8 km but leaves M7.1 at 0 km. Validation is mixed: 55/100 events improve weighted fit, while median chi-square increases and the median absolute Shelly depth difference increases. **Do not adopt the layered representation globally.** Preserve both original catalogs; see the [experiment report](../export/01_baseline/06_diagnose_depth/README.md), [depth profiles](../export/01_baseline/06_diagnose_depth/depth_profiles.png), and [paired table](../export/01_baseline/06_diagnose_depth/comparison.csv).

## Mainshock model and arrival audit

Stage 07 verifies the original Shelly table against standard hypoDD layer semantics: layer-top depths and constant layer velocities. The previous linear interpolation is an expert model variant, not a direct implementation of that table. The author's exact input and elevation convention remain unverified.

```bash
python -u 02_diagnostics/07_audit_mainshocks.py --stage audit
python -u 02_diagnostics/07_audit_mainshocks.py --stage fit
python -u 02_diagnostics/07_audit_mainshocks.py --stage strong_motion
```

Official SCEDC arrivals are isolated diagnostic references. They are never written into the PhaseNet pick table or the full catalog. The audit covers every assigned arrival of both mainshocks, retains same-instrument versus cross-instrument comparisons, and tests onset definitions and phase selection separately under each velocity representation. Only two additional two-minute HN waveform windows are retrieved, into this stage's export directory.

M7.1 remains at the depth bound in all fourteen controlled fits, including official times on the strictly matched subset. Its official 8-km depth is explicitly operator-assigned, with reported 31.61-km uncertainty. Existing HH/EH inputs omit most strong-motion channels used for the official S arrivals. See the [focused report](../export/01_baseline/07_audit_mainshocks/README.md) for observed timing differences, waveform limitations and the bounded next action. Neither a global timestamp shift nor wholesale phase reassignment is justified.

## Short-window HN branch

Stage 08 prepares six M7.1 HN station windows and epoch-specific responses, converts acceleration records to velocity, and runs the unchanged PhaseNet model with two fixed frequency tapers. A same-window HH control separates input changes from processing-window effects. Run `03_experiments/01_strong_motion/08_check_strong_motion.py --stage prepare`, `--stage pick`, then `--stage assess` in `seismoagent`.

All 36 HH/HN component records pass the input checks. Four HH S picks agree with the original catalog within 0.02 s, but **none of the six stations produces an HN S candidate that meets the two-preprocessing stability rule**. WRC2 has only a band-limited candidate, 1.408 s later than the official S time. No HN picks enter the catalog or a modified-observation location run. Keep the mainshock depth unresolved and avoid expanding this into whole-catalog tuning. See the [HN report](../export/01_baseline/08_check_strong_motion/README.md) and [waveform/probability comparison](../export/01_baseline/08_check_strong_motion/figures/s_onsets_01.png).

## Ordinary-event catalog and local magnitude

Run `python -u 01_pipeline/09_estimate_magnitude.py --limit 24 --workers 6` for the isolated pilot, then omit `--limit` for all eligible events. The script preserves all 9,942 event identities, existing location/association flags and both location products. Both mainshocks retain explicit unresolved-depth/arrival/waveform flags and deferred ML. Only stage-05 provisionally usable ordinary events enter this first amplitude pass; all other events remain visible with reasons. This is a provisional expert product, not manual labels.

Use epoch-valid responses to convert horizontal counts to velocity, then simulate Wood–Anderson with magnification 2080 and rotate to N/E. Measure zero-to-peak amplitudes in a short associated-P/S window; require complete padded coverage, acceptable noise, no overlapping associated S in the signal/noise windows, and no raw extreme plateau. Hutton–Boore (1987) gives `ML = log10(A_mm) + 1.11 log10(R_km/100) + 0.00189(R_km-100) + 3`. Average component ML and take the station median; require at least three accepted stations and station MAD <=0.5 for provisional status. No reference-derived station correction or offset is fitted. Reference magnitudes have mixed scales, so comparison is descriptive.

Current NLL geometry supplies distances only for this product; same-amplitude GaMMA-distance magnitudes expose geometry sensitivity. Neither locator is newly declared final. The output [method report](../export/01_baseline/09_estimate_magnitude/README.md) specifies windows, units, filtering, selection and limitations. `catalog.csv` preserves every event; `ordinary_events.csv` contains the provisionally usable ordinary-event working subset; `station_magnitudes.csv` preserves accepted and rejected measurements. Raw observations and earlier outputs remain unchanged.

The first full magnitude pass measured 60,903 event/instrument pairs at 36 instruments. Of 6,628 working ordinary events, **2,086** meet the provisional ML support/dispersion criteria, **1,531** retain estimates requiring magnitude review, and **3,011** have no accepted amplitude. Another 3,312 location/association-review candidates and both unresolved mainshocks remain in the 9,942-row master table. Measurement noise and coda selection are substantial: this magnitude subset is not suitable for inferring catalog completeness or b-values.

## Provisional expert reference v1

Run `python -u 01_pipeline/10_validate_catalog.py` in `seismoagent`. Outputs are in `export/01_baseline/10_validate_catalog/`: `events.csv` retains all 9,942 candidates and explicit region/quality/magnitude flags; `phases.csv` retains all 288,431 associated picks. The study-region working subset has 6,520 ordinary events, including 2,052 provisional ML estimates. Filter `in_v1_working_catalog` explicitly; do not treat every master-table row as accepted. The new `magnitude` column is blank for review-only estimates, whose candidate values remain in `ml_provisional`.

Comparisons reuse the frozen stage-05 cohort and pairs, preserving ambiguity, and report time/region/reference-magnitude strata. They use a different cohort from the newly bounded working subset. ML differences use only reference rows with an established ML type. Four deterministic diagnostic cases have six-station waveform figures and source-window records; their inspection does not constitute manual true/false labels. Mainshock and velocity-model uncertainties persist. See the [v1 report](../export/01_baseline/10_validate_catalog/README.md). Ross is not yet part of these inherited comparisons. Further scientific changes should produce a separate version.

## Direct spatial comparison

Run `python -u 04_comparison/11_plot_catalog_maps.py` in `seismoagent`. The [map report](../export/02_diagnostics/11_plot_catalog_maps/README.md) and two six-panel PNG/PDF figures explicitly separate **Ours: GaMMA / NonLinLoc** from Official, Liu, Shelly and Ross references. The figures show all candidates and the stage-10 ordinary working subset separately, with common axes, point styles and the shared July 4 15:35:29.4–July 7 UTC window. Ross uses only `nbranch > 1` relocations. Plotted event identities, source coverage and selection counts are exported; this does not add Ross to the existing paired validation or alter expert v1.

## Catalog differential-time pilot

Run `python -u 03_experiments/02_relative_location/12_relative_location_pilot.py` in `seismoagent`. The isolated [stage-12 report](../export/03_location_experiments/01_relative_location/12_relative_location_pilot/README.md) tests a fixed local cohort using the existing NonLinLoc receiver grids and unchanged picks. This custom grid-based solver is not hypoDD. Six instruments are withheld from incremental fitting; a weaker location prior and removal of one training station test sensitivity. Of 150 proposed ordinary events, 144 form the training-connected cohort. The output remains experimental and does not replace v1. Waveform cross-correlation has not yet been added.

## Native hypoDD with waveform CC

Run `python -u 03_experiments/02_relative_location/13_hypodd_cc_pilot.py --stage all` in `seismoagent`; `cc`, `locate`, and `report` are separate resumable stages. The [stage-13 report](../export/03_location_experiments/01_relative_location/13_hypodd_cc_pilot/README.md) compares native catalog-only hypoDD with catalog+CC on the fixed stage-12 cohort. It reuses local Fortran sources and the existing correlation core, correcting the pick-window-lag to differential-travel-time conversion in the case adapter. It does not run FDTCC or modify the shared library.

Of 1,204 accepted CC observations, 981 enter fitting and 223 are withheld. Both native variants retain the same 138/144 events; six negative-depth rejections remain explicit. Added CC gives only a small improvement in withheld differential-time residuals and no further depth improvement against Shelly. Native constant-layer/flat-station modeling differs from the stage-12 receiver grids. These are experimental outputs, not replacements for expert v1.

## Fixed hypoDD comparison configurations

Run `python -u 03_experiments/02_relative_location/14_tune_hypodd.py` for the twelve-setting weight/damping comparison, or `--reuse-native` to rebuild its report after checking unchanged native inputs. The [stage-14 report](../export/03_location_experiments/01_relative_location/14_tune_hypodd/README.md) preserves all settings and explicit selection rules. Keep `cc0_d1` as the existing **catalog-only control**: no tested catalog-only variant passes every validation gate. Use `cc3_d1` (CC row factors 3×CC² for P and 1.5×CC² for S; catalog factors 1/0.5; damping 80 then 40) as a **provisional CC candidate** for subsequent tests. Its advantage is in differential-time and horizontal-location metrics, not depth accuracy.

Candidate outputs are `export/03_location_experiments/01_relative_location/14_tune_hypodd/hypodd/events.csv` and `hypodd_cc/events.csv`; exact runnable inputs and logs remain in `runs/cc0_d1/` and `runs/cc3_d1/`. Use the explicit common-event masks for comparisons and retain excluded events in `cohort.csv`. These previously examined stations are development validation, not a fresh benchmark test. Confirm transfer on a different fixed cluster before any whole-catalog adoption; expert v1 stays unchanged.

## Fixed-parameter transfer check

Run `python -u 03_experiments/02_relative_location/15_validate_transfer.py --stage all` in `seismoagent` (or individual `prepare`, `cc`, `locate`, `report` stages). The [stage-15 report](../export/03_location_experiments/01_relative_location/15_validate_transfer/README.md) uses a separate spatial cohort at least 10 km from all development proposals. The 147 connected events share no development event IDs; all CC settings and native controls are unchanged. Catalog-only hypoDD retains 146 events and hypoDD+CC retains 147. On their common 146 events, withheld CC RMS improves from 60.7 to 46.9 ms, with improvement at all six withheld stations relative to catalog-only hypoDD.

The additional absolute-location agreement does not transfer: CC slightly increases horizontal differences against all three references and increases the Shelly depth difference from 0.470 to 0.662 km. Freeze both methods as explicit comparison configurations for subsequent tests, preserving model/depth caveats and expert v1. Do not tune on this transfer cohort or treat either method as ground truth. Native catalogs, inputs, exclusions, phase-pair diagnostics and figures are retained under `export/03_location_experiments/01_relative_location/15_validate_transfer/`.

## Systematic-error diagnosis and selected improvement

Run `python -u 02_diagnostics/16_diagnose_systematics.py` in `seismoagent`. The [stage-16 report](../export/02_diagnostics/16_diagnose_systematics/README.md) diagnoses all 10,419 associated picks from the two fixed cohorts (291 events), separating layer interpretation, receiver elevation, station/phase residual patterns, reference offset vectors and depth geometry. No locations or observations are changed, and no parameter search is run.

Select **empirical station-by-phase travel-time corrections in the existing absolute NonLinLoc model** for the next controlled experiment. Station-phase median residuals correlate at 0.79 between cohorts. Development-only corrections reduce transfer centered RMS from 0.390 to 0.304 s at fixed locations; this supports the choice but does not establish improved location accuracy. The [61 proposed corrections](../export/02_diagnostics/16_diagnose_systematics/proposed_station_corrections.csv) use `T_corrected = T_model + c`; they are model-specific estimates, not established instrument delays. Preserve unsupported phases, uncertainty flags and adverse station-level outcomes. Keep model, picks, associations and search settings fixed when testing corrected versus uncorrected locations. The examined transfer cohort remains development validation, not a blind benchmark test.

## Entry-point migration map

The paths below replace the former root-level filenames. `docs/` and `export/` have not moved. Commands in archived export reports remain historical; use this map when locating their current entry points. No root-level aliases or duplicate code files are retained.

| Former root entry | Current entry |
| --- | --- |
| `01_prepare_inputs.py` | `01_pipeline/01_prepare_inputs.py` |
| `02_pick_phasenet.py` | `01_pipeline/02_pick_phasenet.py` |
| `03_associate_gamma.py` | `01_pipeline/03_associate_gamma.py` |
| `04_locate_nonlinloc.py` | `01_pipeline/04_locate_nonlinloc.py` |
| `09_estimate_magnitude.py` | `01_pipeline/09_estimate_magnitude.py` |
| `10_validate_catalog.py` | `01_pipeline/10_validate_catalog.py` |
| `05_review_catalog.py` | `02_diagnostics/05_review_catalog.py` |
| `06_diagnose_depth.py` | `02_diagnostics/06_diagnose_depth.py` |
| `06_report_depth.py` | `02_diagnostics/06_report_depth.py` |
| `07_audit_mainshocks.py` | `02_diagnostics/07_audit_mainshocks.py` |
| `16_diagnose_systematics.py` | `02_diagnostics/16_diagnose_systematics.py` |
| `08_check_strong_motion.py` | `03_experiments/01_strong_motion/08_check_strong_motion.py` |
| `12_relative_location_pilot.py` | `03_experiments/02_relative_location/12_relative_location_pilot.py` |
| `13_hypodd_cc_pilot.py` | `03_experiments/02_relative_location/13_hypodd_cc_pilot.py` |
| `14_tune_hypodd.py` | `03_experiments/02_relative_location/14_tune_hypodd.py` |
| `15_validate_transfer.py` | `03_experiments/02_relative_location/15_validate_transfer.py` |
| `03_plot_association.py` | `04_comparison/03_plot_association.py` |
| `04_plot_nonlinloc.py` | `04_comparison/04_plot_nonlinloc.py` |
| `11_plot_catalog_maps.py` | `04_comparison/11_plot_catalog_maps.py` |
| `config.yaml` | `00_config/config.yaml` |
| `association.yaml` | `00_config/association.yaml` |
| `nonlinloc.yaml` | `00_config/nonlinloc.yaml` |
| `validation.yaml` | `00_config/validation.yaml` |
| `depth_diagnostic.yaml` | `00_config/depth_diagnostic.yaml` |

All relative values in `00_config/config.yaml` are interpreted from the expert root, including for custom `--config` files; CLI argument paths themselves are relative to the invoking working directory. YAML parameter values are unchanged. The pre-migration source snapshot is `export/_provenance/pre_layout_migration.zip`. Archived output hashes are retained unchanged; a source-hash mismatch is not permission to bypass a resume guard. No full scientific stage was rerun for this directory change.

Migration checks passed: all 19 entry points import under `seismoagent` from outside the expert directory; dynamic imports and configuration paths resolve; five YAML mappings equal their pre-migration values and the baseline input configuration still matches. Reversing the path-only edits gives identical Python syntax trees. Input preparation, NonLinLoc and spatial-transfer `--help` entry points pass from `/tmp`. All local documentation links resolve. The sizes and modification times of 281 existing stage-level/full/candidate output files are unchanged. These are structural checks, not a numerical rerun or a new catalog validation.


## Fixed station-phase correction experiment (stage 17)

```bash
python -u 03_experiments/03_station_corrections/17_test_station_corrections.py --stage all --workers 8
```

The `check`, `locate`, and `report` modes are also available. Design, inputs and code are frozen in `export/03_location_experiments/02_arrival_and_station/17_station_corrections/design.json`; changes must not silently resume this run. Existing stage-04 observations and grids are reused, with LOCDELAY corrections and unchanged errors/search settings. Four branches compare control/corrected locations with all observations and with six fixed instruments withheld. The 588 fits retain all 147 events in each branch. The result is **do_not_promote**: withheld timing and horizontal reference agreement improve, but compatible depth agreement worsens. See the [report](../export/03_location_experiments/02_arrival_and_station/17_station_corrections/README.md), [figures](../export/03_location_experiments/02_arrival_and_station/17_station_corrections/figures/01_paired_diagnostics.png), and EVOLUTION for interpretation. The status column in corrections.csv is copied from the stage-16 source; actual experimental application is recorded by branch and tt_correction_s in fit_phases.csv. No full catalog is replaced.


## Fixed-grid depth attribution (stage 18)

Run `python -u 02_diagnostics/18_diagnose_depth_coupling.py` in seismoagent from the expert root. Outputs stay in `export/02_diagnostics/18_depth_coupling/`. This performs local weighted sensitivity projection, signed station/phase attribution, a constant-layer sensitivity comparison and one +1-km development-depth counterfactual. It runs no locator and changes no catalog. The [report](../export/02_diagnostics/18_depth_coupling/README.md) distinguishes the reproduced numerical mechanism from unresolved physical causes; [the figure](../export/02_diagnostics/18_depth_coupling/depth_coupling.png) shows prediction agreement and influential terms. Derivatives pass finite-difference checks, travel times reproduce the native values, and uniform delays have zero depth projection.


## Bounded SRT/TOW2 arrival review (stage 19)

`python -u 02_diagnostics/19_review_s_arrivals.py` freezes 12 events, reads 24 windows, and generates twelve PNG/PDF figures. Selection and source paths are retained under `export/02_diagnostics/19_s_arrival_review/`. The completed assistant visual assessments are in review.csv, with reasons and exact inspected figure hashes. They are not produced by an automatic onset algorithm or human expert labeling. Once review.csv exists, the entry point stops without overwriting reviewed evidence. See the [report](../export/02_diagnostics/19_s_arrival_review/README.md): 19 compatible, five ambiguous, no justified global repicking. This branch is closed without sample expansion.


## Controlled HK velocity-profile experiment (stage 20)

Run `python -u 03_experiments/04_velocity_model/20_test_hk_model.py --stage all --workers 8` in seismoagent from the expert root. Use `--stage report` to regenerate summaries after the fits complete. Logs and results remain in `export/02_diagnostics/20_velocity_model_qualification/`; the path is retained for continuity. `INPUT_MODEL_NOTES.md` preserves the initial qualification record as an input note, not an optimization step.

The experiment explicitly assigns both profiles the same +0.7-km ASL depth plane; this is not a reconstruction of SCSN's native depth registration. HK uses constant layers with the published tops and Vp, Vs=Vp/1.73, and a constant upper extension to -3 km. Keep receiver elevations and all original observations/settings fixed. Run control/HK and six-instrument-withheld control/HK on the same 147 events. Check generated grid velocities, reproduce baseline, verify all fitted travel times independently, and evaluate 923 withheld arrivals without recentering. No station corrections or parameter sweep. Design/source fingerprints guard resumption; changed scientific inputs require a separate run identity.

Consult the [completed experiment report](../export/02_diagnostics/20_velocity_model_qualification/README.md) for the predeclared gates, adverse results and decision. Passing permits fresh-cohort validation only; the existing full v1 remains unchanged.

## Empirical observation errors (stage 21 / campaign round 01)

Run `python -u 03_experiments/05_catalog_optimization/21_calibrate_observation_errors.py --workers 8` in seismoagent. Results and logs are in `export/03_location_experiments/02_arrival_and_station/21_observation_errors/`. `--report-only` regenerates summaries. Estimate effective uncertainty only from the existing development cohort, freeze it, and test all-data/withheld fits on the 147-event transfer cohort. Original arrivals and model remain unchanged. Native errors change; time corrections do not. Reuse the verified stage-20 baseline controls by frozen hash. See the [campaign ledger](OPTIMIZATION.md) for selection boundaries and reserved events.

## Native EDT likelihood (stage 22 / campaign round 02)

Run `python -u 03_experiments/05_catalog_optimization/22_test_edt.py --workers 8`, then `python -u 03_experiments/05_catalog_optimization/22_finalize_edt.py` in seismoagent. The original Gaussian parser can reject valid native weights rounded to zero, causing the first command to return nonzero after native fits complete. Inspect failures: only the known rounded-zero assertion is handled by the finalizer; missing outputs, input changes or weight inconsistencies still fail. The finalizer uses the same run lock, retains all observations, verifies native identities and reproduces EDT consistency weights, and never reruns or changes the location solutions. Use it for report regeneration.

Results are in `export/03_location_experiments/02_arrival_and_station/22_edt_likelihood/`. `run.log` records execution/parser outcomes; `finalize.log` records successful complete interpretation. `parser_checks.json` fingerprints the parser, native observations/controls/solutions and original execution design. Scientific interpretation must use actual residual RMS, not EDT's method-specific QUALITY misfit.

## EDT analytic origins (stage 23 / campaign round 03)

Run `python -u 03_experiments/05_catalog_optimization/23_refine_edt_origins.py` in seismoagent. It fixes all round-02 xyz and computes inverse-total-variance analytic origins using fit observations only. No NLLoc execution is needed. Results are in `export/03_location_experiments/02_arrival_and_station/23_edt_origins/`; event metadata distinguishes native diagnostics from refined origin/residual RMS. Matched all-station/withheld displacements are inherited from actual round-02 solutions and quantify one common observational perturbation, not a new bootstrap. All previous outputs and reserved events remain unchanged.

## Native common-origin-constrained EDT (stage 24 / round 04)

Run `python -u 03_experiments/05_catalog_optimization/24_test_edt_origin_constraint.py --workers 8` in seismoagent; `--pilot` executes one fixed event, and `--report-only` regenerates summaries. Outputs/logs: `export/03_location_experiments/02_arrival_and_station/24_edt_origin_constraint/`. This runner directly uses the EDT-specific parser, retaining weights rounded to zero, and verifies pairwise weights against the native output. LOCMETH is EDT_OT_WT_ML; source default penalty/floor, errors, grids, observations and search budget are fixed. The completed pilot result is reused by its input/control hash. Archived pilot source/design document the auxiliary-label correction before the full run. No scientific setting changed in that revision.

## Development-depth-constrained station corrections (stage 25 / round 05)

Run `python -u 03_experiments/05_catalog_optimization/25_constrain_station_corrections.py` in seismoagent. The runner projects original 61 development correction coefficients onto zero mean first-order development-depth response using development-count weighting, then freezes coefficients. Outputs are in `export/03_location_experiments/02_arrival_and_station/25_constrained_corrections/`. It reuses stage-17 native delay execution and checks under its own output root, plus verified control tables; its final report documents the new estimator. No earlier script or output is modified. Inspect actual transfer depths and failed gates; the linear mean constraint is not a guarantee of fixed depths elsewhere.

## Original P-only corrections (stage 26 / round 06)

Run `python -u 03_experiments/05_catalog_optimization/26_test_p_corrections.py` in seismoagent. It reuses the stage-25 execution helper and stage-17 native checks/report helpers under `export/03_location_experiments/02_arrival_and_station/26_p_corrections/`, with its own frozen design and actual P-only report. Exactly 32 original development P cells are active; 29 historical S cells remain explicit zeros. No projected coefficients from stage 25 are used. The candidate passes examined-transfer gates and is frozen for round-07 reserved confirmation.

## Reserved P-correction confirmation (stage 27 / round 07)

Run `python -u 03_experiments/05_catalog_optimization/27_validate_reserved_p.py` in seismoagent. It uses exactly the 300 reserved events with frozen round-06 coefficients. All receive primary fits; auxiliary fits require the original native minima of ten arrivals and three S picks after the fixed six-instrument omission. There are 267 eligible auxiliary events, 1,134 valid fits total. Source/native hashes guard reuse; summary and native completion JSON use atomic writes. Original minimum-S preflight failure and its input-only audit are preserved in the output, not hidden. Results: `export/03_location_experiments/02_arrival_and_station/27_reserved_p_corrections/`. Confirmation failed; v1 remains the sole full product.

## Fixed 80-km station selection (stage 28 / round 08)

Run `python -u 03_experiments/05_catalog_optimization/28_test_near_stations.py` in seismoagent. Select instruments using original NLL horizontal model-coordinate distance, keep zero corrections and original settings. All 147 event identities and pick distances remain in selection/eligibility tables; native minimum ten total arrivals and three S arrivals gives 146 primary/144 auxiliary fits. Score all 911 fixed omitted observations on common auxiliary events, including those outside the radius. Baseline tables are reused by frozen identity. Results and logs are in `export/03_location_experiments/02_arrival_and_station/28_near_stations/`; trial rejected.

### Regional 3D numerical pilot (stage 29)

Use the CPU `seismoagent` environment. The first command writes model/travel-time grids; the second performs the fixed pilot locations and compares matched-background travel times against the original 2D baseline. Run sequentially; do not start another builder for the same resolution while its lock is held.

```bash
python 03_experiments/06_3d_velocity/29_build_3d_grids.py --spacing 0.25 --workers 4
python 03_experiments/06_3d_velocity/29_check_grid_pilot.py --spacing 0.25
```

Run from the expert directory. Each resolution has its own export folder. These commands produce a numerical pilot, not a complete regional-model catalog. The `--all` builder option prepares all station grids only; it does not perform or qualify a full cohort location experiment.

After the 0.25 km pilot passes, complete the station set and run the fixed transfer experiment:

```bash
python 03_experiments/06_3d_velocity/29_build_3d_grids.py --spacing 0.25 --all --workers 8
python 03_experiments/06_3d_velocity/29_test_3d_model.py --workers 8
python 03_experiments/06_3d_velocity/29_plot_3d_comparison.py
```

Run these commands sequentially after any existing builder/locator process finishes. The transfer runner verifies all grid buffers/headers and repeats the numerical gate before inversion; native completed fits are reused only with matching input/output hashes. `--stage report` recomputes the comparisons without rerunning native fits. Plots require a completed transfer report. See `export/03_location_experiments/03_velocity_models/29_3d_velocity/transfer/design.json` for the frozen gates and `provenance/dependency_preflight/` for the prepare-only dependency audit before any transfer fits.

### Local-background model comparison (stage 30)

Run the two sequential commands in [the stage30 README](../export/03_location_experiments/03_velocity_models/30_local_background/README.md). The builder creates only candidate grids and links the unchanged matched background. The transfer runner checks grid identities, verifies one fixed native pilot, then executes 294 candidate fits and reuses prior controls. It writes the paired report and figures automatically. `--stage report` regenerates reporting only after fits are complete. Existing jobs must finish before invoking a duplicate command.

## Joint absolute/CC pilot (stage33)

From the expert directory using seismoagent:

```bash
python 03_experiments/07_joint_location/33_joint_location.py --stage all
python 03_experiments/07_joint_location/33_evaluate_joint.py
```

Run sequentially. Existing outputs are reused only with the frozen source design; do not launch concurrent writers. The original native 2D grid contains multiple planes; the predictor uses the same first radial plane as the previously validated predictor. `numerical_checks.json` checks predictor equivalence and the sparse Jacobian. `frozen_candidate.json` identifies the candidate to validate without changing its weights. The second reserve has not been used.

## Support-aware graph experiment (stage39)

From the expert directory, with no existing stage39 writer running:

```bash
python 03_experiments/07_joint_location/39_prepare_graph.py
python 03_experiments/07_joint_location/39_measure_pairs.py
bash 03_experiments/07_joint_location/run_39_pairs.sh
```

The shell runner performs 16 matched absolute/joint solves and then evaluates them. It requires completed measurement checks. CPU threads are limited inside each of four parallel solves. Logs are under `03_experiments/07_joint_location/logs/`; scientific outputs are under `export/03_location_experiments/04_joint_location/39_support_aware_pairs/`. Both earlier reserves have now been consumed: this is exposed development, not a new confirmation sample. Do not rerun measurement while its process is active.

## Joint regional 3D model experiment (stage40)

```bash
bash 03_experiments/07_joint_location/run_40_joint_3d.sh
```

From the expert directory, only when no stage40 job is active. The CPU runner verifies existing grid buffers, checks interpolation/derivatives, executes 16 regional solves and four matched 3D-background controls, then evaluates and plots. Existing solve outputs are reused only after the frozen design checks. It creates no new large grids. Logs are in the script directory's `logs/`; results are in `export/03_location_experiments/03_velocity_models/40_joint_3d_model/`. This is exposed development and failed depth-reference/coverage gates, not a production replacement.

## Disjoint regional P-static experiment (stage41)

```bash
bash 03_experiments/07_joint_location/run_41_p_statics.sh
```

From the expert directory, without a concurrent stage41 writer. This estimates and checks disjoint calibration terms, verifies archived 3D fields, runs/reuses 16 corrected solves, then compares fixed held observations and all earlier joint controls. Logs are in the script directory's `logs/`; outputs are in `export/03_location_experiments/03_velocity_models/41_regional_p_statics/`. The completed experiment fails depth-reference/coverage gates and is not a production replacement.

## Vertical P observation experiment (stage42)

With no stage42 writer active, using seismoagent from the expert directory:

```bash
python 03_experiments/08_vertical_observations/42_vertical_p.py
python 03_experiments/08_vertical_observations/42_extract_vertical.py
bash 03_experiments/08_vertical_observations/run_42_vertical.sh
```

Run sequentially; qualification and extraction must finish before the shell runner.
The runner measures new scalar P CC, executes 16 matched solves on four CPU workers,
and evaluates fixed historical observations. It does not restart extraction.
Logs are under the script directory. Data are under `export/04_observation_experiments/42_vertical_p_observations/`.
The three real EHZ instruments supply P only; DPP step scores are kept separately
from PhaseNet probabilities. No response correction, fabricated horizontal input,
new event detection, reference-guided association or full-product replacement is implied.

## Hidden-P template qualification (stage43)

```bash
bash 03_experiments/09_template_observations/run_43_template.sh
```

Run only without another stage43 writer. This reproduces the frozen waveform
qualification and its report, not a location job. The completed round fails
coverage/timing qualification; its pure template-transfer observations are not
catalog inputs. Logs remain in the script folder, outputs in
`export/04_observation_experiments/43_template_p_observations/`. Do not retune the frozen gates or consume
reserve3 to rescue this method.

## Direct missing-P experiment (stage44)

```bash
python 03_experiments/08_vertical_observations/44_extract_missing_p.py --workers 16
bash 03_experiments/08_vertical_observations/run_44_missing.sh
```

Run sequentially, without existing stage44 writers. The runner does not restart
extraction. It first checks new onsets against existing different-event P onsets,
then measures standard CC, fits 16 matched controls and evaluates. Logs are in
the script folder; outputs are in `export/04_observation_experiments/44_missing_p_observations/`.
Neither stage43 transfer times nor reserve3 outcomes are used.

## Added LB.DAC observations (stage45)

Run `bash 03_experiments/10_added_station/run_45_station.sh` from the expert root. This executes new-station CPU picking, frozen association, native P/S tables, scalar P/vector S correlations,16 matched solves and fixed-gate evaluation. Outputs: `export/04_observation_experiments/45_added_station/`; logs: `03_experiments/10_added_station/logs/`. Original raw data and baseline manifests are retained.

## Alternative picker and missing S (stages46–47)

Qualification: `python 03_experiments/11_alternative_picker/46_qualify_eqtransformer.py --workers 8`, then `python 03_experiments/11_alternative_picker/46_report_qualification.py`. The joint candidate failed; only S passed its predefined checks.

Separately counted S-only experiment: `bash 03_experiments/11_alternative_picker/run_47_s.sh`. It checks those S criteria, extracts missing observations, computes vector S CC, runs16 matched solves and evaluates all unchanged catalog gates. Logs remain under the script folder. Output: `export/04_observation_experiments/47_missing_s_observations/`.

## Stage48: differential-only S and updated support

```bash
cd tasks/2019_ridgecrest_california/expert/03_experiments/12_differential_augmentation
bash run_48.sh
```

The fixed graph is an attribution control, and the refreshed graph is the sole promotion candidate. Source identities are frozen before outcomes; completed location fits can be resumed. Logs remain under `logs/`; results are under `export/04_observation_experiments/48_differential_augmentation/{fixed,refreshed}`. Do not interpret this exposed development cohort as fresh confirmation.

## Stage49: independent Vp/Vs calibration and relocation

```bash
cd tasks/2019_ridgecrest_california/expert/03_experiments/13_velocity_ratio
bash run_49.sh
```

The launcher only runs location if all frozen calibration gates pass. `49_run.py` resumes completed fits without changing sources or settings. Original velocity fields are never overwritten: S tables are scaled in memory. Logs stay beside scripts; results are in `export/03_location_experiments/03_velocity_models/49_velocity_ratio/`.

## Stage50: depth-uncertainty-aware pair candidates

```bash
cd tasks/2019_ridgecrest_california/expert/03_experiments/14_uncertain_depth_pairs
bash run_50.sh
```

Preparation freezes the candidate rule and all source identities. Measurement preserves all previous rows, then16 fits use the stage48 model/objective. Historical held scores use complete original measurement sets, not their intersection with current accepted edges. Logs remain beside scripts. The active detached pipeline has PID/exit records under `logs/`; inspect the actual PID/child and exit status before resuming, to avoid duplicate writers.

## Stage51: final frozen-candidate confirmation

```bash
cd tasks/2019_ridgecrest_california/expert/03_experiments/15_confirmation
bash run_51.sh
```

Round30 applies the stage50 frozen method to all300 third-reserve targets, with no further tuning. The sequential entry point runs preparation, observation completion, graph construction, waveform correlation, original-model omission controls,16 matched fits and final evaluation. Existing raw inference chunks and completed fits are reusable; the observation launcher canonicalizes JSON tuple/list container types for exact request-cache comparison without changing numerical inference or admission rules.

Currently launched jobs are supervised by `51_continue.py` in its default mode; it waits for the specific observation/native-control PIDs, then stops on any failed downstream command. Check live PIDs and logs before invoking the sequential runner to avoid duplicate writers. `51_continue.py --observations` is the observation-only cache-resume entry point. Outputs are in `export/05_confirmation/51_confirmation/`; logs remain beside the scripts. A completed pilot, even with passing gates, is not full-catalog adoption.

## Stage52: fixed full-working-catalog application

```bash
cd tasks/2019_ridgecrest_california/expert/01_pipeline
bash run_52_full_catalog.sh
```

Run preparation, full-graph waveform correlation, four matched primary/withheld fits, product export and comparison figures. Reuse immutable historical waveform windows; verify that the accelerated correlation reproduces old acceptance/lag on overlapping edges. No new parameter scan or picker inference is performed. Logs are under `01_pipeline/logs/52_full_catalog/`; outputs are in `export/06_full_catalog/52_full_catalog/`. Do not launch duplicate writers. The runner skips completed preparation/measurement, and the existing solver resumes complete fits after source-identity checks.

## Export organization maintenance

Read the [output index](../export/README.md) before adding an experiment. New code should use its grouped physical destination directly; existing frozen entry points keep compatibility paths. Run `python 01_pipeline/check_export_layout.py --full` from the expert root to verify layout, migrated symlink targets and stage-52 frozen sources without rerunning inference or inversion. The workspace hides only legacy aliases, not real results.
