# Back-end audit: 2020 Magna, Utah (four GLM-5.3 runs)

Audit date 2026-11-02. Scope: why four runs that built the Magna back end (location, relocation, magnitudes) score differently against the human-in-loop final (expert `r11`), decision by decision. All four used Claude Code with GLM-5.3. All times are UTC from `record/execution.jsonl` (file modification times in the run folders are UTC+8).

Runs (under `workflows/tasks/2020_magna_utah/runs/`):

- **tools**: `tools/claude/glm-5.3/20261028T135931Z`, full pipeline from waveforms, no checker. Its picks and association are the fixed front end of the three back-end arms (`backend/frontend/README.md`).
- **backend**: `backend/claude/glm-5.3/20261101T100247Z`, fixed front end, tools only.
- **checker**: `backend_checker/claude/glm-5.3/20261101T100311Z`, plus the checker skill and the disposition contract.
- **knowledge**: `backend_knowledge/claude/glm-5.3/20261101T100335Z`, plus the checker, the knowledge skill and `data/agent_resource/magnitude/`.

The three `20261031T18*` runs carry `EXCLUDED.md` and are ignored.

Method. Besides reading the scripts, notes and transcripts, every intermediate catalog the agents left on disk (NonLinLoc runs, model tests, relocations) was scored with the benchmark's own matcher and metrics (`SeismoAgentBench.scoring.catalog_metrics`: `versus_final` against `expert/export/r11/60_catalog/catalog_events.csv` and `magnitude_bias` against UUSS, case mask applied). This reproduces the submitted headline values exactly: for example backend +0.14 s / −1.959 km / dmag 0.67, and knowledge recomputed IASPEI dmag 0.518. Each agent's sequence of runs is therefore a set of natural single-factor experiments. The scripts used are read-only and live in the session scratchpad; nothing in the repository was changed except this file.

## 1. Scores

`dmag` is the median magnitude difference against **UUSS ML**, the case's magnitude authority (`evaluation/metrics.yaml` `primary.magnitude: uuss`). It is not measured against the expert final; the expert final itself sits at +0.08 against UUSS. Time, depth, shift and scatter are measured against the expert final. Thresholds come from `metrics.json` → `trust`.

| metric (threshold) | tools | backend | checker | knowledge | expert r1 (blind NLL, BP89, HB87) |
|---|---|---|---|---|---|
| time_bias_final_s (abs ≤ 0.30) | −0.19 | +0.14 | **+0.34** | **+0.38** | +0.24 |
| dz_final_km (abs ≤ 1.0) | **−1.94** | **−1.96** | +0.56 | −0.51 | +0.20 |
| shift_final_km (≤ 1.0) | **2.35** | **2.11** | **1.31** | **1.36** | 1.31 |
| scatter_final_km (≤ 1.0) | 0.51 | 0.54 | 0.82 | **1.017** | 0.74 |
| dmag_median vs UUSS (abs ≤ 0.28) | **0.67** | **0.67** | **0.63** | **0.52** | 0.64 |
| dmag_slope_per_unit | −0.16 | −0.20 | −0.18 | −0.12 | −0.24 |
| dmag spread (≤ 0.307) | 0.20 | **0.352** | **0.3085** | 0.195 | 0.21 |
| depth_mode_share (≤ 0.05) | 0.020 | 0.008 | 0.014 | 0.014 | 0.018 |
| out_of_mask_fraction (≤ 0.10) | 0.027 | 0.033 | **0.1185** | 0.073 | – |
| trust.failed | shift, depth, mag | shift, depth, mag, mag spread | inside_region, time, shift, mag, mag spread | time, shift, scatter, mag | – |

The expert column comes from `evaluation/human_in_loop/expert_ladder.json` (round r1: stage-04 NonLinLoc catalog, BP89 without the basin layer, provisional Hutton–Boore ML). It is the expert's own first attempt scored against the expert's own final, and it carries the same two errors the agents carry: origin times +0.24 s late and magnitudes +0.64 high. The expert removed the magnitude offset in r2 (Utah ML recalibration anchored on UUSS ML, dmag → 0.00) and the time offset in r4 (basin-fill layer, dt → −0.02 s, dz −0.17 km). The expert's own absolute catalogs r1–r6 also sit 1.26–1.31 km from the final horizontally, because the final carries the hypoDD cluster's absolute offset (`expert/PLAN.md` r8 §2). The ≤ 1 km horizontal-shift gate is therefore failed even by the expert's absolute locations, and the CRUST1 arms (1.31/1.36 km) sit at the expert's own absolute level.

### Intermediate products scored the same way

