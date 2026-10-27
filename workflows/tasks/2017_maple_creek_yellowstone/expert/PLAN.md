# Maple Creek 2017 expert pipeline — round plan

Goal: port the Magna expert workflow to the 2017 Maple Creek swarm and tune
it by explicit rounds. Feedback each round: similarity to the ComCat/UUSS
operational catalog (located) and to the Shelly detection table (time only),
measured by stage 05. Same round mechanics as Magna (`../../2020_magna_utah/
expert/PLAN.md`): round identity = config `round` + `export_root`, one
behavioural knob per round, previous rounds immutable, never tune to force
reference agreement.

## DAG

```
01_prepare_inputs → 02_pick_phasenet → 03_associate_gamma → 04_locate_nonlinloc
                  → 05_match_references → 09_estimate_magnitude → 10_validate_catalog
```

## Data preparation (2026-10-22, before r1)

- ComCat query box corrected (was ~40 km east of the swarm: 5 events → 626);
  a separate cluster ~18 km east (~110.80 W) is excluded.
- Shelly phase release → time-only detection table (18,062 window events,
  origin MAD 0.11 s vs ComCat, 624/626 ComCat events covered within 1.5 s).
- UUSS Yellowstone 1-D model registered (Pang et al. 2019 SI Table S1).
- Pang et al. (2019) and the Shelly event catalog stay unpublished (Zenodo,
  ScienceBase, journal SI checked); revisit if a table appears.

## Round-1 gates

1. 01: 17 three-component HH/EH sites selected; deferred list as in README.
2. 02 pilot: all 17 instruments run; picks in the quiet window.
3. 03 pilot: the mainshock window associates an event within ~10 s of
   00:48:46.9 with ≥6 stations; the quiet window is near-empty.
4. 04 full: LOCATED ≥90%; depth sigma recorded.
5. 05: masked counts 626/18,062 (hard asserts); mainshock uu60203137 matched
   at 4 s / 15 km; Shelly chance count from the shifted control well below
   the raw match count.
6. 09: numerical response check on WY.YMC.01.EHE; 10: v1 count equals 05.

## Expected knob ladder

1. Station set: add the ten vertical-only WY sites (P-only picks; three lie
   within 15 km of the swarm and should control depth). Needs a stage 01/02
   input condition for single-component instruments.
2. Velocity model / datum check against ComCat depths and origin times.
3. Association levers if recall is association-limited (Magna: wash).
4. Yellowstone ML calibration against ComCat magnitudes.
5. Detection beyond picking: stage 60 Match&Locate (Shelly's own method; the
   Magna recall lever) and DD relocation (stage 52) with the stage-45 depth
   prior and DD acceptance gate learned in Magna r8.

## Round log

### r1 (2026-10-22) — baseline port, all gates green

- 02: 109,049 picks (P 57,320 / S 51,729) on 17 instruments, 544 blocks.
  Blocks without a common three-component segment (WY.YHL, TA.H17A HH gaps)
  are empty completed blocks, not failures.
- 03 pilot: mainshock window associates all 9 ComCat events (+8 more; 2
  outside the box), mainshock +0.53 s / 1.4 km; quiet window 1 event outside
  the box.
- 03/04 full: 1,633 events, all LOCATED; median RMS 0.19 s; 16 at the depth
  bound. 1,433 in the comparison scope, v1 1,139.
- 05: ComCat 587/626 matched (**0.938**; v1 0.685), median |dt| 0.47 s,
  epicentral 1.17 km, depth +0.88 km (MAD 0.79). Shelly 1,337/18,062
  (0.074; 157 chance matches in the 60-s shifted control, net 0.065; 664
  unambiguous — the reference is dense enough that 1-s windows overlap).
  Mainshock matched (0.53 s, 1.17 km, dZ −2.4 km).
- 09: ML vs ComCat −0.04 (n 202) under provisional HB87; numerical check
  0.4%. 10: checks passed.

