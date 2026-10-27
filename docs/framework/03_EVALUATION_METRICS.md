# Evaluation metrics (v1, pre-registered)

This document fixes how every Agent catalog is scored. It is frozen before the
formal Agent runs (2026-10-27). A change to any definition, gate, mask or
reference role below creates a new version; every run is then re-scored with
that version, and each score file records the version it used
(`metrics_version: 1`).

Two principles follow from the expert work on the six cases:

- **Reference catalogs are not ground truth.** They do not recover each other
  fully (reference-to-reference recall 0.53–0.70 under the gates below), and
  their absolute locations differ by the velocity-model frame (up to ~3.5 km
  at Kaikōura). Every metric is therefore reported against several references,
  each used only for the roles it supports, and next to two yardsticks: the
  reference-to-reference value and the expert value.
- **No composite score.** The output is a capability profile per case and
  configuration; the headline metrics are listed in §7.

## 1. Scored population

- **Rows.** All rows of the Agent's `catalog.csv` except those with
  `status = rejected` (case-insensitive). A sensitivity variant scores only
  `status = accepted`. Rows without latitude, longitude or origin time count
  toward the event total but never enter correspondence.
- **Mask.** Each case's cohort mask in `expert/00_config/validation.yaml`
  (half-open time window, region box, depth bounds) is applied identically to
  references, expert and Agent. Agent rows outside the mask are reported as
  `out_of_mask_fraction` and are not scored further. Rows without a depth are
  kept in the mask test on time and epicentre alone.
- **Depth datum.** `depth_km` is kilometres below sea level, positive down,
  for every variant (§8). Reference depths are converted to the same datum
  where the datum is known; where it is not, the reference has no depth role.

## 2. Event correspondence

- **Matcher.** Greedy one-to-one pairing of candidate events with reference
  events, ranked by epicentral distance, then |Δt|.
- **Primary gates:** |Δt| ≤ 4 s and epicentral distance ≤ 15 km — the gates
  of the expert stage-05 matcher in every case.
- **Sensitivity gates:** 2 s / 5 km and 1 s / 3 km, reported for every
  detection and location metric.
- **Reference-specific gates.** A reference whose origin times are coarse
  keeps its own gates (Isken & Mooney 2017: 60 s / 5 km).
- **Time-only references** (Maple Creek, Shelly & Hardebeck 2019): pairing on
  |Δt| ≤ 1 s alone. The same matcher run against the reference shifted by
  60 s counts chance coincidences; `recall_net = (matched − chance) / N_ref`
  is the reported recall.

## 3. Reference roles

Roles: **D** detection (recall, union support), **L** absolute location,
**S** relative structure, **M** magnitude, **P** phase picks. The primary
detection and location references (bold) feed the headline metrics.

| Case | Reference | Roles | Notes |
|---|---|---|---|
| Ridgecrest 2019 | **Shelly 2020** | D L S M | template matching; primary |
| | Ross 2019 (QTM relocated subset) | D L S | |
| | Liu 2020 | D L S | ML picker + GaMMA, relocated |
| | AWR 2025 v2 | D | long-term GaMMA |
| | ComCat (SCSN) | D L M | operational |
| Magna 2020 | **Pang 2020** | D L S M | relocated; primary |
| | Baker & Whidden 2021 | D P | picks collapsed to events; depth datum unknown → no L depth |
| | ComCat (UUSS) | D L M | operational |
| Prague 2011 | **Cochran 2020** | D L S M | template-enhanced relocated; primary |
| | McMahon 2017 | D S | subspace detections, Bayesloc |
| | Isken & Mooney 2017 | L | 6 M > 3 manual relocations; 60 s / 5 km gates |
| | ComCat | M | 11 events; auxiliary |
| Maple Creek 2017 | **ComCat (UUSS)** | D L S M | only located reference; primary |
| | **Shelly & Hardebeck 2019** | D P | time-only detections; primary for detection (`recall_net`) |
| Kīlauea 2018 | **Shelly & Thelen 2019** | D L M | hypocentroids; primary |
| | Wei 2022 | D L M | 3-D NonLinLoc (frame differs from 1-D) |
| | Matoza 2021 | D S M | GrowClust |
| | ComCat (HVO) | D L M | operational |
| Kaikōura 2016 | **Tan 2024** | D M | detection primary |
| | **Lanza 2019** | L | 122 HypoDD origins; location primary |
| | Chamberlain 2021 | D S M | corrected GrowClust (3-D frame) |
| | GeoNet | D M | operational; fixed-depth solutions → no L |