| product | model / setting | time bias s | dz km | shift km | scatter km | out of mask |
|---|---|---|---|---|---|---|
| tools `runs/nll` (strict set) | generic Wasatch v1, no delays | −0.14 | −2.94 | 2.63 | 0.72 | 0.021 |
| tools `runs/nll_v2` | v2 (Vs +5.4 %), no delays | −0.18 | −2.17 | 2.49 | 0.94 | 0.020 |
| tools `runs/nll_v3` | v2 + station delays | −0.19 | −1.87 | 2.40 | 0.43 | 0.015 |
| tools `runs/nll_perm` (final absolute) | v2 + delays, permissive set | −0.19 | −1.95 | 2.36 | 0.51 | 0.039 |
| backend `run/nll1_out` | model A (Vp/Vs 2.05→1.78) | +0.19 | −3.60 | 1.15 | 1.23 | 0.188 |
| backend `run/nll_B` | own model, Vp/Vs 1.66, no delays | **+0.03** | **−0.89** | 1.63 | 1.03 | 0.059 |
| backend `run/nll_C` | own model, Vp/Vs 1.73, no delays | +0.14 | −2.31 | 2.18 | 1.13 | 0.050 |
| backend `run/nll2_out` | C + 80 station delays | +0.15 | −2.08 | 2.14 | 0.64 | 0.040 |
| backend final | + hypoDD (3,114 adopted) | +0.14 | −1.96 | 2.11 | 0.54 | 0.033 |
| checker `runs/02_locA` | CRUST1 as is (Vp/Vs 1.72), no delays | +0.38 | −0.54 | 1.32 | 0.97 | 0.069 |
| checker `runs/04_locB` | A + 87 station delays, outliers removed | +0.45 | −0.73 | 1.52 | 0.74 | 0.044 |
| checker `runs/11_locC` | CRUST1 Vp/Vs 1.66, no delays | +0.29 | +0.59 | 1.26 | 0.88 | 0.111 |
| checker final | + hypoDD CT+CC (3,279) | +0.34 | +0.56 | 1.31 | 0.82 | 0.118 |
| checker `10_modeltest` (400 ev.) | as-is / Wadati 1.578 / 1.66 + adj. delays / 1.66 no delays | +0.36 / +0.33 / +0.45 / +0.29 | −0.34 / +1.37 / −0.91 / +0.67 | – | – | – |
| knowledge pilot (300 ev.) | crust1 / crust1_vpvs (1.579) / wasatch_step | +0.58 / +0.51 / **+0.13** | −1.23 / +0.52 / −2.10 | – | – | – |
| knowledge `run/full_crust1` (A) | CRUST1 step (Vp/Vs 1.72), no delays | +0.38 | −0.52 | 1.33 | 0.97 | 0.070 |
| knowledge `run/full_crust1_delays` (B) | A + delays | +0.45 | −0.75 | 1.48 | 0.69 | 0.041 |
| knowledge `run/full_crust1_qc` (C) | A after 562 picks rejected | +0.38 | −0.52 | 1.33 | 0.97 | 0.070 |
| knowledge GrowClust ngoodmin 4 | 1,009 relocated | (NLL times kept) | −0.51 | 1.35 | **0.92** | 0.070 |
| knowledge GrowClust ngoodmin 2 (final) | 1,717 relocated | +0.38 | −0.51 | 1.36 | **1.017** | 0.073 |

Earlier replays of the tools run (`workflows/replay/outputs/records/magna_tools_*.json`: EDT_OT_WT, datum 1.48, no station delays) give the following. BP89 as steps: +0.13 s / −1.59 km. BP89 plus the basin layer as steps: +0.01 s / −3.05 km with a 12 % depth pile-up. BP89 as a linear gradient: +0.23 s / −0.88 km.

## 2. Decision table

