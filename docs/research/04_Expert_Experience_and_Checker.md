# Expert experience, parameter sensitivity and the self-improving checker

Status: working summary, 2026-10-28. Numbers are metrics v1 (frozen,
`docs/framework/03_EVALUATION_METRICS.md`) unless a source is named.

## 1. Thesis

An expert-quality earthquake catalog is not the output of a fixed tool chain.
It comes from a loop of *run → diagnose → repair upstream → rerun*, and the
knowledge that drives the loop is experience:

1. **parameter and method strategies** — which choices matter at each stage
   and which ranges are safe;
2. **diagnosis** — when a stage's result looks wrong, which upstream choice
   most likely caused it;
3. **repair** — what to change upstream, and how to confirm the change helped
   without the hidden references.

This experience can be written down as a reference-free **checker**: a set of
internal diagnostics with a symptom → cause → repair playbook, which an
Agent could call to improve its own catalog.

The benchmark's central question follows: **does a general-purpose Agent,
given no such checker, produce a catalog usable for scientific discovery —
and how much of the gap to the expert does the checker close?**

## 2. How much the choices matter

### 2.1 Within the range an expert would consider: modest for detection, large for location and magnitude

Expert ladder (`evaluation/human_in_loop/expert_ladder.json`; each row one adopted round,
one change):

| Stage | Change (case) | Effect |
|---|---|---|
| association | GaMMA DBSCAN window 10 → 15 s (Kaikōura) | recall_norm 0.81 → 0.88; F1 M2+ 0.85 → 0.94; shift 2.38 → 1.14 km |
| picking | PhaseNet threshold 0.3 → 0.2 (Magna) | recall_norm 0.74 → 0.79 |
| picking | vertical-only sites handled (Maple, r3–r4) | recall_norm 1.09 → 1.12 |
| association | method GaMMA / PyOcto / REAL (Prague stage 70) | recall ±1–2 points |
| location | station delays (Kaikōura; Maple) | scatter 2.94 → 2.35 km; 0.83 → 0.69 km, shift 0.86 → 0.46 km |
| location | NLL GAU → EDT (Prague; Kīlauea) | scatter 0.41 → 0.31 km, p90 1.33 → 0.84 km; 0.76 → 0.67 km |
| location | double difference with Match&Locate (Ridgecrest; Magna) | scatter 0.82 → 0.42 km; 0.91 → 0.47 km |
| location | published layered frame (Ridgecrest) | scatter 0.39 → 0.22 km, shift 0.46 → 0.37 km |
| magnitude | ML distance recalibration, station corrections (Magna) | dmag spread 0.21 → 0.13, slope −0.24 → −0.05 |
| magnitude | direct ML for large events (Maple; Magna) | M4+ offset −0.90 → −0.21; M5.7 4.72 → 5.46 |

Detection parameters move the normalised recall by ≤ 0.07; a change of
*method* — template matching — moves it by 0.2–0.6 in every case (Prague
1.17 → 1.81, Magna 0.79 → 1.16, Kīlauea 0.93 → 1.15, Kaikōura 0.88 → 1.17,
Ridgecrest 1.20 → 1.40). Location and magnitude choices change precision by
20–50 %.

### 2.2 Outside that range: an order of magnitude larger

