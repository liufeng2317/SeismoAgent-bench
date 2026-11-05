# Status and work plan

Living document: what is done, what runs, what comes next. The design is defined in the [research plan](../../00_A_Research_Plan_Benchmark.md); the paper's claims are in the [paper outline](../../01_Register.md). Weekly summaries are kept next to this file (`YYYY-MM-DD_progress_summary.md`).

## 1. Status (2026-10-30)

- **Metrics v2** (2026-10-30, [`02_Catalog_Metrics.md`](../../../framework/02_Catalog_Metrics.md) §12). The Maple Creek runs showed that v1's headline hid a scattered `min` catalog and a biased `tools` catalog. v2 sets primary gates at 2 s / 5 km (Kaikōura 4 s / 15 km), corrects every match for chance, compares every catalog directly with the human-in-loop final, adds tight-gate recall, origin time and out-of-region share to the headline, and gives each run a trusted-catalog verdict on four dimensions — event reality, time, space, strength — with completeness against the final reported apart (§7a). All baselines, ladders, runs and swaps were re-scored; single scoring path `python -m SeismoAgentBench evaluate` (catalog-metrics@1).
- **Human-in-loop baselines.** Final and blind rows in each `evaluation/human_in_loop/metrics_baseline.json` (v2); Agent runs are compared with the final only; expert ladder re-scored per case.
- **Zero-cost analyses.** Expert ladder and component swap — [`00_B_Research_Plan_Checker.md`](../../00_B_Research_Plan_Checker.md).
- **Agent stages.** S0 `min` and S1 `tools` implemented; S2 `knowledge` and S3 `checker` designed ([research plan](../../00_A_Research_Plan_Benchmark.md) §3 and the [checker plan](../../00_B_Research_Plan_Checker.md) §3), not implemented.
- **Formal runs** (Claude Code × GLM-5.3, one per case and stage): Prague, Magna, Maple Creek and Kīlauea S0/S1 scored; Kaikōura `min` running; Kaikōura `tools` re-launched 2026-10-29 18:39 UTC after the first attempt was excluded (harness defect: the prompt sat on the Claude process's argv and the Agent's `kill -9` by pattern matched its own session; the runner now passes the prompt on stdin; metrics §11); Ridgecrest queued, with the fixed runner. The four earlier Ridgecrest/Magna runs predate the output conventions and remain development runs.
- **Framework.** Task definitions, input mapping, Agent execution through adapters, run records and the external scorer are documented in [`docs/framework/`](../../../framework).

### Scored runs (metrics v2)

Every number for every case and run, by dimension: [`SCORE_TABLE.md`](../SCORE_TABLE.md); how each is computed: [`../03_Scoring_Method.md`](../../03_Scoring_Method.md).

Trusted-catalog verdict per dimension (✓ pass, ✗ fail, … audit pending) and completeness: recall_norm against the primary detection reference (final in brackets) and the share of the final's events the run recovers. No run reaches the trusted-catalog standard yet.

| Run | Reality | Time | Space | Strength | recall_norm | Recovers of final | Failed criteria |
|---|---|---|---|---|---|---|---|
| Prague min | — | — | — | — | 0 (1.85) | 0 % | no outputs in the run folder |
| Prague tools | ✓ | ✓ | ✗ | ✗ | 1.38 (1.85) | 46 % | depth bias +1.10 km; magnitude −2.77 (unit error) |
| Magna min | — | — | — | — | 0 (1.14) | 0 % | no outputs |
| Magna tools | ✓ | ✓ | ✗ | ✗ | 0.87 (1.14) | 51 % | shift 2.35 km and depth bias −1.94 km vs final; magnitude +0.67 |
| Maple Creek min | ✗ | ✗ | ✗ | ✗ | 0.34 (0.99) | 13 % | 80 % outside the region; scatter 4.0 km; 56 % off structure; depth pile-up; magnitude scale |
| Maple Creek tools | ✗ | ✗ | ✗ | ✗ | 0.96 (0.99) | 22 % | 13 % outside the region; origin times +1.15 s; depth bias −2.18 km; scatter 1.9 km; 12 % off structure; magnitude slope −0.44 (limit 0.41) |
| Kīlauea min | ✗ | ✗ | ✗ | ✗ | 0.90 (1.22) | 42 % | 45 % outside the region; origin times −0.96 s; depth bias +1.29 km; depth pile-up; magnitude −2.43 |
| Kīlauea tools | … | ✗ | ✓ | ✓ | 0.88 (1.22) | 37 % | origin times −0.36 s (limit 0.3 s) only |

Component swap (Agent picks, expert locator): the back-end errors largely disappear — Maple Creek tools depth −2.18 → −0.31 km and origin time 1.01 → 0.20 s; Prague tools depth +1.10 → 0.00 km; Magna tools depth −1.94 → −0.96 km, shift 2.50 → 1.61 km; Kīlauea min depth +1.29 → −0.03 km and origin time 0.90 → 0.19 s.

## 2. Work plan

| Phase | Work | Runs | Estimate |
|---|---|---:|---|
| A (now) | finish S0/S1 on six cases (Prague, Magna, Maple Creek, Kīlauea scored; Kaikōura running; then Ridgecrest); swap, blind audit (labels for Maple Creek and Kīlauea), second-rater check. In parallel without compute: tier table (research plan §2.2), intervention coding (`00_B_Research_Plan_Checker.md` §7) | 4 left | ~1 week, single queue, 5–8 h per run |
| B | build the checker CLI (symptoms only) and validate it on the human-in-loop catalogs and the scored S0/S1 runs before freezing its thresholds; the knowledge skill; skill delivery in the runner; checker contract and scorer verification; debug on a pilot run (not counted) | 0 formal | 4–6 days |
| C | first S2c `checker` (tools + checker, no knowledge) on six cases, then S2 `knowledge` and S3 `knowledge_checker`; S1 repeats on Prague and Magna; second model S1/S3 on three cases | ~30 | ~9–10 days single queue |
| D | analysis, figures, writing | — | — |

## 3. Trusted-catalog standard

Fixed with metrics v2 on 2026-10-30: [`02_Catalog_Metrics.md`](../../../framework/02_Catalog_Metrics.md) §7a. Event reality, then time, space and strength, each judged on accuracy (offset from the final) and stability (spread and consistency); completeness against the final is reported apart. The scorer writes the verdict into every run's `metrics.json` (`trust`) and the per-configuration `trusted_runs` into `metrics_summary.json`.

## 4. Open items

- Second model and harness choice (research plan §2.6).
- Held-out case: whether, and which (research plan §2.6).
- Prompts state the time window but not the region, so out-of-region events are gated (event reality) but not counted as false. Decide whether future task versions should state the region.
- The labelled audits of Prague tools and Magna tools keep their v1 samples (a subset of the v2 unsupported events); decide whether to add a v2 supplement.
- The task-level `VARIANTS.md` files still list `guided` as the knowledge arm (Q3). Update them when S2/S3 task files are added in Phase B.
