# Back-end audit: 2011 Prague, Oklahoma (four GLM-5.3 runs)

Audit date 2026-11-02. Read-only: no run, product or scorer was changed. All four runs locate the same fixed front end, the PhaseNet picks and PyOcto association of the formal tools run (115,524 picks, 3,589 associated events; `workflows/tasks/2011_prague_oklahoma/backend/frontend/README.md`). The tools run built that front end itself, and its back end works on the same events. Event IDs are shared by all four catalogs. Every score is relative to the expert human-in-the-loop final catalog (`expert/export/r7/60_catalog/catalog_events.csv`), except the magnitude scores, which are against Cochran et al. (2020) (`evaluation/metrics.yaml`, `primary.magnitude: cochran`).

Run directories (relative to `workflows/tasks/2011_prague_oklahoma/runs/`):

- **tools**: `tools/claude/glm-5.3/20261028T043719Z` (full pipeline from waveforms, no checker)
- **backend**: `backend/claude/glm-5.3/20261101T000000Z` (fixed front end, tools view without checker)
- **checker**: `backend_checker/claude/glm-5.3/20261101T000024Z` (adds the catalog-checker skill and disposition contract)
- **knowledge**: `backend_knowledge/claude/glm-5.3/20261101T000047Z` (adds the checker plus the catalog-knowledge skill and `agent_resource/magnitude`)

In this document, "the checker run" and "the knowledge run" mean the backend_checker and backend_knowledge runs. "Checker" alone means the tool.

## 1. Summary

- **Depth bias and origin-time bias come from the velocity model, not the locator.** Each run's own NonLinLoc travel-time grids were used to relocate synthetic Keranen-model arrival times at the expert hypocentres (§5.1). This predicts the observed NonLinLoc-stage depth and time bias of every run to within about 0.1–0.25 km and 0.03 s. Tools and backend chose generic models. These models have Vp/Vs of about 1.70–1.73 throughout and no slow, high-Vp/Vs sediment layer, so their S−P time per km is too small near the surface (0.60–0.64 s to 3.6 km, against 0.77 s for Keranen). Events therefore go about 1.1 km too deep. The knowledge run fell back on CRUST1.0, whose sediment layer (Vs 1.07 km/s, Vp/Vs 2.34) happens to reproduce the Keranen S−P (0.78 s). This gives dz +0.26 km.
- **The checker run's near-zero depth bias is mostly a hypoDD artefact, not a better model.** Its absolute locations were +0.72 km (step) and +0.62 km (linear). hypoDD then moved the cluster centroid up by 0.68 km (`hypoDD.log`, "mean centroid shift … −683.7 m"). It also squeezed the depth range: shallow events moved down by up to 1.1 km and deep events up by about 1.4 km. The final median dz is −0.02 km, but the residual still depends on depth: +0.54 km for expert depths below 2 km and about −0.1 km below 3 km.
- **The checker run's time bias of +0.29 s was caused by a checker flag.** The step-model pass gave 18.1 % of events in thin depth slices (`space.depth_layers`). The agent switched to the linear representation of the same model. Origin times then moved from +0.17 s to +0.29 s against the expert (threshold 0.30 s), and the depth MAD doubled from 0.30 to 0.60 km. The 725 events in the "artefact" pile have expert depths of about 2.0 km. The pile tracks a real concentration in the expert catalog, mapped about 0.6 km too deep.
- **The magnitude offsets are two textbook unit and response errors, verified numerically.**
  - Tools used A in mm (magnification 2080) with the −2.09 constant, which expects A in nm at magnification 1. That costs exactly −2.682. Swapping in the +0.591 constant moves the submitted ML from −2.51 to +0.17 against the expert, the same level as the two correct runs.
  - Backend applied ObsPy's one-zero (velocity-input) Wood-Anderson response to displacement. That costs −log10(2πf): −1.14, −1.41 and −1.71 at 2, 4 and 8 Hz. The observed offset is −1.5 against the expert for M ≥ 1.5. It is smaller for small events, where low-frequency noise and SNR selection inflate amplitudes, and that causes the failed slope.
  - The checker and knowledge runs implemented the IASPEI chain correctly. Neither got it from a flag. The checker run copied it from the checker's own source (`magnitude_recompute.py`, read 2026-11-01T00:09:55Z). The knowledge run imported `ml_reference.py`.
