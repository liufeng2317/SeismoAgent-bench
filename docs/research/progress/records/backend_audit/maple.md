# Back-end audit: 2017 Maple Creek, Yellowstone (four GLM-5.3 runs)

Audit date 2026-11-02. Read-only: no run, product or scorer was changed, and no agent was run. The four runs locate the same fixed front end: the PhaseNet picks and PyOcto association of the formal tools run (89,447 picks, 3,906 associated events, picks at 19 of 27 stations; `workflows/tasks/2017_maple_creek_yellowstone/backend/frontend/README.md`). All four catalogs share the event IDs. "Truth" is the expert human-in-the-loop final catalog (`expert/export/r11/60_catalog/catalog_events.csv`, 12,600 events, depth in km below sea level). Magnitude scores are against ComCat/UUSS (`evaluation/metrics.yaml`). Every catalog reports `depth_km` below sea level (bsl), and the scorer treats it that way.

Run directories (relative to `workflows/tasks/2017_maple_creek_yellowstone/runs/`):

- **tools**: `tools/claude/glm-5.3/20261028T220746Z` (full pipeline from waveforms; no checker; its picks are the fixed front end)
- **backend**: `backend/claude/glm-5.3/20261101T185337Z` (fixed front end; tools view without the checker)
- **checker**: `backend_checker/claude/glm-5.3/20261101T185359Z` (adds the catalog-checker skill and the disposition contract)
- **knowledge**: `backend_knowledge/claude/glm-5.3/20261101T185422Z` (adds the checker, the catalog-knowledge skill and `agent_resource/magnitude`)

In this document, "the checker run" and "the knowledge run" mean the backend_checker and backend_knowledge runs. "Checker" alone means the tool. No arm was given the regional model file `data/2017_maple_creek_yellowstone/data/models/velocity_models.json`, so every agent picked its velocity model itself (`input_backend*.json`).

## 1. Summary

- **The knowledge run reproduced the formal tools run's absolute catalog almost exactly**, because it made the same velocity-model choice. Both used the Husen & Smith (2004, BSSA 94, 880–896) Table 1 minimum 1-D model, interpolated linearly between nodes, with sea level as the datum (`reference_elevation_km 0`) and the depth search starting at 0 km bsl. Against the expert final, the knowledge run's absolute NonLinLoc catalog has dz −2.22 km and dt +1.18 s; the tools catalog has −2.18 km and +1.15 s. The scored −2.50 km comes from hypoDD, which added −0.28 km overall and −0.53 km on the 2,113 relocated events (§6).
- **The +1.18 s origin-time bias is caused by the velocity model, not by the datum or the representation.** In the expert's UUSS model, P travels at 2.72–2.79 km/s from the surface (2.3 km above sea level) down to 2.0 km bsl. Husen & Smith, interpolated linearly, already reaches 3.7–5.4 km/s there. One-way vertical P time from the surface to 6.5 km bsl is 1.75 s in the knowledge model against 2.40 s in the expert's (S: 3.05 s against 3.87 s). An independent single-factor test confirms this (§5): the same 500 events, the same fixed picks and the same L1 grid-search locator, with only the model changed. The knowledge model gives origin times +0.94 s later than the expert's model. The checker run's model gives −0.25 s. The same test reproduces the expert's own r1 diagnosis that the linear ramp makes origins +0.47 s late, and it reproduces the checker-minus-knowledge differences of the real catalogs: +2.77 km against the observed +2.53 km, and −1.19 s against the observed −1.18 s.
- **The −2.5 km depth bias is only partly the model.** With the same locator, the knowledge model is only 0.4 km shallower than the expert's model. The rest is shared by every agent or added by the knowledge run's own processing:
  - −0.8 km is the gap between a plain single-pass location with the expert model and the expert final. The expert used its own picks, including P at the vertical-only site YGC 6 km from the swarm, two passes of station delays, and Match&Locate. The expert final is also 1.46 km deeper than ComCat with the same model.
  - hypoDD adds −0.3 to −1.0 km.
  - The knowledge run's error is largest for poorly constrained events: −2.9 km and +1.26 s for events with 4–7 picks.
  - Against ComCat, the knowledge run is only −0.91 km too shallow, and the checker run is +2.64 km too deep.
- **The checker run's near-zero bias (dt −0.05 s, dz +0.44 km) comes from three decisions it did not plan as such, and its depth is a cancellation.**
  1. It intended its "generic Yellowstone" Vp profile to start at the surface (2.389 km above sea level). It ran it with `reference_elevation_km 0`, so the profile starts at sea level. The 3.0 km/s cover therefore extends 2.4 km deeper than intended and imitates the expert's slow 2.7–2.8 km/s layer. In the same-locator test this datum shift alone moves origin times by −0.66 s (from +0.41 to −0.25 s).
  2. A travel-time calibration from its own residuals set Vs = Vp/1.546, below the data's Wadati Vp/Vs of 1.608. This moves depths about 0.9 km deeper.
  3. GrowClust kept the centroid fixed (−0.05 km).
  Its depth error is −0.84 to −1.0 km for events with 4–7 picks and +1.2 to +1.5 km for events with 10 or more picks. The median of +0.44 averages errors of opposite sign, and its dz MAD (1.30 km) is almost twice the knowledge run's (0.71 km).
