# Evaluation metrics (v2, pre-registered)

This document fixes how every Agent catalog is scored. Version 1 was pre-registered on 2026-10-27, revised while it was implemented and before any formal Agent run was scored (§10), and frozen on 2026-10-28. **Version 2 replaced it on 2026-10-30** (§12): the first scored runs showed that v1's headline hid catalogs that were scattered or systematically biased (Maple Creek). Every baseline, ladder round and run has been re-scored with v2. A change to any definition, gate, mask, reference role, expert catalog or trust threshold from now on creates a new version; every run is then re-scored with that version, and each score file records the version it used (`metrics_version: 2`) and the scorer commit.

Two principles follow from the expert work on the six cases:

- **Reference catalogs are not ground truth.** They do not recover each other fully (primary-reference ceilings 0.49–0.69 under the gates below; Maple Creek 0.98, where ComCat holds only 626 larger events), and their absolute locations differ by the velocity-model frame (up to ~3.5 km at Kaikōura). Every metric is therefore reported against several references, each used only for the roles it supports, and next to two yardsticks: the reference-to-reference value and the human-in-loop final, which every catalog is also compared with directly (v2).
- **No composite score.** The output is a capability profile per case and configuration; the headline metrics are listed in §7.

## 1. Scored population

- **Rows.** All rows of the Agent's `catalog.csv` except those with `status = rejected` (case-insensitive). A sensitivity variant scores only `status = accepted`. Rows without latitude, longitude or origin time count toward the event total but never enter correspondence.
- **Mask.** Each case's cohort mask in `expert/00_config/validation.yaml` (half-open time window, region box, depth bounds) is applied identically to references, expert and Agent. Agent rows outside the mask are reported as `out_of_mask_fraction` and are not scored further. v2 puts `out_of_mask_fraction` in the headline and the trusted-catalog standard (§7a, event reality); it does not count those rows as false events, because the prompts state the time window but not the region, so an out-of-region event may be a real regional earthquake. Rows without a depth are kept in the mask test on time and epicentre alone.
- **Depth datum.** `depth_km` is kilometres below sea level, positive down, for every variant (§8). Reference depths are converted to the same datum where the datum is known; where it is not, the reference has no depth role.

## 2. Event correspondence

- **Matcher.** Greedy one-to-one pairing of candidate events with reference events, ranked by epicentral distance, then |Δt|.
- **Primary gates (v2):** |Δt| ≤ 2 s and epicentral distance ≤ 5 km. A case may set `primary_gates` in its `evaluation/metrics.yaml`: Kaikōura keeps 4 s / 15 km, where the 260-km network and the 1-D vs 3-D frame offset leave the final's own epicentres 1.9 km scattered about the references (its recall falls from 0.81 to 0.64 at 2 s / 5 km; in the other cases by ≤ 0.04). v1 used 4 s / 15 km everywhere, a gate larger than the whole Maple Creek swarm.
- **Sensitivity gates:** 4 s / 15 km and 1 s / 3 km, reported for every detection and location metric. The 1 s / 3 km recall is the headline `recall_tight`.
- **Chance correction (v2, every pairing).** The same matcher run against the reference shifted by 60 s counts coincidences at the sequence's own event density: chance rate p = chance / N. An observed rate m = matched / N is m = r + (1 − r) p for a true rate r, so `recall_net = (m − p) / (1 − p)`, clipped at 0. The same correction gives `union_support` and the precision against the final. v1 corrected only time-only pairing and subtracted p, which over-corrects a dense, complete catalog (Maple Creek final: 0.76 instead of 0.98).
- **Reference-specific gates.** A reference whose origin times are coarse keeps its own gates (Isken & Mooney 2017: 60 s / 5 km).
- **Time-only references** (Maple Creek, Shelly & Hardebeck 2019): pairing on |Δt| ≤ 1 s alone, chance-corrected as above.

## 3. Reference roles

Roles: **D** detection (recall, union support), **L** absolute location, **S** relative structure, **M** magnitude, **P** phase picks. The primary detection and location references (bold) feed the headline metrics. The primary detection reference must have an informative ceiling, i.e. another independent catalog of comparable completeness; where the largest catalog has none (Kaikōura: Tan; Maple Creek: Shelly) its raw recall is reported alongside the normalised headline.

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

