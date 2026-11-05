# Back-end audit — 2018 Kīlauea summit, four GLM-5.3 runs on the same picks

Audit date 2026-11-02. Question: the three back-end arms located, relocated and sized the same 2,710 events from identical fixed picks; why do their scores differ, and why did the two checker arms end with a worse origin-time bias and horizontal scatter than the arm without the checker?

## 0. Runs, sources and how the numbers were obtained

Task directory `T = workflows/tasks/2018_kilauea_hawaii`. Run directories (each has `control/`, `work/`, `record/execution.log`, `record/execution.jsonl`, `evaluation/metrics.json`):

| short name | arm | run directory |
|---|---|---|
| tools | formal tools run (front end + back end, no checker) | `T/runs/tools/claude/glm-5.3/20261029T084718Z` |
| backend | fixed front end, tools only | `T/runs/backend/claude/glm-5.3/20261101T050124Z` |
| bchk | fixed front end + checker skill + disposition contract | `T/runs/backend_checker/claude/glm-5.3/20261101T050148Z` |
| bknw | fixed front end + checker + knowledge skill + magnitude resource | `T/runs/backend_knowledge/claude/glm-5.3/20261101T050213Z` |

- The front end of the three back-end arms is the tools run's own PhaseNet/PyOcto product (`work/input/frontend/README.md` of each back-end arm: built from `runs/tools/.../work/picks.csv`). All four runs therefore located the same 2,710 events from the same 52,528 non-rejected associated picks (tools `work/run/03_location/arrivals.csv` holds 78,586 rows, of which the 26,058 rows of the 1,486 rejected events are the difference). Events carry the same `event_id` in all four catalogs, so locations can be compared event by event.
- The yardstick is the expert final catalog (`T/expert/export/r9/60_catalog/catalog_events.csv`): NonLinLoc `EDT_OT_WT`, HVO Klein linear-gradient model (Vp 1.9/6.5/6.9/8.3 km/s at 0/4.6/15/16.5 km, Vp/Vs 1.78) with its top at the mean station surface (`reference_elevation_km 1.07`), grid 0.25 km, `model_error_s 0.30`, min 10 phases / 3 S, no station delays, no relative relocation for picked events (`T/expert/00_config/nonlinloc.yaml`, `T/expert/PLAN.md` r7, `data/2018_kilauea_hawaii/data/models/velocity_models.json`). Magnitudes: WA simulation with obspy `WOODANDERSON` (velocity input) and magnification 2080, Hutton & Boore in mm (`T/expert/01_pipeline/09_estimate_magnitude.py`, `65_direct_magnitude.py`).
- The scorer's component swap already relocated these same picks with the expert locator (`T/runs/tools/.../evaluation/swap/`): against the expert final it gives shift 0.00 km, dz 0.00 km, |dt| 0.03 s (`swap.json`). For these 2,710 events the yardstick is therefore, to within 0.03 s, "the expert back end applied to the agents' own picks". Every difference below is a back-end difference.
- All numbers not copied from `metrics.json` come from read-only analyses (python3 scripts in the session scratchpad, not in the repository): (a) event-by-event comparison of every intermediate location product with the swap catalog (`swap/catalog_relocated.csv`); (b) re-scoring of substituted catalogs with the scorer's own library (`SeismoAgentBench.scoring.catalog_metrics`: `load_case`, `score_population`, `headline`), which reproduces the submitted headline numbers exactly; (c) 1-D P travel times for each run's model; (d) the checker location stage run on the tools, backend and swap catalogs (`seismo_checker/interface/run.py --stage location --no-model-ensemble`, output in the scratchpad).

## 1. Score table