- **The magnitude-scale failure of the two correct runs is common to direct standard ML here.** Their slopes are −0.33/−0.34 against Cochran, with a threshold of 0.314 and the expert at −0.21. Against the expert, small events are +0.4–0.55 too large. Requiring R ≥ 10 km or SNR ≥ 5 does not help; tested read-only, both make the slope steeper. The tools run, whose amplitude path has a 0.5–1 Hz high-pass, shows a smaller slope against the expert (−0.13). Long-period noise leaking into the small-event amplitudes is the leading hypothesis (medium-low confidence).
- **The checker's S−P depth check pointed the wrong way in this sedimentary setting.** It said catalog depths were 1.9 km too shallow on the knowledge run's pilot (model A) and 1.23 km too shallow on the checker run's final catalog. Against the expert, those catalogs were 0.42 km too deep and 0.02 km too shallow. The knowledge run argued correctly that the far-path S−P scale does not transfer to sediment-covered near paths, and kept model A over model B. Following the flag would have chosen model B (pilot dz +1.14 km against +0.42 km).

## 2. Scores

Headline from each run's `evaluation/metrics.json`. My own re-matching (2 s / 5 km, Cochran box, `match.py` in the session scratchpad) reproduces dz and time bias within 0.01.

| Score | tools | backend | checker | knowledge | expert / threshold |
|---|---|---|---|---|---|
| time_bias_final_s (run − expert) | +0.059 | −0.112 | **+0.294** | +0.163 | \|·\| ≤ 0.30 |
| time_mad_final_s | 0.049 | 0.043 | 0.087 | 0.034 | ≤ 0.30 |
| dz_final_km (run − expert, below sea level) | **+1.099** | **+1.108** | −0.016 | +0.256 | \|·\| ≤ 1.0 |
| dz_mad_final_km | 0.386 | 0.377 | 0.312 | 0.361 | — |
| shift_final_km | 0.031 | 0.036 | 0.044 | 0.044 | ≤ 1.0 |
| scatter_final_km | 0.257 | 0.269 | 0.222 | 0.236 | ≤ 1.0 |
| depth_mode_share | 0.018 | 0.024 | 0.008 | 0.012 | ≤ 0.111 |
| dmag_median (vs Cochran) | **−2.77** | **−1.43** | −0.07 | −0.11 | expert −0.23; \|·\| ≤ 0.43 |
| dmag_std | 0.374 | **0.481** | 0.371 | 0.390 | ≤ 0.473 |
| dmag_slope_per_unit | −0.275 | **−0.425** | **−0.345** | **−0.332** | expert −0.214; \|·\| ≤ 0.314 |
| dML vs expert final (my match), median / slope | −2.51 / −0.13 | −1.15 / −0.39 | +0.20 / −0.24 | +0.15 / −0.19 | — |
| events with ML / non-rejected | 3,723 / 3,744 | 1,502 / 3,583 | 3,260 / 3,585 | 3,325 / 3,589 | — |
| trust.failed | depth_bias, magnitude_offset | depth_bias, magnitude_offset, magnitude_spread, magnitude_scale | magnitude_scale | magnitude_scale | — |
| recall_final | 0.464 | 0.451 | 0.451 | 0.455 | (front end, not audited) |

Recall and precision come from the shared front end and are not discussed further. The tools catalog also carries 155 Match&Locate rows.

## 3. Decision table