A reference's depth enters L only when its datum is known (sea level or
stated surface datum convertible with the case's model datum).

## 4. Yardsticks

- **Reference ceiling** for a detection reference R:
  `ceiling(R) = max over other D references S of matched(S, R) / N_R`,
  computed with the same matcher, mask and gates. It is the recall that an
  independent high-quality catalog actually reaches; values above it are
  possible (the expert exceeds it in all five scoreable cases) and are not
  capped.
- **Expert rows.** Two expert catalogs are scored with the same code:
  - *expert (final)* — the final round of each case. It was tuned with the
    hidden references in view and is reported as a **reference-informed upper
    control**, not as a blind result;
  - *expert (blind)* — the located-event catalog of the first round
    (Ridgecrest `01_baseline`, other cases `r1` stage 04), configured from the
    ported pipeline and published velocity models before any comparison with
    the case's references.
- **Method-variance floor** for location: the spread between locators on the
  same associations (Prague stage 70: median 0.37 km, the largest epicentre
  distance from the median of four locators; `expert/PLAN.md` "Method
  comparison"). Agent–reference location differences
  below the larger of this floor and the reference-to-reference offset are
  read as equivalent.

## 5. Metrics

### L0 — Completion and validity

| Metric | Definition |
|---|---|
| `completed` | the run ended with contract-valid `catalog.csv` and `picks.csv` (required columns present) |
| `consistency` | fraction of checks passed: every non-empty pick `event_id` exists in the catalog; `n_picks`, `n_p_picks`, `n_s_picks` equal the linked pick counts; timestamps parse; coordinates in range |
| `out_of_mask_fraction` | §1 |
| `completion_rate` | completed runs / launched runs for a configuration |

### L1 — Detection

| Metric | Definition |
|---|---|
| `recall[R]` | matched / N_R, for every D reference |
| **`recall_norm[R]`** | `recall[R] / ceiling(R)` — headline for the primary detection reference |
| `recall_by_mag[R]` | recall in 0.5-unit bins of the reference magnitude |
| `M90[R]` | lowest reference magnitude M (taken from the reference's own magnitudes, to 0.1) such that recall of reference events with magnitude ≥ M is ≥ 0.9, over at least 10 events (calibration-free completeness proxy; undefined if never reached) |
| `event_ratio` | scored Agent events / N of the primary detection reference |
| **`union_support`** | fraction of scored Agent events matched (primary gates) to at least one event of U = all located D references ∪ expert (final) — headline precision proxy. Time-only references are not members (their chance coincidences cannot be removed per event); for expert and reference rows U excludes the row itself and the expert |
| `audited_false_rate` | see below |

**Audit of unsupported events.** From each scored run, draw a stratified
random sample of the events without support in U (50, or all if fewer;
strata by Agent `n_picks` tercile), with a fixed seed recorded in the score
file. Each sampled event is reviewed blind to its source on waveform plots
(three-component, nearest six stations, ±10 s) and labelled *earthquake*,
*not an earthquake* or *undecidable*. The estimated false-event rate is
`(1 − union_support) × p_false` with a Wilson 95 % interval on `p_false`.
Reviews are stored next to the run evaluation and reused across metric
versions.

### L2 — Absolute location (L references, matched pairs)

| Metric | Definition |
|---|---|
| **`epi_median[R]`**, `epi_p90[R]` | epicentral distance of matched pairs — `epi_median` vs the primary location reference is a headline |
| `dz_median[R]`, `dz_mad[R]` | Agent − reference depth (sea-level datum), median and median absolute deviation; only for references with a known datum |
| `dt_median[R]` | median |Δ origin time| |

### L3 — Relative location and structure (S references)

| Metric | Definition |
|---|---|
| `pair_distance_error[R]` | for each matched event, its 10 nearest matched neighbours in the reference within 5 km; median of |d_Agent − d_ref| over these pairs (3-D distances). Insensitive to a common frame shift |
| `off_structure_fraction` | fraction of located scored Agent events whose epicentre is farther than r_off from every epicentre of the case's S references (epicentral, so depth errors — scored by L2 — and unknown datums do not enter); r_off = 1 km (Kaikōura 5 km). The same value for each reference (against the other S references) and the expert is reported alongside |
| `local_thickness` | median over events of the minor-axis standard deviation of the 20 nearest neighbours; reported with the reference value of the same region |

### L4 — Magnitude (M references, matched pairs with magnitudes)

| Metric | Definition |
|---|---|
| `mag_coverage` | fraction of scored Agent events with a magnitude |
| `dmag_median[R]`, `dmag_mad[R]` | Agent − reference magnitude, by Agent `magnitude_type` |

A constant offset reflects calibration (the expert itself runs 0.22 below
Cochran); the MAD is the quality measure.

### L5 — Phase picks (P references; Magna, Maple Creek)

Scored with `SeismoAgentBench/scoring/picks.py`: P and S recall and precision
at 0.1 s and 0.5 s tolerance, median and MAD of the time residual, for picks
on stations common to both sets.

### L6 — Process and cost

From the run record: wall time, cost (USD), input/output/cached tokens,
turns, tool calls over 300 s, compactions. **Leakage flags:** every URL and
file path accessed outside the run directory is listed from the transcript;
an access matching the case's withheld products (reference DOIs, data
repositories and catalogue services in `data/<case>/data/catalogs/*/README.md`)
sets `leakage_flag`. A flagged run is reported but excluded from headline
means.

### L7 — Reliability self-assessment (optional columns)

Computed only when the Agent fills `horizontal_uncertainty_km` (and
`depth_uncertainty_km`), against the primary location reference:

| Metric | Definition |
|---|---|
| `uncertainty_coverage` | fraction of matched events with epicentral error ≤ the reported value (compare with 0.68 for a 1σ quantity, stated by the Agent) |
| `uncertainty_rank_corr` | Spearman ρ between reported uncertainty and epicentral error |

The missing columns do not change any other score.

## 6. Repeats and failed runs

- Each configuration (case × variant × harness × model) runs at least twice,
  target three times. Means are reported with the min–max range.
- **Detection metrics** (`recall`, `recall_norm`, `M90` as "not reached")
  count a failed run (no contract-valid catalog) as zero and are averaged
  over all launched runs.
- **Location, structure, magnitude and pick metrics** are averaged over
  completed runs only and are always shown together with `completion_rate`.

## 7. Headline table

Per case and configuration:

1. `completion_rate`;
2. `recall_norm` vs the primary detection reference (raw `recall` in brackets);
3. `union_support` and `audited_false_rate`;
4. `epi_median` vs the primary location reference;
5. `off_structure_fraction`;
6. cost and wall time.

Rows: each Agent configuration, *expert (blind)*, *expert (final)*, and each
reference scored against the primary reference (the ceiling rows).

## 8. Output conventions fixed for scoring

These are format conventions, not scientific guidance, and are stated in
every variant's prompt (`min`, `tools`, `guided`):

- `depth_km` is kilometres below sea level, positive down.
- `status` is `accepted`, `uncertain` or `rejected`; rejected rows stay in
  the files and are not scored.
- `catalog.csv` may carry, after the required columns, the optional columns
  `horizontal_uncertainty_km`, `depth_uncertainty_km` and
  `origin_time_uncertainty_s` (1σ). Empty values are allowed.

Runs launched before these conventions (Ridgecrest and Magna, 2026-10-13 to
2026-10-22) are scored with depth metrics omitted unless their report states
the datum.

## 9. Implementation

The scorer is shared code in `SeismoAgentBench/scoring/`; each case provides
only its configuration (reference readers, roles, mask, gates, expert
catalogs). Every score file records `metrics_version`, the scorer's git
commit, the gates, the reference counts after masking and the audit seed.
