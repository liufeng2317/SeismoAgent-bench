# Development loop, round 1: checker 1.4 on one day around the mainshock (2026-11-07)

First round of the development loop ([`dev_window`](../../../../workflows/development/dev_window/README.md)): the S3 arm (`dev_knowledge`, checker 1.4 with the knowledge skill) on the five cases without a window score yet; Maple Creek is represented by its formal S3 run scored over the same window. Claude Code × GLM-5.3, up to three runs at a time. The first attempt (2026-11-06) was stopped after one hour by the provider's weekly limit and is excluded; the repeat ran 3.5–6.5 h per case, none used its 12-h budget.

## Results over the development window

| Case | Run | Failed criteria | Values (threshold) | Checker flags at the end and their disposition |
|---|---|---|---|---|
| Prague | 20261106T182429Z | 2 | after-large-events recall 0.67 (0.72); off-structure 5.03 % (5.0 %) | `depth_layers`, justified with evidence |
| Magna | 20261106T182043Z | 4 | origin time +0.31 s (0.30); horizontal shift 2.31 km (1.0); depth −1.75 km (1.0); magnitude +0.30 (0.24) | `sp_depth_offset` (catalog 2.68 km too shallow), justified with evidence |
| Maple Creek | formal 20261105T225355Z, cut to the window | 6 | origin time +1.30 s; shift 1.89 km; scatter 1.38 km; off-structure; magnitude spread and scale | five flags, all justified (record 16) |
| Kīlauea | 20261106T232339Z (rescue) | 0 | — | none |
| Ridgecrest | 20261106T182236Z (rescue) | 2 | depth +1.26 km (1.0); M4 recall 0.84 (1.0) | `silent_stations`, `station_day_gaps`, `depth_layers`, justified with evidence |
| Kaikōura | 20261106T214922Z | 5, time and space insufficient | outside station coverage 7.1 % (5 %); off-structure 14 % (7.8 %); depth pile-up 10.6 % (5 %); magnitude −0.37 (0.28) and scale | `isolated_events`, `depth_single_value`, both "justified" without evidence (audit: incomplete) |

Kīlauea and Ridgecrest wrote catalog, picks and checker report into `$BENCH_OUTPUT/work/` instead of `$BENCH_OUTPUT`; formally they did not complete. Their products were scored over the same window as a reference-only rescue (`evaluation/rescue/` of each run).

## Findings

1. **An instruction defect, not an Agent error, cost two of five runs.** The catalog-checker skill named its deliverables in the run-root form `work/checker/final/checker_report.json`, while the prompt and the contract mean paths relative to `$BENCH_OUTPUT` (which is itself `work/`). Agents that followed the skill created `$BENCH_OUTPUT/work/` and put their products there (Maple S3 also kept a `work/work/` tree). The audit resolves `report_before` relative to `$BENCH_OUTPUT` too, so the skill's own example could never validate. Fixed on 2026-11-07 (4ef4492): all paths relative to the output directory, next to `catalog.csv`.
2. **Correct flags dismissed with fit statistics (Magna).** `sp_depth_offset` said the catalog was 2.68 km too shallow; the reference says 1.75 km. The Agent tested a slower near-surface Vs and a lower Vp/Vs, rejected both because the residuals got worse, and absorbed the rest in station S delays of one sign per side of the fault (−0.5 to −1.6 s east, +0.9 to +1.5 s west). The knowledge entry on `sp_depth_offset` invites this: it tells the Agent to test a change on "the residuals", which contradicts the rule against choosing by residual elsewhere in the skill, and it says only that the sign is unreliable below the limit, not that the direction above the limit (1.5 km) has always been right.
3. **A fix declared to be tuning (Kaikōura).** 178 events sat at the top of the search grid (`depth_single_value` 10.8 %). The Agent saw that they had no depth constraint and that their expectation depths spread normally, but kept the maximum-likelihood depths and justified the flag, calling a change "fabrication/metric-tuning". Reporting the expectation hypocentre (with its uncertainty) for events whose maximum-likelihood point sits at a grid edge is standard practice; the knowledge does not say so. The dispositions file had no evidence, which the audit caught.
4. **A flag that asks for more data led to bad data (Maple; record 16).** DPPPicker picks of eight vertical-only stations, added for `silent_stations`, moved a quarter of the epicentres by more than 5 km.
5. **What went well.** Every run used template matching; magnitude offsets are within 0.4 everywhere (no unit or response error); flags at the end are few (0–5) and the scorer's re-run agreed with every submitted report; Kīlauea passes every criterion and Ridgecrest fails only depth and the M4 recall.

## Candidate changes for checker 1.5

- Knowledge, `sp_depth_offset`: above the limit the direction has been right in every case so far; do not dismiss it with residuals or absorb it with one-sided station delays; test a model change on the S−P depths of near stations and on the depth distribution, not on the fit.
- Knowledge, depth piles at a grid edge: for events without depth constraint, report the expectation hypocentre and its uncertainty (or mark the depth as unconstrained); this is a correction, not tuning.
- Knowledge and check, added pick groups: after adding picks from a new picker or station group, compare the locations with and without them and their residual spread against the stations used before; `station_residual_spread` relative to the established stations.
- Contract wording: done (finding 1).

Open, not yet a candidate: the out-of-coverage events of Kaikōura (the prompt does not give the study region by design), the M4 recall after the Ridgecrest mainshock (coda), and the origin-time bias of Maple Creek (velocity model, layer C).