| decision | tools | backend | checker | knowledge | expert (r11 chain) |
|---|---|---|---|---|---|
| velocity model source | "generic Wasatch Front crust" written from memory (`work/runs/assoc/velocity_model.txt`), Vs +5.4 % from a residual regression (v2) | "generic eastern Basin-and-Range" written from memory (`work/run/velmodel_A.txt`); B and C rescale Vs; C chosen at 11:04:02 because it had the smallest residuals (mean \|res\| 0.212 vs 0.227 s) | CRUST1.0 columns under the network via the checker's `catalog_checker.velocity.regional_models` (decided 10:05:09, "defensible, case-agnostic") | CRUST1.0 via the same helper (10:09:38); a Wasatch model written from memory and a Wadati-Vs variant were tested on a pilot and rejected | Bjarnason & Pechmann (1989) Wasatch-front model plus a Salt Lake Valley basin-fill layer (`data/2020_magna_utah/data/models/velocity_models.json`, `bjarnason_pechmann_1989_plus_slv_basinfill2km`) |
| Vp under the stations (top ~3.5 km) | 3.2 / 4.0 / 4.8 / 5.6 km/s at 0 / 0.5 / 1.5 / 3 km below sea level | 4.0 / 5.0 / 5.7 / 5.95 at 0 / 1 / 2 / 3 km below sea level | 2.5 km/s from 1.76 to 1.26 km above sea level (above most sensors; median sensor 1.41 km), then **6.1 km/s** down to 8.74 km below sea level | same CRUST1 model (`work/run/models/crust1_step.txt`) | 3.4 at 1.48 km above sea level → 4.0 at sea level → 5.9 at 2.0 km below (linear ramps) |
| vertical one-way time, 1.44 km above sea level → 9 km below (P / S) | 2.19 / 3.66 s | 1.95 / 3.38 s (C), 1.95 / 3.25 s (B) | **1.75 / 2.91 s** (Vp/Vs 1.66) | **1.75 / 3.06 s** | 1.96 / 3.39 s |
| Vp/Vs | ≈ 1.70 (v2) | 1.73 (C); Wadati with intercept gave 1.59 | 1.72 → **1.66** (run C, tuned so that `sp_depth_offset` ≈ 0) | 1.72 (CRUST1 Vs); the Wadati value 1.579 was rejected because S residuals grew with distance | 1.73 |
| layering | step (locate.py default) | step | step | step | **linear** (step was tested in r9 and rejected: −0.22 s, −0.66 km) |
| datum / station elevations | reference 0 km (sea level), StationXML sensor elevations | same | same | same (`work/run/nll_config.json`) | reference 1.48 km above sea level (= model datum); station z = 1.48 − elevation |
| slow basin layer | partly (3.2–4.8 km/s in the top 3 km, no explicit basin) | no (4.0 km/s at the top) | **no** | **no** (the Wasatch candidate had 3.5 km/s from 0 to 1 km and was rejected) | **yes**, 4.0 km/s from sea level to 2 km below |
| station corrections in location | yes: per-phase mean residual, ≥ 30 picks, clipped ±1 s (`runs/nll_in/delays2.csv`) | yes: 80 median residuals (`run/delays_C.csv`, up to ±0.9 s) | tried in run B (87 delays), **removed** after the `sp_depth_offset` flag | tried in run B, **rejected** by `compare.py` (worse) | none in location (31 station corrections only in ML) |
| locator, method | NLL `locate.py`, EDT_OT_WT | NLL `locate.py`, EDT_OT_WT, model error 0.1 s | same | same | NLL **GAU_ANALYTIC**, model error 0.30 s (EDT was tested on 2026-10-27 and not adopted: depths moved by ~1 km) |
| grid / depth search | 0.5 km; region 0.5–25 km below sea level; min 6 phases | 0.5 km; default region 0–30 km below sea level | 0.5 km, min node 0.25–0.5 km; region **0–25** km below sea level | 0.5 km; default 0–30 km; 114 depths emptied when within 0.75 km of a grid bound | 0.25 km grid; grid −3…35 km below the datum; association depth 0–20 km below the datum |
| pick weighting | defaults P 0.10 / S 0.20 s | PhaseNet half trigger width as `uncertainty_s` (median ≈ 0.17–0.18 s, overrides the defaults) | same as backend | same as backend | P 0.10 / S 0.20 s |
| outlier rejection | picks with \|res\| > 1.5 s marked uncertain afterwards | 430 picks with \|res\| > 1 s marked rejected after the final run (no relocation) | 1,810 picks (> 1 s and > 4 MAD) removed after run A, before runs B and C | 562 picks (P > 1.0 s, S > 1.5 s) removed, run C relocated (`compare.py`: no_difference) | GaMMA association consistent with the locator; depth prior for weak events (stage 45) |
| relative relocation | ccdt (CC ≥ 0.6, 72,627 dt) → GrowClust with 20 bootstraps; 1,034 adopted, NLL origin times kept; hypoDD tried and rejected (1.5 km drift) | ccdt (CC ≥ 0.7, 52,994 dt) + ph2dt (MAXSEP 2 km) → hypoDD CT+CC, model C, ratio 1.73; 3,114 adopted (hypocentre and origin time) | ccdt on run-C origins (46,144 dt) + ph2dt (MAXSEP 4, MAXOBS 8) → hypoDD CT+CC, 14 × 2 km layers from CRUST1, ratio 1.66; 3,279 adopted, origin times moved by a median +0.028 s | ccdt (38,481 dt) → GrowClust (CRUST1 clipped at 0); ngoodmin 4 → 2 adopted through `compare.py`; 1,717 relocated, NLL origin times kept | hypoDD CT+CC (r6/r8) with a 3 km vertical acceptance gate, plus Match&Locate events shifted with their templates |
| ML formula | IASPEI nm relation, then a data-driven distance correction pinned to IASPEI at R0 = 17.45 km, plus zero-mean station terms | Bakun & Joyner (1984) in mm, magnification 2080 | IASPEI standard (`ML = log10 A_nm + 1.11 log10 R + 0.00189 R − 2.09`) | IASPEI standard; the Utah entry (`pechmann_2007_utah`) computed alongside but **not** submitted | HB87 in r1; from r2 a Utah fit `2.934 log10 R + 0.00189 R − 2.313` (mm), plus 31 station corrections (`expert/00_config/config.yaml`) |
| response, amplitude | PZ + sensitivity reconstruction; WA T0 0.8 s, h 0.8; half peak-to-peak, larger horizontal; 0.3–20 Hz; SNR ≥ 2 | evalresp DISP, own WA filter (T0 0.8, h 0.8, ×2080); half peak-to-peak, larger horizontal; SNR ≥ 3 | `remove_response(DISP, water_level 60)` + IASPEI WA PAZ; half peak-to-peak per component; SNR ≥ 3, clip check | same chain as `ml_reference.py` (checked: catalog − reference +0.004, MAD 0.021) | obspy WOODANDERSON on velocity (×2080, mm); maximum \|amplitude\| of N and E; mean of log10 |
| window | P − 1 s to S + 0.25 (S − P) + 5 s | P − 1 s to S + 12 s | P − 1 s to S + max(30 s, 4 (S − P)) | first P − 1 s to last pick + max(3 s, 0.5 × travel time) + 2 s | P − 0.5 s to P − 0.5 s + 2 (S − P) |
| event ML, coverage | median of corrected station values; 2,423 events | MAD-trimmed mean; 1,366 events | median of components (≥ 3); 1,788 events | median of components (≥ 2); 3,854 events | median of station values; M&L chain for detections |
| large events (mainshock) | ML 6.01; dmag M5 +0.31 | 5.87; +0.17 | 5.68; −0.02 | 5.66 (Utah 5.44); −0.04 | magnitude deferred for the mainshock; r10 adds direct ML |

