# Prague 2011 expert pipeline — round plan

Same round mechanics as Magna and Maple Creek: round identity = config
`round` + `export_root`, one behavioural knob per round, previous rounds
immutable, never tune to force reference agreement. Feedback: stage 05
against Cochran (primary), McMahon, Isken (location anchor) and ComCat.

## Data preparation (2026-10-23, before r1)

- Velocity model: Keranen et al. (2013) located via figshare (GSA DR
  2013191 = article 12529799); numbers extracted from the vector Figure DR1;
  registered as `keranen2013_prague_1d` (6 layers; Vp 2.76–6.30, Vs
  1.48–3.66 km/s; Vp/Vs 1.68–1.87). The repository's references hold no
  numeric table (Cochran cites Keranen; McMahon uses McNamara et al.).
- ComCat benchmark box checked: a wide query returns 15 events in the window
  (all `us`, M ≥ 1.6) — the 11-row snapshot is genuine sparsity.
- Masked reference counts (hard gates): Cochran 2,078, McMahon 2,343,
  Isken 6, ComCat 11.

## Round-1 gates

1. 01/02 pilot: 22 instruments; 250/40 Hz input resampled; picks everywhere
   except gaps (OK.FNO partial days → empty blocks). Passed 2026-10-23
   (120 picks in 16:00–16:10Z).
2. 03 pilot: the `largest` window associates the Isken Mw 3.2 at 19:19Z.
3. 04: LOCATED ≥ 90 %.
4. 05: masked counts as above; matched fractions and dt/epicentral/depth per
   reference.
5. 09 numerical check; 10 checks pass with no mainshock row.

## Expected knob ladder

1. NLL station delays (Maple r5: RMS halved, epicentral −23 %).
2. Detection beyond picking: stage 60 Match&Locate (Cochran is itself
   template-enhanced; Maple pilot raised Shelly recall 5.6 → 31 %).
3. Association levers if recall is association-limited.
4. DD (stage 52) for relative locations against Cochran/McMahon.

## Round log

### r1 (2026-10-23) — baseline port, all gates green

- 02: 125,900 picks on 22 instruments, 704 blocks. First pass: 18 TA blocks
  failed the component-grid check — TA day files change the components'
  native sample phase, and FFT resampling kept those start times. Fix:
  resample onto the absolute 100 Hz grid (anti-alias low-pass at 40 Hz
  before downsampling, Lanczos a=20); rerun with no failures.