Headline values from `evaluation/metrics.json` (`headline`, `trust.failed`, `checker`). Thresholds: |time bias| ≤ 0.3 s, scatter ≤ 1.0 km, shift ≤ 1.0 km, |dz| ≤ 1.0 km, |magnitude offset| ≤ 0.469, recall_M4 = 1. Magnitude offset is against ComCat (the case's magnitude authority); the expert final itself sits at −0.27.

| metric | tools | backend | bchk | bknw |
|---|---|---|---|---|
| time_bias_final_s (run − expert) | −0.364 | −0.190 | **+0.505** | **−0.405** |
| time_mad_final_s | 0.074 | 0.166 | 0.204 | 0.102 |
| shift_final_km | 0.065 | 0.215 | 0.569 | 0.125 |
| scatter_final_km | 0.380 | 0.695 | **1.582** | **1.091** |
| scatter vs Shelly (`scatter_median_km`) | 0.614 | 0.537 | 0.877 | 0.853 |
| dz_final_km (run − expert, + = deeper) | +0.449 | +0.620 | +0.476 | +0.312 |
| depth_mode_share | 0.037 | 0.011 | 0.051 | 0.018 |
| dmag_median (vs ComCat) | −0.06 | **−0.99** | −0.18 | −0.15 |
| dmag_slope_per_unit | −0.162 | −0.121 | −0.123 | −0.102 |
| events with a magnitude | 961 of 4,196 rows | 2,698 / 2,710 | 2,710 / 2,710 | 2,710 / 2,710 |
| recall_M4 (large_events_present) | 1.0 | 1.0 | **0.5** | 1.0 |
| recall_final / recall_norm | 0.375 / 0.883 | 0.378 / 0.881 | 0.291 / 0.820 | 0.379 / 0.883 |
| out_of_mask_fraction | 0.212 | 0.173 | 0.343 | 0.153 |
| trust.failed | time_bias | magnitude_offset | time_bias, horizontal_scatter, large_events_present | time_bias, horizontal_scatter |
| checker runs (audit / actual) | – | – | 15 / 15 | 1 / 7 (see §4.2) |

## 2. Decision table

| decision | tools | backend | bchk | bknw |
|---|---|---|---|---|
| Velocity model source | Self-derived: distance-binned apparent velocities from its own picks (`work/run/02_association/wadati.py`, `velocity_model_kilauea_1d.txt`, `work/DOCUMENTATION.md` §3) | Self-derived: 12 hand-written 1-D candidates scored by NLL RMS on an 80-event subset (`work/scripts/modeltest*.sh`, `work/runs/modeltest/`); chosen at 05:37:51 | Generic: CRUST1.0 rows for the site taken from the checker's own source (`catalog_checker.velocity`, transcript msg 52–65), Vp scaled ×0.9 to zero the checker's `sp_depth_offset` on a 300-event pilot (05:31:09–05:34:12; `work/prep/vel_crust1_w_s09.txt`, `work/checker/pilot_hi_vel_*`) | Published: HVO Klein linear-gradient model found on the web (USGS OFR 2004-1242, 05:10:49), same values as the expert's (`work/work/location/inputs/vel_hvo_linear.txt`) |
| Vp values (km/s at depth km) | 2.2 @0, 4.0 @1, 5.5 @3, 6.7 @6, 7.3 @10, 8.1 @17, 8.3 @25 | 3.2 @0, 4.9 @3, 6.2 @6, 7.0 @10, 7.6 @15, 8.0 @25 (`work/runs/prep/velocity_model.txt`) | NLL form 1.8 @−0.73, 4.5 @−0.23, 5.85 @1.17, 6.39 @4.87, 7.30 @17.87; HypoInverse form 4.5 @0, 5.85 @1.17, 6.39 @4.87, 7.30 @17.87 (`work/prep/hi_vel_crust1_w_s09.txt`), read by hyp1.40 as interfaces at 1/4/17 km (§4.1) | 1.9 @0, 6.5 @4.6, 6.9 @15, 8.3 @16.5 |
| Step vs gradient | step | step (tool default) | step (CRH constant layers) | linear (`velocity_layering: linear`) |
| Vp/Vs | 1.60 / 1.67 in the top two layers, 1.73 below | 1.75 (RMS minimum flat between 1.70 and 1.80) | 1.77 (own Wadati fit) | 1.74 (Lin et al.; own Wadati median 1.735) |
| Datum / reference elevation | sea level (`reference_elevation_km 0`, `work/run/03_location/config_nlloc.json`); first layer extended up to the stations | sea level; 3.2 km/s extended up to the stations | HypoInverse CRH: stations placed on the model surface (elevations ignored), surface = 0 km, depths reported as "below sea level" although they are below the station plane; the 1.8/4.5 km/s rows above sea level were dropped for HypoInverse (msg 132) | sea level (`work/work/location/location_setup.json`), i.e. the HVO model's 1.9 km/s top sits ~1.07 km below the stations, where the expert puts it |
| Station elevations | used (NLL, z = −elevation) | used (NLL) | ignored by HypoInverse; used in the NLL cross-checks | used (NLL) |
| Locator, method | NonLinLoc catalog locator, `EDT_OT_WT` | NonLinLoc, `EDT_OT_WT` (EDT vs GAU compared on the subset) | HypoInverse hyp1.40 (linearised L2 with residual/distance reweighting), chosen at 05:20:01 because the host was oversubscribed (load ≈ 52 from the sibling arms); NLL `EDT_OT_WT` only on 120 + 478 events | NonLinLoc, `EDT_OT_WT` |
| Grid / search | 0.5 km grid; region depth 0–20 km bsl (5.1 % of events pinned at 0.03 km) | 0.5 km; region depth −2…25 km, grid −3…30 | HypoInverse trial depth 5 km (`ZTR`), min 4 stations; NLL checks 0.5 km, region depth 0–20/0–25 km bsl (`work/prep/nll_config*.json`) | 0.5 km; default region depth 0–30 km bsl, then edge reruns (east, deep to 60 km) and a free-top rerun (−3 km) for 177 events (`run1b_edge`, `run1c_deep`, `run1d_shallow`, `merged2`) |
| Pick weighting | default P 0.1 s, S 0.2 s, model error 0.1 s | default | PhaseNet probability → σ, ×1.6 for S, mapped to HypoInverse weight codes with 0.4 s as the zero-weight limit (`work/scripts/make_arrivals.py`, `location/full_s09_r1/config.json`): 55.5 % of S picks carry zero weight (`location/full_s09_r1/arrivals.csv`) | default |
| Station corrections | none | yes: pass-1 median residuals (≥ 30 picks), P −0.13…+0.08 s, S −0.32…+0.07 s (`work/runs/pass2/delays.csv`) | none (statics ±0.12 s judged small, 05:35:05) | none |
| Outlier rejection | none (status labels only) | 3,555 + 904 picks (> 1.5 s or > 8× event MAD) | 1,687 picks with residual ≥ 1.5 s in events with rms < 0.35 s | none (picks.csv byte-identical to input) |
| Relative relocation | hypoDD CT (3,108 relocated) **not adopted** | ccdt CC + catalog dt, hypoDD CT+CC, minobs 4/4 after a cluster1.f fix (08:05:10); 2,412 DD positions adopted; DD origin times recomputed from the NLL grids (08:10:25) | ccdt CC (2,674 events, 16,098 pairs) + ph2dt-style dt.ct, hypoDD CT+CC; adopted where ≥ 8 differential observations (1,761 events, median move 1.39 km); GrowClust only as cross-check | ccdt CC only (≈ 2.5 dt per pair), GrowClust candidate A `ngoodmin 0` adopted (1,693 events, median move 1.1–1.5 km) over B `ngoodmin 4` (1,025 events); NLL origin times kept |
| Magnitude method | IASPEI standard (nm, half p-p) on a hand-coded WA filter `H = ω0²/(ω0² − ω² + 2ihω0ω)` applied to displacement (`work/run/04_magnitude/ml_events.py` l. 92), i.e. a low-pass instead of the two-zero displacement response; SNR ≥ 2 and noise-ceiling gates leave 961 MLs | `remove_response(output="DISP")` then obspy `WOODANDERSON` (one zero, velocity-input) with sensitivity 2800, peak amplitude in mm, Hutton & Boore mm form + zero-mean station terms (`work/scripts/magnitudes.py` l. 29, 67–70; `ml_regression.py`) | IASPEI standard: DISP + two-zero IASPEI WA (`gain 1.0028`, magnification 1), half p-p in nm, median of channels, long window for the 20 largest (`work/scripts/magnitudes.py`) | IASPEI standard, mirroring `agent_resource/magnitude/ml_reference.py`; no Hawaii entry in `calibrations.json`; long window for large events (`work/work/scripts/ml_catalog.py`) |
| Final product | NLL absolute positions | hypoDD positions (2,412) + NLL | hypoDD positions (1,761) + HypoInverse | GrowClust A positions (1,693) + NLL, NLL origin times |

## 3. Attribution of the score differences

### 3.1 Origin-time bias: a model-plus-datum effect, ordered exactly by the near-surface slowness of each setup

P travel times from a source at 0 and 2 km bsl to a station at 1.07 km asl, epicentral 1/3/6/10 km, in each run's model as the run used it (1-D ray computation, read-only):

| setup | mean travel-time difference from the expert setup | observed time bias |
|---|---|---|
| bknw: HVO model with its top at sea level (1.07 km of extra 1.9 km/s material) | +0.55 s (range +0.16…+0.93) | −0.40 s |
| tools: 2.2 km/s from the stations to 1 km bsl | +0.38 s | −0.36 s |
| backend: 3.2 km/s from the stations to 3 km bsl | +0.05 s (−0.26…+0.64) | −0.19 s |
| expert: HVO top at the station surface | 0 | 0 |
| bchk HypoInverse: stations on a 4.5 km/s surface, interfaces 1/4/17 km | −0.66 s | +0.50 s |
| bchk NLL check, same CRUST1×0.9 incl. slow rows above sea level | −0.20 s | +0.06 s (120 events vs the expert locator) |

A model that predicts longer travel times moves origin times earlier, and the ranking is the same in both columns. Two direct confirmations:

- bknw used the expert's model and method; its only systematic difference is the datum (sea level instead of the station surface). The bias is −0.40 s already in the absolute NLL locations (`work/work/location/merged2`: −0.399 s against the expert locator), and GrowClust changed nothing in time (origin times kept). Confidence: high.
- bchk's own NLL cross-check on the same picks and CRUST1×0.9 profile (`work/location/nllcheck_s09`, 103 box events) has +0.06 s against the expert locator, HypoInverse on the same events +0.64 s; the 478 interface-parked events relocated with NLL (`work/location/nll_parked`) +0.05 s versus HypoInverse +0.28 s. The +0.5 s bias is therefore the HypoInverse setup (stations on a fast model surface, slow near-surface rows dropped), not the CRUST1 velocities alone. Confidence: high.
- backend's model was chosen by RMS over 12 candidates (the knowledge skill says not to choose by residual), but the winning profile happens to match the HVO-at-surface average slowness to ~3 km depth, hence the smallest bias. The extra −0.14 s beyond the travel-time estimate is plausibly Vp/Vs and deeper-layer differences; DD changed origin times by a median −0.015 s only. Confidence: medium.

Why the checker arms did not catch it: the checker measured it and did not flag it. `wadati_origin_offset` (origin from each event's own S−P fit minus catalog origin; a report-only check with a 0.3 s limit, `seismo_checker/source/catalog_checker/checks.py` l. 24 and l. 483) gives:

| catalog | wadati_origin_offset | time bias vs expert |
|---|---|---|
| expert locator on these picks (swap) | +0.06 s | 0 |
| backend | +0.19 s | −0.19 s |
| tools | +0.43 s | −0.36 s |
| bknw | +0.41 s (final report; +0.40 at the location stage) | −0.40 s |
| bchk | −0.33 s (final report; −0.35 on the s09 pilot, −0.44 at scale 1.0, +0.06 at scale 0.65) | +0.50 s |

On this case the report-only check tracks the scored bias with the right sign and nearly the right size, and a 0.3 s flag would have separated the three failing runs from the passing one. bknw also saw `model_ensemble_time` median excess −0.25 s and `travel_time_intercept` 0.89 s (both report-only) and moved on. bchk's pilot table (transcript msg 195–197) shows the slower scale 0.65 had the smallest Wadati offset, but the agent chose 0.9 because it zeroed `sp_depth_offset`.

### 3.2 Horizontal scatter: absolute locator in bchk, relocation choice in bknw

Scatter against the expert locator on the same events (event-by-event, all box events; absolute product vs final product):

| run | absolute product | final product | relocation effect |
|---|---|---|---|
| tools | NLL 0.318 km | 0.317 (no DD) | none |
| backend | NLL pass 1 0.686 → pass 2 (delays, outliers) 0.637 | hypoDD 0.739 | +0.10 |
| bchk | HypoInverse 2.349 (p90 9.0 km) | hypoDD 2.165 | −0.18 |
| bknw | NLL 0.595 | GrowClust A 1.084 | +0.49 |

Re-scored with the scorer (`scatter_final_km`, matched pairs; `scatter_median_km` vs Shelly in brackets):

| catalog | scatter_final | vs Shelly | time bias | dz |
|---|---|---|---|---|
| backend submitted | 0.695 | 0.537 | −0.190 | +0.62 |
| backend, NLL pass-2 positions instead of hypoDD | 0.624 | 0.516 | −0.180 | +0.58 |
| bknw submitted (GrowClust A) | 1.091 | 0.853 | −0.405 | +0.31 |
| bknw, NLL merged2 positions | 0.636 | 0.561 | −0.404 | +0.43 |
| bknw, GrowClust B (`ngoodmin 4`, 1,025 events) + NLL elsewhere | **0.665** | **0.478** | −0.404 | +0.43 |
| bchk submitted | 1.582 | 0.877 | +0.505 | +0.48 |
| bchk, HypoInverse positions only | 1.619 | 1.015 | +0.496 | +0.32 |
| bchk submitted + NLL positions for the 478 parked events | 1.182 | 0.863 | +0.338 | +0.15 |

- bknw: the scatter failure is the GrowClust candidate choice, not the location. Its absolute catalog passes (0.64 km); candidate B would have passed (0.665 km) and is the best of all catalogs against the independent Shelly reference (0.478 km). The agent's own pre-written rule selected B (msg 431); it switched to A because B raised the checker's `relocated_share` flag (38 % < 50 %, `work/work/checker/relocation_b/checker_report.json`) while the GrowClust interface README it had read warns that `ngoodmin 0` with sparse CC data (here ≈ 2.5 dt per pair) does not improve inter-event distances. Confidence: high (direct substitution).
- bchk: the scatter failure is the absolute locator. HypoInverse with the station-plane datum, a fast surface layer, the trial-depth/interface parking and 55 % of S picks at zero weight gives 2.35 km scatter against the expert locator; hypoDD reduced it a little. Its own NLL runs on the same model were close to the expert (0.23 km on 103 events, 0.36 km on the 373 parked box events, against 3.67 km for HypoInverse on those events). Confidence: high that HypoInverse+setup is the cause; medium on the split between datum, S weighting and the fast model (no single-factor run exists).
- backend: hypoDD CT+CC slightly worsened agreement with the expert (+0.07 km) and with Shelly (+0.02 km); still passes. Confidence: high (substitution).
- tools vs the NLL back-end arms: same picks and method, but the tools absolute catalog agrees better with the expert locator (0.32 km) than backend (0.64) and bknw (0.60). The remaining differences are the velocity model (shape, Vp/Vs 1.60–1.67 near the surface, datum handling) and backend's delays/outlier rejection. Confidence: low; experiment E6.
- Caveat: the final yardstick is an absolute NLL catalog. Relative relocation that is right can still raise `scatter_final_km`; the Shelly column is the independent check, and there GrowClust B improves while GrowClust A and backend's hypoDD do not.

### 3.3 large_events_present and recall (bchk)

ComCat has two M ≥ 4 events in the box. Event `ev001191` (ComCat M4.64, 2018-05-04 22:42:42, 19.310 N, 6.7 km) is placed by HypoInverse at 19.285 N, −155.199 (gap 295°, 7 of 18 S picks weighted), 4.6 km SE of the expert locator (19.327 N) and outside the scoring box; hypoDD left it at 19.293 N (`work/location/full_s09_r1/events.csv`, `work/catalog.csv`). The other three runs keep it in the box (19.327–19.336 N). The failure is a location failure, not a magnitude one (bchk ML 4.80). The same absolute mislocation moves 362 of the 2,108 events that the expert locator puts in the box out of it (backend 38, tools 50, bknw 10), which explains bchk's out_of_mask_fraction 0.34 and its lower recall_final (0.29) and recall_norm (0.82). Confidence: high.

### 3.4 Depth

All four pass (|dz| ≤ 0.62 km). bchk's depths are mislabelled: HypoInverse CRH depths are below the station plane but reported as below sea level (NOTES.md "Depth datum: km below sea level, hypoinverse convention"); relabelled, its dz would be about −0.6 km instead of +0.48. backend's +0.62 is the largest and is already present in its absolute locations (+0.56 against the expert locator); the absolute NLL catalogs of tools, backend and bknw sit within 0.13 km of each other (+0.48, +0.56, +0.43 against the expert locator), and GrowClust A moved bknw a further 0.1 km shallower. Confidence: medium; depth is not where the arms differ in verdict.

### 3.5 Magnitude (backend −0.99)

backend applied obspy's `WOODANDERSON` (zeros `[0j]`, poles −6.283 ± 4.7124i — a velocity-input response) to displacement, and set its sensitivity to 2800. The error relative to a correct chain (displacement × two-zero WA × 2080) is log10(2800/2080) − log10(2πf) = +0.13 − log10(2πf): −0.67 at 1 Hz, −0.97 at 2 Hz, −1.15 at 3 Hz. Event by event on the same 2,698 events, backend − bknw = −0.73 (MAD 0.12) and backend − bchk = −0.81, i.e. a nearly constant offset consistent with a dominant WA frequency near 1.6–2 Hz (it shrinks to −0.6 below ML 1 and is −0.8 at ML 2.5–4). The remaining part of −0.99 is the −0.15 that the correct IASPEI chains (bchk −0.18, bknw −0.15) share against ComCat. The agent's only check was plausibility ("WA amplitude 0.93 mm … plausible", msg 193, 05:42–05:50); it read the obspy header for the gain (msg 181) but not the zero count. Confidence: high. The knowledge resource names exactly this mistake (`agent_resource/magnitude/README.md` §2–3), and bknw avoided it by mirroring `ml_reference.py`; bchk avoided it by reading the checker's `magnitude_recompute.py` (msg 238–241) and copying its IASPEI PAZ.

The tools run's ML (outside the back-end comparison) uses a low-pass WA form on displacement; its near-zero median offset comes from noise-gated selection (only 961 events) and the error's frequency dependence (tools − bknw +0.6 at ML 1, ~0 at ML 3; slope −0.16). Confidence: low.

## 4. Checker and knowledge behaviour

### 4.1 backend_checker: 15 checker runs, 2 dispositions

| time (UTC, `record/execution.log`) | checker run (`work/checker/…`) | flags | response | effect on the score |
|---|---|---|---|---|
| 05:07–05:20 | `data`, `picks_input` | 0; 1 (`silent_stations`: 5 vertical-only stations unpicked) | none needed; later justified | none |
| 05:31–05:34 | 6 × `--stage location --pilot` on HypoInverse pilots, CRUST1 ×1.0/0.9/0.85/0.8/0.65 (`pilot_hi_vel_*`) | `sp_depth_offset` at every scale except 0.9 (+1.71, +0.11, −1.54, −2.18, −2.34 km) | **changed product**: adopted Vp × 0.9 because it zeroes `sp_depth_offset` | mixed: 0.9 is slower than 1.0 (Wadati offset −0.44 → −0.35 s), but the check's own target was off: it computes the source depth below the station as catalog depth + station elevation (`checks.py` l. 85), while HypoInverse depths are already below the station plane, so the measured offset is biased by about −1.07 km; corrected, the zero crossing lies near 0.85–0.8, a slower model with a smaller time bias |
| 06:18–06:20 | (sizing of `relocated_share` from the check's definition) | – | **changed product**: relocation widened from the 870-event summit cluster to 2,674 events | slightly better (HypoInverse 1.71 → hypoDD 1.58 km vs the expert) |
| 06:48 | `location` on the pre-relocation catalog | `depth_layers` 11.1 % (1.0–1.3 and 4.9–5.1 km) | expected relocation to smear it | – |
| 06:48–06:51 | `magnitude_probe` | 0 | confirmed the IASPEI convention | kept the magnitudes right |
| 06:52–06:55 | (relocation shares: 109 events moved > 5 km) | – | **changed product**: adopt DD positions only with ≥ 8 differential observations (65 %, large moves 4 %) to keep `relocated_share` and `relocation_large_moves` in range | neutral to slightly positive |
| 06:55 | `relocation` | `depth_layers` 9.9 % | experiment 1: NLL on the 478 parked events (`location/nll_parked`) | – |
| 07:05–07:08 | `picks`, `association` (one failed for a missing column, rerun) | 1 (`silent_stations`); 0 | none | none |
| 07:20 | (NLL parked result) | – | **rejected** the NLL positions: "epicenters move a median 4.22 km … 265/478 collapse to < 0.5 km depth" | **wrong decision**: against the expert locator the NLL positions are far better (scatter 0.36 vs 3.67 km, bias +0.05 vs +0.28 s); adopting them gives scatter_final 1.58 → 1.18 km, time bias 0.50 → 0.34 s, dz 0.48 → 0.15 km. The "collapse" is pinning at the agent's own NLL search top (`depth_km [0.0, 25.0]` bsl in `prep/nll_config_parked.json`): the events want to be above sea level, under a 1.1 km high summit |
| 07:20–07:27 | `location_fine` (1-km layers, `prep/vel_s09_fine.txt`) | `depth_layers` 6.1 % + `depth_single_value` 6.1 % (trial depth 5 km) | rejected, kept the s09 model | none |
| 07:32 | `--stage all` → `checker/final` | `silent_stations`, `depth_layers` 9.9 % | both justified (`work/checker/dispositions.json`) | none |

`compare.py` and `pilot.py` were not used (the agent built its own 300-event pilot with `scripts/make_pilot.py` and passed `--pilot`).

Assessment of the `depth_layers` justification:

1. Mechanism — correct. hyp1.40 reads CRH layers with `FORMAT (2F5.2)` (`seismotools/hypoinverse/source/upstream/source/hycrh.for` l. 13–14), while the seismotools writer prints depth as `%7.2f` (`seismotools/hypoinverse/interface/run.py` l. 136–137: `f"{r[col]:5.2f}{r[0]:7.2f}"`). Columns 6–10 of "   1.17" are "   1.", so 1.17/4.87/17.87 km become 1/4/17 km (`work/location/full_s09_r1/p.crh`). This is a bug in the shared HypoInverse interface (any non-integer interface depth is truncated; depths ≥ 100 km would be misread), not in the agent's code. The 1.0–1.3 km slices sit just below the effective 1-km interface and 4.9–5.1 km is the `ZTR` trial depth; the parked events have erz median 9.4 km.
2. Evidence that the pile is "honest residue" — not shown. The remediation that was run (NLL) was rejected on a wrong reading: a large move away from a HypoInverse solution is not evidence against the new solution, and the depth collapse was the agent's own search ceiling at sea level. The flag was a symptom of the absolute-location setup that also produced the failing time bias, scatter and the missing M4.6; the disposition explains the pile and leaves the setup in place.
3. Not considered: the station-plane datum, the dropped slow surface rows, and the zero-weighted S picks, all of which the agent had noted itself (msg 132: "inconsistent datum handling between the two tools … a known limitation").

Confound: bchk chose HypoInverse because its 1-CPU share was starved by the two sibling arms running NLL on the same host (msg 121–125, 05:20:01). The locator choice was driven by compute, not by the checker, but the checker then steered the model scale and the relocation coverage around that choice.

### 4.2 backend_knowledge: what it read, followed and skipped

Files read (Read tool calls in `record/execution.jsonl`, transcript msg 15–34, 102, 110–113, 190–192, 348–350): `skills/catalog-checker/SKILL.md`; `skills/catalog-knowledge/SKILL.md`, `protocol/pilot_then_full.md`, `playbooks/decide_between_candidates.md`, `symptoms/README.md`, `symptoms/not_visible.md`, `symptoms/location_relocation.md` (twice, the `depth_layers` rows again at msg 348–350), `symptoms/magnitude_completeness.md`, `symptoms/data_picks_association.md`; `magnitude/README.md` (twice), `magnitude/ml_reference.py`, `magnitude/calibrations.json` (grep for Hawaii/HVO: none); `seismotools/growclust/interface/README.md`. It also used Z.ai web reading to find the HVO model (05:08–05:10; URLs in `metrics.json` `process.leakage.urls`, no leakage hit).

Checker runs: 7, not 1. The audit counts `work/checker/**/checker_report.json` (`SeismoAgentBench/scoring/catalog_metrics/checker_audit.py` l. 78); this agent kept its working tree under `work/work/` and wrote `work/work/checker/{location, relocation_a, relocation_b, location2, relocation, magnitude, final}`, copying only `final` to `work/checker/final` (09:57:58). Plus one `compare.py` (msg 442) and a 0.25-km-grid relocation experiment for `depth_layers` (`work/work/tmp/pile_025`).

Followed:

- `not_visible.md` §1 "use the regional model": published HVO model, linear representation as published.
- Magnitudes: IASPEI standard via `ml_reference.py`, no regional entry → standard relation, long window for large events, `magnitude_recompute` 0.0004. Result: dmag −0.15, the best-calibrated magnitudes of the four runs.
- Rule 3 / playbook: wrote adoption rules before experiments (depth_layers: "pile disperses → finer grid; persists → justify"; GrowClust: "prefer B if it relocates ≥ half as many with lower rms"); the `depth_layers` experiment was well designed (pile on octree ML-node centres 4.4531/4.5469 km, unchanged with a 0.25-km grid) and the pile disappeared after relocation.
- Edge-pinned events: reran east-edge, deep and top-pinned events with wider bounds.

Deviated:

- Datum. `not_visible.md` §1 says "use its datum as the reference elevation, start the depth search at that datum", and `location_relocation.md` (row "at the shallowest depth, many events … the datum wrong (events pushed above the model top)") names the exact symptom it then met: 137–177 events pinned at the 0-km search top that moved above sea level (median −0.83 km) when the top was freed (08:22–08:28). It applied the "widen the bounds" half of the remedy and not "check that the reference elevation equals the model datum". This is the whole −0.40 s time bias (§3.1).
- Candidates and representations: `pilot_then_full.md` asks for `pilot.py events` and candidate comparisons on a pilot; it ran a 10-event smoke test only (`pilot.py` was called with `--help`, msg 239) and never compared datum or step/linear representations (`not_visible.md` §2).
- Relocation decision. It broke its own pre-written rule (B) after the checker flagged B's `relocated_share`; `compare.py` said "mixed … decide with an experiment that separates the explanations, not by counting checks"; the experiment it ran explained A's surface pile (an absolute-catalog artefact) but did not test which candidate places events better, and `location_relocation.md` states that a low `relocated_share` is "not an error when the events are small and isolated". Adopting A doubled the scatter (0.64 → 1.09 km) and failed `horizontal_scatter`.
- Report-only signals: `wadati_origin_offset` +0.41 s, `travel_time_intercept` 0.89 s and `model_ensemble_time` −0.25 s were recorded in `work/work/notes/run_log.md` as "in range" and not connected to the datum choice.

### 4.3 Why the checker arms ended worse than the no-checker arm

1. Time bias (both checker arms): set by the datum/near-surface handling of the absolute locator (bchk: HypoInverse station plane on a fast surface; bknw: HVO top at sea level). The checker measured it (`wadati_origin_offset`) but only reports it; no flag, so no disposition was required. The no-checker backend's RMS-chosen model happened to have the right average near-surface slowness.
2. Scatter, bknw: a checker threshold (`relocated_share ≥ 50 %`) overrode the agent's own adoption rule and the tool README, and selected the loose GrowClust candidate.
3. Scatter and large events, bchk: compute starvation pushed it to HypoInverse; the checker then (a) tuned the model scale with a check whose datum assumption does not hold for HypoInverse output, (b) kept relocation coverage high, and (c) turned the one informative flag (`depth_layers`) into a disposition after rejecting the remediation that would have fixed much of the problem.
4. What the checker did well: both checker arms got the magnitude convention right (bchk by reading `magnitude_recompute.py`; bknw via the knowledge resource and the recompute check), where the no-checker arm lost a whole magnitude unit.

## 5. Proposed single-factor experiments

Each changes one factor, keeps the run's picks (`prep/arrivals.csv` or `location/inputs/arrivals.csv` of that run) and is scored with the scorer library or against `swap/catalog_relocated.csv` by `event_id`.

1. **E1 — bknw datum only (confirms 3.1, highest value).** Rerun `nonlinloc/interface/locate.py` on `bknw work/work/location/inputs/arrivals.csv` with `work/work/location/inputs/config_nll.json` unchanged except `reference_elevation_km: 1.07` and region depth starting at 0 below that datum (free top). Prediction: time bias −0.40 → within ±0.1 s, `wadati_origin_offset` → ~0.1, pinned-at-top events disappear, absolute scatter ≈ 0.6 km unchanged. Then reapply GrowClust B on the new positions.
2. **E2 — bchk locator/datum only (confirms 3.1–3.3).** Locate all 2,710 bchk arrivals (same pick rejections, same `vel_crust1_w_s09.txt` incl. the rows above sea level) with NLL `EDT_OT_WT`, `reference_elevation_km 0`, region depth −3…25 km, everything else as `prep/nll_config.json`; keep its hypoDD step unchanged. Prediction from the 120- and 478-event subsets: time bias +0.5 → ~0 to +0.1 s, scatter_final 1.58 → ~0.5–0.7 km, `ev001191` back in the box (recall_M4 1.0), out_of_mask ~0.17. As a second single factor, rerun HypoInverse with `uncertainty_codes_s` widened so no S pick gets weight 4, to size the S-weighting contribution.
3. **E3 — bknw relocation candidate only (confirms 3.2).** GrowClust B (`ngoodmin 4`) on `merged2` positions (the agent's B ran on `merged`) with the same `ccdt_full/dt.cc`. The substitution above already gives scatter_final 0.665 km and 0.478 km vs Shelly; a clean rerun removes the `merged`/`merged2` mismatch. Pair it with a checker-design test: does `relocated_share` need an exception when most events have few CC links?
4. **E4 — backend magnitude response only (confirms 3.5).** Rerun `backend work/scripts/magnitudes.py` with `remove_response(output="VEL")` (or the IASPEI two-zero PAZ on DISP) and sensitivity 2080, same windows, gates and regression; or run `ml_reference.py recompute --events 30` on the submitted catalog. Prediction: offset −0.99 → about −0.2, slope unchanged.
5. **E5 — checker `sp_depth_offset` under HypoInverse (checker design).** Repeat bchk's six-scale pilot with HypoInverse depths converted to below sea level (subtract each event's station-plane elevation, ≈ 1.07 km) before the checker; predict the zero crossing moves from 0.9 to ~0.85–0.8 and the Wadati offset towards zero. Also compute `wadati_origin_offset` for the other cases' runs to see whether a flag at 0.3 s is safe beyond Kīlauea.
6. **E6 — model only among NLL arms (explains tools' better absolute scatter).** Locate the common 52,528 arrivals with one fixed NLL configuration (reference 0, grid 0.5 km, region −3…30 km, `EDT_OT_WT`, no delays) and the three models (tools, backend, HVO at sea level), then HVO at 1.07 km; compare scatter and time bias against the swap catalog.
7. **E7 — bchk parked events only.** Rerun `location/nll_parked` with the search top at −3 km and substitute; separates the ceiling artefact from the true depth of those events (expected: smaller dz than +0.15 km, scatter unchanged at ~0.36 km for that subset).

## 6. Side findings for the maintainers

- `seismotools/hypoinverse/interface/run.py` l. 136–137 writes CRH depths with `%7.2f`, hyp1.40 reads `F5.2`: non-integer layer tops are truncated to whole kilometres. The README says nothing about it. Fix the writer to `f"{vp:5.2f}{z:5.2f}"` (and refuse depths ≥ 100 km) and add a regression test with a 1.17-km interface.
- `checks.py` l. 85 assumes catalog depths below sea level (adds the station elevation). Depths below the station plane (HypoInverse CRH, hypoDD) bias `sp_depth_offset`, `travel_time_intercept` and every station-depth geometry by one station elevation. Either state the requirement in the skill or read the datum from `--location-setup`.
- `checker_audit.py` counts checker runs only under `work/checker/`; bknw's 7 runs under `work/work/checker/` were counted as 1.
- `wadati_origin_offset` is report-only; on this case it predicts the scored time bias of all five catalogs within 0.2 s (§3.1). Worth a cross-case check before promoting it.
- The final-yardstick scatter rewards matching the expert's absolute NLL frame; relative relocation is judged better against Shelly. Reading `scatter_final_km` alone would have called GrowClust B and the absolute catalog equivalent, while Shelly prefers B.
- The three back-end arms ran concurrently on one host; bchk's locator choice was a consequence. Future arms should run with a reserved CPU share or sequentially.
