# Magna 2020 expert pipeline — experiment summary

Distilled record of the expert-catalog experiment (2026-10-18 → 2026-10-22):
what was built, what each round changed, the headline result, and where the
remaining difference against the published catalogs comes from. The full
round-by-round log with all diagnostics is `PLAN.md`; operations are in
`README.md`; scoring conventions in `evaluation/README.md`.

## Setup

- **Data**: 8-day window 2020-03-18T00:00Z → 03-26T00:00Z, 1,184 daily
  per-component MiniSEED files (~11 GB), 43 primary three-component
  short-period instruments (EN/EH families, one per site).
- **Pipeline** (ported from Ridgecrest): PhaseNet picking → GaMMA association
  → NonLinLoc location → reference matching → Wood–Anderson ML → validation.
  Since r6 a hypoDD double-difference layer runs on top (post-processing);
  since r7 a Match&Locate template-detection stage (60, `seismotools/
  match_and_locate`) adds the events below the picking floor.
- **References** (masked cohort, hard-gated counts): Pang et al. (2020)
  relocated catalog 4,169; Baker & Whidden (2021) picks-as-events 3,712;
  UUSS/ComCat operational 1,432. Gates 4 s / 15 km, one-to-one.

## Round ladder

| Round | One knob | pang / baker / uuss matched | Verdict |
|---|---|---|---|
| r1 | baseline port | .522 / .578 / .913 | all gates green; v1 2,080 events |
| r2 | Utah ML recalibration (spreading 1.11→2.93) | unchanged (by design) | ML medians +0.62 → ≈0 vs all three |
| r3 | ML station corrections (31 stations) | unchanged | station-ML MAD 0.131 → 0.071 |
| (assoc) | dbscan/oversample/sigma/min sweep | wash → degrading | **negative result**, rung closed |
| r4 | velocity model + SLV basin fill (2 km @ 4.0) | .522 / .578 / .913 | dt +0.34 → +0.08 s; dZ +0.28 → +0.06; v1 +135 |
| r5 | PhaseNet thresholds 0.3 → 0.2 | **.565 / .618 / .927** | largest recall gain; 0.15 rejected (uncalibrated) |
| r6 | double-difference relocation (stage 52) | (positions, not recall) | dEpi 1.42 → **0.85 km**; dZ MAD 1.07 → **0.81 km** |
| r7 | Match&Locate detection (stage 60), 311 templates | **.817 / .849 / .980** | 2,724 new events; null-test false 1.4–2.3%; M&L positions DD-grade |
| r8 | depth prior for weak events (stage 45) + DD acceptance gate | .817 / .849 / .981 | shallow artifact 528 → 224 rows; dZ MAD 0.83 → **0.72**, \|dZ\|>4 km 7.7% → 2.8% |

Round r8 catalog = the case's expert reference: 5,522 events
(`export/r8/60_catalog/catalog_events.csv`; round events with DD positions
where relocated and accepted, else the depth-prior NLL position, plus M&L
events shifted with their templates and chained relative magnitudes; per-row
`location_source`, `magnitude_source`). r7 had the same detections but a
shallow 0–5 km band that was a location artifact (PLAN.md r7 known issue, r8).

## Headline numbers (r8, evaluation matcher)

| | matched (P / R) | median \|Δt\| | median dEpi | dZ median (MAD) |
|---|---|---|---|---|
| vs Pang | 3,407 (61.7% / 81.7%) | 0.13 s | 1.09 km | +0.09 km (0.73) |
| vs Baker | 3,153 (57.1% / 84.9%) | 0.20 s | 1.11 km | different depth datum, excluded |
| vs UUSS | 1,405 (25.4% / 98.1%) | 0.10 s | 1.18 km | +0.36 km (0.85) |

dEpi is up from r7 (0.88 km) by a rigid offset of the DD cluster between
hypoDD runs, not by scatter (0.45 km in both rounds after removing the
median offset; PLAN.md r8).

### r7 headline

| | matched (P / R) | median \|Δt\| | median dEpi | dZ median (MAD) |
|---|---|---|---|---|
| vs Pang | 3,407 (61.8% / 81.7%) | 0.14 s | 0.88 km | −0.24 km (0.84) |
| vs Baker | 3,152 (57.2% / 84.9%) | 0.21 s | 1.02 km | different depth datum, excluded |
| vs UUSS | 1,404 (25.5% / 98.0%) | 0.10 s | 0.95 km | +0.10 km (0.86) |