Diagnosis — systematic origin-time/depth bias: NLL origins are +0.47 s late
and +0.9 km deep vs ComCat (GaMMA +0.43 s). Picks are not the cause:
PhaseNet vs Shelly arrivals (UUSS analyst picks + correlation lags) at the
same station-phase differ by +0.04 s (P) / −0.03 s (S), 7,520 pairs. The
residual pattern (P late, S early) and the size point to the model
representation: stages 03 and 04 interpolate *linearly* between the
registry's layer tops (GaMMA eikonal grid; NLL `LAYER` gradients), so the
1.3–4.3 km layer at 2.79 km/s ramps to 5.21 km/s instead of stepping. One-way
vertical P from 8 km: 2.26 s layered vs 1.93 s linear (−0.33 s; S more),
absorbed as late origins and deeper hypocentres. The Shelly origin times,
derived with the true layered tracer, sit at −0.10 s vs ComCat (also a
layered HYPOINVERSE model). Magna used the same linearisation, but BP89's
steep step is only in the top 1.5 km (later absorbed by the r4 basin layer).

### r2 — knob: layered (step) velocity representation in GaMMA and NLL

(2026-10-22) `association.yaml velocity_layering: step` — stage 03 adds a
node 1 m above each layer top carrying the layer above (GaMMA `np.interp`
then keeps constant layers); stage 04 writes zero-gradient NLL `LAYER` cards.
Default `linear` keeps r1 reproducible. 01/02 hardlinked from r1.

| | r1 linear | r2 step |
|---|---|---|
| events / v1 | 1,633 / 1,139 | 1,622 / 1,259 |
| ComCat matched (v1) | 0.938 (0.685) | 0.931 (0.826) |
| dt vs ComCat (signed median) | +0.47 s | **−0.05 s** |
| dt vs Shelly | +0.57 s | **+0.03 s** |
| dZ vs ComCat (MAD) | +0.88 (0.79) | +1.06 (0.96) |
| epicentral vs ComCat | 1.17 km | 1.38 km |
| NLL median RMS | 0.19 s | 0.29 s |
| ML vs ComCat | −0.04 (n 202) | −0.10 (n 217) |

Verdict: adopted. The origin-time bias was the linear ramp (confirmed). The
higher RMS is not a worse model: r2 residuals are P +0.1…+0.35 s and S
−0.1…−0.4 s at every station regardless of distance, i.e. observed S−P is
systematically shorter than the model predicts; r1's ramp hid part of that
behind a late origin. Per-event Wadati slopes from our picks give a
path-averaged Vp/Vs of 1.61 (IQR 1.57–1.64, 1,398 events) vs ~1.63–1.67 in
the model's source-depth layers, and Pang et al. (2019) report anomalously
low near-source Vp/Vs of 1.50–1.66 for exactly this sequence (regional
average ~1.74). A 1-D model cannot carry that; operational practice
(HYPOINVERSE at UUSS) absorbs it with station delays. v1 grew because fewer
events trip the quality flags under the step model.

Next rounds: r3 station set (add the ten vertical-only WY sites, P picks
only; YGC 6 km, YHB 13 km, YHH 14 km from the epicentre) — before station
terms, because terms depend on the station set; r4 NLL station delays
(LOCDELAY) estimated from our own well-constrained events, iterated.

### r3 (2026-10-22) — knob: vertical-only WY sites (P picks only)

`channel_policy.vertical_only_families: [EH]`: stage 01 selects EHZ-only
instruments as a separate input condition (a three-component instrument
still wins at a shared site, so WY.YPP/YTP keep HH) → 25 instruments (17 +
8). Stage 02 feeds them to PhaseNet with zero-imputed horizontals (SeisBench
`strict=False`) and keeps P picks only.