- **The checker did not drive the checker run's good result.** The checker was first run on the location after the model had already been calibrated (20:45 UTC). All three flags were justified, and `compare.py`/`pilot.py` were never used. The model change was driven by the station residuals of NonLinLoc pass 1. One residual, YHL P −1.9 s, disappeared after calibration.
- **The knowledge run followed the playbook closely, but the playbook could not see this error.** `not_visible.md` names it ("a near-surface layer that is too fast pushes them shallower"), and the run read it at 18:55:02. It then picked a published regional model, kept that model's sea-level datum, compared step and linear on a pilot, ran the grid experiment and `compare.py` with an adoption rule written beforehand, and cross-checked with HypoInverse and GrowClust. It also ran `--model-ensemble`, which found an origin-time agreement of only 0.25 with an ensemble spread of 1.18 s, the size of the eventual bias. The run reported this but did not act on it. The reference-free check `wadati_origin_offset` pointed the wrong way: −0.29 s for the knowledge run against +0.88 s for the checker run.
- **The backend run is a different failure: a wrong Vs model plus over-aggressive pick rejection.** It misread its Wadati slope of 1.60 as Vp/Vs 2.65 and built a model with Vp/Vs 1.73–1.83. This left large negative S residuals (YHL −5.3 s, YMC −1.7 s) and moved pass-1 epicentres a median 8.4 km from the other runs. It then judged the mismatch to be "physically impossible" swarm-contaminated picks and rejected 10,570 picks (28 %). These included 44–80 % of the picks at the three stations nearest the swarm (YMC, YHL, YMR). The final epicentres sit 9.6 km SE of the other runs: recall 0.148, out-of-mask 0.586.

## 2. Score table

From `evaluation/metrics.json` → `headline` (dt and dz are run minus expert final; positive dz means deeper). Recall is against ComCat.

| metric | tools | backend | checker | knowledge |
|---|---|---|---|---|
| time_bias_final_s | +1.149 | −0.277 | **−0.051** | +1.177 |
| dz_final_km | −2.184 | +0.113 | **+0.445** | −2.505 |
| dz_mad_final_km | 0.986 | 1.748 | 1.302 | **0.708** |
| shift_final_km | 0.907 | 0.809 | **0.258** | 0.553 |
| scatter_final_km | 1.898 | 2.873 | 1.953 | **1.587** |
| depth_mode_share | 0.038 | 0.103 | 0.024 | **0.023** |
| out_of_mask_fraction | 0.127 | 0.586 | 0.128 | **0.122** |
| off_structure_fraction | 0.118 | 0.286 | 0.235 | **0.086** |
| dmag_median | 0.19 | 0.34 | **0.15** | 0.19 |
| dmag_slope_per_unit | −0.444 | −0.511 | −0.500 | −0.484 |
| recall (ComCat) | 0.944 | 0.148 | 0.888 | **0.946** |
| dz_median_km vs ComCat | −0.07 | +3.05 | +2.64 | −0.91 |
| dt_median_s vs ComCat | +1.011 | +0.387 | +0.227 | +1.100 |
| trust.failed | inside_region, time_bias, depth_bias, horizontal_scatter, off_structure, magnitude_scale | inside_region, after_large_events, horizontal_scatter, off_structure, depth_pileup, magnitude_spread, magnitude_scale | inside_region, horizontal_scatter, off_structure, magnitude_spread, magnitude_scale | inside_region, time_bias, depth_bias, horizontal_scatter, off_structure, magnitude_scale |
| checker audit | – | – | 6 runs, 3 flags (events_with_few_picks, silent_stations, depth_layers), all justified, flags_agree | 10 runs, 2 flags (events_with_few_picks, silent_stations), both justified, flags_agree |

The knowledge run is the best of the four on every within-catalog quality metric (scatter, depth MAD, mode share, off-structure). It is worst on both bias metrics. The checker run wins on time bias, depth bias and shift, but has 2.7× the off-structure share and nearly twice the depth MAD.

## 3. Decision table