| Decision | tools | backend | checker | knowledge | expert final (r7) |
|---|---|---|---|---|---|
| Velocity model, source | Invented "generic central-Oklahoma (assumed)" model; no search for a published one (`work/runs/inputs/velocity_model_1d.txt`, written 2026-10-28T04:51:14Z) | Invented "generic central-Oklahoma" model; Vs from Wadati (`work/run/prep/velocity_model.txt`, 2026-11-01T00:07:21Z) | Invented `ok_v1` ("generic central-Oklahoma style crust"; `work/work/scripts/prep_inputs.py`, `work/work/data/model_ok_v1.txt`) | CRUST1.0, slowness-averaged under the stations and events, built with the checker's `velocity.py` (`work/run/model_A_crust1.txt`), after a failed attempt to download the Schoenball & Ellsworth (2017) preprint for its model (00:07:24 WebSearch, 00:07:52 curl, 00:15:48 "Network is unusable") | Keranen et al. (2013) GSA DR Fig. DR1, vector-extracted (`data/2011_prague_oklahoma/data/models/velocity_models.json`) |
| Vp, top ≈ 4 km | 0: 4.00 → 1.5: 4.80 → 3: 5.40 → 6: 5.95 | 0: 2.90 → 0.4: 3.60 → 1.2: 4.30 → 2.5: 4.90 → 4: 5.50 → 6: 5.95 | 0: 4.2 → 1: 5.0 → 3: 6.0 → 6: 6.2 | 0: 2.50 / 0.23: 3.94 / 0.73: 4.60 / 1.23: 5.40 / 1.73: 5.73 / 4.33: 6.10 | 0: 2.76 / 1.46: 5.75 / 2.25: 5.74 / 5.18: 6.17 / 8.13: 6.22 (km below the 0.28-km datum) |
| Vp/Vs | 1.73 constant | 1.70 constant (Wadati median 1.695, TLS 1.724) | about 1.74–1.75 constant | Depth-varying from CRUST1: 2.34 / 1.95 / 1.78 / 1.75 / 1.74 / 1.73; Wadati-scaled 1.673 tested as model B and rejected | Inverted jointly, 1.68–1.87 (top layer 1.86) |
| Layering | `linear` (nodes) | `linear` | Pass 1 `step`, pass 2 `linear` (adopted after the checker flag) | `step` (Alin = linear tried on pilot only) | `step` |
| Datum and stations | Reference 0 (sea level); stations at −elevation (`nll_config.json`) | Reference 0; stations at −elevation | Reference 0 (default); stations at −elevation | Reference 0; CRUST1 top at −0.27 clipped to 0 (no effect: top layer extends up to the grid top) | Reference 0.28 km ASL (mean station elevation); depths converted to below sea level for scoring |
| Vertical S−P to 3.6 km bsl (diagnostic, §5.1) | 0.60 s | 0.64 s | 0.60 s step, 0.56 s linear | 0.78 s | 0.77 s |
| Locator, method | NLL `locate.py` EDT_OT_WT | NLL EDT_OT_WT, two passes | NLL EDT_OT_WT, two passes; HypoInverse cross-check not adopted | NLL EDT_OT_WT, one full pass | NLL EDT_OT_WT (r5) |
| TT grid / search | 0.5 km; region depth 0–20 km; grid −1…40 | 0.5 km; default region (station box + 20 km, depth 0–30) | 0.5 km; region 35–36 N, −97.2…−96.3, **depth 0.5–20 km** (136 events pinned at 0.530 km in pass 2) | 0.5 km; default region (depth 0–30); 2.3 % pinned at the 0.05-km top | 0.25 km; −3…35 km |
| Pick weighting | Pick uncertainty from probability (0.05/0.10/0.15/0.25 s); model error 0.1 s | Default P 0.10 / S 0.20 s (no `uncertainty_s` column); model error 0.1 s | Front-end `uncertainty_s`; model error 0.1 s | Front-end `uncertainty_s`; model error 0.1 s | P 0.10 / S 0.20 s; model error 0.30 s |
| Station corrections | None | Pass-1 median residuals (≥ 30 picks, clipped ±0.6 s) as LOCDELAY in pass 2 (`run/prep/delays.csv`; ZQ terms ≈ 0, TA up to −0.47 s); depth unchanged by them (pass 1 +1.109, pass 2 +1.108) | None | None | Two iterated LOCDELAY passes |
| Pick rejection | Post hoc: \|res\| > 2.5 s or unassociated → rejected in picks.csv | \|res\| > 1.0 s (1,062 picks) before pass 2 | First \|res\| > 1.0 s (1,228), then relaxed to \|res\| > 2.0 s and > 6σ, plus S-before-P (210 total) after a checker flag | None (picks.csv byte-identical to the input) | EDT down-weights outliers |
| ZQ.LC17 (placeholder latitude 35.0000) | Used as given | Excluded from location and ML after a failed position solve (`run/prep/lc17_solution.json`) | Used as given | Used as given | Excluded |
| Relative relocation | hypoDD CT+CC: ph2dt MAXDIST 100, MAXSEP 4, MINLNK 8, MINOBS 8, MAXOBS 20; ccdt 2–15 Hz, CC ≥ 0.7, 97,282 dt.cc | hypoDD CT and CT+CC: private build (MAXDATA 12 M), MAXSEP 8, CC weight 6× CT, 58,199 dt.cc on 12 local stations | ccdt 0.5–12 Hz, 92,302 dt.cc; ph2dt MAXSEP 2, MINLNK 6, MAXOBS 10; hypoDD CT+CC, damping 60/40/30, fixed-second residual cutoffs | ph2dt MAXDIST 70, MAXSEP 5, MINLNK 8, MAXOBS 15; ccdt ≤ 4 km, 8 neighbours, 44,398 dt.cc; hypoDD CT, then CT+CC, damping 120 → 60 | None in final (GrowClust only in the stage-70 comparison) |
| hypoDD model | 7 step layers of the same nodes, Vp/Vs 1.73 | 9 constant layers (3.2 at the top), Vp/Vs 1.70 | 6 step layers (= `ok_v1` steps) while NLL used linear, Vp/Vs 1.74 | 14 CRUST1 layers, Vp/Vs 1.73 (not CRUST1's own Vs) | — |
| Relocation in catalog | Overlays NLL for 3,320 events | **Not adopted**: catalog = NLL; hypoDD in `relocations_hypodd.csv` ("additional result, not a substitute", 01:46:01) | Applied where ≥ 4 CC obs and shift ≤ 5 km (2,931); 99 bound-pinned depths without hypoDD blanked | CT+CC for 3,033 events; 555 keep NLL | — |
| hypoDD centroid depth drift (from `hypoDD.log`) | +6 m | −377 m (CT+CC) | **−684 m** | −4 m | — |
| Magnitude response chain | `remove_response(DISP)` + WA 2 zeros, poles −6.2832 ± 4.715i, gain 1, × 2080 × 1000 → mm (`work/scripts/magnitudes_par.py`) | evalresp DISP deconvolution + WA with **one zero** (`WA_ZEROS = [0j]`), gain 2080, × 1e3 → mm (`work/scripts/local_magnitude.py`) | `remove_response(DISP)` + IASPEI WA (2 zeros, −5.49779 ± 5.60886i, magnification 1) × 1e9 → nm (`work/work/scripts/measure_amplitudes.py`) | `ml_reference.wa_trace_nm` (DISP + IASPEI WA, nm) (`work/scripts/ml.py`) | `remove_response(VEL)` + ObsPy WOODANDERSON (1 zero, 2080) × 1000 → mm (`expert/01_pipeline/09_estimate_magnitude.py`) |
| Formula | log10(A_mm) + 1.11 log10 R + 0.00189 R **− 2.09** | log10(A_mm) + 1.11 log10 R + 0.00189 R + 0.5919 (correct for mm) | log10(A_nm) + … − 2.09 (correct) | log10(A_nm) + … − 2.09 (correct) | Hutton & Boore, mm, +3 at 100 km |
| Unit/response error, verified (§5.4) | −2.682 constant | −log10(2πf): −1.14 / −1.41 / −1.71 at 2 / 4 / 8 Hz | none | none | — |
| Amplitude / window | Zero-to-peak; RMS of the E,N maxima; [P, S + 8 s]; decimated to 50 Hz, pre-filter 0.5–1–18–22 Hz | Half p-p; geometric mean of components; [P − 1, S + 45 s]; band 0.4–18 Hz | Half p-p per component; median of components; [P − 0.5, S + max(3, 0.5(S−P))]; pre-filter 0.05–0.1 Hz to 0.4–0.45 fs | Half p-p per component; median; [P − 1, S + max(6, 2·tt) + 4 s] capped at the next event's pick; pre-filter 0.05–0.1 Hz | Peak per N,E; mean of logs; [P − 0.5, P − 0.5 + 2(S−P)]; R ≥ 10 km; ≥ 3 stations; final ML mostly template-chained |
| Distance | Hypocentral incl. elevation | Hypocentral | Hypocentral from relocated positions | Hypocentral from catalog | Hypocentral ≥ 10 km |
| SNR / coverage | None (21 events with ML < −4 blanked after an SNR audit) | SNR ≥ 3 → only 1,502 events | SNR ≥ 3 vs median component noise | Filter SNR ≥ 2.5 | Flag only |
| Large events / clipping | None | None ("no clipping detection was available") | Clip-run test (0 found); checker largest-10 offset −0.01 | Extreme-value share test | Plateau flag |
| ML station terms | None | Alternating-median station corrections, zero-mean gauge | None | None | None (provisional HB) |
| Checker use | — | — | 8 reports, 3 flags, all "fixed" (§4) | 10 reports (4 pilot), 3 `compare.py`, 0 flags on submitted-path reports | — |
| Validity notes | — | `pip install pypdf` into the shared `seismoagent_eval` environment (00:19:58; declared in `notes.md`) | — | Downloaded an Oklahoma relocated-catalog preprint (S&E 2017) to `/tmp/refs` for its model; unreadable, nothing used | — |

## 4. Checker and knowledge behaviour

### 4.1 Checker run: every checker run and what followed

| Report (`work/checker/…`) | Generated (UTC) | Flags | Agent action | Effect on score (my match to expert) |
|---|---|---|---|---|
| `data` | 00:07:56 | none | — | — |
| `picks_input` | 00:21:23 | none | — | — |
| `location` (pass 1: step, 1.0-s pick rejection) | 01:23:51 | `reality.events_with_few_picks` 0.212; `space.depth_layers` 0.181 (slices 2.4–2.9 km) | (a) Few-picks: found that its own 1.0-s rule caused it (input share 17.5 %); relaxed to 2.0 s and 6σ (thinking 01:24:51–01:26:10). Justified: it reverses a self-inflicted change. (b) Layers: called it a step-interface artefact and relocated everything as `linear` (text 01:25:40, adopted 01:38:12, while noting the RMS got worse, 0.071 → 0.099 s). The playbook's discriminating experiment (finer grid, piled subset) was not run; no `compare.py`. | Pick-rule change: no measurable effect. Step → linear: dz +0.72 → +0.62 km, **dz MAD 0.30 → 0.60 km**, **time bias +0.17 → +0.29 s**, epicentral median 0.25 → 0.30 km, shallow events pinned at the 0.5-km floor 86 → 170. The 725 piled events have expert depths of 2.0 km (IQR 1.94–2.5): the pile was a real (or expert-shared) concentration mapped 0.6 km deep. **Net effect: worse.** |
| `location2` (pass 2) | 01:39:39 | none | Adopted | — |
| `relocation_prelim` (first hypoDD build; regenerated at 02:25:09 after being overwritten) | about 02:11 | `space.depth_layers` 0.062 (0.5–0.6, 2.8–2.9, 7.3–7.4 km) | Root cause found by experiment on the products: 136 events at exactly 0.530469 km, the floor of its own region `depth_km [0.5, 20]` (02:16:16). Blanked depth and magnitude (status `uncertain`) for 99 floor-pinned events without a hypoDD depth. Kept the 2.8–2.9 km slice of 170 events as "fault-patch structure" (02:17:26). | Blanking: neutral to slightly positive (removes bound-set depths). The kept slice is a hypoDD compression: those events' expert depths span 1.9–3.1 km (median 2.5), dz +0.38. The justification is not supported. |
| `relocation` | 02:19:49 | none | — | — |
| `magnitude` | 02:22:58 | none (recompute offset +0.22, MAD 0.11, slope 0.93; largest-10 −0.01) | none | The ML was already correct; the method came from reading the checker's `magnitude_recompute.py` (00:09:55) before writing `measure_amplitudes.py` (00:12:10) |
| `final` (`--stage all`) | 02:28:51 | none (45 checks) | `dispositions.json`: 3 entries, all `fixed` (verified gone by the scorer: `metrics.json['checker']`) | — |

`compare.py` and `pilot.py` were listed (00:09) but never run. `--model-ensemble` was not run. The hypoDD centroid drift (−0.68 km) and depth compression raised no flag; `relocated_share` and the shift checks passed. The flag-driven change (step → linear) made the time bias and depth precision worse. The final depth score passed largely because of an unflagged hypoDD artefact. NLL alone would also have passed depth bias (+0.62 or +0.72 km against the 1.0-km threshold).

### 4.2 Knowledge run: what it read and did

Skill files read, all at the start, by `cat` in Bash (timestamps from `record/execution.jsonl`):

- `catalog-checker/SKILL.md` 00:01:19
- `catalog-knowledge/SKILL.md` 00:01:21
- `protocol/pilot_then_full.md` and `symptoms/not_visible.md` 00:01:26
- `playbooks/decide_between_candidates.md` and `symptoms/README.md` 00:01:28
- `symptoms/location_relocation.md` 00:01:29
- `magnitude_completeness.md` and `data_picks_association.md` 00:01:30
- `magnitude/README.md` 00:01:43
- `ml_reference.py` 00:32:06–00:32:08

It also read the checker source `ensemble.py`, `velocity.py` (00:12:23–25) and `pilot.py` (00:15:44). `calibrations.json` was only listed, never opened.

| Procedure | Followed? | Evidence |
|---|---|---|
| `not_visible.md` §1: look for the regional model | Tried (WebSearch, then curl of the S&E 2017 preprint); failed; fell back on CRUST1.0 from the checker's generator, sea-level datum | 00:07:24–00:15:48; `WORKFLOW_NOTES.md` |
| Pilot chosen with `pilot.py events` | Yes: 296 events (180 representative, 56 busiest, 60 largest) | 00:16:41, `run/pilot/pilot.json` |
| Candidates run on the same pilot, checker `--pilot` per candidate | Yes: A (CRUST1 step), B (Vs scaled to Wadati 1.673), C (LITHO1), Alin (A linear) | `run/pilot/nll_{A,B,C,Alin}`, `run/pilot/chk_*` (00:23:30–00:31:33) |
| Item-check verdicts | A, C and Alin flagged `space.sp_depth_offset` (1.91 / 2.05 / 1.89 km); B unflagged (0.28) but 20 % of events at the 0.05-km top | `run/pilot/chk_*/checker_report.json` |
| "Drop candidates that fail item checks" | **Deviated**: kept A. Reasoning was correct but only in words: the S−P scale is calibrated on far TA paths and does not transfer to sediment-covered near paths (thinking 00:25:03). Confirmed afterwards on the full catalog (0.75 km, unflagged). Relative to the expert this was the right call: pilot dz A +0.42, B +1.14 km. | thinking 00:24:47–00:28:51 |
| `compare.py` | C vs A and Alin vs A: `no_difference` → kept A (playbook: keep the simpler product); B vs A never compared; relocation CT vs CT+CC: `no_difference` → adopted CT+CC "because it uses more data" (playbook says keep the simpler one) | 00:28:21, 00:31:18, 01:02:43 |
| Rule 2 / pilot §2: decide on the full run | **Deviated**: the model was chosen on the pilot ("Decision: model A", 00:31:47); no full run of a second candidate | timeline |
| Rule 3: write the adoption rule first | **Not done**: no adoption rule appears before the experiments in the text or the thinking | thinking 00:20:21 ("run model B … and compare") |
| "Do not choose by RMS" | **Partly deviated**: "A has best RMS" is among its reasons | thinking 00:28:51 |
| `not_visible.md` §2: compare representations on the full catalog | **Deviated**: step vs linear only on the pilot. On the pilot, linear was closer to the expert (dz +0.27 vs +0.42 km, dt +0.20 vs +0.15 s). | `run/pilot/nll_Alin` |
| `not_visible.md` §4: report model sensitivity (`--model-ensemble`) | **Not done** | final report has no ensemble |
| Magnitude: units and response | Followed: imported `wa_trace_nm`, `ml_iaspei`, `half_peak_to_peak`; standard IASPEI chain; `selftest` and `recompute` not run (relied on the checker's recompute: MAD 0.058, measured 0.0695) | `scripts/ml.py`, `checker/magnitude/` |
| Magnitude: regional calibration | Not examined (`calibrations.json` holds `kim_1998_eastern_north_america`, a possible central-US alternative; IASPEI used) | — |

The knowledge run's location advantage over backend (dz +0.26 vs +1.11 km) comes from CRUST1's sediment layer. The skill's "look for a regional model" pushed the agent to search, but it was the fallback that worked. Its pilot experiments correctly rejected model B against a misleading item check. It spent about a quarter of the backend run's wall time (4,536 s vs 17,130 s) and about half the cost ($11.3 vs $22.2).

## 5. Attribution

### 5.1 Evidence: a model-only prediction from each run's own grids

`synth.py` (session scratchpad, read-only):

1. Took 800 random events matched to the expert final and their actual non-rejected front-end stations and phases (LC17 dropped).
2. Computed "true" arrival times from the expert r5 Keranen grids (`expert/export/r5/04_locate_nonlinloc/grids`, 0.25 km, datum 0.28) at the expert hypocentres.
3. Relocated those times with each run's own NonLinLoc grids: L2 with P/S weights 1/0.1² and 1/0.2², origin time solved, depth searched in 0.02-km steps, epicentre fixed.

The expert's own grids recover 0.00 km and 0.000 s (control).

| Grids | Predicted dz (MAD) | Predicted dt | Observed at NLL stage (dz / dt) | Observed final |
|---|---|---|---|---|
| tools (generic, linear) | +1.02 (0.31) | +0.052 | +1.03 / +0.070 | +1.10 / +0.059 |
| backend pass 2 (generic, linear) | +1.17 (0.33) | −0.124 | +1.11 / −0.112 | +1.11 / −0.112 |
| checker pass 1 (ok_v1 step) | +0.62 (0.17) | +0.145 | +0.72 / +0.166 | — |
| checker pass 2 (ok_v1 linear) | +0.38 (0.39) | +0.267 | +0.62 / +0.294 | −0.02 / +0.294 |
| knowledge A (CRUST1 step) | +0.16 (0.14) | +0.165 | +0.30 / +0.163 | +0.26 / +0.163 |
| knowledge Alin (pilot) | +0.07 (0.15) | +0.200 | pilot +0.27 / +0.202 | — |
| knowledge B, Vp/Vs 1.673 (pilot) | +0.73 (0.70) | +0.118 | pilot +1.14 / +0.131 | — |
| knowledge C, LITHO1 (pilot) | +0.47 (0.42) | +0.023 | pilot +0.58 / −0.010 | — |

Intermediate products matched to the expert (my re-match):

| Product | dz | dz MAD | dt | epicentral median |
|---|---|---|---|---|
| tools NLL → hypoDD (3,320) | +1.03 → +1.11 | 0.40 → 0.37 | +0.070 → +0.058 | 0.247 → 0.251 |
| backend NLL pass 1 → pass 2 (final) | +1.109 → +1.108 | 0.38 → 0.40 | −0.108 → −0.112 | 0.267 → 0.268 |
| backend hypoDD CT / CT+CC (not adopted) | +0.67 / +0.67 | 0.47 / 0.45 | −0.114 / −0.113 | 0.356 / 0.321 |
| checker NLL step → linear → hypoDD (final) | +0.72 → +0.62 → −0.04 | 0.30 → 0.60 → 0.29 | +0.166 → +0.294 → +0.294 | 0.248 → 0.302 → 0.221 |
| checker HypoInverse (same model, not adopted) | +0.93 | 0.49 | +0.219 | 0.347 |
| knowledge NLL → CT → CT+CC (final) | +0.30 → +0.27 → +0.26 | 0.37 | +0.163 | 0.264 → 0.240 → 0.241 |

### 5.2 Score difference → cause

| Score difference | Most plausible cause | Confidence | Why |
|---|---|---|---|
| dz: tools +1.10 and backend +1.11 vs knowledge +0.26 | Velocity model: generic models with constant Vp/Vs 1.70–1.73 and no slow high-Vp/Vs sediment layer give too little S−P per km near the surface, so events go deep. CRUST1's sediment (Vs 1.07, Vp/Vs 2.34) mimics Keranen's slow top layer (Vs 1.48, 1.46 km thick). | High | Model-only prediction from each run's own grids matches within 0.15 km. Station delays (backend), pick rejection (backend, checker) and relocation (tools, knowledge) each change dz by ≤ 0.1 km. Expected vertical S−P to 3.6 km: 0.60 / 0.64 vs 0.78 (CRUST1) vs 0.77 (Keranen). |
| dz: checker −0.02 vs its own NLL +0.62/+0.72 | hypoDD centroid drift −0.68 km plus depth compression toward about 2.5–3 km. Mechanism inside hypoDD uncertain: low damping 60/40/30, absolute residual cutoffs 0.2–0.8 s, step hypoDD model on linear NLL starting locations, or a combination. | High that hypoDD did it; medium-low on why | `hypoDD.log` centroid lines; per-event shift +1.13 km for start depth < 0.6 and −1.35 km for 6–8 km. Tools (damping 120 → 60, multiple-of-σ cutoffs) and knowledge (120 → 60) drift ≤ 6 m. Backend (CC weight 6×, damping 120/80) drifts −0.38 km. |
| dz: depth_bias pass/fail of backend | Partly the decision to keep NLL as the catalog: its own hypoDD would have scored +0.67 (pass), via the same kind of centroid drift (−0.38 km) | High (counterfactual is in the run's own `relocations_hypodd.csv`) | — |
| time bias: checker +0.29 vs others | Linear representation adopted in response to `space.depth_layers` (a faster near-surface model → later origins). Step would have given +0.17. | High | Observed pass 1 vs pass 2 on identical inputs: +0.166 → +0.294; prediction +0.145 → +0.267 |
| time bias: backend −0.11 vs tools +0.06 vs knowledge +0.16 | Velocity model average (backend slow at 1.2–4 km: 4.3–5.5 vs 5.75; CRUST1 fast below 1.7 km) | High | Prediction −0.124 / +0.052 / +0.165 |
| dz MAD: checker 0.31 (best) | hypoDD compression (from 0.60 at the linear NLL stage) | Medium | — |
| scatter: checker 0.222 < knowledge 0.236 < tools 0.257 < backend 0.269 | Relocation adopted or not (checker and knowledge gain about 0.02–0.08 km from CT+CC; tools' hypoDD gains nothing; backend NLL only) | Medium (small differences) | Epicentral medians in the table above |
| dmag: tools −2.77 | A in mm used with the −2.09 constant (nm, magnification-1 form): −2.682 exactly | High | Recomputing from `runs/magnitude/ml_stations.csv` with +0.591: −2.51 → +0.17 vs expert, the same as the correct runs (+0.15 / +0.20). The agent rationalised ML down to −8 as "borehole noise floor" (`NOTES.md` §8). |
| dmag: backend −1.43, slope −0.43, std 0.48, ML for only 1,502 events | ObsPy-type one-zero WA (velocity input) applied to displacement: −log10(2πf) ≈ −1.1 to −1.7. Its 1/f weighting lets low-frequency noise inflate small-event amplitudes (dML vs expert −0.76 at M < 0, −1.5 at M ≥ 1.5 → negative slope) and lowers SNR, so the SNR ≥ 3 cut keeps only 11–47 % of the M < 0.5 events. | High for offset; medium for slope and coverage | Response ratio computed (§3); README §2 documents this exact trap |
| dmag: checker −0.07 and knowledge −0.11 (pass, better than the expert's −0.23) | Correct IASPEI chain; +0.15–0.20 above the expert's template-chained ML | High that the chain is correct; low on why they sit above the expert | — |
| slope: checker −0.345 and knowledge −0.332 (fail) vs tools −0.275 (pass) | Small events +0.4–0.55 above the expert. Not R < 10 km and not low SNR (tested: R ≥ 10 km → slope vs expert −0.19 → −0.25; SNR ≥ 5 → −0.25). Leading hypothesis: long-period noise (pre-filter corner 0.05–0.1 Hz; microseisms leak through WA) and long windows inflate small-event amplitudes. Tools' 0.5–1 Hz high-pass would explain its smaller slope. | Medium-low | `mag.py` and the recompute tests in §5.4 |

### 5.3 What the checker and knowledge arms changed

- **Checker arm vs backend.** The location score improved, but not through the checker. The checker run's own model happened to be less biased than backend's (+0.62/+0.72 vs +1.11). Its depth bias then reached about 0 through an unflagged hypoDD drift. The one flag-driven change (step → linear) worsened the time bias by 0.12 s and doubled the depth MAD. The magnitude improvement came from reading checker source code. No flag fired on magnitudes, because the method was already right.
- **Knowledge arm vs backend.** The location improvement came from the CRUST1 fallback model, chosen through a proper pilot comparison. The agent resisted a misleading item check, which was correct relative to the expert. The magnitude improvement came from `ml_reference.py`. The protocol deviations (pilot-level decision, no adoption rule, no full-catalog representation comparison, no sensitivity report) did not hurt here. They would have mattered if the linear representation (pilot dz +0.27 vs +0.42) had been the better choice at full scale.
- **Checker design findings.**
  - `sp_depth_offset` is biased by about +1 to +1.5 km where a slow, high-Vp/Vs sediment layer covers the source region. It flagged the better model and passed the worse one on the knowledge run's pilot.
  - `depth_layers` cannot tell an interface pile from a real concentration that the reference catalog also has.
  - No check sees a hypoDD centroid drift of −0.68 km. A check comparing the relocated and absolute median depth and origin time (a `catalog_before` comparison) would.

### 5.4 Read-only verifications done for this audit

- WA response ratios (Python):
  - One zero applied to displacement vs IASPEI two zeros: −0.85 / −1.14 / −1.41 / −1.71 / −1.98 log units at 1 / 2 / 4 / 8 / 15 Hz.
  - Tools' two-zero poles vs IASPEI: ≤ 0.05 at 1–15 Hz.
  - log10(2080 × 10⁻⁶) = −2.682.
- Tools ML recomputed with the mm constant: median vs expert +0.17, slope −0.134 (unchanged slope; the offset error is purely constant).
- Knowledge and checker ML recomputed from their component amplitudes with the R ≥ 10 km and SNR ≥ 5 variants (table in §5.2); neither reduces the slope.
- Model-only prediction and intermediate-product matching (§5.1).

## 6. Proposed single-factor experiments

1. **Model swap on fixed back-end inputs (highest value).**
   - Setup: rerun the backend run's pass 2 exactly (`work/run/prep/arrivals_pass2.csv`, `stations_pass2.csv`, `delays.csv`, `nlloc_config.json`, `locate.py`), changing only the model.
   - (a) Keranen, step, `reference_elevation_km 0.28`, depths converted to below sea level. Predicted: dz +1.11 → +0.0 to +0.2 km, dt −0.11 → ≈0.
   - (b) The knowledge run's `model_A_crust1.txt`. Predicted: +0.2 to +0.3 km, +0.16 s.
   - (c) The tools model. Predicted: +1.0 km, +0.05 s.
   - This confirms that the location ranking of all four runs is the model and nothing else. Cost: about three NLL runs.
2. **hypoDD drift test (checker run).**
   - Setup: rerun `work/work/reloc/hypodd_run` with identical dt.ct, dt.cc and starting locations, changing one factor at a time.
   - (a) Damping 120 → 60 with multiple-of-σ cutoffs (−9 / 6 / 4), as the knowledge and tools runs used.
   - (b) A hypoDD layer model densified (0.25 km) to match the NLL linear profile.
   - (c) Starting locations from step pass 1.
   - Read the centroid shift in `hypoDD.log` and dz against the expert. If (a) removes most of the −0.68 km, the checker run's depth "pass" is a damping artefact. The same test on the backend run's `out_cc` explains its −0.38 km.
3. **Magnitude.**
   - (a) Backend: rerun `scripts/measure_amplitudes.py` + `compute_ml.py` with `WA_ZEROS = [0j, 0j]` (one line) on a stratified 300-event sample. Predicted: offset shifts by +1.1 to +1.5, slope from −0.43 toward −0.3, coverage rises from 42 % to ≥ 90 %.
   - (b) Knowledge: recompute amplitudes one factor at a time:
     - pre-filter high-pass 0.5–1 Hz (as in tools);
     - the expert window [P − 0.5, P − 0.5 + 2(S−P)];
     - mean of log N,E instead of the median of components.
   - Then measure the slope against Cochran. Predicted: the high-pass removes most of the +0.4–0.55 small-event excess and brings the slope inside 0.314.
4. **Representation at full scale (knowledge run).** Run CRUST1 `linear` on the full catalog (the pilot predicts dz +0.27 → +0.07 to +0.27, dt +0.16 → +0.20) and compare with `compare.py`. This tests whether the pilot-level decision was right.
5. **Region floor (checker run).** Rerun pass 2 with region depth [−0.3, 20] km. Predicted: the 136 events at 0.530 km disperse, the dz MAD at the NLL stage falls from 0.60 toward 0.35, and the 99 blanked depths are recovered.
6. **Checker calibration.** Run the location stage on the expert final catalog with the same picks. If `sp_depth_offset` reports about +1 km for the expert too, the check is biased in sediment-covered regions, and its range or its S−P scaling, which uses a crustal k from far paths, needs revisiting before it is used to choose models.