| | r2 | r3 |
|---|---|---|
| picks (P) | 109,049 (57,320) | 113,180 (61,451) |
| events / v1 | 1,622 / 1,259 | 1,698 / 1,328 |
| ComCat matched (v1) | 0.931 (0.826) | **0.941 (0.867)** |
| dt / epicentral vs ComCat | −0.05 s / 1.38 km | +0.01 s / **1.18 km** |
| dZ vs ComCat (MAD) | +1.06 (0.96) | +1.22 (**0.70**) |
| Shelly net of chance | 0.069 | 0.072 |

Adopted. But the vertical-only sites under-pick: WY.YGC (6 km) gave 502 P
picks in eight days vs 12,822 at WY.YMC (3 km) and 8,352 at WY.YMR
(13.6 km, 3C), with a high association rate (358/502) — real picks, just
few. PhaseNet is trained on three components and zero horizontals depress
its P probability. Test on 06-16 00–06Z: Z copied to N/E gives YGC 220 P
picks (85% with a YMC P pick within 3 s) vs 68 with zeros (93%); YHB 200
(71%) vs 103 (73%) — about three times the corroborated picks.

### r4 — knob: vertical-only horizontals = copy of Z (`picking.vertical_only_horizontals: copy_z`)

| | r3 (zeros) | r4 (copy_z) |
|---|---|---|
| P picks | 61,451 | **82,554** (vertical-only sites 1,052–5,158 each; YGC 502 → 2,336) |
| events / v1 | 1,698 / 1,328 | **2,059 / 1,630** |
| ComCat matched (v1) | 0.941 (0.867) | **0.957 (0.933)** |
| Shelly net of chance | 0.072 | **0.086** (1,741 matched of 1,789 in scope; 183 chance) |
| dt / epicentral vs ComCat | +0.01 s / 1.18 km | +0.03 s / **1.12 km** |
| dZ vs ComCat (MAD) | +1.22 (0.70) | +1.30 (0.68) |
| NLL median RMS | 0.29 s | 0.30 s |

Adopted: the largest single gain so far. New events are not noise — 97% of
the in-scope events have a Shelly detection within 1 s (chance level ~10%).
Remaining: a +1.3 km depth offset vs ComCat and the P-late/S-early residual
pattern from the low near-source Vp/Vs.

### r5 — knob: NLL station delays (`nonlinloc.yaml station_delays`, 2 iterations)

Stage 04 locates, takes per station-phase median residuals (≥20 picks) of
events with RMS ≤ 0.5 s, gap < 180°, σz ≤ 3 km, removes the pick-weighted
mean (origin datum fixed), adds them to `LOCDELAY` and relocates; passes in
`events_raw_pass<k>/`, final in `events_raw/`, delays in
`full/station_delays.csv`. 01–03 hardlinked from r4.

| | r4 | r5 |
|---|---|---|
| NLL median RMS | 0.295 s | **0.158 s** |
| epicentral vs ComCat | 1.12 km | **0.86 km** |
| dt vs ComCat / Shelly | +0.03 / +0.10 s | −0.06 / +0.08 s |
| dZ vs ComCat (MAD) | +1.30 (0.68) | +1.39 (0.66) |
| ComCat matched (v1) | 0.957 (0.933) | 0.957 (0.899) |
| Shelly net of chance | 0.086 | 0.086 |

Delays converged (pass 1 increments ≤ 0.47 s, pass 2 ≤ 0.09 s; 39
station-phases from ~1,800 events). They carry the Vp/Vs signature: P
+0.1…+0.4 s, S −0.1…−0.55 s. Adopted. v1 fell 1,630 → 1,545 only through the
`large_locator_shift` flag (NLL vs GaMMA > 2 km: 69 → 190) — GaMMA has no
delays, so the flag now measures GaMMA's error, not NLL's; revisit the flag
before using v1 as a quality cut.