**Magnitude authority.** Magnitude classes and the strength dimension use one catalog per case, the operational network catalog with calibrated ML/Mw that is complete above M 2–3: Ridgecrest ComCat (SCSN), Magna UUSS, Kīlauea ComCat (HVO), Kaikōura GeoNet, Maple Creek ComCat (UUSS). Prague's 2011 ComCat holds 11 events in the window, so Cochran sets its classes. Research catalogs use differing magnitude scales (Magna M2+: Pang 375, UUSS 140 events) and are not used for classes.

A reference's depth enters L only when its datum is known (sea level or stated surface datum convertible with the case's model datum).

## 4. Yardsticks

- **Reference ceiling** for a detection reference R: `ceiling(R) = max over other D references S of recall_net(S, R)`, computed with the same matcher, mask and gates. It is the recall that an independent high-quality catalog actually reaches; values above it are possible (the expert exceeds it in all five scoreable cases) and are not capped.
- **Expert rows.** Two expert catalogs are scored with the same code:
  - *expert (final)* — the final round of each case. It was tuned with the hidden references in view and is reported as a **reference-informed upper control**, not as a blind result;
  - *expert (blind)* — the located-event catalog of the first round (Ridgecrest `01_baseline`, other cases `r1` stage 04), configured from the ported pipeline and published velocity models before any comparison with the case's references.
  - *Reporting convention (2026-10-29, §11):* Agent runs are compared with the final row only — the human-in-loop agent's result is the Agent's upper bound. The blind row is still computed but is not a yardstick: it used no template matching, while the `tools` arm offers Match&Locate. The gap to the final, including its reference-informed part, is attributed step by step with the expert ladder.