| Wrong choice | Effect | Source |
|---|---|---|
| Agent's own velocity model / locator (Ridgecrest tools, min) | depth +8 to +9 km, origin time −0.6 / +0.5 s; relocating the same picks with the expert locator gives −1.0 / −1.5 km | component swap, `runs_pilot/*/evaluation/swap/` (pilot runs, pre-2026-10-28 prompts) |
| Agent fixes depth at 10 km (Magna min) | 42 % of events at one depth; 2 % after expert relocation | swap |
| Agent magnitude scale (Ridgecrest min, Magna min) | −0.99 and +0.57 offsets, b 0.38 vs 0.60 | metrics v1 strength |
| Grid bound at the surface (Ridgecrest blind) | 16 % of events at the grid top; the mainshocks among them | ladder, stage 66 |
| Velocity interface (Prague) | 9–12 % of events at 2.00 km, the 2.25-km Keranen interface | depth profile |
| Linear ramp between layer tops (Maple, Magna) | origins +0.47 s late against the published layered model | Maple r2, Magna r9 |
| Step layering without re-tuning the basin layer (Magna r9) | every location statistic worse (dZ −0.08 → −0.74 km) | Magna PLAN r9, rejected |
| EDT where the model was calibrated under GAU (Magna) | epicentres +0.4 km | stage-04 EDT test |
| One mislocated template (Kīlauea r5) | its 160 detections ~6 km off | Kīlauea PLAN r5, rejected |
| Template-derived arrivals in dt.ct (Ridgecrest) | DD collapses detections onto templates (fake 0.05 km thickness) | Ridgecrest PLAN stage 62 |
| Bulk QC rule applied to large events (Ridgecrest) | M7.1, M6.4, M5.4 lost from every later round | stage 66 |
| Chained relative magnitudes (all cases) | large events compressed (direct − chain +0.36 at M2–3, +0.74 for M5.7); spread doubles at Kīlauea | stage 65 |
| Coda of large events in Match&Locate (Ridgecrest) | 629 ghost detections, inflated M2–3 | stage 67 review |

Choices also **interact**: the Magna basin layer was tuned under a linear
ramp, so the physically more faithful step layering made results worse
until re-tuned; EDT helped five cases and hurt Magna for the same reason.

### 2.3 Where Agent errors actually sit (component swap)

Relocating an Agent's own picks and associations with the expert's model and
locator (no station delays):

| Run | Agent's own locations | Expert locator, Agent's picks | Expert blind |
|---|---|---|---|
| Ridgecrest tools | scatter 1.04 km, dZ +8.1 km, off-structure 14 % | 0.80 km, −1.0 km, 8 % | 0.82 km, −1.2 km, 8 % |
| Ridgecrest min | 3.27 km, +9.1 km, 44 % | 1.75 km, −1.5 km, 33 % | 0.82 km, −1.2 km, 8 % |
| Magna min | 1.03 km, fixed depth 42 %, off 4 % | 1.00 km, 2 %, 0.4 % | 0.83 km, 2 %, 0.4 % |

With tools, the Agent's front end (picking, association) reaches the expert
blind level; its large errors are back-end *choices*. Without tools, both
ends fail. These are exactly the errors a checker can see without references
(depth pile-ups, origin-time–depth coupling, fixed depths, magnitude-scale
sanity).

### 2.4 Summary

- Within an expert's working range, parameters change detection little and
  precision moderately; the big detection gain needs a different method.
- Outside it, single choices produce errors 5–10× the expert's (depth, frame,
  magnitude scale) and are invisible in a recall number.
- The expert reached the final catalog by detecting such failures in
  intermediate results and repairing upstream; several of those repairs were
  only found because the evaluation looked at the right diagnostic (depth
  profile, magnitude by class, event lists of large events).

## 3. The checker: stage diagnostics, likely causes, upstream repairs

Every check below uses only the Agent's own data and products (no reference
catalog). "Evidence" names where the rule was learned.