Depth datum check: ComCat depths are below the local surface, as assumed.
Shelly & Hardebeck (2019) put the two M~3 swarm-initiation events of
2017-06-12 16:46 UTC "approaching 10 km below mean surface elevation (~2 km
above sea level)"; ComCat lists them at 10.83 and 11.09 km (a sea-level
datum would make them ~13 km below the surface). The +1.4 km median offset
vs ComCat is therefore not a datum mix-up; it varies event to event (r5 vs
ComCat for those four events: −1.1, −2.1, +2.9, +0.8 km) and stays open.

State after r5: ComCat recall 0.957, epicentral 0.86 km, |dt| 0.09 s;
Shelly recall 0.086 net — the detection gap to a template-matching catalog
is the dominant remaining difference, as in Magna before stage 60.

Next candidates: (1) stage 60 Match&Locate (port from Magna; Shelly's own
method, Magna recall +25 points); (2) DD relocation (stage 52) with the
Magna r8 depth prior / DD acceptance gate; (3) Yellowstone ML calibration
(ML vs ComCat already −0.09 under HB87, low priority); (4) the depth offset.

### r6 (2026-10-23) — stage 60 Match&Locate (detection beyond picking)

`01_pipeline/60_match_locate.py` + `00_config/match_locate.yaml`, ported from
Magna stage 60 with Maple scoring (ComCat 4 s / 15 km; Shelly origin time
1 s + shifted-reference chance count). Templates: r5 v1 events with ≥ 10
stations and σz ≤ 2 km, 0.5 km cover (NLL positions with station delays);
near (≤ 20 km) SNR ≥ 5 rows, min 8 rows/channels (≤ 14 rows exist within
20 km here; Magna used 12).

- Pilot (06-13, 20 templates): Shelly net recall 5.6 → 30.9 % at N×MAD 9;
  ~95 % of the union matches Shelly. 30 km selection not tested (prepare
  cost; see below).
- Full (8 days, 219 templates, 207 kept, 2,274 rows): prepare 84 min —
  WY.YHL has ~1,200 segments/day and the tool Lanczos-resamples each
  off-grid segment separately; run 58 min (1,656 jobs).
- Null run (`04_comparison/08_null_run.py`, copied from Magna; 06-13 + 06-16,
  6 s separation): false fraction 34 % at N×MAD 8, 7.6 % at 8.5, **1.2 % at
  9**, 0.2 % at 9.5, 0 from 10. Final threshold N×MAD 9 / 6 s (as Magna).
  At 9, ~22 % of union events have no Shelly detection within 1 s; with a
  1.2 % noise rate these are mostly real events absent from Shelly (whose
  templates were routine UUSS events, ours are our own).

r6 catalog (`--stage export --catalog-round r6` → `export/r6/60_catalog/
catalog_events.csv`): 12,648 events (2,059 r5 NLL + 10,589 M&L), 12,372 in
the box; magnitudes chained from 71 ML templates to 205/207 templates
(median M −0.27).

| | r5 | M&L | **r6 union** |
|---|---|---|---|
| events in box | 1,783 | 12,207 | **12,372** |
| ComCat recall | 0.957 | 0.987 | **0.995** |
| Shelly recall net of chance | 0.086 | 0.482 | **0.486** |

Vs ComCat: r5 NLL rows epicentral 0.87 km, dZ +1.4 (MAD 0.67), dM +0.15;
M&L rows (only 42 ComCat pairs — the ComCat events r5 missed) epicentral
2.59 km, dZ +2.8 (MAD 2.7), dM +0.22. M&L positions are bounded to ±0.5 km
of the detecting template, so a far template misplaces an event; their
location quality is open (no located reference for the new events).

## Benchmark layer (2026-10-23)