Magnitudes vs UUSS ML: +0.08 (MAD 0.12, n 1,346). Low precision against a
single reference is by construction: r7 holds ~1.3× Pang's count and the
channel-shuffled null attributes only 1.4–2.3% of detections to noise, so
most unmatched events are not in the references (not verified one by one).

### Previous headline (r6)

| | matched (P / R) | median \|Δt\| | median dEpi | dZ median (MAD) |
|---|---|---|---|---|
| vs Pang | 2,374 (85.1% / 56.9%) | 0.15 s | 1.47 km | −0.08 km (1.07) NLL → −0.19 (0.81) DD |
| vs Baker | 2,307 (82.7% / 62.1%) | — | 1.4 km | different depth datum, excluded |
| vs UUSS | 1,331 (47.7% / 92.9%) | — | 1.5 km | +0.09 km (0.83) DD |

Reading: where we detect, agreement is tight (sub-0.2 s, sub-2 km, ML ≈ 0);
the open difference is **completeness against the template-detected catalogs**
(Pang, Baker), not position, time or magnitude calibration. Vs UUSS
(operational, higher completeness threshold) recall is 92.9%; precision
47.7% simply reflects that our catalog is ~2× denser.

## Why the r6 gap (root causes, evidence in PLAN.md; cause 1 addressed by r7)

1. **Detection-method class (dominant)**: the unmatched bulk has median
   magnitude 0.9 — matched-filter detections below the PhaseNet pick floor.
   Association tuning is provably unable to reach it (negative-result sweep);
   threshold 0.2 is the calibrated floor.
2. **Multiplet association limit**: 98 first-48 h M≥2 unmatched events *have*
   picks (13/8 vs 65/33 for matched) but fail per-block BGMM assembly — 78%
   of their picks absorbed by other events, half sub-second multiplets.
   Also visible as the mid-sequence lull (hours ≈ 50–90) in the rate figure.
3. **Window edge**: no 2020-03-17 pre-roll; first-48 h matched fractions run
   systematically below the later period.
4. **Station geometry**: Pang's 39 stations are unpublished; we process the
   47-station superset. Baker mixes nodal stations into "UU".
5. **Absolute vs relative location**: single-event NLL posterior depth σ is
   1.46 km vs Pang's hypoDD tightness — the r6 DD layer is the remedy and
   takes dEpi/dZ most of the way to the references' own scatter.

## Next levers (priority order)

1. ~~Matched-filter detection stage~~ — done in r7 with Match&Locate
   (template detection + grid location, 0.5 km template cover, ±0.5 km grid,
   near/high-SNR channels; PLAN.md r7). The r7 shallow depth tail was a
   location artifact, fixed in r8 (depth prior + DD acceptance). Remaining:
   52 well-phased but shallow NLL events (some are templates) need a
   constrained relocation; DD absolute offset (~0.9 km) needs an anchor.
2. **Multiplet splitting before association** — re-examine absorbed picks with
   CC lag refinement (same kernel) and split sub-second duplicates that GaMMA
   merged. Targets cause 2 (~98 events above M2 alone).
3. **Pang-39 station masking** — align station geometry with the reference;
   tests how much of the residual gap is geometry (cause 4).
4. **DD layer into scoring** — evaluate agent runs against DD positions where
   available (already exported as `relocated_events.csv`).
5. **Pre-roll data** — acquire 2020-03-17 if the archive permits (cause 3);
   PhaseNet weight variant (2023 retrain) is a bigger picking lever but
   changes two things at once — keep as a separate round if tried.

The benchmark layer is ported (`../` task package + `../evaluation/`, now
scoring against r8); the next milestone is the first agent runs (`min` arm).

## Storage note (2026-10-20)

`export/` was trimmed 5.9 GB → **2.3 GB** (−61 %). Every round keeps its
result products: `01` (config snapshot), `05/06` (comparison + calibration
fits), `09/10` (magnitudes, catalogs); r5/r6 additionally keep the full
pipeline (the r6 chain is the live reference and feeds DD retuning; per-round
sizes now 52/52/52/102/489/532 MB). Deleted as regenerable:
`02_pick_phasenet` and `03_associate_gamma` of r1–r4, `04/…/events_raw` of
r1–r4 (r1–r3 grids too, superseded by r4's), and r6's `52/cache` CC windows +
`52/run_ctonly` control (its numbers are recorded in `PLAN.md` r6; rerun with
IDATA=2 to reproduce). This relaxes the "per-round exports immutable once
recorded" convention for bulky intermediates — result products and the round
log remain the round's permanent record; anything deleted is reproducible
from the recorded configs, the git-locked pipeline and the external waveform
archive.