- **Direct comparison with the final (v2).** Every other catalog — reference rows, the blind round, ladder rounds, Agent runs and their component swaps — is also matched one to one with *expert (final)* under the primary gates (`versus_final`): `recall_final` (share of the final's events recovered), `precision_final` (share of the catalog's events the final contains), both chance-corrected; `event_ratio_final`; and the catalog minus the final: `shift_final_km`, `scatter_final_km`, `dz_final_km`, `dt_final_s`. The final is the Agent's upper bound, and against a sparse primary reference (Maple Creek ComCat, 626 events) only this comparison shows how much of the small-event population a catalog misses.
- **Method-variance floor** for location: the spread between locators on the same associations (Prague stage 70: median 0.37 km, the largest epicentre distance from the median of four locators; `expert/PLAN.md` "Method comparison"). Agent–reference location differences below the larger of this floor and the reference-to-reference offset are read as equivalent.

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
| `recall[R]`, `recall_net[R]` | matched / N_R, and the chance-corrected rate (§2) used for every derived value; headline `recall_ref_<R>` for every D reference |
| **`recall_norm[R]`** | `recall_net[R] / ceiling(R)` — headline for the primary detection reference |
| **`recall_tight`** | `recall_net` against the primary detection reference at 1 s / 3 km: a catalog with right events at wrong times or places falls here, not in `recall_norm` |
| `recall_by_mag[R]` | recall in 0.5-unit bins of the reference magnitude |
| `M90[R]` | lowest reference magnitude M (taken from the reference's own magnitudes, to 0.1) such that recall of reference events with magnitude ≥ M is ≥ 0.9, over at least 10 events (calibration-free completeness proxy; undefined if never reached) |
| `event_ratio` | scored Agent events / N of the primary detection reference |
| **`union_support`** | fraction of scored Agent events matched (primary gates) to at least one event of U = all D references ∪ expert (final) — headline precision proxy. Time-only members match on \|Δt\| ≤ 1 s. Chance-corrected (§2) with the events U shifted by 60 s would support (`union_support_raw` keeps them). For expert and reference rows U excludes the row itself and the expert |
| `audited_false_rate` | see below |

**Audit of unsupported events.** From each scored run, draw a stratified random sample of the events without support in U (50, or all if fewer; strata by Agent `n_picks` tercile, fixed seed); `audit_sample.csv` is drawn once and never redrawn. `catalog_metrics audit` turns it into a blind review package (`<run>/evaluation/audit/`): figures `aNN.png` in random order, each showing the six nearest stations (2–15 Hz) with the event's predicted P/S and those of the run's own other events — no reference catalog — and `key.csv` (aNN → event), opened only after labelling. The first reviewer (Claude) labels every figure *earthquake* (own P/S arrivals at ≥ 2 near stations), *not_earthquake* (none at the predicted times) or *undecidable* in `labels.csv`; a second reviewer (the user) labels the random subset in `spot_check.csv` (10 figures), and their agreement is reported. The estimated false-event rate is `(1 − union_support) × p_false`, with `p_false = not / (earthquake + not)` and a Wilson 95 % interval; it is computed only when every sample is labelled. Reviews are kept next to the run evaluation and reused across metric versions.

### L2 — Absolute location (L references, matched pairs)

A median epicentral offset mixes a common shift (velocity-model or frame difference) with scatter (location precision), hides tails, and says nothing about depth artefacts. L2 therefore separates them:

| Metric | Definition |
|---|---|
| `epi_median[R]`, `epi_p90[R]`, `epi_gt2km`, `epi_gt5km` | epicentral offset of matched pairs: median, 90th percentile, fractions above 2 and 5 km |
| **`shift[R]`** (`shift_east_km`, `shift_north_km`, `shift_km`) | component-wise median of the offset vectors — the common shift |
| **`scatter_median[R]`**, `scatter_p90` | distance of each offset vector from the shift — the precision part |
| `epi_median_by_period` | median offset in four equal-count periods of origin time (a problem confined to part of the sequence does not move the overall median) |
| **`dz_median[R]`**, `dz_mad[R]`, `dz_gt2km` | candidate − reference depth (sea-level datum). Reported also when a datum is unknown, flagged `depth_datum_known: false`; the value is then uncertain by up to the surface elevation, which does not hide errors of several km |
| `dt_median[R]` | median \|Δ origin time\| — headline `dt_median_s` against the primary location reference |

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

A constant offset reflects calibration (the expert itself runs 0.22 below Cochran); the MAD is the quality measure.

### Time, space and strength by magnitude class

Every catalog is also read along three dimensions against the magnitude authority (A) and the primary detection reference:

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

**Magnitude classes M ≥ 2, 3, 4, 5** (by A magnitude; classes with no A event are omitted). A candidate event enters class M ≥ T when its magnitude minus the candidate's median offset from A (over all matched pairs, ≥ 5 pairs) is ≥ T, so precision and F1 measure detection and the calibration is scored by `dmag`; `precision_unaligned` uses the raw magnitudes. A candidate event of the class counts as real when it matches an A event or is supported by U (§5 L1): operational catalogs are not complete at M 2 during crises (Kīlauea 4–5 May 2018: half of the expert's M2+ events missing from HVO are in Shelly, Wei or Matoza); `precision_authority_only` keeps the stricter value. Per class:

| Metric | Definition |
|---|---|
| `recall` | matched A events of the class / A events of the class |
| `precision` | candidate events of the class matched to any A event or supported by U / candidate events of the class |
| **`f1`** | 2PR / (P + R) |
| `dt_s`, `epi_km`, `dz_km`, `dmag` | distributions (n, mean, median, std, p90) over the matched A events of the class |
| `events` | every A event of the class, matched or missed, with its errors — listed for classes of ≤ 20 events and for M ≥ 4 |

M ≥ 4 has enough events for distributions only at Ridgecrest (88) and Kaikōura (12); M ≥ 5 (≤ 6 events per case) is read from the event list.

### L5 — Phase picks (P references; Magna, Maple Creek)

Reference picks (`pick_reference` in `metrics.yaml`): Magna, Baker & Whidden (2021) manual picks; Maple Creek, the Shelly & Hardebeck (2019) correlation-derived release, collapsed to one arrival per detection, station and phase (highest weight; the release repeats each arrival once per matching template, ~12 times) and merged within 0.5 s per station and phase. Only the evaluation window and the stations present in both sets are used. Within each station and phase, candidate and reference picks are paired one to one, greedily by |dt| ≤ 0.5 s; the 0.1 s figures are the subset of those pairs.