Task package ported from Magna next to `expert/`: `input.json`,
`task_{min,tools,guided}.json`, `prompt_{min,tools,guided}.md` (case name,
window 2017-06-11 → 06-19, example station WY.YMC), output contracts
(verbatim), `run.sh` (agent name `*-maple-<variant>`), README, VARIANTS.
`evaluation/scripts/{plot_evaluation_comparison,evaluate_run}.py` adapted:
ComCat located (4 s / 15 km), Shelly time-only (1 s + 60 s shifted chance
count), expert depths converted to below-surface; spatial figures skip
Shelly. Cross-run figures generated for r6; per-run script smoke-tested.
No agent run yet.

### r7 — knob: Match&Locate template density

Templates `min_stations` 10 → 8 and `cover_radius_km` 0.5 → 0.3 (both set
template density): 219 → 519 templates, v1 cover 0.90 → 0.92 (offline
`select_templates` on r5 v1; ≥ 6 stations / σz ≤ 3 would give 707 but admits
poorly constrained templates). Source catalog r5 unchanged; full run, null
run, export to `export/r7/60_catalog`.

Depth-offset diagnostic (2026-10-23, r5, 250 ComCat-matched events): RMS of
our picks (layered UUSS tracer, origin time free) at our hypocentre vs at
ComCat's — without station delays 0.281 vs 0.356 s (our epicentre with
ComCat's depth 0.319 s); with delays 0.123 vs 0.222 s (0.188 s); median dZ
+1.3 km either way. Our depths are what our picks require under this model;
the offset is not a locator trade-off and not caused by the station delays
(it is present without them). A lower Vp/Vs (Wadati 1.61) would push depths
deeper, not shallower. The difference to ComCat comes from its different
inputs (analyst picks, station set, HYPOINVERSE elevation/delay handling);
with no independent depth truth it is documented, not tuned away.

r7 result (2026-10-23): 519 templates, 453 kept by prepare (4,790 rows),
3,624 jobs, run 2.1 h. Null run (06-13 + 06-16): 51.6 % false at 8, 14.8 % at
8.5, 2.6 % at 9, **0.95 % at 9.25**, 0.3 % at 9.5 — more templates raise the
noise floor (r6: 1.2 % at 9). Final N×MAD **9.25** / 6 s (the ~1 % level).

| union (6 s merge) | r6 @ 9 | r7 @ 9 | **r7 @ 9.25** | r7 @ 9.5 |
|---|---|---|---|---|
| events in box | 12,372 | 14,897 | **13,399** | 12,318 |
| ComCat recall | 0.995 | 0.994 | 0.994 | 0.994 |
| Shelly recall net | 0.486 | 0.535 | **0.521** | 0.504 |
| null false fraction | 1.2 % | 2.6 % | 0.95 % | 0.3 % |

(The stage-60 sweep table merges at 4 s and overstates the gain.) Doubling
the templates buys +3.5 points of Shelly recall: template density is not the
main limit. Shelly's templates span three months of routine events and half
its detections carry < 4 station-phases — below what our channel set
resolves.

M&L positions improved more than recall. Same events located by M&L and by
NLL (r5 rows re-detected): epicentral difference median 0.74 → **0.49 km**
(p90 3.02 → 2.63), depth MAD 0.93 → **0.47 km** — denser templates sit
closer to the true sources, and M&L searches ±0.5 km around the detecting
template. Against ComCat (40 pairs, the events r5 missed) 2.59 → 1.93 km.

r7 catalog: `export/r7/60_catalog/catalog_events.csv`, 13,675 events
(2,059 NLL + 11,616 M&L); magnitudes chained to 450/453 templates. Cross-run
evaluation switched to r7 (complete catalog: ComCat 0.994, Shelly 0.583 /
net 0.521, epicentral 0.87 km, dZ +1.43). Residual: a few shallow template
families (streaks near 1 km and 2–3 km below the surface in figure 01).

## r8 (2026-10-26) — location quality (cross-case review after Ridgecrest)