| decision | tools (formal) | backend | checker | knowledge | expert |
|---|---|---|---|---|---|
| Vp source | Husen & Smith 2004 Table 1 minimum 1-D (`run/assoc/velocity_model.txt`) | "generic 16-layer Yellowstone profile from tomography averages", agent-built (`runs/prep/velocity_model_1d.txt`, 19:05 UTC) | "generic Yellowstone crust" 8 layers, agent-built (`scripts/prep_inputs.py`, 19:00:23), then a data fit with factors 1.0/1.0/0.85 for <4 / 4–14 / >14 km bsl (`run/locate-input/model_fit.json`, 20:28:49) | Husen & Smith 2004 Table 1, PDF downloaded from uusatrg.utah.edu and transcribed (19:03:42–19:04:33), matches the table | UUSS Yellowstone 1-D (Pang et al. 2019 SI Table S1) |
| Vs / Vp/Vs | tabulated H&S Vs (Vp/Vs 1.96 at 0 km bsl, 1.35–1.6 at 14–18 km) | tabulated, Vp/Vs 1.83 shallow to 1.73 deep; misread Wadati slope 1.60 as Vp/Vs 2.65 (18:59:08) | pass 1: Vp/1.608 (Wadati); pass 3: Vp/1.5462 (Vs × 1.04 from the S-residual fit, 20:30:43) | tabulated H&S Vs | tabulated, 1.60–1.66 |
| datum / reference elevation | sea level (ref 0) | sea level (ref 0) | intended 2.389 km ASL (`model.txt` header), run with ref 0, so the model starts at sea level; noticed 20:16 and kept "as written" | sea level (ref 0), the datum H&S states | 2.3 km ASL (`association.yaml reference_elevation_km`) |
| station elevations | NonLinLoc station z = −elevation (GRID2D) | same | same | same; hypoDD ignores elevations | z = 2.3 − elevation (GRID2D) |
| step vs linear | linear (step put about 50 % on the 2-km interface) | linear | step | linear (pilot: step put 46 % at 2.016 km, 19:10:49) | step (r2: linear was +0.47 s late) |
| locator, method | NonLinLoc EDT_OT_WT; HypoInverse cross-check | NonLinLoc EDT_OT_WT | NonLinLoc EDT_OT_WT; GAU_ANALYTIC retry for 10 events | NonLinLoc EDT_OT_WT; HypoInverse 1.40 cross-check | NonLinLoc EDT_OT_WT (r9) |
| travel-time grid | 0.5 km, −4.5 to 40 km | 0.5 km, −3 to 42 km | 0.5 km, −3 to 40 km | 0.5 km, then 0.1 km (`runs/nll_full_g01`) | 0.25 km, −3 to 35 km |
| depth search | [0, 25] km bsl | [0, 20] km bsl, lat 44.35–44.95, lon −111.45 to −110.45 | default [0, 30] km bsl | default [0, 30] km bsl (a −2 km top was tested on the pilot and dropped, 19:14:54) | [0, 20] km below the datum = [−2.3, 17.7] km bsl |
| pick weights | 0.10 / 0.20 s; model error 0.1 s | σP = 0.06 + 0.34(1−p), σS = 1.5σP; model error 0.1 | 0.10 / 0.20 s; model error 0.1 | σP = clip(0.05 + 0.5(1−p)², 0.05, 0.40), σS = 1.8σP; model error 0.1 | 0.10 / 0.20 s; model error 0.30 s |
| station corrections | none | pass 2: median terms clipped to ±0.75 s | pass 2 with delays of the wrong sign (YHL −2.03 → −4.36 s), abandoned; none in the final | none ("not separable") | two iterated LOCDELAY passes |
| outlier rejection | none | 10,570 picks rejected (residual < −1.5 s or > +2.5 s after terms) | 413 picks marked rejected after pass 3 (weight 0 and \|res\| > 2 s); not relocated | none (picks byte-identical) | EDT robustness only |
| relative relocation | ccdt + hypoDD, auxiliary, not merged | ccdt + hypoDD and GrowClust, not merged (cross-check failed) | ccdt (≤ 6 km, 25 neighbours) + GrowClust ngoodmin 2, merged for 2,601 events | ccdt + ph2dt + hypoDD CT+CC, merged for 2,114 events; GrowClust cross-check | Match&Locate template frame (stage 64) |
| magnitude | IASPEI form, A in nm, [S−1, S+10] s, station median | Hutton & Boore with 2800 magnification, A in mm, [S−1, S+8] s, SNR ≥ 2 | IASPEI, [P−1, S+max(3, …)+2] s, SNR ≥ 3, mean of components, median of stations | IASPEI, R = depth bsl + station elevation; Pechmann 2007 considered (−0.12) but not adopted | chain ML (template) + direct ML |

The expert's choices are verified in `expert/00_config/nonlinloc.yaml`, `association.yaml` (reference_elevation_km 2.3, velocity_layering step, depth_bounds [0, 20]), `01_pipeline/04_locate_nonlinloc.py` (LAYER cards with gradient 0 for step, GTSRCE z = 2.3 − elevation, LOCDELAY passes) and `PLAN.md` r2/r5/r9.

## 4. The velocity models, numerically

Below are Vp and Vs at depths below a 2.3 km ASL surface (z_bsl = d − 2.3), as each run represented the model in NonLinLoc. Values above the first node take the top value. That is the NonLinLoc interface's `layer_lines` behaviour, and the expert's too.

| depth below surface (km) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Vp expert UUSS step (datum 2.3 ASL) | 2.72 | 2.72 | 2.79 | 2.79 | 2.79 | 5.21 | 5.21 | 5.21 | 5.56 | 5.56 | 5.56 |
| Vp knowledge/tools H&S linear (sea level) | 3.73 | 4.31 | 4.88 | 5.16 | 5.31 | 5.37 | 5.39 | 5.40 | 5.41 | 5.58 | 5.82 |
| Vp H&S step (sea level) | 2.76 | 2.76 | 2.76 | 5.05 | 5.05 | 5.35 | 5.35 | 5.40 | 5.40 | 5.41 | 5.41 |
| Vp checker calibrated step (sea level) | 3.00 | 3.00 | 3.00 | 3.00 | 3.80 | 4.40 | 4.40 | 4.40 | 5.10 | 5.10 | 5.10 |
| Vp backend linear (sea level) | 2.60 | 2.60 | 2.60 | 2.88 | 3.35 | 3.92 | 4.42 | 4.83 | 5.20 | 5.46 | 5.68 |
| Vs expert | 1.66 | 1.66 | 1.74 | 1.74 | 1.74 | 3.23 | 3.23 | 3.23 | 3.42 | 3.42 | 3.42 |
| Vs knowledge/tools | 1.89 | 2.19 | 2.49 | 2.85 | 3.23 | 3.35 | 3.35 | 3.37 | 3.39 | 3.42 | 3.44 |
| Vs checker | 1.94 | 1.94 | 1.94 | 1.94 | 2.46 | 2.85 | 2.85 | 2.85 | 3.30 | 3.30 | 3.30 |
| Vs backend | 1.42 | 1.42 | 1.42 | 1.56 | 1.80 | 2.10 | 2.39 | 2.65 | 2.87 | 3.05 | 3.20 |

One-way vertical travel time from the surface (2.3 km ASL):