| Stage | Reference-free check | Symptom | Most likely cause | Upstream repair | Evidence |
|---|---|---|---|---|---|
| inventory | channel families, sample rates, vertical-only sites, clipping | stations without horizontals; plateaus | sensor type, saturation | P-only handling or Z copy; exclude clipped traces | Maple r3–r4; stage 65 |
| picking | picks per station vs distance; P/S ratio; pick − onset offset on large events | near stations missing; late picks on mainshocks | threshold; probability-peak vs onset | lower threshold; onset-based times for large events | Magna r5; Ridgecrest mainshock audit |
| association | events per hour vs pick rate; duplicate origins within seconds; picks per event | split or merged events | time window (DBSCAN eps), region bounds | widen window; restrict bounds to the source region | Kaikōura r3; Kīlauea r2 |
| location | **depth profile**: share at one value / at the grid bounds / at a model interface | pile-ups (fixed depth, grid top, 2.00 km) | grid bounds, model interface, depth not resolved | widen the grid; depth prior or flag; never fix depth silently | Prague, Ridgecrest blind, Magna r8, Agent runs |
| location | **origin time vs depth** coupling; residual mean per station | origins early with deep events; station residual bias | velocity model too fast/slow; datum; missing station terms | change model or representation (step vs linear); station delays | Ridgecrest tools (swap); Maple r2/r5 |
| location | **locator spread** (GAU, EDT, HypoInverse on the same picks) | events whose solutions disagree | outlier picks, poor geometry | EDT; flag high-spread events | Prague stage 70 (ρ 0.59 with error) |
| location | gap, σx, RMS, CC links to neighbours | isolated off-trend events | weak geometry, wrong association | location-quality rule — but exempt large events | Ridgecrest r08, stage 66 |
| relative relocation | thickness of DD clusters; source of dt | implausibly thin clusters | template-derived arrivals in dt.ct | picks-only dt.ct plus CC | Ridgecrest stage 62 |
| detection beyond picking | null run (shifted data) false rate; detections per template; CC near larger events | false rate > 1–2 %; template families offset; ghosts in coda | threshold, mislocated template, coda | raise N×MAD; quality-filter templates; remove low-CC detections near larger events | Magna/Prague null runs; Kīlauea r5; stage 67 |
| magnitude | direct ML on a subset vs chained ML; slope vs magnitude; b-value and Mc plausibility | large events compressed; b far from ~1 | relative chains, clipping, calibration | direct ML for large events; distance and station terms; flag saturation | stage 65; Magna r2–r3 |
| QC / completeness | largest events present; per-period counts | mainshocks or aftershock bursts missing | bulk rule deleting large events | restore depth-bound large events, keep flags | stage 66 |

Checks that did **not** work and should not be in a checker: an RMS onset
test for coda ghosts (39 % of real M2–3 detections fail it in dense coda);
RMS-based location rules (too blunt; high-RMS templates still detect well).

## 4. Implications for the evaluation design

1. The checker must be reference-free and case-agnostic (rules and ranges,
   no case-specific numbers), and its use logged, so a checker arm does not
   become a leakage channel.
2. The checker was learned on these six cases. Report checker-arm results
   separately for the cases a rule came from and the others, or hold out
   cases when writing it, so the gain is not circular.
3. Some expert gains are reference-informed (Ridgecrest layered frame from
   Shelly's model; Magna ML recalibration against UUSS); the expert blind row
   and the ladder separate them from what an Agent could have known.
4. Every run gets the component swap: front-end versus back-end attribution
   is the most direct test of what a checker would have fixed.

## 5. Agent evaluation stages

Each stage differs from the previous one by exactly one factor, so its gain
is attributable. The expert blind and expert final rows are the yardsticks.

| Stage | The Agent additionally gets | Question it answers |
|---|---|---|
| S0 `min` | task, data, output contract | Can a general Agent build a usable catalog on its own? |
| S1 `tools` | the validated tool library (`seismotools`) with usage docs | Is the gap tool access/execution, or scientific judgement? |
| S2 `tools + checker` | a checker skill that runs the §3 diagnostics on its own products and reports symptoms, without causes or fixes | Once told *that* something is wrong, does the Agent find and repair the cause? |
| S3 `tools + checker + playbook` | the §3 symptom → cause → repair knowledge | Does encoded expert experience let the Agent close the gap (self-improving loop)? |

`guided` (generic workflow scaffolding, fixed window, report contract)
varies a different axis — how prescriptive the task statement is — and
changes the window and contract; it is not on this ladder and is optional.

Minimal run plan: S0, S1 and S3 on all six cases (18 runs); S2 on three
cases chosen from the S1 failure modes (3 runs), because S2 versus S3 is the
cleanest test of "diagnosis versus repair knowledge"; repeats only where the
spread between two runs exceeds half the stage effect. Every run is scored
with metrics v1 and gets the component swap.