| Metric | Definition |
|---|---|
| `recall_0.5s`, `recall_0.1s` | paired / reference picks, per phase — headline `pick_recall_P`, `pick_recall_S` |
| `precision_0.5s`, `precision_0.1s` | paired / candidate picks; a lower bound, since the reference covers only its own catalog's events |
| `residual_median_s`, `residual_mad_s` | candidate − reference time of the 0.5 s pairs — headline `pick_residual_mad_<phase>_s` |

The expert's own stage-03 picks are scored the same way (baseline expert-final row).

### L6 — Process and cost

From the run record: wall time, cost (USD), input/output/cached tokens, turns, tool calls over 300 s, compactions. **Leakage flags:** every URL and file path accessed outside the run directory is listed from the transcript; an access matching the case's withheld products (reference DOIs, data repositories and catalogue services in `data/<case>/data/catalogs/*/README.md`) sets `leakage_flag`. A flagged run is reported but excluded from headline means.

### L7 — Reliability self-assessment (optional columns)

Computed only when the Agent fills `horizontal_uncertainty_km` (and `depth_uncertainty_km`), against the primary location reference:

| Metric | Definition |
|---|---|
| `uncertainty_coverage` | fraction of matched events with epicentral error ≤ the reported value (compare with 0.68 for a 1σ quantity, stated by the Agent) |
| `uncertainty_rank_corr` | Spearman ρ between reported uncertainty and epicentral error |

The missing columns do not change any other score.

## 6. Repeats and failed runs

- Each configuration (case × variant × harness × model) runs at least twice, target three times. Means are reported with the min–max range.
- **Detection metrics** (`recall*` including `recall_tight` and `recall_final`, `f1_*`, `M90` as "not reached") count a failed run (no contract-valid catalog) as zero and are averaged over all launched runs. A failed run does not reach the trusted-catalog standard (§7a).
- **Location, structure, magnitude and pick metrics** are averaged over completed runs only and are always shown together with `completion_rate`.

## 7. Headline table

Per case and configuration:

1. `completion_rate` and the trusted-catalog verdict (§7a) per dimension — reality, time, space, strength — with the failed criteria;
2. detection: `recall_norm` vs the primary detection reference, `recall_tight` (1 s / 3 km), `recall_ref_<R>` for every other D reference (Maple Creek: Shelly), and against the final `recall_final` and `event_ratio_final`;
3. precision and region: `union_support`, `precision_final`, `audited_false_rate`, `out_of_mask_fraction`;
4. vs the primary location reference: `shift`, `scatter_median`, `epi_gt5km`, `dz_median`, `dt_median_s`; vs the final: `shift_final_km`, `dz_final_km`, `dt_final_s`;
5. depth artefacts: `depth_mode_share`;
6. by magnitude class: `f1` (with recall, precision) and mean `dt`, `epi`, `dmag`; strength: `dmag` median and std, `dmag_slope_per_unit`; time: mean `dt`, `recall_after_large`;
7. `off_structure_fraction` and `off_structure_after_shift`; phase picks where a pick reference exists: `pick_recall_P/S`, `pick_residual_mad_P/S_s`;
8. cost and wall time.

Read the headline with the run's map and depth section next to the final's (`evaluation/comparison/` figures): a scattered or shifted catalog is obvious there, and every v2 headline item was added because a figure showed what the v1 numbers did not.

Rows: each Agent configuration, *expert (final)* (the upper bound), and each reference scored against the primary reference (the ceiling rows). *Expert (blind)* appears only as the first step of the expert ladder (§11).

## 7a. Trusted-catalog standard (v2)

Does a run's catalog reach the standard of a trusted catalog? The verdict is read on four dimensions against the human-in-loop final of the same case (`trust.py`; per run in `metrics.json` → `trust`, per configuration `trusted_runs` in the summary). First, the events must be real; then time, space and strength are each judged on **accuracy** (a systematic offset from the final) and **stability** (spread and consistency). A run is trusted when all four dimensions pass; the verdict also lists each dimension, so the profile shows where a catalog fails.