The vertical travel times were computed by integrating 1/v from the mean sensor elevation (1.44 km above sea level) to 9 km below sea level through each model as the locator sees it (datum, step or linear). They isolate the near-surface difference: CRUST1 is 0.21 s (P) and 0.33–0.48 s (S) faster than the expert model, while the tools model is 0.23 s (P) and 0.27 s (S) slower.

## 3. Attribution

### 3.1 Origin-time bias (checker +0.34 s, knowledge +0.38 s; backend +0.14 s; tools −0.19 s)

The cause is the near-surface velocity of the adopted model. Confidence is high.

- **Same signature as the expert's own error.** The expert's r3 catalog under BP89 (5.9 km/s right below sea level, no basin) ran +0.34 s late and too deep against both Pang and UUSS. The basin layer took it to +0.05 s (`expert/PLAN.md` r4; the registry entry's `derivation` field). CRUST1 is faster still (6.1 km/s from 1.26 km above sea level). The checker and knowledge arms reproduce exactly that "late and deep" fingerprint.
- **The agents' own runs order the models by near-surface slowness.** At Vp/Vs ≈ 1.72 without delays: CRUST1 +0.38 s; the backend's own model (4.0/5.0/5.7 km/s on top) +0.14 s; the knowledge arm's Wasatch candidate (3.5 km/s top) +0.13 s on the pilot, against +0.58 s for CRUST1 on the same pilot (−0.45 s); the tools model (3.2/4.0/4.8 km/s) −0.14 to −0.19 s. Ordered by vertical P time (1.75 → 1.95 → 2.03 → 2.19 s), the time bias goes +0.38 → +0.14 → (+0.13 − 0.58 + 0.38 ≈ −0.07, pilot-transferred) → −0.19 s.
- **Vp/Vs and station delays are second-order for time.** Checker arm: Vp/Vs 1.72 → 1.66 moved time +0.38 → +0.29 s, and adding delays moved it +0.38 → +0.45 s. Knowledge A → B (delays) moved it +0.38 → +0.45 s. Backend: Vp/Vs 1.73 → 1.66 moved it +0.14 → +0.03 s.
- **The relocation step pushed the checker arm over the gate.** Run C (absolute) had +0.29 s, just inside 0.30. hypoDD (CRUST1 interpolated into 14 flat 2 km layers, ratio 1.66, no station elevations) shifted origin times by a median +0.028 s (5–95 % −0.18…+0.25 s). On the 2,753 pairs matched in both catalogs the median went 0.299 → 0.340 s. The knowledge and tools arms kept NLL origin times through GrowClust, so relocation did not touch their time bias.
- **Why CRUST1 was used.** Both checker arms took it from the checker's runtime (`seismotools/checker/runtime/velocity_models/`), which the README presents as generic models that "give a range of plausible 1-D models for any region; none is assumed correct for a given case". The checker arm called it "the defensible, case-agnostic source" (10:05:09). The knowledge arm adopted it on the pilot (10:43:51) after misreading its 2.5 km/s cap, which sits 1.76–1.26 km above sea level, mostly above the sensors, as "the slowest surface layer" of the three candidates. No arm used the regional Bjarnason & Pechmann model. It is in the repository registry but was not in the run input, and the agents' notes show they deliberately avoided Magna-specific published models (backend 10:08:31, checker 10:05:04, knowledge 10:04:53).

### 3.2 Depth bias (tools −1.94 / backend −1.96 → checker +0.56 / knowledge −0.51 km)

Several factors are layered here. Their ordering is supported by the intermediate runs; the magnitudes of the method and layering terms are inferred from the expert's own tests and are not yet confirmed on agent picks.

- **Model change, CRUST1 versus the agents' own shallow-slow models (largest single step, high confidence).** At the same Vp/Vs, without delays and with the same front end: backend own model −2.31 km, CRUST1 −0.52/−0.54 km. Most of the "fix" was therefore in place in run A of both checker arms, before any checker flag, as a by-product of adopting the checker's generic model. The fast near-surface that fixed the depth is the same factor that broke the time (§3.1). Under one fixed locator setup the agents traded depth error for time error; neither checker arm found a model that fixed both.
- **Vp/Vs (high confidence).** Backend 1.73 → 1.66: −2.31 → −0.89 km. Checker CRUST1 1.72 → 1.66: −0.54 → +0.59 km. Checker Wadati 1.578 on the subsample: +1.37 km. Vp/Vs is the knob that `sp_depth_offset` measures. Across the CRUST1 runs, `sp_depth_offset` and dz line up: 0.01 → +0.56, 1.09–1.22 → −0.51…−0.54, 1.51–1.57 → −0.73…−0.75 km. So dz ≈ 0 against the expert final corresponds to `sp_depth_offset` ≈ +0.6 km, not 0. The relation does not carry across models: the BP89 replay had 1.15 km with dz −1.59 km.
- **Station delays (medium–high confidence).** At a fixed model, per-station median delays made depths shallower: checker A → B −0.54 → −0.73 km; knowledge A → B −0.52 → −0.75 km; backend C → C + delays −2.31 → −2.08 km (here they deepened, but horizontal scatter tightened 1.13 → 0.64). Delays always reduced scatter (0.97 → 0.69–0.74). The checker arm diagnosed that the S delays peak at 10–25 km stations and absorb the S−P depth signal (12:56:05, `work/runs/NOTES.md` §2).
- **Locator method and layering, agent defaults versus expert choices (medium confidence, not measured on agent picks).** All four arms used `locate.py` defaults, EDT_OT_WT and step layers. The expert used GAU_ANALYTIC and linear. On Magna the expert measured EDT moving depths by ~1 km against GAU (2026-10-27 test, `expert/PLAN.md`) and step against linear moving them −0.66 km and −0.22 s (r9). The backend's model C has the same vertical P and S times as the expert model (1.95/3.38 against 1.96/3.39 s) yet sits 2.3 km shallower. Method plus layering is the most plausible remainder. If so, CRUST1's fast near-surface depth push partly cancels the EDT and step shallowing in the checker arms, so their depths are right for partly the wrong reasons.
- **Tools versus backend (both ≈ −1.95 km).** The coincidence has different causes. Tools: a slow model with depth limited by Vp/Vs ≈ 1.70 and delays (v1 −2.94 → v2 −2.17 → + delays −1.87 km), time −0.19 s. Backend: a near-expert vertical time but Vp/Vs 1.73 chosen by residual (B at 1.66 would have passed both gates: +0.03 s / −0.89 km).

### 3.3 Magnitude offset (+0.52 … +0.67 against UUSS, in every arm)

The cause is the distance correction at Magna's short hypocentral distances: a regional calibration level (tier C), not a bug in the agents' code. Confidence is high.

- The median station hypocentral distance is 17.3 km (IQR 14.9–22.6 km, knowledge amplitudes). There, HB87, IASPEI and Bakun–Joyner all give −log A0 ≈ 2.00 (mm, 2080 equivalent), while the expert's UUSS-anchored Utah fit gives 1.36. The difference is +1.08 at 10 km, +0.64 at 17.4 km, +0.53 at 20 km and ≈ 0 at 40 km. Bakun–Joyner (backend) and IASPEI (checker, knowledge) are numerically equivalent to HB87 below 30 km. The tools arm's data-driven correction is pinned to IASPEI at R0 = 17.45 km by construction, so it reshapes the curve without moving its level.
- **The expert had the identical offset.** Expert r1 with provisional HB87 scored dmag +0.645 against UUSS (`expert_ladder.json`). Its r2 fit (spreading 1.11 → 2.93) removed it. The agents' 0.63–0.67 is the expert's r1 value.
- **Recompute test (done here, read-only).** With the knowledge arm's own amplitudes (`work/run/full_amplitudes.csv`) and final locations, IASPEI reproduces dmag 0.518. Swapping in the expert's r2 coefficients, without station corrections, gives **−0.10**. Using the library's `pechmann_2007_utah` entry (Richter 1958 table, epicentral distance, old WA ×2800; the agent's own `ml_utah` column) gives **0.27**, which would pass the 0.28 gate by 0.01. The +0.6 is therefore the distance correction, with no unit or response error. The checker's `magnitude_recompute` passed in both checker arms (+0.096 and −0.02), and `ml_reference.py` agreed to +0.004, which confirms the code.
- **Why the knowledge arm stayed at 0.52 rather than 0.63–0.67.** Its window is shorter, ending about 0.5 travel times after the last pick, while the checker arm uses S + ≥ 30 s and the backend S + 12 s. Its event value is the median of components, with no SNR gate, so it also gives magnitudes to 3,854 events. A ~0.1 smaller amplitude level is the likely cause; this is not verified.
- **Why the residual offset is ~0.3 even with the Utah entry.** The Utah entry lacks the UUSS station corrections ("not included" in `calibrations.json`), and the Richter table is coarse at 0–20 km. UUSS ML is the only anchor that fully closes the gap, and the validity rules forbid it to the agents. A residual of ~0.1–0.3 is the honest floor for a blind agent.
- **Spread failures.** These belong to the backend (0.352: larger horizontal, MAD-trimmed mean, SNR ≥ 3) and the checker arm (0.3085, long window). The knowledge arm's component median passes at 0.195. This is not investigated further.

