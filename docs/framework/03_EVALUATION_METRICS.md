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
detection and location references (bold) feed the headline metrics. The
primary detection reference must have an informative ceiling, i.e. another
independent catalog of comparable completeness; where the largest catalog
has none (Kaikōura: Tan; Maple Creek: Shelly) its raw recall is reported
alongside the normalised headline.

| Case | Reference | Roles | Notes |
|---|---|---|---|
| Ridgecrest 2019 | **Shelly 2020** | D L S M | template matching; primary |
| | Ross 2019 (QTM relocated subset) | D L S | |
| | Liu 2020 | D L S | ML picker + GaMMA, relocated |
| | AWR 2025 v2 | D | long-term GaMMA |
| | ComCat (SCSN) | D L M | operational |
| Magna 2020 | **Pang 2020** | D L S M | relocated; primary |
| | Baker & Whidden 2021 | D S P | picks collapsed to events; depth datum unknown → no L depth |
| | ComCat (UUSS) | D L M | operational |
| Prague 2011 | **Cochran 2020** | D L S M | template-enhanced relocated; primary |
| | McMahon 2017 | D S | subspace detections, Bayesloc |
| | Isken & Mooney 2017 | L | 6 M > 3 manual relocations; 60 s / 5 km gates |
| | ComCat | M | 11 events; auxiliary |
| Maple Creek 2017 | **ComCat (UUSS)** | D L S M | only located reference; detection and location primary, ceiling from Shelly |
| | Shelly & Hardebeck 2019 | D P | time-only detections (`recall_net` reported; no ceiling) |
| Kīlauea 2018 | **Shelly & Thelen 2019** | D L S M | hypocentroids; primary |
| | Wei 2022 | D L S M | 3-D NonLinLoc (frame differs from 1-D) |
| | Matoza 2021 | D S M | GrowClust |
| | ComCat (HVO) | D L M | operational |
| Kaikōura 2016 | Tan 2024 | D S M | largest detection catalog (raw recall reported) |
| | **Lanza 2019** | L S | 122 HypoDD origins; location primary |
| | **Chamberlain 2021** | D S M | corrected GrowClust (3-D frame); detection primary, ceiling from Tan |
| | GeoNet | D M | operational; fixed-depth solutions → no L |

**Magnitude authority.** Magnitude classes and the strength dimension use
one catalog per case, the operational network catalog with calibrated
ML/Mw that is complete above M 2–3: Ridgecrest ComCat (SCSN), Magna UUSS,
Kīlauea ComCat (HVO), Kaikōura GeoNet, Maple Creek ComCat (UUSS). Prague's
2011 ComCat holds 11 events in the window, so Cochran sets its classes.
Research catalogs use differing magnitude scales (Magna M2+: Pang 375,
UUSS 140 events) and are not used for classes.

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
| **`union_support`** | fraction of scored Agent events matched (primary gates) to at least one event of U = all D references ∪ expert (final) — headline precision proxy. Time-only members match on \|Δt\| ≤ 1 s; the events that only the 60-s shifted time-only reference would support (among those no located member supports) are subtracted as chance (`union_support_raw` keeps them). For expert and reference rows U excludes the row itself and the expert |
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

A median epicentral offset mixes a common shift (velocity-model or frame
difference) with scatter (location precision), hides tails, and says nothing
about depth artefacts. L2 therefore separates them:

| Metric | Definition |
|---|---|
| `epi_median[R]`, `epi_p90[R]`, `epi_gt2km`, `epi_gt5km` | epicentral offset of matched pairs: median, 90th percentile, fractions above 2 and 5 km |
| **`shift[R]`** (`shift_east_km`, `shift_north_km`, `shift_km`) | component-wise median of the offset vectors — the common shift |
| **`scatter_median[R]`**, `scatter_p90` | distance of each offset vector from the shift — the precision part |
| `epi_median_by_period` | median offset in four equal-count periods of origin time (a problem confined to part of the sequence does not move the overall median) |
| **`dz_median[R]`**, `dz_mad[R]`, `dz_gt2km` | candidate − reference depth (sea-level datum). Reported also when a datum is unknown, flagged `depth_datum_known: false`; the value is then uncertain by up to the surface elevation, which does not hide errors of several km |
| `dt_median[R]` | median \|Δ origin time\| |

Population depth profile (no matching), for every catalog:

| Metric | Definition |
|---|---|
| `depth p05 / p50 / p95` | depth quantiles |
| **`depth_mode_share`** | largest share of events at one depth value (to 0.01 km): fixed-depth solutions, grid-edge pile-ups |
| `depth_band_share` | largest share of events in any 1-km depth window, read against the reference's value |

### L3 — Relative location and structure (S references)

| Metric | Definition |
|---|---|
| `pair_distance_error[R]` | for each matched event, its 10 nearest matched neighbours in the reference within 5 km; median of |d_Agent − d_ref| over these pairs (3-D distances). Insensitive to a common frame shift |
| `off_structure_fraction` | fraction of located scored Agent events whose epicentre is farther than r_off from every epicentre of the case's S references (epicentral, so depth errors — scored by L2 — and unknown datums do not enter); r_off = 1 km (Kaikōura 5 km). The same value for each reference (against the other S references) and the expert is reported alongside |
| `local_thickness` | median over events of the minor-axis standard deviation of the 20 nearest neighbours; reported with the reference value of the same region |
| `off_structure_after_shift` | `off_structure_fraction` after removing the L2 shift from the candidate epicentres: what remains is misplaced or spurious, not a frame offset |