**Completeness is reported next to the verdict, not judged**: `recall_norm`, `recall_tight`, `recall_final`, `event_ratio_final`. An incomplete catalog of accurate events can be trusted — an operational catalog is the usual example — and the gap in completeness is read separately against the final.

| Dimension | Aspect | Criterion | Metric | Passes when |
|---|---|---|---|---|
| reality | | events inside the region | `out_of_mask_fraction` | ≤ max(0.10, final + 0.05) |
| reality | | few false events | `audited_false_rate` | ≤ 0.02; *pending* until the blind review is labelled |
| time | accuracy | origin-time bias | `time_bias_final_s` (median signed candidate − final) | \|value\| ≤ 0.3 s |
| time | stability | origin-time spread | `time_mad_final_s` | ≤ 0.3 s |
| time | stability | detection after large events | `recall_after_large / recall_other` | ≥ 0.8 × final |
| space | accuracy | horizontal shift | `shift_final_km` | ≤ 1.0 km |
| space | accuracy | depth bias | `dz_final_km` | \|value\| ≤ 1.0 km |
| space | stability | horizontal scatter | `scatter_final_km` | ≤ max(1.0 km, the final's own scatter about the primary reference) |
| space | stability | events on the known structure | `off_structure_fraction` | ≤ max(0.05, 3 × final) |
| space | stability | no depth pile-up | `depth_mode_share` | ≤ max(0.05, final + 0.02) |
| strength | accuracy | magnitude offset | `dmag_median` (vs the magnitude authority) | \|value\| ≤ \|final\| + 0.2 |
| strength | accuracy | large events present | `recall_M4`, `recall_M5` | 1.0 for each class the final has |
| strength | stability | magnitude spread | `dmag_std` | ≤ max(0.3, final + 0.1) |
| strength | stability | no compressed scale | `dmag_slope_per_unit` | \|value\| ≤ max(0.2, \|final\| + 0.1) |

Thresholds are absolute, relaxed to the final's own value plus a margin where the final itself would fail them; criteria measured against the final use absolute thresholds. A criterion whose metric the final lacks does not apply; a metric the run lacks fails it. A dimension is *pending* when only the audit is open; `trusted` is true when all dimensions pass, false when any fails, null while only the audit is pending. A failed run is not trusted.

## 8. Output conventions fixed for scoring

These are format conventions, not scientific guidance, and are stated in every variant's prompt (`min`, `tools`, `guided`):

- `depth_km` is kilometres below sea level, positive down.
- `status` is `accepted`, `uncertain` or `rejected`; rejected rows stay in the files and are not scored.
- `catalog.csv` may carry, after the required columns, the optional columns `horizontal_uncertainty_km`, `depth_uncertainty_km` and `origin_time_uncertainty_s` (1σ). Empty values are allowed.

Runs launched before these conventions (Ridgecrest and Magna, 2026-10-13 to 2026-10-22) carry `depth_datum_known: false`; their depth differences are reported with that flag.

## 9. Implementation

The scorer is shared code in `SeismoAgentBench/scoring/catalog_metrics/`; each case provides only `evaluation/metrics.yaml` (mask, roles, datums, primary references, optional `primary_gates`, expert catalogs, leakage patterns) and, where its references are not read by the expert stage-05 module, a `metrics_adapter.py` (Ridgecrest). File names carry no version since v2. Every score file records `metrics_version`, the scorer's git commit and dirty flag, the gates, the reference counts after masking and the audit sample.

```bash
python -m SeismoAgentBench.scoring.catalog_metrics baseline --task-dir workflows/tasks/<case>
python -m SeismoAgentBench.scoring.catalog_metrics run --task-dir workflows/tasks/<case> \
    --run-dir workflows/tasks/<case>/runs/<variant>/<harness>/<model>/<run_id>
python -m SeismoAgentBench.scoring.catalog_metrics summary --task-dir workflows/tasks/<case> [--rescore]
python -m SeismoAgentBench.scoring.catalog_metrics audit --task-dir workflows/tasks/<case> --run-dir <run>
```

`python -m SeismoAgentBench evaluate --run-dir <run>` runs the same scorer: every task spec declares `artifact-contract@1` and `catalog-metrics@1`; this is the only scoring path. (`@1` is the scorer's interface version; the metric definitions are versioned by `metrics_version`.) Score the baseline before runs: the trust verdict reads the final's headline from `metrics_baseline.json`.

Terminology (2026-10-29): the *human-in-loop agent* is the catalog earlier called "expert" — an Agent workflow in which we steered every stage by hand; file and metric keys keep `expert` (`expert_final`, `expert_blind`, `expert_ladder`, the `expert/` pipeline).

| Output | Content | Tracked |
|---|---|---|
| `evaluation/human_in_loop/metrics_baseline.json` | ceilings; reference, expert-final and expert-blind rows | yes |
| `<run>/evaluation/metrics.json` | one run: completion, catalog notes, all metrics, headline, trust verdict, process, leakage | no (runs/ is ignored) |
| `<run>/evaluation/location_diagnostics.png` | offset vectors (shift vs scatter), offset CDF with expert yardsticks, depth distribution with the densest band, map of offsets and off-structure events | no |
| `<run>/evaluation/audit_sample.csv`, `audit/` | the audit sample (drawn once) and its blind review package: `plots/`, `key.csv`, `labels.csv`, `spot_check.csv` | no |
| `evaluation/agents/metrics_summary.json` | per configuration over repeated runs (§6), with `trusted_runs` | yes |
| `evaluation/agents/<variant>__<harness>__<model>__<run_id>/` | `scores.json` (formal state, metrics version, headline, trust verdict, process, audit, swap; reference-only rescue score when present) and `figures/` | yes |

The leakage scan reads only the Agent's tool-call inputs (its accesses), not text that appears in tool results such as fetched documents or directory listings; withheld-product patterns are reference DOIs, repository paths of reference data, expert outputs and scores, and earthquake-catalogue services.

## 10. Revision history before the freeze

All revisions below were made between pre-registration (2026-10-27, commit 2255ccf) and the freeze; no formal Agent run had been scored. The four development runs (Ridgecrest base/min/tools, Magna min) were used to test the scorer.

| Date | Change | Reason |
|---|---|---|
| 10-27 | Off-structure distance epicentral, against all located S references (McMahon, Liu gain S) | 3-D distance double-counted depth errors (Prague expert 11 % vs 0.04 %) |
| 10-27 | Primary detection reference must have an informative ceiling (Kaikōura → Chamberlain, Maple Creek → ComCat; Tan and Shelly reported raw) | Tan's and Shelly's ceilings were 0.16 and 0.03 |
| 10-27 | Time-only references join U with aggregate chance correction | Maple Creek U was otherwise ComCat alone |
| 10-27 | M90 thresholds are the reference's own magnitudes | 0.1 steps gave non-existent magnitudes |
| 10-27 | Leakage scan reads tool-call inputs only; repository-path patterns replace catalog-folder names | Folder names appear in the supplied station metadata of every case |
| 10-27 | L2 split into shift and scatter, tails, periods, depth reported with unknown datum, depth profile; L3 off-structure after shift | A median epicentral offset hid frame shifts, 8–9 km depth errors and fixed depths |
| 10-27 | Time, space and strength by magnitude class (M ≥ 2–5, operational-catalog magnitudes, candidate offset removed) | Requested evaluation by magnitude with F1 and error distributions |
| 10-27 | Class precision counts union-supported events as real | HVO incomplete at M 2 on 4–5 May 2018 |
| 10-28 | Expert finals replaced by the corrected rounds (stages 65–67) | Missing Ridgecrest mainshocks, compressed large-event magnitudes, coda ghosts |
| 10-28 | catalog-metrics@1 is the only scoring path (`SeismoAgentBench evaluate`) | Three scoring paths with different statistics |
| 10-28 | Blind review package and spot check | Reviewer workflow decided (Claude labels, user spot-checks 10) |
| 10-28 | L5 phase picks wired (Baker; Shelly release collapsed per event/station/phase) | Decided to score picks before the formal runs |

## 11. Reporting conventions after the freeze

These change how results are presented, not any metric or scoring code. Conventions of 10-29 carry over to v2.

| Date | Convention | Reason |
|---|---|---|
| 10-29 | Agent runs are compared with the *expert (final)* row only; *expert (blind)* is described only as the first ladder step | Blind used no template matching while the `tools` arm offers Match&Locate, so it is not a fair yardstick; the final is the Agent's upper bound and the ladder attributes the gap |
| 10-29 | The expert catalog is called the *human-in-loop agent* in figures and text; keys keep `expert` | It is an Agent workflow steered by hand |
| 10-30 | A run stopped by a harness defect, not by the Agent's own work, is marked with `EXCLUDED.md` (the reason) in its run folder, left out of the summary and the export (listed under `excluded_runs`), and repeated once the defect is fixed. Failures of the Agent's own making still count (§6) | Kaikōura `tools` 20261029T123626Z: the runner put the prompt on the Claude process's argv, so the Agent's `ps \| grep MatchLocate2 \| kill -9` killed its own session; the runner now passes the prompt on stdin |

## 12. Version 2 (2026-10-30)

Trigger: the first scored Maple Creek runs. The `min` catalog was scattered over the whole region and its depths sat on velocity-model interfaces; the `tools` catalog was 2 km shallower than the final with origin times 1 s late and held a quarter of the final's events. v1 gave them recall_norm 1.06 and 1.12 against the final's 1.15, and the draft usability criteria passed `tools`. The causes were the gates (4 s / 15 km is larger than the swarm, so v1's `min` recall fell from 0.91 to 0.05 at 1 s / 3 km), a sparse primary reference (ComCat, 626 events) that saturates, out-of-region rows that left no trace in the headline (80 % for `min`), and location compared only with a reference whose depths are 1.5 km shallower than the final's.

| Change | Section |
|---|---|
| Primary gates 2 s / 5 km; case override `primary_gates` (Kaikōura 4 s / 15 km); 4 s / 15 km becomes a sensitivity gate | §2 |
| Chance correction for every pairing, as `(m − p) / (1 − p)` | §2 |
| Every catalog compared directly with the human-in-loop final | §4 |
| Headline adds `recall_tight`, `recall_ref_<R>`, `dt_median_s`, `out_of_mask_fraction` and the comparison with the final | §5, §7 |
| Trusted-catalog standard: event reality, then time, space and strength by accuracy and stability, thresholds relative to the final; completeness reported apart | §7a |
| File names without version (`metrics.yaml`, `metrics.json`, `metrics_baseline.json`, `metrics_summary.json`, `metrics_adapter.py`) | §9 |

Effect on the human-in-loop finals: recall_norm Prague 1.85, Magna 1.14, Maple Creek 0.99, Kīlauea 1.22, Ridgecrest 1.38, Kaikōura 1.17 (v1: 1.83, 1.16, 1.15, 1.16, 1.39, 1.17); Maple Creek's ceiling rises from 0.86 to 0.98 because v1 over-corrected Shelly's time-only matches.

Revision on the same day, before any conclusion rested on it: the first v2 draft judged one *usability* list of eleven criteria, with completeness against the final among them, and called every run "not usable". It was replaced by the trusted-catalog standard above (four dimensions, accuracy and stability, completeness reported apart), which says where a catalog fails and does not mark an accurate but incomplete catalog as untrustworthy. It also adds the signed origin-time comparison with the final (`time_bias_final_s`, `time_mad_final_s`) and `dz_mad_final_km`.

Audit samples are drawn once. The labelled reviews of Prague `tools` and Magna `tools` keep their v1 samples, drawn from the events v1 left unsupported; v2's tighter gates leave more events unsupported, so those samples cover a subset of the v2 unsupported events. The unlabelled Maple Creek samples were redrawn under v2; Kīlauea's were first drawn under v2.

v1 scores remain in git history (last v1 state: commit 9a7c066; v2 definition fe5ffe9, re-scored outputs 68dfa28) and in each run's `evaluation/metrics_v1.json`.
