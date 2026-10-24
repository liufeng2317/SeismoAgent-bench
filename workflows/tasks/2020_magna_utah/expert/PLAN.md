# Magna 2020 expert pipeline — round plan

Goal: migrate the settled Ridgecrest expert monitoring workflow to the Magna
(M5.7, 2020-03-18, Utah) eight-day case, then tune it by explicit rounds. The
feedback signal each round is the similarity between our expert catalog and the
three case references (Pang et al. 2020 relocated, Baker & Whidden 2021 picks,
UUSS/ComCat operational), measured by stage 05.

## DAG

```
01_prepare_inputs → 02_pick_phasenet → 03_associate_gamma → 04_locate_nonlinloc
                                                       → 05_match_references (NEW)
                                                       → 09_estimate_magnitude → 10_validate_catalog
```

05 runs after 04 full and before 09 (09 consumes `event_quality.csv` /
`reference_matches.csv`; 10 imports 05 as a module for `load_trace`). Stages
52/53 (double difference) and Ridgecrest's `02_diagnostics/` /
`03_experiments/` are not ported; future diagnostics are written fresh here,
driven by results.

## Round mechanics

- Round identity: `00_config/config.yaml` keys `round` + `export_root`
  (e.g. `r1` + `export/r1`). Every stage writes only under the round's export
  root; previous rounds are immutable — relaxed 2026-10-20 for bulky
  regenerable intermediates (r1–r4 picks/association/NLL raw dumps, r6 DD
  cache + ct-only control deleted; see `SUMMARY.md` "Storage note"). Result
  products (`01/05/06/09/10`, and the full r5/r6 chain) are permanent.
- One behavioral knob per round. Everything else stays fixed so
  round-over-round `matched_fraction(_v1)` diffs are attributable.
- Knob ladder (expected order):
  1. velocity model (`methods.velocity_model` in config.yaml; registry at
     `data/2020_magna_utah/data/models/velocity_models.json`, currently
     Bjarnason & Pechmann 1989 Wasatch front)
  2. association levers (`association.yaml`: `dbscan_*`, `minimum_*`,
     `oversample_factor`, `max_sigma11`)
  3. pick/quality thresholds (`validation.yaml` quality block,
     PhaseNet thresholds)
  4. ML calibration for Utah (Hutton–Boore SoSoCal correction is provisional;
     swap in a Utah recalibration)
- Never tune to force reference agreement: report both the moved metric and
  the side effects (event count, false-split risk, medians of the other
  references).

## Round-1 gates (checked before advancing)

| stage | gate |
|---|---|
| 01 pilot | waveform inventory validates; ~43 primary 3-component instruments |
| 02 pilot | ≥35 instruments with ≥1 pick |
| 03 pilot | mainshock window (13:05–13:20Z) associates ≥1 event with ≥6 stations within ~10 s of 13:09:31.5; quiet window near-empty |
| 04 full | LOCATED ≥90%; median depth σ ≤ ~2 km |
| 05 | masked reference counts exactly pang 4,169 / baker 3,712 / uuss 1,432; exactly one mainshock row per catalog, matched at primary gates |
| 09 | numerical WA recovery on UU.AVE.01.ENE < 1.5%; mainshock magnitude deferred |
| 10 | v1 working count equals 05's `v1_working_events`; README/figures written |

Round-1 deliverable: `export/r1/05_match_references/report.json` + `summary.md`
+ frozen v1 catalog in `export/r1/10_validate_catalog/`.

## Reference cohort (frozen in validation.yaml)

Common mask = window [2020-03-18T00:00Z, 2020-03-26T00:00Z) ∩ box
(lat 40.69–40.84, lon −112.14–−111.94) ∩ depth −1.3–13.1 km below sea level,
**no magnitude floor** (Pang's 61 sentinel-Mc events are real events; our
parser also absorbs Pang's 5 noncanonical-seconds rows, hence pang 4,169 vs
the originally audited 4,162). Matching gates: primary 4 s / 15 km (= the
benchmark evaluation matcher), sensitivity 2 s/5 km and 1 s/3 km; Hungarian
one-to-one per reference; ambiguous pairs kept but reported separately.
v1 working catalog = NLL region ∩ `provisional_quality == provisionally_usable`
∩ not mainshock.

## Known limits carried into every round

- No 2020-03-17 pre-roll: completeness at the window start edge is limited
  (per-period matched fractions make the bias visible).
- Pang depths are sea-level referenced; depth differences are computed on that
  datum only, and depth never gates matching.
- Magnitudes are secondary to time/position in round feedback (SoCal
  Hutton–Boore provisional for Utah).

## Round log

### r1 (2026-10-18) — baseline port, all gates green

Pipeline: 1,184 files / 43 primary instruments (EN/EH, WTU deduped) →
141,343 picks (P 70,208 / S 71,135) → 2,488 GaMMA events, 49.5% picks
associated, median RMS 0.37 s → NLL 2,487/2,488 LOCATED (99.96%), median
depth σ 1.46 km → matching gates → 18,241 ML measurements (4,064 accepted,
strict SNR/gap gates) → v1 frozen: 2,080 working events, 441 with
provisional ML.

| reference | masked | matched | fraction | v1 fraction | median NLL dt | median NLL epi |
|---|---|---|---|---|---|---|
| pang | 4,169 | 2,177 | 0.522 | 0.405 | 0.35 s | 1.35 km |
| baker | 3,712 | 2,144 | 0.578 | 0.500 | 0.44 s | 1.29 km |
| uuss | 1,432 | 1,307 | 0.913 | 0.851 | 0.34 s | 1.36 km |