### 3.4 Other differences

- **checker inside_region fail (0.1185).** It was caused by the Vp/Vs 1.66 change: the share of in-box events deeper than the 13.1 km mask bottom went 1.5 % (run A) → 5.0 % (run C) → 6.0 % (final). Out of mask overall: A 0.069, B 0.044, C 0.111.
- **knowledge scatter fail (1.0167).** Two checker-driven choices produced it. Rejecting station delays took scatter 0.69 → 0.97. Adopting GrowClust ngoodmin 2 over 4 took it 0.92 → 1.02: `compare.py` called ngoodmin 2 "better" because `relocated_share` cleared its < 50 % flag.
- **Horizontal shift.** CRUST1 runs sit at 1.3 km, the backend's own model at 2.1–2.2 km and tools at 2.4 km, tracking the model and Vp/Vs. The expert's absolute catalogs sit at 1.26–1.31 km from its own final (DD offset), so ≈ 1.3 km is the floor for any absolute-only catalog here.

## 4. Checker behaviour (checker and knowledge arms)

### 4.1 Checker arm: every run (report `generated_utc`)

| when | stage, product | flags | agent response |
|---|---|---|---|
| 10:09 | data (`work/checker/00_data`) | none | – |
| 10:36 | association on the input (`01_association_input`) | none (events had no origin times) | – |
| ~11:27 | location, run A (written to `checker/location`, then overwritten) | `events_with_few_picks` 25.4 % | 11:27:46: noticed `wadati_origin_offset` −1.17 s ("WAIT, that's huge!"), found it report-only (11:28:12) and let it go; `sp_depth_offset` +1.22 passes |
| 12:21 | location, run B (`checker/location`) | few_picks; **`sp_depth_offset` 1.513** | 12:22–12:56: diagnosed station S delays absorbing the S−P depth signal; tested Vp/Vs 1.578, 1.66 + adjusted delays and 1.66 without delays on 400 events; adopted 1.66 without delays (13:05:16) |
| 14:01 | location, run C (`locationC`) | few_picks | `sp_depth_offset` 0.21; `wadati_origin_offset` −1.10 noted as report-only (14:02:27) |
| 14:40 | relocation (`relocationC`) | none | – |
| 15:22 | magnitude (`magnitudeC`) | few_picks | `magnitude_recompute` +0.096, largest events −0.002 |
| 15:31 | all (`final`) | few_picks (25.35 %) | disposition `justified`: 24.2 % already in the given association; evidence cites the input files and the unchanged share |