- 03 pilot: the `largest` window associates the Isken Mw 3.2 (19:19:15Z,
  15 stations, ~0.2 km from Isken's epicentre); 2 / 6 / 9 events in the
  low-rate / active / largest windows.
- 03/04 full: 2,860 events, 2,859 LOCATED; median RMS 0.20 s; 140 pinned at
  the top depth bound (z ≈ 0) — open item. 2,582 in scope, v1 2,338.
- 05:

| Reference | Masked | Matched (v1) | median \|dt\| | epicentral | dZ median (MAD) |
|---|---|---|---|---|---|
| Cochran | 2,078 | **0.619** (0.576) | 0.10 s | **0.48 km** | −0.04 (0.59) |
| McMahon | 2,343 | **0.720** (0.654) | 0.22 s | 0.34 km | −0.52 (0.69) |
| Isken | 6 | 6/6 | (minute times) | 0.32 km | −1.94 (0.34) |
| ComCat | 11 | 9/11 | 0.26 s | 0.76 km | +0.09 (0.31) |

  Signed dt vs Cochran +0.07 s: the extracted Keranen model with step
  layers needs no origin-time correction. Isken's depths are ~2 km deeper
  than ours and Cochran's alike (gradient half-space model there).
- 09: ML vs Isken Mw +0.02 (n 6); vs McMahon +0.96 (n 199, magnitude type
  unresolved — not a calibration target). Numerical check 0.4 %. 10: checks
  passed with no mainshock row.

Reading: locations are already at the reference level in r1; recall vs the
template-enhanced Cochran catalog (0.62) is the gap, as in Magna/Maple r1.

### r2 — knob: NLL station delays (`nonlinloc.yaml station_delays.iterations: 2`)

01–03 hardlinked from r1; 04–10 rerun.

| | r1 | r2 |
|---|---|---|
| NLL median RMS | 0.200 s | 0.195 s |
| Cochran matched / epicentral | 0.619 / 0.48 km | 0.619 / 0.48 km |
| dZ vs Cochran (MAD) | −0.04 (0.59) | −0.05 (0.60) |
| signed dt vs Cochran | +0.074 s | +0.071 s |
| top-bound events | 140 | 153 |

Neutral. Delays converge (increments ≤ 0.29 → 0.07 s; 31 station-phases
from ~2,370 events) to |delay| ≤ 0.05 s everywhere except the distant OK.FNO
(P +0.10, S +0.35 s). The Keranen model was inverted from this sequence's
own arrivals, so there is no Maple-style Vp/Vs residual to absorb. Kept
(harmless; same stage settings as Maple). 10: checks passed.

Next: r3 stage 60 Match&Locate (Cochran is template-enhanced; recall 0.62 is
the gap).

### r3 (2026-10-23) — stage 60 Match&Locate

`01_pipeline/60_match_locate.py` + `00_config/match_locate.yaml`, copied from
Maple; scoring reads the references through stage 05's readers and mask
(Cochran, McMahon, ComCat at 4 s / 15 km; Isken not scored — minute times).
Templates from r2 v1 (≥ 10 stations, σz ≤ 2 km; 1,144 candidates), 0.5 km
cover; 12 three-component sites within 20 km → Magna row/channel minimum 12.
`04_comparison/08_null_run.py` copied for the threshold check.

- Pilot (11-13, 20 templates, 35 % cover; prepare 5 min — 250 → 50 Hz is an
  integer decimation, unlike Maple's off-grid segments):

| | source r2 | r2 ∪ M&L @ N×MAD 9 | @ 8 |
|---|---|---|---|
| events | 306 | 563 | 916 |
| Cochran recall | 0.589 | **0.807** | 0.893 |
| McMahon recall | 0.709 | **0.882** | 0.927 |

- Full: 319 templates (316 kept, 7,811 rows), 2,528 jobs, run 2.3 h (prepare
  6 min). Sweep (union with r2): N×MAD 8 → 27,212 events; 9 → 8,174 (Cochran
  0.980, McMahon 0.984); 9.5 → 7,121 (0.975 / 0.978); 10 → 6,581.
- Null run (11-11 + 11-14, 6 s): false fraction 75 % at 8, 27 % at 8.5,
  **4.9 % at 9** (Magna/Maple 1–2 %), **0.7 % at 9.5**, 0.2 % at 10. More
  rows per template (~25) widen the N×MAD distribution here. Final
  threshold **N×MAD 9.5** / 6 s.

r3 catalog (`--stage export --catalog-round r3` → `export/r3/60_catalog/
catalog_events.csv`): 7,156 events (2,860 r2 NLL + 4,296 M&L), 6,833 in the
box; magnitudes chained from 59 ML templates to all 316 (median M −0.27).

| | r2 | M&L | **r3 union** |
|---|---|---|---|
| events in box | 2,551 | 6,879 | **6,833** |
| Cochran recall | 0.614 | 0.964 | **0.952** |
| McMahon recall | 0.709 | 0.966 | **0.951** |
| ComCat | 10/11 | 10/11 | 10/11 |

Location/magnitude vs Cochran by row source — M&L rows are as good as the
picked ones (dense, well-located templates; contrast Maple r6):

| source | pairs | epicentral | \|dt\| | dZ (MAD) | dM (MAD) |
|---|---|---|---|---|---|
| r2 NLL | 1,309 | 0.49 km | 0.10 s | −0.05 (0.61) | −0.22 (0.23) |
| M&L | 716 | 0.50 km | 0.11 s | −0.05 (0.67) | −0.24 (0.23) |

The union scoring ~1 point below M&L alone is a box-scoring artifact,
not lost events (checked 2026-10-24): 75 in-box M&L detections deduplicate
onto the same event's r2 NLL row (kept by design) that lies just outside
the comparison box, so stage 60's boxed score drops them while the catalog
keeps them; the evaluation layer scores complete catalogs (Cochran 0.967 >
M&L-alone 0.964). Tighter dedupe gates gain little and start duplicating:
1 s / 2 km → Cochran 0.9557 (2 s / 5 km: 0.9524), near-duplicates 9 → 9;
0.5 s / 2 km → 0.9581, duplicates 65; 0.5 s / 1 km → 0.9605, 396. Kept
2 s / 5 km; no new round.

## Benchmark layer (2026-10-23)

Task package ported from the Maple package: `input.json`,
`task_{min,tools,guided}.json`, `prompt_{min,tools,guided}.md` (case name,
window 2011-11-11 → 11-19, example station GS.OK021), output contracts,
`run.sh` (`*-prague-<variant>`), README, VARIANTS. Evaluation scripts from
the Magna version (all references located): Cochran/McMahon/Isken/ComCat
readers, per-reference gates (Isken 60 s / 5 km), expert depths converted to
below-surface (0.28 km), figures centred on the Mw 5.7 from the expert
config (no anchor file; no mainshock marker — outside the window). Style
module copied to `data/2011_prague_oklahoma/scripts/figures/figure_style.py`.
Cross-run figures generated for r3; per-run script smoke-tested.

2026-10-24: evaluation scripts now read and mask the references through the
expert stage-05 module (no second copy of the readers); the script is shared
with Kīlauea/Kaikōura apart from its settings block, and `evaluate_run.py` is
case-independent. Outputs unchanged (Cochran 96.7 %, McMahon 97.4 %, Isken
6/6 at 0.32 km); the depth-section axis now points NE (was SW).

## r4 (2026-10-26) — location quality (cross-case review after Ridgecrest)

Off-fault share (> 1 km from every Cochran/McMahon event): r3 1.5 %
(McMahon itself 0.8 %). Off-fault NLL rows: RMS 0.47 vs 0.19 s, gap 130°
vs 77°; off-fault M&L rows: 93 % from 5 off-fault templates. Candidate rules
(complete-catalog evaluation): v1 + RMS ≤ 1.5× median → 0 % but Cochran
0.967 → 0.909; templates only → 0.7 %, 0.925; **≥ 1 waveform CC link (events
and templates) → 1.0 %, Cochran 0.964, McMahon 0.968** (adopted); adding the
Ridgecrest gap/σx limits did not help (1.7 %). CC links: `60_match_locate.py
--stage cclinks` (ccdt; 2,136 of 2,860 source events linked). r4 = export
with `location_quality`: 6,964 events, 724 picked events in
`low_quality_events.csv`; epicentral vs Cochran 0.49 → 0.47 km, McMahon
0.34 → 0.31 km. Evaluation layer = r4.

## Method comparison (stage 70, 2026-10-27)

The seismotools library gained association (PyOcto, REAL), absolute
location (NonLinLoc method switch + catalog locator `locate.py`,
HypoInverse) and relative relocation (GrowClust) methods, each validated
first (`seismotools/support/tools_usage_validation/`). Stage 70
(`04_comparison/70_method_comparison.py`, `00_config/method_comparison.yaml`,
figure `71_plot_method_comparison.py`) runs them on identical inputs: r2
PhaseNet picks, r2 stations, Keranen model as step layers, 0.28-km datum, no
station delays (r2 stage 04 used two delay passes). GaMMA = the r2 stage-03
association; PyOcto and REAL use GaMMA's minima (10 picks, 4 P, 3 S).
HypoInverse needs `lvz_policy: clip` (the Keranen model has two small
inversions). Scored like the evaluation layer (masked references, 4 s /
15 km). The GaMMA + NLL-GAU arm reproduces the r2 expert catalog (Cochran
0.630 vs 0.630, 0.483 vs 0.486 km), so the frame is sound.

| association (events) | locator | Cochran | McMahon | epi median / p90 (km) | dZ median (MAD) | \|dt\| (s) |
|---|---|---|---|---|---|---|
| GaMMA (2,860) | NLL GAU_ANALYTIC | 0.630 | 0.734 | 0.48 / 1.33 | −0.05 (0.59) | 0.11 |
| | NLL EDT | 0.630 | 0.734 | **0.37 / 0.84** | +0.10 (**0.41**) | **0.07** |
| | NLL EDT_OT_WT | 0.630 | 0.734 | 0.37 / 0.86 | +0.10 (0.42) | 0.07 |
| | HypoInverse | 0.630 | 0.734 | 0.45 / 2.10 | −0.06 (0.65) | 0.25 |
| PyOcto (3,058) | NLL GAU / EDT | 0.642 / 0.644 | 0.750 / 0.753 | 0.60 / 1.75; 0.39 / 0.88 | | |
| | HypoInverse | 0.641 | 0.748 | 0.50 / 2.73 | | |
| REAL (2,641) | NLL GAU / EDT | 0.612 / 0.612 | 0.713 | 0.43 / 1.06; 0.38 / 0.85 | | |
| | HypoInverse | 0.611 | 0.713 | 0.41 / 1.62 | | |
| GaMMA + NLL-GAU, model ×0.95 / ×1.05 | | 0.630 | 0.734 | 0.47 / 0.53 | +0.39 / −0.76 | |
| ccdt + GrowClust (2,047 of 2,859 relocated) | | (subset) | | 0.38 / 0.82 | −0.22 (**0.30**) | |

Findings:
- **Recall is set by the association, not the locator** (the 15-km gate):
  PyOcto +1.2 points over GaMMA (Cochran), REAL −1.8; REAL is the most
  conservative (precision proxy 0.81 vs 0.80/0.79).
- **NLL EDT beats GAU_ANALYTIC** for every association: median epicentral
  offset −0.1 km, p90 1.33 → 0.84 km, depth MAD 0.59 → 0.41 km, origin
  |dt| 0.11 → 0.07 s. The expert stage 04 uses GAU_ANALYTIC; switching
  is a candidate round for all cases (EDT is robust to outlier picks —
  validate_nonlinloc: one 2-s outlier moved GAU 2.3 km in depth).
- HypoInverse with the NCSN weighting defaults has a heavy tail (p90
  2.1–2.7 km) and origins 0.16–0.25 s late; its distance weighting is tuned
  for dense California networks, not this geometry.
- ±5 % velocity moves depths systematically (+0.4 / −0.8 km) but barely the
  epicentres.
- GrowClust (`ngoodmin 4`) gives the tightest depths (MAD 0.30 km) on the
  72 % of events it links.

Cross-method spread as an internal quality indicator (GaMMA association,
1,310 events matched to Cochran, 3.8 % with errors > 2 km): the locator
spread (largest epicentre distance from the median of the four locators)
correlates with the error (Spearman 0.59; top 5 % → 6.4× the large-error
rate), unlike the NLL posterior σh (0.10). RMS is as strong (0.64) and
correlated with the spread (0.76): beyond RMS the spread keeps a partial
correlation of 0.20; flagging the top 10 % by either catches 33 of 50 large
errors (spread 26, RMS 24). The ±5 % model spread is not informative (0.10)
— a model change shifts all events alike. Not yet tested across
associations (pick-set linking).

## r5 (2026-10-27) — NonLinLoc LOCMETH EDT_OT_WT

Stage 70 found NLL EDT better than GAU_ANALYTIC for every association.
Knob: `nonlinloc.yaml location_method: EDT_OT_WT` (stage 04 now reads it;
the arrival-weight assertion applies to GAU only, since EDT zero-weights
outlier arrivals — 3 of 2,860 events have one). r5 = r2 stages 01–03
(hardlinked) + stage 04 rerun with its two station-delay passes + stage 05;
stages 09/10 not rerun (magnitudes and v1 flags carried). New stage
`01_pipeline/64_locator_frame.py` moves the r4 catalog into the r5 frame:
2,136 picked events take their EDT solution, 4,828 Match&Locate events move
with their template's r2 → r5 displacement (median 0.27 km, p90 1.08 km;
depth +0.03 km, origin −0.007 s). Membership and magnitudes are r4's.

| final catalog | Cochran R | epi median / p90 | dZ (MAD) | McMahon R | epi median / p90 | > 1 km from Cochran ∪ McMahon (box) |
|---|---|---|---|---|---|---|
| r4 | 0.964 | 0.465 / 1.200 | −0.03 (0.57) | 0.968 | 0.312 / 1.026 | 0.98 % |
| **r5** | 0.965 | **0.365 / 0.840** | +0.12 (**0.40**) | 0.967 | **0.213 / 0.504** | **0.04 %** |

M&L rows improve as much as picked rows (vs Cochran 0.487 → 0.383 km,
picked 0.446 → 0.356). **Adopted**; evaluation layer = r5.