Mainshock matched in all three (NLL 0.69 s / 1.32 km). Per-period v1
fractions: pang 0.389 (first 48 h) → 0.447 (later); baker 0.607 → 0.353;
uuss 0.865 → 0.819.

Reading: agreement is tight where we detect (medians well inside the 4 s/15 km
gates; NLL epicentral slightly better than GaMMA). The pang/baker gap is
mostly completeness — both references include template/matched-filter
detections below our pick-based detection floor, while UUSS (operational,
higher completeness threshold) matches at 91%. Provisional ML runs a
systematic +0.62…+0.65 above all three references (median differences) —
consistent offset = calibration, not catalog disagreement; the designated
Utah ML recalibration knob.

r2 candidates (one knob each, in order): association levers to lift
first-48h matched fraction under M5.7 coda saturation; Utah ML
recalibration; velocity-model refinement (BP89 layering is already real).

### r2 (2026-10-18) — knob: Utah ML recalibration

The r1 diagnostic (`04_comparison/06_fit_ml_calibration.py`, fitted on frozen
r1 exports) showed the provisional HB87 offset is **not a constant**: station
residuals to UUSS ML fall from +0.96 (10–15 km) to +0.20 (40–60 km) — the
HB87 geometric spreading is too strong for Utah at close range. 95% of anchor
measurements lie within ~35 km, where log10(r) and r are collinear, so the
anelastic term was kept at HB87's 0.00189/km and only the geometric spreading
and constant were refit (anchor: 385 UUSS-ML-matched events, 3,363 accepted
station measurements, 11 sigma-clipped, cluster-robust SEs):

    correction(r) = 2.934 * log10(r_km) + 0.00189 * r_km − 2.313
    (HB87: 1.11, 0.00189, 0.591; delta −1.08 at 10 km → +0.74 at 100 km)

Coefficients live in `00_config/config.yaml` (`magnitude.ml_calibration`);
stage 09 applies them when the block is present (HB87 remains the default).
Stages 01–05 are untouched by this knob: `export/r2` hardlink-reuses r1's
01–04 outputs, and r2's stage-05 data files are byte-identical to r1's
(matched fractions unchanged; magnitudes never gate matching).

| reference | r1 median (MAD) | r2 median (MAD) |
|---|---|---|
| pang (Mc) | +0.616 (0.303) | −0.018 (0.224) |
| baker (mixed) | +0.648 (0.196) | +0.006 (0.118) |
| uuss (ML, anchor) | +0.646 (0.193) | +0.003 (0.119) |

Only UUSS ML was fitted; pang Mc and the Baker scales are independent
validation and land at ≈0 as well. Scatter drops ~40% (the distance-dependent
bias was inflating it). Median provisional ML 2.27 → 1.65. Measurement set
identical (18,241 / 4,064 accepted); provisional 443 (442 in v1, one event
moved across the station-MAD gate); v1 still 2,080 events; stage-10 checks
pass. Self-consistency: refitting on r2 selects `constant` with c ≈ +0.0002 —
no residual distance structure remains.

Residual structure left for later rounds: per-station medians span roughly
−0.5…+0.35 after recalibration (HRU −0.49, ICF +0.31, LKC +0.34 with n≥40) →
station corrections are the natural r3+ magnitude knob; the r3 ordering below
keeps association levers (first-48h completeness) ahead of it.

r3 candidates (one knob each): association levers to lift first-48h matched
fraction under M5.7 coda saturation; ML station corrections; velocity-model
refinement.

### Association rung (2026-10-19) — closed as a negative result

Before opening r3 the association levers were tested exhaustively offline
(`/tmp/sweep_r3.sh`: each variant re-runs 03/04/05 into `export/<variant>`
with 01–02 and the NLL grids hardlink-reused from r1; pristine configs
restored on exit). Baseline = r2 (identical to r1 here: pang 2,177,
first-48h M≥2 0.704, v1 2,080, median rms 0.373 s):

| variant | pang matched | 48h M≥2 | v1 | median rms | verdict |
|---|---|---|---|---|---|
| x_eps6 (dbscan_eps 10→6) | 2,174 | 0.701 | 2,066 | 0.373 | wash |
| x_os15 (oversample_factor 5→15) | 2,179 | 0.704 | 2,079 | 0.373 | wash (+5 near-dups) |
| x_sig3 (max_sigma11 1.5→3.0) | 2,193 | 0.710 | 2,049 | 0.381 | marginal, degrading |
| x_min8 (min 10/4/3/6 → 8/3/2/4) | 3,227 events | — | — | — | rejected: 624 NLL failures |

Diagnosis of the residual pang gap (98 M≥2 first-48h events passing all
gates yet unmatched): they *have* picks (median 13 picks / 8 stations vs 65/33
for matched controls) and the merge-stage `rejected_candidates.csv` is empty —
they fail per-block BGMM assembly, not the final gates. 78% of their picks are
absorbed by other events; half are sub-second multiplets of their absorber
(median |Δt| ≤ 0.6 s), 25–49% sit 5–10 s away. The unmatched bulk below M2
(median unmatched magnitude 0.9) is template/matched-filter detection below
the PhaseNet pick floor — unreachable by association tuning. Conclusion: no
association lever moves the needle without paying in rms, near-duplicates, or
NLL failures; the rung is closed and r3 proceeds to the next knob in order
(ML station corrections).

### r3 (2026-10-19) — knob: ML station corrections