`compare.py` and `pilot.py` were never used. Decisions were made on full runs and a 400-event subsample, with the agent's own reproduction of the S−P depth (`work/scripts/12_spdepth.py`). The disposition is complete and audited as `justified` (`evaluation/metrics.json` → `checker`, flags agree with the rerun).

Effect of the one flag that drove a change (`sp_depth_offset`, run B → run C):

- depth −0.73 → +0.59 km (abs 0.73 → 0.59, sign flipped);
- time +0.45 → +0.29 s (better, below the gate until hypoDD added +0.04);
- out of mask 0.044 → 0.111 (worse, causes the inside_region fail);
- scatter 0.74 → 0.88 (worse, still passing).

Against the benchmark this is mixed: one failure removed for the time being (time), one added (inside_region). Depth passed either way. The flag pointed at a real inconsistency, but its zero point is not the expert's: dz ≈ 0 corresponds to `sp_depth_offset` ≈ +0.6 km.

### 4.2 Knowledge arm: every run

| when | stage, product | flags | agent response |
|---|---|---|---|
| 10:16 | association on the input (`association_input`) | few_picks 24.2 % | baseline for the disposition |
| 10:23 / 10:34 / 10:43 | location, pilot (`pilot_loc_crust1`, `_vpvs`, `_wasatch`; `pilot.py events`, 300 events) | none judged (pilot) | adoption rule written first (`work/notes/decisions.md`); wasatch best RMS and intercept (+0.19 vs −0.53 s) but 12.3 % pile at 0.05 km depth → rejected; vpvs → S residuals grow with distance → rejected; CRUST1 adopted |
| 11:29 | location, full A | few_picks | – |
| 12:15 | location, full B (+ delays) | few_picks, **`sp_depth_offset` 1.57** | `compare.py --change other` → `worse` (12:16) → A kept |
| 13:00 | location, full C (QC picks) | few_picks | `compare.py --change picks` → `no_difference` → C adopted |
| 14:05 / 14:06 | relocation (`reloc_growclust`, `_n2`) | `relocated_share` 0.35 (ngoodmin 4) | `compare.py --change relocation` → `better` for ngoodmin 2 → adopted |
| 14:12 | all (`final`) | few_picks 25.5 % | disposition `justified`, evidence with file paths |

Effects of the checker-driven choices on the benchmark:

- rejecting delays (B → A): dz −0.75 → −0.52, time +0.45 → +0.38 (both better, time still failing), scatter 0.69 → 0.97 (worse);
- ngoodmin 4 → 2: scatter 0.92 → 1.02, which **created the scatter failure**;
- rejecting the Wasatch model on the pilot: time would have been about −0.07 s instead of +0.38 s (pilot-transferred), but depth about −1.4 km instead of −0.5. The rejection kept the depth passing and the time failing.