| model | tP to 4.0 km bsl | tS to 4.0 km bsl | tP to 6.5 km bsl | tS to 6.5 km bsl | S−P to 6.5 km bsl |
|---|---|---|---|---|---|
| expert UUSS step | 1.94 | 3.13 | 2.40 | 3.87 | 1.48 |
| knowledge/tools H&S linear | 1.28 | 2.31 | 1.75 | 3.05 | 1.31 |
| H&S step | 1.60 | 3.04 | 2.07 | 3.78 | 1.72 |
| checker calibrated | 1.84 | 2.84 | 2.36 | 3.64 | 1.29 |
| backend | 2.05 | 3.77 | 2.54 | 4.68 | 2.13 |

The key difference is the top 4.3 km below the surface. The UUSS model holds 2.72–2.79 km/s down to 2.0 km bsl. Husen & Smith has a single node at −4 km (2.76 km/s) and the next at sea level (5.05 km/s). As a linear gradient, the near-surface is fast. As steps, the slow layer stops 2 km higher than in UUSS. The tools and knowledge runs read the H&S datum correctly: Table 1 marks −4.0 as "above sea level" and 2.0 as "below sea level", and the knowledge run transcribed it at 19:04:20. Below about 2 km bsl, H&S (5.35–5.41) and UUSS (5.21–5.56) are similar. The checker run's model is about 0.2–0.6 km/s faster than UUSS above 1 km bsl and much slower between 2 and 8 km bsl (4.4 against 5.21). These errors cancel in the vertical P time (2.36 s against 2.40 s to 6.5 km bsl).

## 5. Same-locator test: velocity model and datum as the only factor

Method: I wrote a small 1-D first-arrival tracer (thin-layer direct waves plus head waves along every layer top, so gradients become turning rays). Each model was used exactly as the run represented it (step or linear, datum, extension above the first node, Vs as used). An L1 grid-search locator then relocated the same 500 events: a random sample of in-box knowledge-run events with ≥ 10 picks, seed 1, using the fixed front-end picks with weights P 1/0.1 and S 1/0.2. Origin time is the median residual; the search covers ±6 km at 0.5 km and depth −1 to 20 km bsl at 0.25 km, then refines to 0.1 km horizontally and 0.05 km in depth. Scripts and outputs are in the session scratchpad (`tt1d.py`, `minilocate.py`, `minilocate_500*.csv`). They are not part of the repository.

Validation:

- With the expert model, this locator lands dz −0.81 km and dt +0.07 s from the expert final, with a 1.48 km epicentral difference (n = 480 matched).
- UUSS linear against UUSS step gives +0.47 s. This is exactly the bias the expert measured for its r1 linear ramp (`expert/PLAN.md` r2: "+0.47 s").
- Against the runs' real NonLinLoc catalogs on the same events, the offsets are +0.63 km / −0.09 s (knowledge final) and +0.49 km / −0.02 s (checker final).