One knob: `magnitude.station_corrections` (31 entries, config), applied in
stage 09 as `ml_station = mean(log10 A) + correction(r) − station_term`. The
terms are the per-station median corrected residuals from the r2
self-consistency fit (`06_fit_ml_calibration.py` on frozen r2, UUSS-ML
anchor, n≥20 measurements; no entry = 0). Stages 01–05 are again untouched:
`export/r3` hardlink-reuses r1's 01–04 outputs, so stage 05 must be
byte-identical to r2 and only 09/10 move.

Sign convention (learned the hard way): the config entries are the fit.yaml
medians **verbatim** — the fit's residual is `ml_station − reference`, and
stage 09 *subtracts* the entry, so `ml_new = ml_station − median(our − ref)`.
The first r3 run had the block negated; the station-MAD *doubled*
(0.131 → 0.246) — the doubling signature of a sign-flipped correction — and
every reference MAD widened. That run was discarded (same knob, application
bug); the corrected run is r3's result:

| metric | r2 | r3 |
|---|---|---|
| median per-event station-ML MAD | 0.131 | **0.071** |
| pang (Mc) event median / MAD | −0.018 / 0.151 | −0.013 / 0.136 |
| baker (mixed) event median / MAD | +0.006 / 0.079 | +0.006 / 0.071 |
| uuss (ML, anchor) event median / MAD | +0.003 / 0.080 | +0.004 / 0.068 |
| provisional ML count (in v1) | 443 (442) | 443 (442) |
| v1 working events | 2,080 | 2,080 |

Measurement set identical (18,241 / 4,064 accepted); stage-05 data files
byte-identical to r2; stage-10 checks pass. Self-consistency refit on r3:
constant dead (t=0.25), per-station medians |max| 0.030 — the fitted station
structure is gone. A small residual geometric term re-emerges (t=3.3,
a=0.083 → ±0.08 mag over 10–60 km): station terms and distance are partly
confounded (stations sit at characteristic ranges), so removing station
structure exposes a sliver of it. Not chased further — ±0.08 is below the
reference scatter and a third nested correction would overfit the anchor.