The `dispositions.json` entry has no `flag_id`. `work/scripts/make_dispositions.py` keys its `ENTRIES` dict by flag id but writes `out = [ENTRIES[f] for f in flags]`, so the key is dropped. The scorer reports `entries_without_flag_id: 1`, `problem: no disposition` and `complete: false`. This is a script bug in the agent's code, not a missing judgement; the evidence text itself is sound.

### 4.3 What the checker could and could not see

- **Time bias had a signal, but it was report-only.** `wadati_origin_offset` was −1.09 to −1.28 s and `travel_time_intercept` −0.45 to −0.62 s in every CRUST1 report. They were −0.57 s and +0.23 s for the tools run (time −0.19 s) and −0.78 s and +0.19 s for the knowledge Wasatch pilot. Within the agents' setups the intercept tracked the time bias. The replays show it does not transfer across setups (BP89 steps: +0.30 s intercept with +0.13 s bias), which is consistent with its report-only status. Both agents saw it and dismissed it explicitly because it is in REPORT_ONLY (checker 11:28:12; knowledge 14:14:45: "travel_time_intercept −0.45?? … flag=False").
- **Depth: `sp_depth_offset` is a depth gauge within one model family only.** Calibrating it to 0 moves the S−P scale, not the absolute model. It cannot distinguish "fast near-surface + EDT + steps" from "slow basin + GAU + linear".
- **Magnitude: the checker cannot see a calibration level.** `magnitude_recompute` compares against the same IASPEI relation and therefore rewards matching it. The knowledge arm chose IASPEI over the Utah entry *because* the checker recomputes IASPEI ("apples-to-apples", 10:08:21 and 10:51:45), even though `not_visible.md` says to use the regional calibration.

## 5. Knowledge use (knowledge arm)

Files read, from `record/execution.jsonl` tool calls:

- `catalog-checker/SKILL.md` and `catalog-knowledge/SKILL.md` (10:04:15–16);
- `protocol/pilot_then_full.md`, `symptoms/not_visible.md` and `playbooks/decide_between_candidates.md` (10:04:18–20);
- `symptoms/README.md` (10:04:20);
- `seismotools/checker/README.md` (10:04:26);
- `magnitude/README.md` (10:04:38);
- `calibrations.json`, through Python at 10:07:12–37, including `pechmann_2007_utah`;
- `magnitude/ml_reference.py` (10:16:34, 10:53);
- the parsed DS 3.1 PDF, searched for "Intermountain/Pechmann" (10:51:46).

**Not read:** `symptoms/location_relocation.md` (it appeared only in a `find` listing), `symptoms/magnitude_completeness.md` and `symptoms/data_picks_association.md`.

Procedures followed:

- pilot before full (`pilot.py events`, 300 events);
- adoption rules written before each experiment (`work/notes/decisions.md`);
- full-run decisions through `compare.py`;
- magnitude code checked against `ml_reference.py recompute`;
- the Utah calibration computed and reported as a scale uncertainty.

Deviations:

1. **Regional velocity model (`not_visible.md` rule 1).** The arm used a generic model (CRUST1). Its "knowledge-based Wasatch" model was written from memory, not taken from a published table, and it was not used "the way it was meant to be used" (datum at sea level, search starting at 0 below sea level, steps only). Rule 2, comparing step and gradient representations, was not done.
2. **Shallow pile.** `location_relocation.md`, which it did not read, lists "at the top of the search region → check the reference elevation and search start; at the shallowest depth with S−P deeper → near-surface too fast or datum; relocate with the datum at the model datum, then with a slow surface layer". The agent instead read the pile as evidence against the slower model and adopted the fastest near-surface model. This deviation is the one that cost the time gate.
3. **"Do not choose by residual."** It did not choose by RMS (the Wasatch model had the best RMS and was rejected), so this rule was followed.
4. **Magnitude level (`not_visible.md`: "Use the calibration of the region").** It used IASPEI, citing the checker's IASPEI recompute and convention risks in the Utah entry. That choice costs about 0.25 in dmag and the gate (0.27 against 0.518).
5. **Disposition.** The output is missing `flag_id` (script bug, §4.2).

## 6. Proposed single-factor experiments

All of these use the recorded picks of the named run. They can be built with `workflows/replay` (`relocate` intervention: model, datum, layering) or directly with `seismotools/nonlinloc/interface/locate.py`, and scored with `score_run`-equivalent code as in this audit. Each changes one factor and predicts the direction of change.