### L4 — Magnitude (M references, matched pairs with magnitudes)

| Metric | Definition |
|---|---|
| `mag_coverage` | fraction of scored Agent events with a magnitude |
| `dmag_median[R]`, `dmag_mad[R]` | Agent − reference magnitude, by Agent `magnitude_type` |

A constant offset reflects calibration (the expert itself runs 0.22 below
Cochran); the MAD is the quality measure.

### Time, space and strength by magnitude class

Every catalog is also read along three dimensions against the magnitude
authority (A) and the primary detection reference:

| Dimension | Metric | Definition |
|---|---|---|
| time | `dt_s` (mean, median, std, \|dt\| p90) | signed candidate − reference origin time of matched pairs; a mean offset trades off against depth |
| time | `recall_by_day` | recall of the primary detection reference per day of the window |
| time | `recall_after_large` vs `recall_other` | recall of reference events within 1 h after any A event of M ≥ 4 (M ≥ 3 where none) against all other events: short-term incompleteness after large events |
| space | L2, L3 | as above |
| strength | `dmag` (mean, median, std, MAD, \|dmag\| p90) | candidate − A magnitude of matched pairs |
| strength | `dmag_slope_per_unit` | least-squares slope of dmag against the A magnitude; negative = compressed scale or saturation of large events |
| strength | `Mc`, `b` (± σ), `b_difference` | maximum curvature + 0.2 and the Aki–Utsu b-value (Shi & Bolt σ) above it, for candidate and A |
| strength | `magnitude_coverage` | fraction of candidate events with a magnitude |

**Magnitude classes M ≥ 2, 3, 4, 5** (by A magnitude; classes with no A event
are omitted). A candidate event enters class M ≥ T when its magnitude minus
the candidate's median offset from A (over all matched pairs, ≥ 5 pairs) is
≥ T, so precision and F1 measure detection and the calibration is scored by
`dmag`; `precision_unaligned` uses the raw magnitudes. Above M 2–3 the
authority is complete, so precision against it is meaningful, unlike at
small magnitudes (§5 L1). Per class:

| Metric | Definition |
|---|---|
| `recall` | matched A events of the class / A events of the class |
| `precision` | candidate events of the class matched to any A event / candidate events of the class |
| **`f1`** | 2PR / (P + R) |
| `dt_s`, `epi_km`, `dz_km`, `dmag` | distributions (n, mean, median, std, p90) over the matched A events of the class |
| `events` | every A event of the class, matched or missed, with its errors — listed for classes of ≤ 20 events and for M ≥ 4 |

M ≥ 4 has enough events for distributions only at Ridgecrest (88) and
Kaikōura (12); M ≥ 5 (≤ 6 events per case) is read from the event list.

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
4. vs the primary location reference: `shift`, `scatter_median`, `epi_gt5km`, `dz_median`;
5. depth artefacts: `depth_mode_share`;
6. by magnitude class: `f1` (with recall, precision) and mean `dt`, `epi`, `dmag`; strength: `dmag` median and std, `dmag_slope_per_unit`; time: mean `dt`, `recall_after_large`;
7. `off_structure_fraction` and `off_structure_after_shift`;
8. cost and wall time.

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
2026-10-22) carry `depth_datum_known: false`; their depth differences are
reported with that flag.

## 9. Implementation

The scorer is shared code in `SeismoAgentBench/scoring/catalog_metrics/`;
each case provides only `evaluation/metrics_v1.yaml` (mask, roles, datums,
primary references, expert catalogs, leakage patterns) and, where its
references are not read by the expert stage-05 module, a
`metrics_v1_adapter.py` (Ridgecrest). Every score file records
`metrics_version`, the scorer's git commit and dirty flag, the gates, the
reference counts after masking and the audit sample.

```bash
python -m SeismoAgentBench.scoring.catalog_metrics baseline --task-dir workflows/tasks/<case>
python -m SeismoAgentBench.scoring.catalog_metrics run --task-dir workflows/tasks/<case> \
    --run-dir workflows/tasks/<case>/runs/<variant>/<harness>/<model>/<run_id>
python -m SeismoAgentBench.scoring.catalog_metrics summary --task-dir workflows/tasks/<case> [--rescore]
```

| Output | Content | Tracked |
|---|---|---|
| `evaluation/metrics_v1_baseline.json` | ceilings; reference, expert-final and expert-blind rows | yes |
| `<run>/evaluation/metrics_v1.json` | one run: completion, catalog notes, all metrics, headline, process, leakage | no (runs/ is ignored) |
| `<run>/evaluation/location_diagnostics.png` | offset vectors (shift vs scatter), offset CDF with expert yardsticks, depth distribution with the densest band, map of offsets and off-structure events | no |
| `<run>/evaluation/audit_sample.csv` | the audit sample, drawn once and never redrawn; reviewers add `audit_labels.csv` (`event_id,label`) | no |
| `evaluation/metrics_v1_summary.json` | per configuration over repeated runs (§6) | yes |

The leakage scan reads only the Agent's tool-call inputs (its accesses), not
text that appears in tool results such as fetched documents or directory
listings; withheld-product patterns are reference DOIs, repository paths of
reference data, expert outputs and scores, and earthquake-catalogue services.