| model, as represented | dz vs expert model, same locator (km) | dt (s) | epi (km) | dz vs expert final (km) | dt vs expert final (s) | median L1 misfit (s) |
|---|---|---|---|---|---|---|
| expert UUSS step, datum 2.3 ASL (reference) | 0 | 0 | 0 | −0.81 | +0.07 | 0.186 |
| **knowledge/tools: H&S linear, sea level** | **−0.40** | **+0.94** | 0.99 | −1.52 | +1.04 | 0.117 |
| H&S step, sea level (the representation the knowledge run rejected) | −1.35 | +0.53 | 0.71 | −2.42 | +0.59 | 0.255 |
| H&S linear, Vs = Vp/1.62 (Vs factor) | +0.08 | +0.95 | 1.43 | −0.82 | +1.01 | 0.091 |
| H&S linear, nodes taken below a 2.3 km surface (datum factor) | −0.50 | +0.37 | 1.24 | −1.65 | +0.43 | 0.323 |
| UUSS linear, datum 2.3 (representation factor) | +0.27 | +0.47 | 1.00 | −0.63 | +0.54 | 0.111 |
| UUSS step, datum at sea level (datum factor) | +0.45 | −0.74 | 1.32 | −0.49 | −0.67 | 0.336 |
| UUSS step, Vs × 1.04 (checker's Vs scaling) | +0.65 | −0.01 | 1.12 | −0.21 | +0.06 | 0.109 |
| **checker calibrated step, sea level (as run)** | **+2.37** | **−0.25** | 1.14 | +1.54 | −0.18 | 0.129 |
| checker calibrated with Vs = Vp/1.608 | +1.50 | −0.25 | 0.90 | +0.78 | −0.18 | 0.212 |
| checker pass-1 generic model (no deep factor, Vp/1.608) | +1.50 | −0.25 | 0.91 | +0.78 | −0.18 | 0.212 |
| checker generic, datum 2.389 ASL as intended | +1.00 | +0.41 | 1.14 | +0.04 | +0.49 | 0.105 |
| checker calibrated, datum 2.389 ASL | +1.05 | +0.45 | 1.72 | +0.17 | +0.49 | 0.105 |
| backend linear, sea level | +0.95 | −0.47 | 2.72 | −0.50 | −0.37 | 0.641 |

Readings:

- **Time.** Every Husen & Smith variant is late, from +0.37 s (shifted datum) to +0.95 s (as used). Neither the representation nor the datum removes the lateness; the model itself is too fast in the top 4 km below the surface. The checker run's model is −0.25 s early as run. With the datum it intended it would have been +0.41 s late.
- **Depth.** The model alone explains only −0.4 km of the knowledge run's depth error. The H&S Vs structure accounts for about −0.5 km of that (Vp/Vs 1.96 at sea level; with Vs = Vp/1.62 the offset is +0.08 km). The checker run's +2.37 km is driven by its slow 2–8 km bsl section and its low Vp/Vs. Vs × 1.04 alone moves depths +0.65 to +0.87 km in both the UUSS and the checker model.
- **The deep 0.85 factor** in the checker calibration has no effect in this locator: travel times differ only beyond about 70 km. Its large effect in NonLinLoc (pass 1 → pass 3) is therefore not explained here; see experiment E5.
- **Misfit does not rank the models.** The knowledge model fits the picks better (L1 0.117 s) than the expert's model (0.186 s) and the checker model (0.129 s), yet it places origins about 1 s late. This is `not_visible.md` rule 3 in action.
- **Expected shift, first order.** The vertical-leg deficit of the knowledge model (P −0.65 s, S −0.82 s to 6.5 km bsl) predicts about +0.7 s of origin-time lateness. The full test gives +0.94 s, and the knowledge run's well-recorded events (≥ 10 picks) show +1.03 s against the expert final.

## 6. Stage-by-stage bias (intermediate products against the expert final)

I used my own matcher, which follows the scorer's convention: in-box candidate events, nearest expert event within 2 s and 5 km, medians. It reproduces the scored finals to within 0.03 km and 0.01 s.

| product | n matched | dz (km) | dt (s) | shift (km) | scatter (km) | median depth bsl |
|---|---|---|---|---|---|---|
| tools final (NonLinLoc absolute) | 3,136 | −2.18 | +1.15 | 0.93 | 1.91 | 4.26 |
| knowledge pilot, step (300 events) | 224 | −4.19 | +1.24 | 3.32 | 1.36 | 2.02 |
| knowledge pilot, linear (300 events) | 230 | −2.25 | +1.16 | 0.50 | 1.59 | 4.55 |
| knowledge NonLinLoc 0.5 km grid | 3,160 | −2.28 | +1.17 | 0.97 | 1.95 | 4.17 |
| knowledge NonLinLoc 0.1 km grid (= abs) | 3,162 | −2.22 | +1.18 | 0.97 | 1.89 | 4.17 |
| knowledge final (hypoDD merged) | 3,151 | −2.50 | +1.18 | 0.57 | 1.61 | 3.98 |
| checker pass 1 (generic, Vp/1.608) | 1,545 | −1.22 | +0.22 | 2.25 | 2.68 | 5.02 |
| checker pass 2 (delays with the wrong sign) | 1,190 | −2.97 | +0.62 | 3.91 | 1.17 | 2.20 |
| checker pass 3 (calibrated) = absolute | 2,798 | +0.38 | −0.04 | 0.51 | 2.00 | 6.70 |
| checker final (GrowClust merged) | 2,751 | +0.44 | −0.05 | 0.26 | 1.96 | 6.80 |
| backend pass 1 | 1,054 | −0.01 | −0.29 | 1.02 | 3.16 | 6.47 |
| backend pass 2 (= final) | 978 | +0.14 | −0.28 | 0.80 | 2.90 | 6.56 |

Bias by number of picks, absolute catalog → final:

| picks per event | knowledge abs dz / dt | knowledge final dz / dt | checker abs dz / dt | checker final dz / dt |
|---|---|---|---|---|
| 4–7 | −2.87 / +1.26 | −2.87 / +1.26 | −0.84 / +0.13 | −1.00 / +0.17 |
| 8–9 | −2.47 / +1.20 | −2.72 / +1.17 | +0.16 / −0.02 | +0.14 / −0.00 |
| 10–14 | −1.31 / +1.03 | −2.16 / +1.13 | +1.22 / −0.18 | +1.25 / −0.17 |
| ≥ 15 | −1.33 / +1.03 | −2.34 / +1.15 | +1.47 / −0.21 | +1.20 / −0.17 |

Readings:

- **Knowledge, grid refinement.** The 0.5 → 0.1 km grid change cleared the checker's depth flags but changed bias by only 0.06 km.
- **Knowledge, hypoDD.** hypoDD moved relocated events shallower: median −0.53 km on the 2,113 moved events, and −0.7 km for 10–19 picks. That costs −0.28 km on the scored set and turns well-recorded events from −1.3 to −2.2 km. The hypoDD model was H&S Vp clipped at 0 km with a single Vp/Vs of 1.62, and hypoDD ignores station elevations (`notes/decisions.md` §4). decisions.md reports a "depth median 0.11 km" shift, but that is diluted by the 1,782 events hypoDD did not move.
- **Checker, calibration.** Calibration (pass 1 → pass 3) moved depth +1.6 km and time −0.26 s. It also halved the shift (2.25 → 0.51 km) and recovered matches (1,545 → 2,798). GrowClust changed the centroid by only −0.05 km (signed median on 2,598 moved events) and reduced the shift to 0.26 km.
- **Checker, cancellation.** The checker run's +0.44 km is the median of a shallow-biased group (few picks) and a deep-biased group (≥ 10 picks).

## 7. Attribution, run by run

### 7.1 knowledge: dz −2.50 km, dt +1.18 s

The hypothesis "the velocity model or its datum causes the bias" holds for time and holds only partly for depth.

1. **Velocity model: about +0.95 s and about −0.4 km.** The same-locator test gives +0.94 s and −0.40 km relative to the expert's model. The datum convention (sea level) is the one the source states and is not an error: moving H&S to a 2.3 km surface datum changes dt to +0.37 s and dz to −0.50 km. The linear representation is not the cause either: step gives dt +0.53 s and dz −1.35 km. The cause is the H&S near-surface itself, a single −4 km node and then 5.05 km/s at sea level, where UUSS has 2.79 km/s down to 2 km bsl. H&S is a minimum 1-D model for the whole park from 1995–2002 data. The same paper's 3-D relocations came out systematically about 2 km deeper than the original routine 1-D locations; the knowledge run read this in the abstract (19:04:12).
2. **Locator and front-end gap shared with every agent: about −0.8 km.** A single-pass location with the expert model on the fixed front-end picks lands 0.81 km shallower than the expert final (+0.07 s). The expert's final rests on its own picks, including P at the vertical-only YGC 6 km from the swarm, which the front end lacks (the `silent_stations` flag). It also rests on station delays and Match&Locate. The expert itself documents a +1.4 km offset to ComCat with the same model and attributes it to input differences (`expert/PLAN.md` r7, "Depth-offset diagnostic").
3. **Weakly constrained events: down to −2.9 km.** Events with 4–7 picks carry −2.87 km and +1.26 s against −1.31 km and +1.03 s for ≥ 10 picks (§6). With few S picks near the source, the depth–origin-time trade-off goes shallow and late in a model whose near-surface is fast.
4. **hypoDD: −0.28 km overall (−0.53 km on moved events), about 0 s.** See §6.
5. **The other knowledge decisions moved bias by less than 0.1 km and 0.01 s:** the 0.1 km grid, the pick-σ mapping, no station delays, and Wadati origin times for the 10 unlocatable events.

### 7.2 checker: dz +0.44 km, dt −0.05 s

1. **Datum mismatch (sea level instead of 2.389 km ASL): about −0.66 to −0.70 s and +0.5 to +1.3 km.** The prepared model was "depths km below reference elevation 2.389 km ASL" (`run/locate-input/model.txt`), but pass 1 ran with `reference_elevation_km 0.0` (`run/nll_pass1/config.json`). At 20:15–20:16 the run noticed this. It concluded only that its −2.389 depth conversions had been wrong, then re-declared the profile to be "below sea level" and kept it (NOTES decision 2). In the same-locator test, the generic profile gives +0.41 s and +1.00 km with the intended datum and −0.25 s and +1.50 km with the run datum. The calibrated profile gives +0.45 s and +1.05 km against −0.25 s and +2.37 km. The time accuracy is therefore largely a by-product of this datum shift.
2. **Residual calibration (20:05–20:31): +1.6 km and −0.26 s in NonLinLoc (pass 1 → pass 3).** Pass 1 had YHL P −1.89 s and S −3.04 s, and its epicentres sat about 2.2 km from the expert's. The fit traced P travel times of the pass-1 locations with pyrocko cake and chose depth-band factors 1.0/1.0/0.85, then scaled Vs × 1.04. In the same-locator test the Vs scaling explains about +0.9 km of the deepening, and the deep factor explains almost nothing. Pass 3 removed the YHL residual (−0.007 s), cut the shift to 0.51 km and nearly doubled the matched events. This is "choosing by residual", which `not_visible.md` warns against; the checker run never saw that file. Here it helped horizontally and in time, and it pushed well-recorded events +1.2 to +1.5 km too deep.
3. **Station delays of the wrong sign (pass 2): no effect on the final, which reverted.** Pass 2 is the worst product in the run (dz −2.97 km, shift 3.91 km).
4. **GrowClust ngoodmin 2: about +0.06 km, and the shift fell 0.51 → 0.26 km.**
5. **The depth result is a cancellation.** Few-pick events sit −0.8 to −1.0 km too shallow and well-recorded events +1.2 to +1.5 km too deep (§6). That gives dz MAD 1.30 km and off-structure 0.235, against 0.71 km and 0.086 for the knowledge run. Against ComCat the same catalog is +2.64 km too deep.

### 7.3 backend: dt −0.28 s, dz +0.11 km, recall 0.148

1. **Vs model.** At 18:59:08 the run misread a Wadati slope of 1.607 ("Vp/Vs = 1.607/0.607 = 2.65"), discarded it as noise, and built Vs for Vp/Vs 1.83 → 1.73. This is far above the data's 1.61. S predictions came out late: pass-1 S residuals were −5.34 s at YHL, −6.14 s at FLWY and −1.69 s at YMC, and the pass-1 epicentres sit a median 8.4 km from the knowledge run's.
2. **Pick QC.** At 19:24–19:27 the run read the residuals as "physically impossible arrivals" caused by swarm contamination. It tested contamination against other catalog events and found 0 % matches, but rejected the picks anyway. 10,570 picks were rejected, including 53 % and 44 % of YMC's S and P picks, 80 % and 50 % of YHL's, and 38 % and 25 % of YMR's. This removed the near-field constraint and locked in the mislocation (pass 2: 9.6 km from the knowledge run, out of mask 0.586). The dt and dz scores near zero come from only the 978 events that still match.
3. **Magnitude.** Hutton & Boore with A in mm on a 2800-gain Wood-Anderson is +0.13 above the IASPEI nm form the other runs used (log10(2800/2080) with the constants), and the mislocated distances add to it. This explains most of dmag_median 0.34 against 0.15–0.19.

### 7.4 tools (formal)

Its absolute NonLinLoc catalog uses the knowledge run's model, datum, representation and method on the same picks. It differs in the 0.5 km grid, the fixed 0.10/0.20 s pick errors, `min_s_phases 1`, a [0, 25] km depth region, and in not merging hypoDD. Its bias is therefore the knowledge run's absolute bias (−2.18 km, +1.15 s). Its higher recall comes from its own Match&Locate detections, not from the back end.

### 7.5 Magnitudes (all runs)

dmag_slope is −0.44 to −0.51 per unit in every run, against −0.31 for the expert final. This is the common IASPEI/Hutton & Boore distance correction applied to Yellowstone, not an arm effect. The knowledge run's Pechmann 2007 sensitivity (−0.12) would have moved its dmag_median from 0.19 to about 0.07, but not the slope.

## 8. Checker behaviour

**Checker run.** Six reports were kept (`work/checker/`): 00_data (0 flags), 00_picks (silent_stations), 05_location_pass3 (events_with_few_picks, depth_single_value 5.5 %, depth_layers 13.4 %), 06_relocation (events_with_few_picks, depth_layers 7.3 %), 07_magnitude, and final (3 flags).

Invocations, from `record/execution.jsonl`:

- 19:00:06: data and picks
- 20:45:51: location, on pass 3 only
- 21:05:13 and 21:05:50: relocation (the first call used a wrong `--dtcc` path)
- 21:06:56: magnitude
- 21:09:43: all

How the run used the checker:

- No location check was run on pass 1 or pass 2. The model, datum, station-delay and calibration decisions were all taken without the checker.
- `compare.py` and `pilot.py` were never used.
- At 20:46:39 the location flags were explained as "NLL depth quantisation, should soften after relocation". The checker did not trigger any experiment.
- The final dispositions justify silent_stations and events_with_few_picks as input properties, and depth_layers as model interfaces plus quantisation (reduced from 13.4 % to 7.3 % by GrowClust).
- `wadati_origin_offset` measured +0.88 s and was noted as normal.

Effect on scores: none attributable. The good bias numbers come from the datum mismatch and the residual calibration (§7.2).

**Knowledge run's use of the checker (10 runs).** It ran data, picks and association at 18:56–19:01, `pilot.py events` (300 events) at 19:06:24, and the pilot location check at 19:11:42. The full location check at 19:21:30 flagged depth_single_value 6.7 % and depth_layers 6.0 %. After the grid experiment it ran the 0.1 km location check, then `compare.py` at 19:36:58 (verdict "better", nothing worsened, adopted by a rule written before running). It then checked relocation (with and without `--dtcc`), magnitude, `--model-ensemble` (20:06:47), and the final stage. Every flag it acted on was a representation or quantisation artefact. None of these checks can see a common-mode velocity error, as the checker README says ("velocity structure alone can offset this value by close to a second").

## 9. Knowledge behaviour

Files read, all in a single read at the start:

- 18:55:02: `catalog-knowledge/SKILL.md`, `protocol/pilot_then_full.md`, `playbooks/decide_between_candidates.md`, `symptoms/README.md` and `symptoms/not_visible.md` (one `cat`)
- 18:55:04: `symptoms/data_picks_association.md`, `location_relocation.md`, `magnitude_completeness.md`
- 18:55:10: `magnitude/README.md`
- 19:15–19:16: `calibrations.json` and `ml_reference.py`

Procedures followed:

- **Pilot first.** `pilot.py events` gave 300 events. Step and linear were each run on the pilot and the medians compared (lin − step: depth +1.1 km, OT +0.07 s). The item checks ran with the pilot. Runtime was extrapolated before the full run.
- **Adoption rule before the experiment.** `runs/location_setup.json` and the grid rule ("adopt the finer grid if the depth pile flags clear and no judged check worsens") were written down first, then `compare.py` on the full runs was used to decide.
- **Experiment that separates the explanations** (playbook §3): 288 piled events plus 200 random ones were relocated on 0.5, 0.25 and 0.1 km grids. The pile dispersed (262 → 85), which the run read as a quantisation artefact.
- **Independent locator.** HypoInverse 1.40 on the same picks gave 0.74 km median epicentral agreement for well-constrained events. Its depths were +1.7 km deeper, which the run correctly attributed to HypoInverse ignoring elevations. The run also cross-checked hypoDD with GrowClust (inter-event distance correlation 0.993).
- **Sensitivity report.** `--model-ensemble`: depth agreement 0.61 and origin-time agreement 0.25, with an ensemble spread of 1.18 s and 5.5 km.

How `not_visible.md`'s velocity-model advice was applied:

1. "Use the regional model, the way it was meant to be used" and "use its datum": applied. The run searched the web (19:02:55), downloaded Husen & Smith 2004 and took its sea-level datum.
   - It did not pursue the UUSS operational model, even though the H&S paper and the search results point to "a velocity model used since 1988 to locate earthquakes".
   - A minimum 1-D model from VELEST is a stack of constant layers, so the published representation is step. The run used it as linear nodes.
   - "Start the depth search at that datum" was read literally, as 0 km bsl. Stations stand 2.0–2.9 km above that.
2. "Compare representations": done on the pilot only. The playbook (§3) says to build both full candidates and compare them; the run dropped step after the pilot (19:10:49) because 46 % piled at 2.016 km. This deviation did not cost score: step would have been worse in depth (−1.35 km against −0.40 km in the same-locator test) and better in time (+0.53 s against +0.94 s).
3. "Do not choose by residual": respected. RMS was noted (linear 0.125 s against step 0.181 s) but not used as the reason.
4. "Report the sensitivity": the ensemble was run and recorded in `decisions.md` §6. It was not carried into the catalog. `origin_time_uncertainty_s` was filled with the NonLinLoc RMS (about 0.13 s), which understates the model-driven 1.18 s spread.
5. "Independent information settles it": none was available, and the run did not say so explicitly beyond "no case-specific tuning was possible without reference data".

The decisive gap: the playbook names the error, but it gives no test the agent could run to detect a regional model whose near-surface is too fast. The only two signals pointed the other way or were ignored. The Wadati offset favoured the knowledge run's late origins. The model ensemble showed that the origin time was model-dependent but not which way it was wrong. Note also that the expert's model comes from Pang et al. (2019) SI, a paper on this very sequence whose DOI is on the case's leakage list (`evaluation/metrics.yaml`). Whether the UUSS model is published in a source the agents could legitimately use was not checked.

## 10. Proposed single-factor experiments

All of these are NonLinLoc relocations with `seismotools/nonlinloc/interface/locate.py` on the fixed front-end arrivals, scored with the standard scorer on a copy of the catalog. Predictions come from the same-locator test (§5) and the stage table (§6).

| id | change (one factor) | starting point | prediction | what it settles |
|---|---|---|---|---|
| **E1 (top)** | Expert UUSS model, step, datum 2.3 ASL (equivalently: tops shifted to bsl, reference 0) | knowledge `runs/cfg_linear_g01.json` + `runs/prep/arrivals.csv` (absolute stage, no hypoDD) | dt about +0.1 to +0.3 s (from +1.18); dz about −1.3 to −1.8 km (from −2.22) | That the time bias is the H&S near-surface, and how much of the depth bias is model and how much is front end/locator |
| **E2 (top)** | Swap the two configurations: knowledge config with the checker model `model_cal.txt` (step, reference 0), and checker `nll_pass3/config.json` with the H&S linear model | both runs' arrival files (identical picks) | knowledge + checker model: dz about +0.3 km, dt about −0.05 s (what the checker run got); checker + H&S: dz about −2.2 km, dt about +1.15 s | That the run-to-run difference is model only (same-locator test: +2.77 km / −1.19 s) and not weights, σ mapping or search settings |
| **E3 (top)** | Checker model with the datum it intended (`reference_elevation_km 2.389`, profile as in `model_cal.txt`), and separately with Vs = Vp/1.608 instead of 1.546 | checker pass-3 configuration | intended datum: dt about +0.5 to +0.7 s, dz about −1.3 km (to about −0.9 km against the final); Vp/Vs 1.608: dz about −0.9 km, dt about 0 | How much of the checker run's score is the datum mismatch and the low Vp/Vs, and whether its depth "accuracy" is a cancellation |
| E4 | H&S step, full catalog, with `compare.py` against linear (the step the knowledge run skipped) | knowledge config | dz about −1 km worse, dt about −0.4 s better; depth flags fire | Completes the playbook's §3; shows that representation cannot fix this model |
| E5 | Checker calibration without the deep 0.85 factor (pass-1 Vp, Vs/1.546) | checker pass-3 configuration | same-locator test says about 0 change; if NonLinLoc moves more than 0.5 km or 1 km horizontally, far-station head waves drive the pass-1 YHL/shift problem | Whether the deep low-velocity zone matters in NonLinLoc (the same-locator test and NonLinLoc disagree) |
| E6 | Knowledge relocation with GrowClust instead of hypoDD, or hypoDD with station elevations and the H&S Vs | knowledge `catalog_abs.csv` + `runs/ccdt` | dz back to about −2.2 km overall, about −1.3 km for ≥ 10 picks | That hypoDD's −0.5 km centroid move is a model/elevation mismatch |
| E7 | Backend pass 2 without the 10,570 pick rejections (station terms only), then with Vs = Vp/1.61 | backend `scripts/nll_config.json` + `runs/prep/arrivals.csv` | epicentres back within about 1–2 km of the others, recall about 0.9; with the data Vp/Vs, the S residuals at YHL/FLWY collapse | That the backend failure is the Vs model plus QC, not the front end |
| E8 | The E1 relocation, plus two LOCDELAY passes as the expert did | E1 output | dz moves toward 0 by a few tenths of a km; dt unchanged | The size of the station-delay part of the front-end/locator gap |
| E9 | Score knowledge and checker on depth against ComCat and against the expert final side by side, by number of picks | existing catalogs | knowledge −0.9 km (ComCat) and −2.5 km (final); checker +2.6 km and +0.4 km | How much of "checker best on depth" depends on the yardstick (the expert final is 1.46 km deeper than ComCat) |

The top three are E1, E2 and E3. E1 checks the core claim (H&S near-surface → +1 s) on the real locator. E2 is the swap the audit asks for. E3 shows whether the checker run's win is a datum accident plus a Vp/Vs that cancels a shared shallow bias.

## 11. Caveats

- The same-locator test is an L1 grid search with a simple 1-D tracer, not NonLinLoc EDT_OT_WT. It reproduces differences between models well (validation in §5) but sits 0.5–0.6 km away from the runs' NonLinLoc depths. Its absolute dz against the expert final should not be read as a NonLinLoc prediction.
- The sample is 500 events with ≥ 10 picks. Few-pick events carry larger biases in both runs (§6), so whole-catalog effects are larger than the sample's.
- The depth "truth" is uncertain at the 1–1.5 km level. The expert final is +1.46 km relative to ComCat, both with the UUSS model. Time is robust: both references put the knowledge run about 1.1 s late.
- I verified the H&S Table 1 values against the run's own PDF extraction in the execution log (19:04:20), not against the paper directly.