1. **Near-surface velocity explains the time bias (top priority).** Checker-arm picks (`runs/03_delays/arrivals_runB.csv` minus the rejected picks), CRUST1 Vp/Vs 1.66, no delays, EDT, steps, datum 0. Replace only the top section with the expert's shallow column (3.4 → 4.0 km/s down to sea level, 4.0 → 5.9 km/s to 2 km below sea level), everything else unchanged. Prediction: time +0.29 → about 0.0 ± 0.1 s; depth shallower by ~1 km; `travel_time_intercept` up by ~0.6 s; `wadati_origin_offset` toward −0.6 s. Repeat on the knowledge picks. Confirms §3.1 and tests whether the intercept is a usable time signal.
2. **Expert-setup anchor, then one factor at a time back toward the agent setup.** Relocate the backend picks with the expert's absolute setup: BP89 + basin, linear, datum 1.48, GAU_ANALYTIC, model error 0.3 s, P/S errors 0.1/0.2 s, no delays. Prediction: about (−0.02 s, −0.2 km), the expert's r4/r5 ladder values. Then flip one factor each: EDT_OT_WT, step, datum 0, PhaseNet `uncertainty_s` weights, station delays, Vp/Vs 1.66. This measures the method and layering terms of §3.2 that were inferred only from expert tests. GAU_ANALYTIC needs a `location_method` key in the replay `relocate` spec (`replay_lib.relocate` hard-codes EDT_OT_WT).
3. **Magnitude calibration level.** For the backend and checker arms, which keep their amplitudes (`run/magnitudes_nll2.csv.detail.json`, `runs/20_final/measurements.csv`), recompute event ML with (a) the submitted relation, (b) `pechmann_2007_utah`, (c) the expert r2 coefficients, and (d) (c) plus the expert station corrections. Prediction from the knowledge arm (done here): 0.52 → 0.27 → −0.10. Expect 0.63–0.67 → ~0.3 → ~0.0 for the others, and dmag_slope toward 0 under (c). This confirms that the offset is tier C, not code, in every arm.

Further checks, cheaper or already partly answered:

4. **hypoDD origin times.** Re-score the checker-arm final with the hypoDD hypocentres but NLL run-C origin times. Prediction: time 0.34 → 0.30 s, the gate edge.
5. **Delays × Vp/Vs on one model.** Complete the 2 × 2 on the backend picks: model B (1.66) with delays. This tells whether delays or Vp/Vs dominate depth on a slow-top model, and whether B + delays keeps both gates while lowering scatter.
6. **Wasatch pile-up as a datum/bound artefact.** On the knowledge pilot, relocate `wasatch_step` with the search top above sea level (region depth −1.5 km) or with reference elevation 1.4 km. Prediction: the 0.05 km pile disperses, and time stays ≈ +0.1 s on the pilot. This tests whether the rejection of the slower model was an artefact of the default region top.
7. **GrowClust ngoodmin.** Already measured: scatter 0.92 (ngoodmin 4) against 1.02 (ngoodmin 2). The open question is whether `relocated_share < 0.5` should outrank `relocation_thinning` in `compare.py --change relocation` when the extra relocated events are weakly linked.

## 7. Implications

- The depth gain of the checker arms came mostly from adopting the checker's generic model (CRUST1) before any flag. The sp-depth flag then tuned Vp/Vs. The same fast near-surface produced the failing time bias. The checker supplies one depth gauge (S−P) but no judged time gauge, so the agents optimised depth at the cost of time.
- `wadati_origin_offset` and `travel_time_intercept` were the only time signals. Both agents saw and dismissed them because they are report-only. Promoting them is not justified by Magna alone (the replays break the relation across setups), but a knowledge-skill symptom of the form "large negative intercept together with a fast near-surface model and no basin" would have given the agents an experiment to run.
- The magnitude offset is the expert's own r1 error, removed in the expert pipeline only through an anchor the agents are not allowed to use. The library's Utah entry gets to ~0.27. The knowledge arm had it and did not submit it because the checker's recompute favours IASPEI. Either the checker should recompute on the entry the agent declares, or the skill should say that matching the checker's IASPEI recompute is not the goal.
- For a fair comparison (conclusion-framing rule), every arm is compared against the expert final. The expert's own first pass (r1) shows the same pattern: time +0.24 s against the final (+0.34 s against Pang and UUSS before the basin layer), magnitude +0.64 and horizontal shift 1.31 km. The agents' failures are therefore the errors of a careful first pass, not unusual mistakes. The expert fixed them with a regional basin layer and a UUSS-anchored ML fit; neither was available to the agents.

## Files

- Scores: `runs/<arm>/.../evaluation/metrics.json`; expert ladder: `workflows/tasks/2020_magna_utah/evaluation/human_in_loop/expert_ladder.json`.
- Agent notes:
  - tools: `work/REPORT.md`
  - backend: `work/run_notes.md`
  - checker: `work/runs/NOTES.md`, `work/checker/dispositions.json`
  - knowledge: `work/notes/decisions.md`, `work/checker/compare_*.json`, `work/scripts/make_dispositions.py`
- Expert choices: `expert/README.md`, `expert/PLAN.md` (r1, r2, r4, r9, the EDT test), `expert/00_config/{config,association,nonlinloc}.yaml`, `expert/01_pipeline/09_estimate_magnitude.py`.
- Regional model registry: `data/2020_magna_utah/data/models/velocity_models.json`. Magnitude resource: `data/agent_resource/magnitude/{README.md,calibrations.json}`.
- Replays: `workflows/replay/outputs/records/magna_tools_regional{,_basinfill,_linear}.json`.