Off-fault share (> 1 km from every ComCat event — a sparse 626-event
skeleton, so overstated): r7 3.5 % (NLL rows 7.2 %, M&L rows 2.9 %).
Off-fault NLL rows: RMS 0.38 vs 0.13 s, 7 vs 10 stations, half outside v1;
off-fault M&L rows: 89 % from 24 off-fault templates. Candidate rules
(complete-catalog evaluation): v1 + RMS ≤ 1.5× median → 0.2 % but Shelly net
−3.8 points (high-RMS templates still detect well); templates only → 1.2 %,
−3.7 points; ≥ 1 waveform CC link only → 3.3 % (95 % of events have a link:
compact swarm); **≥ 1 CC link + gap ≤ 150° + σx ≤ 0.8 km (the Ridgecrest
rule) → 1.5 %, ComCat 0.994 → 0.990, Shelly net 0.521 → 0.507** (adopted).
CC links: `60_match_locate.py --stage cclinks` (ccdt, 3 km / 30 neighbours;
1,962 of 2,059 source events linked). r8 = export with `location_quality`:
12,602 events, 929 picked events in `low_quality_events.csv`. Evaluation
layer = r8.

### r9 (2026-10-27) — NonLinLoc LOCMETH EDT_OT_WT (Prague r5 method)

`nonlinloc.yaml location_method: EDT_OT_WT`. r9 = r5 stages 01–03
(hardlinked) + stage 04 (two station-delay passes) + stage 05; 09/10 not
rerun. Stage-04 test on the r5 associations (seismotools locate.py, fixed r5
delays): ComCat epicentral 0.867/1.827 → 0.828/1.684 km, depth MAD 0.67 →
0.63 km. Stage 64 moves the r8 catalog into the r9 frame: 1,130 picked
events relocated, 11,472 M&L events shifted with their templates (template
displacement median 0.25 km, p90 2.05 km).

| final catalog (evaluation matcher) | ComCat R | epi median / p90 | dZ (MAD) | Shelly R (net) | > 1 km from ComCat (box) |
|---|---|---|---|---|---|
| r8 | 0.990 | 0.908 / 2.164 | +1.43 (0.85) | 0.564 (0.507) | 1.53 % |
| **r9** | 0.989 | **0.895 / 1.898** | +1.46 (**0.69**) | 0.569 (**0.511**) | **0.28 %** |

M&L rows vs ComCat 1.22 → 0.91 km; picked rows 0.86 → 0.90 km (median; the
p90 and the off-fault share improve). One ComCat event fewer matched.
**Adopted**; evaluation layer = r9. The +1.4 km depth offset to ComCat is
unchanged (documented r5–r7 input difference).

## Baseline corrections (2026-10-28) — stages 65, 67

Metrics v1 exposed three pipeline defects shared across cases (user decision 2026-10-28:
unfreeze the expert baselines). Catalog-level rounds, no rerun of stages 01-60:

- **r10** (stage 65, direct ML): 10 picked events with a direct ML
  (≥ 3 stations, MAD ≤ 0.5), 2 adopted (1 had no magnitude);
  direct − chain by direct ML: (-9.0, 1.0] -0.06 (n 1), (1.0, 2.0] +0.56 (n 7), (4.0, 5.0] +0.69 (n 1).
- **r11** (stage 67, coda ghosts): 2 Match&Locate detections removed (of 14 with M ≥ 1.5); rule from the Ridgecrest blind review.
- Final catalog **r11** (12,600 events) replaces r9 as expert final in `evaluation/metrics_v1.yaml`. Metrics v1, expert final:

| metric | r9 | r11 |
|---|---|---|
| f1_M2 | 1.00 | 1.00 |
| f1_M3 | 1.00 | 1.00 |
| f1_M4 | – | 1.00 |
| precision_M2 | 1.00 | 1.00 |
| dmag_mean_M4 | -0.90 | -0.21 |
| dmag_slope_per_unit | -0.32 | -0.31 |
| recall_norm | 1.15 | 1.15 |