r4 candidates (one knob each): velocity-model refinement (depths more
dispersed than Pang's 8–9 km concentration); picking thresholds; the residual
geometric term above (documented, deliberately not taken).

### r4 (2026-10-19) — knob: velocity-model basin-fill layer

Diagnosis on r3: the NLL catalog is simultaneously **deep** (median depth
difference +0.86 km vs pang / +0.62 vs uuss on ML-bearing events; +0.28/+0.61
on the full matched set) and **late** (signed origin-time difference +0.34 s
vs both references). Same-sign depth+time bias is the fingerprint of a model
too fast above the source: BP89 puts 5.9 km/s immediately below sea level, a
smoothed regional average with no Salt Lake Valley basin fill. (Depth datum
is not the cause — stage 05 already compares pang on the sea-level datum.)

Offline sweep (`/tmp/sweep_r4.sh`, NLL-only relocation of r1's frozen
associations, fresh grids per variant; r1's `inputs.json` rewritten atomically
per variant so hardlinks stay intact). Baseline r3: pang dZ +0.28 / uuss
+0.61, dt +0.34 s, dEpi 1.35 km:

| variant | dZ pang | dZ uuss | dt pang/uuss | dEpi | verdict |
|---|---|---|---|---|---|
| basin fill 0–3 km bsl @ 3.5 | +0.30 | +0.54 | −0.14 / −0.16 | 1.33 | overshoots dt |
| basin fill 0–2 km bsl @ 4.0 | +0.26 | +0.54 | **+0.05 / +0.04** | 1.35 | **adopted** |
| main layer 5.9 → 5.7 | +0.59 | +0.91 | +0.21 / +0.20 | 1.36 | degrades depth |
| Vp/Vs 1.73 → 1.68 | +0.66 | +1.00 | +0.36 / +0.37 | 1.37 | degrades everything |

All variants: matched counts unchanged, zero NLL failures. The two non-basin
levers are negative results — the depth offset does not yield to 1-D model
knobs (it sits near the absolute-locator resolution floor: posterior depth σ
1.46 km vs pang's hypoDD tightness). The adopted model is registered as
`bjarnason_pechmann_1989_plus_slv_basinfill2km` (BP89 rows + one layer,
sea level–2.0 km bsl @ Vp 4.0, Vs = Vp/1.73; status `adopted_round4`).

Note the residual degeneracy: part of the +0.34 s baseline dt may be PhaseNet
pick lateness rather than model error; the basin layer absorbs whichever
mixture it is. The matched-fraction feedback does not distinguish the two.

Round run (03 re-associated under the new model → fresh grids → 04 → 05 → 09
→ 10; 01–02 hardlink-reused). The full round beats the NLL-only sweep: with
GaMMA consistent with the locator, depth moves further toward the references:

| metric | r3 (BP89) | r4 (basin fill) |
|---|---|---|
| dZ pang / uuss (matched set) | +0.28 / +0.61 km | **+0.06 / +0.39 km** |
| signed dt pang / uuss | +0.34 / +0.34 s | **+0.08 / +0.06 s** |
| median NLL dEpi | 1.35 km | 1.41 km |
| matched fractions pang/baker/uuss | .522/.578/.913 | .522/.578/.913 |
| v1 fractions pang/baker/uuss | .405/.500/.851 | **.430/.530/.873** |
| v1 working events | 2,080 | **2,215** |
| near_depth_bound flag | 194 | **46** |
| azimuth_gap_gt_180 flag | 122 | 88 |
| ML medians pang/baker/uuss | −.013/+.006/+.004 | −.026/−.007/−.009 |
| station-MAD / measurements | 0.050 / 18,241 | 0.053 / 18,698 |

Reading: under BP89 a quarter of events were pinned at/near the depth grid
bound (`near_depth_bound` 194) — a pathology the basin fill removes, which is
where the +135 v1 events come from (matched fractions constant → real
detections retained, not splits). The ML calibration survives relocation
unchanged (medians shift ≤0.026; MADs flat). The +0.06 km dEpi cost is well
inside the matching gates. Stage-10 checks pass; mainshock located; v1 frozen
at 2,215.

r5 candidates (one knob each): picking thresholds (PhaseNet 0.3 → pick-bias
probe on the residual dt; interacts with the degeneracy note above); station
subset (Pang-39 masking); the r3 leftover geometric term (documented, low
priority). The depth rung is now closed: remaining dZ ≈ +0.06/+0.39 sits at
the absolute-locator resolution floor (posterior depth σ 1.46 km).

### r5 (2026-10-19) — knob: PhaseNet pick thresholds 0.3 → 0.2

Motivation: the pang-gap diagnosis said the unmatched bulk is template
detections below the pick floor — the pick threshold *is* that floor. ~20% of
r4 picks sit at probability 0.30–0.40, so the density at the floor is real.
Sweep (`/tmp/sweep_r5.sh`: per variant a fresh 01+02 (02 re-runs PhaseNet —
thresholds apply at classify time; full probability streams are only exported
for the pilot), fresh 03, NLL reuses r4's grids — model/stations unchanged).
Stage 02 refuses a config that differs from 01's snapshot, so 01 re-runs too
(seconds):

| | r4 (0.3) | t20 (0.2) | t15 (0.15) |
|---|---|---|---|
| picks | 141,343 | 189,955 | 229,949 |
| GaMMA events / assoc rate | 2,490 / 49.2% | 2,791 / 40.7% | 3,011 / 35.9% |
| median rms | 0.370 s | 0.381 s | 0.389 s |
| pang / baker / uuss matched | .522 / .578 / .913 | .565 / .618 / .927 | .592 / .648 / .937 |
| pang 48h M≥2 / M≥1 | .701 / .540 | .722 / .573 | .731 / .594 |
| v1 (orphan*, fraction) | 2,215 (100, 4.5%) | 2,415 (159, 6.6%) | 2,598 (209, 8.0%) |
| v1 pairs ≤2 s / NLL fails | 3 / 0 | 7 / 0 | 7 / 0 |
| dt / dEpi / dZ pang | +.08 / 1.41 / +.06 | +.08 / 1.45 / −.08 | +.08 / 1.46 / −.14 |

*v1 events matched to none of the three references.

Reading: the largest single-round matched gain since r1 — anchored growth is
~70% of v1 growth at both steps (no collapse), all three references rise
(UUSS +21/+14 = real events by the cleanest anchor), zero NLL failures, dup
pairs flat. But gains diminish (+176→+116 pang) while noise keeps climbing
(assoc rate −8.5 pp/step, orphan share +1.5 pp/step) and PhaseNet scores are
explicitly not calibrated precision below ~0.2. **Adopted 0.2**: ~70% of the
two-step anchored gain at half the noise cost. A threshold probe of the dt
degeneracy came back negative: dt is +0.08 s at every threshold — the r4
model absorbed it; pick lateness is not threshold-driven.

Round run (01–05 fresh, NLL grids hardlink-reused from r4, 09/10 with the
r2+r3 magnitude calibration unchanged) reproduces t20 exactly and passes all
gates: pang 2,354 (.565) / baker 2,294 (.618) / uuss 1,328 (.927); v1 2,415;
first-48h M≥2 0.722, M≥1 0.573; NLL failures 0; stage-10 checks pass. The ML
calibration survives the larger pick set: measurements 20,317 (4,203
accepted), ML−reference medians −.035/−.007/−.009 with MADs 0.144/0.077/0.076
(pang MAD widens slightly — the new events are smaller and noisier);
provisional ML on 441 events (445 in r4: the new v1 events are mostly below
the amplitude-SNR measurement gates).

r6 candidates (one knob each): station subset (Pang-39 masking — aligns the
station set with the reference's, tests how much of the residual gap is
geometry); PhaseNet weight variant (original vs the 2023 retrain), a bigger
lever than thresholds but changes two things (picker + thresholds interplay);
stages 52/53 double difference (depth precision, closes the dZ MAD gap that
1-D model knobs cannot).

### r6 (2026-10-19) — knob: double-difference relocation (new stage 52)

Motivation: r4 closed the 1-D-model rung at pang dZ MAD 1.07 km — the
absolute-locator floor (NLL posterior σ 1.46 km vs pang's own hypoDD). DD
relocation consumes *differential* times, so static model error cancels; it
is the method designed for exactly the residual we have, and the strongest
lever left for dEpi (1.4 km) as well.

Architecture: FDTCC rejected (expects one mseed per net-station-day; Magna
waveforms are per-station-component-day, 1,184 files) and RC 52/53 are
experiment-entangled, so stage 52 is a self-contained kernel driving hypoDD
directly: `00_config/double_difference.yaml` +
`01_pipeline/52_double_difference.py` → `export/r6/52_double_difference/`.
Inputs are r5's stage-04 outputs (2,788 located events, 77,365 picks, 43
stations); hypoDD is rebuilt from the TRACE LIB with capacity overrides
(MAXEVE 2,937, MAXDATA = ct+cc+1,000); the control file is RC's tuned
`14_tune_hypodd/runs/cc3_d1` verbatim (CT+CC, damping 80/40, 12 iterations);
velocity model = the round's association model. Export = r5's 01–05/09/10
hardlinked + the new 52 output dir (DD is a post-processing layer; the round
catalog and v1 stay on NLL positions, so stage-05 round metrics are
unchanged by design).

Kernel (curve/whiten copied verbatim from RC `38_vector_s.py`): windows cut
pick-aligned at 100 Hz, scalar P on Z / vector S on N+E whitened so component
RMS = SNR, full-vector-norm dot product over ±40-sample lags. Sign
convention unit-tested in-run with synthetic two-trace checks (lag = the
differential pick error; cc arrival difference = (t_a−t_b) − lag recovers the
true arrival difference to 0.008 s). Gates: two bands (2–10 / 1–6 Hz with the
|Δlag| ≤ 0.020 s cycle-skip check), SNR ≥ 2.0, CC ≥ 0.75 in both bands, peak
margin 0.08 outside ±8 samples, |lag| < 0.39 s. Pairing: k=8 nearest events
within 10 km in NLL 3-D (14,116 pairs).

CC yield (the case's honest limit): 243,089 candidate observations → 5,538
accepted (2.3%), median accepted CC 0.843. The dominant rejection is the
all-gates-at-once combo (low CC + ambiguous peak + band instability, 102k) —
genuinely dissimilar waveforms, not gate tuning: Magna aftershocks are
distinct sources, not template repeats of one another. Net effect: a
thin-but-clean CC layer (367 pairs ≥ 4 obs → 3,303 dt.cc rows) riding on a
strong catalog layer (242,394 dt.ct rows). hypoDD relocates 2,638/2,788
events (150 without sufficient links); median position shift 1.15 km, origin
shift +0.043 s.

Depth datum: hypoDD's flat-layer analytic tracer with stations pinned to the
model top (station.dat takes no elevations) runs ~0.9 km shallower than NLL's
eikonal solution on the same model. Two controls: a ct-only rerun (IDATA=2,
`run_ctonly/`) reproduces the shift (paired pang dZ median −1.18 vs −1.09,
MAD 0.81 both → the CC layer is not the cause), and the shift is spatially
uniform across populated lon/lat bins (−0.8…−0.9). Adopted the constant
`depth_datum_offset_km: 0.90` inside stage 52 — an in-sample calibration of
the same status as the r2 ML constant. Post-offset dZ by pang reference
depth (paired events, MAD in parentheses):

| pang ref depth | n | NLL dZ | DD dZ |
|---|---|---|---|
| 4–8 km | 370 | −0.23 (1.68) | −0.27 (1.26) |
| 8–12 km | 1,644 | +0.01 (0.98) | −0.18 (0.74) |

Results (DD matched = one-to-one match on relocated positions; paired rows =
events matched by both locators, so the deltas are like-for-like):

| | NLL matched | DD matched | dEpi NLL→DD | dEpi MAD | dt NLL→DD | dZ med (MAD) NLL→DD |
|---|---|---|---|---|---|---|
| pang | 2,102 | 2,290 | 1.42→0.85 | 0.53→0.27 | +.079→+.098 | −0.00 (1.07) → −0.19 (0.81) |
| baker | 2,241 | 2,241 | 1.32→0.91 | 0.61→0.38 | +.172→+.190 | −1.73 (0.84)* |
| uuss | 1,295 | 1,322 | 1.46→0.94 | 0.44→0.29 | +.084→+.060 | n/a → +0.09 (0.83) |

*baker depths follow a different convention (median −1.73 stable across
rounds); excluded from depth claims as in r1–r5.

Reading: DD cuts dEpi median ~40% and halves its MAD against all three
references, pulls +188/+0/+27 events inside the 15 km match gate, and takes
pang dZ MAD 1.07 → 0.81 km — below the r4 absolute-locator floor. Origins
move +0.04 s median (pang dt +0.02 s, uuss dt improves to +0.060 s). The
rung is closed as a win; the layer ships as `relocated_events.csv` (2,638
events, `*_nll`/`*_dd` columns) with its own report
(`52_double_difference/report.json`).

r7 candidates (one knob each): port the RC benchmark evaluation layer to
Magna (figures + scorer — makes the case agent-runnable; recommended, no
catalog change); Pang-39 station-subset masking; hypoDD control tuning
(least promising — the control file is already RC's tuned values).

### r7 pilot (2026-10-21) — Match&Locate detection (stage 60), one day

New stage `01_pipeline/60_match_locate.py` + `00_config/match_locate.yaml`,
built on `seismotools/match_and_locate` (two-step interface prepare.py →
run.py). Templates: greedy 1 km spatial cover of the r6 v1 catalog by v1
events with ≥15 stations and σz ≤ 2 km, DD positions; marks from stage-04
picks (|residual| ≤ 0.3 s) else BP89+basin model times; 50 Hz, 2–10 Hz, P on
Z / S on N,E, 2 s windows (0.3 s before mark); grid ±1 km at 0.25 km, depth
±1 km at 0.5 km (405 nodes); run thresholds permissive (N×MAD 8), final
thresholds chosen by an offline merge sweep. Scored on 2020-03-20 against the
masked references (evaluation matcher 4 s / 15 km). Pilot: 20 templates
covering 66.7% of v1 events within 1 km; 528 Pang events that day; r6 baseline
285 events, Pang recall 47.0%, 97.5% matched to some reference.

| channels | rows | run wall | N×MAD | M&L events | Pang recall | r6 ∪ M&L | matched any ref |
|---|---|---|---|---|---|---|---|
| all ≤ 60 km, SNR ≥ 3 | 1,791 | 530 s | 9 | 181 | 28.6% | 50.2% | 85.6% |
|  |  |  | 10 | 127 | 23.3% | 49.4% | 98.4% |
| ≤ 25 km, SNR ≥ 5 | 874 | 329 s | 9 | 301 | 44.5% | **58.1%** | 85.7% |
|  |  |  | 10 | 188 | 32.8% | **52.7%** | 96.8% |
|  |  |  | 8 | 1,427 | 70.3% | 73.5% | 30.2% |

Readings: (1) channel dilution is the dominant lever — averaging ~90 rows of
mostly far, low-SNR channels buries M ≈ 0.7–0.8 events; near/high-SNR rows
raise M&L-alone recall ×1.5 at equal precision and halve the cost. (2) A sharp
noise floor sits between N×MAD 8 and 9 for 405-node grids (look-elsewhere);
at 8 most detections match no reference — whether some are real uncatalogued
events needs waveform review, not assumed. (3) Recall does not fall with
distance to the nearest template between 0.25 and 2 km (27/33/23%); the
pilot has almost no events within 0.25 km of a template, so the dense-template
regime is untested. (4) Matched detections: |dt| median 0.11 s, epicentral
0.75 km. Fixes found by the pilot (tool side): off-grid interpolation bounds,
km→degree grid lost a node (360 vs 405), zero-filled template windows passed
the SNR gate (SNR = ∞), now rejected.

r7 next: second pilot axis on the near-channel setting — distance 15–20 km and
min_rows, and a denser template set (radius 0.5 km) at equal cost; waveform
review of the N×MAD 8–9 band to place the threshold; then the full 8-day run.

### r7 pilot round 2 (2026-10-21) — channels, template density, null test

Same day (2020-03-20) and scoring; r6 alone 47.0% Pang recall.

| variant | templates / rows | run wall | r6 ∪ M&L @ N×MAD 9 | @ 10 | matched-any @ 10 |
|---|---|---|---|---|---|
| all ≤ 60 km, SNR ≥ 3, 1 km cover, ±1 km grid | 20 / 1,791 | 530 s | 50.2% | 49.4% | 98.4% |
| ≤ 25 km, SNR ≥ 5 | 20 / 874 | 329 s | 58.1% | 52.6% | 96.8% |
| ≤ 20 km | 20 / 692 | 267 s | 59.7% | 53.2% | 95.6% |
| ≤ 15 km (min_rows 9) | 20 / 410 | 174 s | 59.3% | 53.8% | 93.2% |
| 0.5 km cover, 40 templates, ±0.5 km grid (75 nodes) | 40 / 1,719 | 215 s | **62.1%** | **56.4%** | 94.7% |

Channel distance plateaus at 20–25 km (15 km loses precision). More
templates with a smaller grid beat fewer templates with a larger one at
lower cost (the dense set covers only 39% of v1 events yet recovers most).

Null test (`04_comparison/08_null_run.py`, every continuous channel
circularly shifted by its own random lag >= 600 s, same templates and
parameters) on the dense variant: false/real = 362/798 at N×MAD 8, 54/460 at
8.5, **5/355 at 9 (1.4%)**, 2/298 at 9.5, 0 at >= 10. So N×MAD 9 is the
threshold, and most of the ~11% of N×MAD >= 9 detections that match no
reference catalog are not noise (the null explains ~1.4 points) — likely
events the references miss (caveat: the null measures noise-driven false
alarms only, not detections triggered by other real events). Waveform
review (`04_comparison/07_review_match_locate.py`): templates align on the
data at the detected node; >= 3 of the 6 nearest rows at CC >= 0.3 in 66–72%
of matched vs 40–49% of unmatched detections at N×MAD >= 9.

Full-run configuration adopted (match_locate.yaml): 0.5 km cover (320
templates, 77.9% of v1 events), ±0.5 km grid at 0.25/0.5 km, rows <= 20 km
with SNR >= 5, final N×MAD 9 / CC 0.

### r7 full run (2026-10-22) — Match&Locate over the eight-day window

Configuration as adopted after pilot round 2: 320 templates selected (0.5 km
cover, 77.9% of v1), 311 kept by prepare (9 had < 12 near rows), 11,700
channel-phase rows; 2,488 (day, template) jobs, all successful, run wall
3.0 h (8 jobs × 8 threads), prepare 4.6 min. Final catalog threshold N×MAD 9,
CC 0, merge separation 6 s.

Threshold and duplicates. Mainshock-day null run (channels shuffled):
49/2,170 false at N×MAD 9 (2.3%), 6/1,966 at 9.5; 03-20 pilot null 1.4%.
The 14 detections in the 13 h before the mainshock (no reference events) are
all N×MAD 9.0–9.9, CC 0.13–0.34 — consistent with the null rate scaled to 311
templates (~1/h). Unmatched detections are enriched 4–15 s after known
events (2–3× a random baseline); widening the merge separation 4 → 6 s
removes 382 detections of which 301 match no reference, for −68 Pang matches
(8 s starts removing real pairs: 43% of removals Pang-matched) → 6 s adopted.

| catalog (masked, 8 days) | events | Pang | Baker | UUSS |
|---|---|---|---|---|
| r6 | 2,661 | 55.4% | 60.9% | 92.0% |
| M&L alone | 5,219 | 79.5% | 81.8% | 95.4% |
| **r6 + M&L new** | **5,412** | **80.8%** | **84.1%** | **97.4%** |

Per period (r6 → r6 + M&L, Pang): first 48 h 54.6% → 80.2%, later 57.7% →
82.4%. 5,220 M&L events, 2,468 coincide with r6 events (2 s / 5 km), 2,752
new; union 5,543 rows (`export/r7/60_match_locate/full/catalog/`:
`ml_events.csv`, `r6_plus_ml_events.csv`). On the mainshock day most
unmatched detections have high N×MAD (median 11.2) and are not explained by
the null — consistent with events the references miss under coda
saturation, but not verified event by event.

Open for the r7 catalog: (1) relocate the new events with the DD layer — they
carry no picks, so the input is waveform differential times against their
detecting templates (and neighbours), not dt.ct; (2) magnitudes — 200 of 311
templates have no ML, so their detections carry NaN; calibrate the relative
M&L magnitudes on the 111 ML templates or extend stage 09 to the templates;
(3) M&L magnitudes read high near the noise (tool METHOD_NOTES).
Storage: pilot and null continuous folders removed (regenerable); the full
dataset (17 GB) is kept for (1).

### r7 catalog (2026-10-22) — relocation decision, magnitudes, assembly

Relocation. Feeding the 2,752 new events to the stage-52 DD layer was tried
via a round-shaped input with "derived picks" (template arrival + M&L node
moveout, refined by template correlation within ±0.2 s, CC >= 0.5): only
10,070 picks (median 3 per event, 223 events with >= 8; 231 with none) — the
new events are M ≈ 0.5–1 and too weak per channel for pick-pair DD, which is
why the pick-based pipeline missed them. Not needed either: against Pang the
M&L positions are already DD-grade (matched events: M&L on r6-coincident
events dEpi 0.82 km / dZ MAD 0.74; M&L new events 0.96 / 0.86; r6 DD 0.85 /
0.80; r6 NLL 1.42 / 1.08) because each template sits at its DD position and
M&L locates relative to it on the network-stacked correlation. Decision: new
events keep M&L positions; the derived-pick stage was removed (negative
result recorded here).

Magnitudes. MatchLocate2 writes user0 + median log10 amplitude ratio; for
templates without ML the ratio is recovered from the native output (user0 =
-12345). Templates without ML take the median of M_T1 + L over detections of
their own event by ML templates (two passes: 111 → 310 of 311 templates);
each event takes the median over all templates that detected it (median 8).
Bias vs UUSS ML: +0.07 (MAD 0.08) for direct-ML templates, +0.11 (0.12) for
chain-only; the catalog overall +0.08 (0.12, n 1,346).

r7 catalog = `export/r7/60_match_locate/full/catalog/r6_plus_ml_events.csv`:
5,515 events (r6 2,791 with DD positions where relocated — 2,638 — else NLL
153; plus 2,724 M&L events), magnitudes r6 ML 441 / M&L chain 4,781 / none
293, with event_id, location_source, magnitude_source per row.

| r7 vs references (masked, 8 days) | events | Pang | Baker | UUSS |
|---|---|---|---|---|
| r6 | 2,661 | 55.4% | 60.9% | 92.0% |
| **r7 (r6 + M&L)** | **5,414** | **81.1%** | **84.3%** | **97.6%** |

Location vs Pang over the whole r7 catalog: dEpi median 0.88 km, dZ MAD 0.83
km (DD rows 0.84/0.80, M&L rows 0.95/0.84). The 153 NLL-only rows (no DD
link) are poor (49 matched: dEpi 2.1 km, dZ −6.4 km) — flag them, do not trust
their depths. Full-run continuous data deleted after export (17 GB,
regenerable in ~5 min); export/r7 now holds tables, templates and run outputs.

### r7 known issue (2026-10-22) — the shallow "structure" at 0–5 km is a location artifact

The along-strike section of the r7 catalog shows a band at 0–5 km below sea
level (528 rows within ±6 km along strike, 9.6%) absent from Pang (1.2% of
its events shallower than 5 km there). It is not a new structure:

- Same events, different depth: 325 of the 528 match Pang events (4 s / 15 km);
  Pang puts 95% of them deeper than 5 km (median 8.2 km; Baker 9.4, UUSS 6.9).
  Matched shallow events sit 1.5 km west and ~6 km shallower than Pang's
  positions for them (r7 median 2.1 km vs 8.2 km) — the band is part of the
  main 8–10 km cluster displaced up and west.
- Origin: the NLL absolute locations (stage 04), not DD. 80% of the shallow DD
  rows were already shallower than 5 km in NLL (median 0.5 km bsl); DD moved
  them 1.3 km deeper, not enough. 100 NLL-only rows (no DD link) are shallow.
- Mechanism: weakly constrained small events — half the picks (median 7 P +
  7 S vs 13 + 14), nearest picked station 6.1 vs 4.4 km, posterior σz 2.2 vs
  1.35 km, 9 vs 13 stations — trade depth for origin time: they are
  +0.23 s late vs Pang (deep events +0.05 s) and 3.5 km off horizontally
  (1.3 km for deep). The low-velocity top layers (basin fill) let a shallow,
  late solution fit as well. Not a coda/association effect: shallow and deep
  events have the same timing (23% vs 26% in the first 6 h).
- Propagation: 134 of the 135 shallow M&L events were detected by the 17
  templates that are themselves shallow (templates inherit their DD depth).
- The quality gates miss them: 71% of the shallow r6 rows are in v1.

Fix candidates (r8, one at a time): (1) NLL depth prior / minimum-pick gate
(e.g. relocate events with < 10 picks or σz > 2 km under a Gaussian depth
prior on the sequence depth) and a quality flag for the rest; (2) start DD
from corrected depths for those events so the cc/ct links can hold them;
(3) drop or relocate the 17 shallow templates and re-run stage 60 (their
134 shallow detections then come out at the template depth). Until then,
treat r7 depths shallower than ~5 km bsl as unreliable. Done in r8 (below):
(1) and (2) as stated, (3) replaced by shifting the M&L events with their
templates, plus a DD acceptance gate found along the way.

### r8 (2026-10-22) — depth prior + DD acceptance (fixes the r7 shallow artifact)

Knob: absolute depths of weakly constrained events. Stages 01–04 hardlinked
from r6 (unchanged); new stage 45, then 05/09/10/52 and the stage-60 catalog
export rerun under `export/r8`.

1. **Stage 45 depth prior** (`01_pipeline/45_depth_prior.py`, config
   `depth_prior`): weak events (n_phases < 20 or σz > 2 km; 1,428) have their
   NLL posterior scatter re-weighted by N(9.24 km bsl, 2 km) — the median of
   this round's own 1,199 well-constrained events, no reference input — and
   take the weighted median; origin time shifted by the change in predicted
   travel time (same layered tracer). 1,414 applied, 14 `depth_unresolved`
   (ESS < 30). Applied events vs Pang: dZ median −1.29 → −0.19 km, MAD 1.79 →
   0.85, |dZ| > 4 km 23.8% → 3.3%, dt +0.055 → −0.002 s. Stage 05 reads the
   stage-45 table when it exists.
2. **DD from corrected depths** (stage 52 unchanged, new input): 2,694/2,788
   relocated; Pang dZ +0.09 (MAD 0.71; r6 −0.19/0.81). Median dEpi 1.06 km
   (r6 0.85) is a rigid offset of the DD cluster, not scatter: after removing
   the median vector offset (r6 −0.59 E/−0.38 N, r8 −0.41/−0.84 km) both
   rounds sit at 0.45 km. hypoDD's absolute position floats between runs; an
   absolute anchor (e.g. centroid tied to well-constrained NLL) is open.
3. **DD acceptance gate** (`double_difference.yaml` `max_vertical_shift_km:
   3.0`, applied in the stage-60 export): the first r8 figure still showed a
   thin line at ~2 km bsl. hypoDD traps weakly linked events under the strong
   contrast at 3.5 km model depth (~2.0 km bsl, Vp 4.0 → 5.9): 104 events moved
   up > 3 km; vs Pang their DD depth is off by 5.08 km (median |err|), their
   DD-start depth by 1.51 km. The 63 moved down > 3 km are neutral (2.19 vs
   2.29 km), so the gate is symmetric. Rejected rows keep the start position
   (`location_source = dd_rejected`, 167).
4. **Catalog** (`60_match_locate.py --stage export --catalog-round r8` →
   `export/r8/60_catalog/catalog_events.csv`): the r7 M&L detections (no
   rerun), each shifted by its template's position change r7 → r8 (311
   templates moved). 5,522 events.

| | r7 | r8 |
|---|---|---|
| rows < 5 km bsl within ±6 km along strike | 528 | **224** |
| vs Pang dZ median (MAD), \|dZ\| > 4 km | −0.23 (0.83), 7.7% | **+0.09 (0.72), 2.8%** |
| vs Pang dEpi (DD offset, see 2) | 0.88 | 1.09 |
| recall pang / baker / uuss | .817 / .849 / .980 | .817 / .849 / .981 |

Residual (r9 candidate): 52 *well-phased* events (≥ 20 phases, σz ≤ 2 km)
are located at ~0.6 km bsl where Pang has them at 7.4 km (37 matched, 97%
deeper than 4 km). Their NLL posteriors carry < 1% mass near the sequence
depth, so re-weighting cannot move them; they need a constrained relocation
(NLL with a depth prior in the misfit, or a pick-outlier pass). Several are
M&L templates (e.g. gamma_0000376, gamma_0001329, gamma_0002171), so their
families form the short streaks still visible at 1–3 km bsl (124 of the 260
rows above 5 km bsl are M&L rows).

### r9 (2026-10-23) — test: step velocity layering (rejected)

Prompted by the Maple Creek port, where stages 03/04 turned out to ramp
linearly between the registry's layer tops (GaMMA `np.interp` of the node
list; NLL `LAYER` gradients to the next top) and the ramp made origins
+0.47 s late against a published layered model. Stage 03/04 now take
`association.yaml velocity_layering: linear|step` (default linear). r9 =
r6 + step (01–02 hardlinked from r6; 03, 04, 05 rerun):

| vs reference | r6 linear | r9 step |
|---|---|---|
| pang matched (v1) | 0.565 (0.455) | 0.562 (0.472) |
| pang dt / epicentral | +0.08 s / 1.45 km | −0.14 s / 1.76 km |
| pang dZ (MAD) | −0.08 (1.13) | −0.74 (1.21) |
| uuss dt / epicentral | +0.09 s / 1.46 km | −0.14 s / 1.71 km |
| NLL median RMS | 0.376 s | 0.375 s |

Rejected: every location statistic degrades, recall is flat. Here the model
in use is not the published one — the r4 basin-fill layer was chosen by a
sweep run under the ramp, so "BP89 + basin + ramp" is the calibrated
combination; under steps the shallow section is slower and origins come out
early and shallow. A fair step test would re-sweep the basin layer; not
pursued (r6–r8 already agree with the references at the absolute-locator
floor). Config restored to round r8 with `velocity_layering: linear`;
export/r9 (03–05) kept as the record.
