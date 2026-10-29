# Status and work plan

Living document: what is done, what runs, what comes next. The design is defined in the [research plan](../00_Research_Plan.md); the paper's claims are in the [paper outline](../02_Paper_Outline.md). Weekly summaries are kept next to this file (`YYYY-MM-DD_progress_summary.md`).

## 1. Status (2026-10-30)

- **Metrics v2** (2026-10-30, [`03_EVALUATION_METRICS.md`](../../framework/03_EVALUATION_METRICS.md) §12). The Maple Creek runs showed that v1's headline hid a scattered `min` catalog and a biased `tools` catalog. v2 sets primary gates at 2 s / 5 km (Kaikōura 4 s / 15 km), corrects every match for chance, compares every catalog directly with the human-in-loop final, adds tight-gate recall, origin time and out-of-region share to the headline, and gives each run a usability verdict (§7a). All baselines, ladders, runs and swaps were re-scored; single scoring path `python -m SeismoAgentBench evaluate` (catalog-metrics@1).
- **Human-in-loop baselines.** Final and blind rows in each `evaluation/human_in_loop/metrics_baseline.json` (v2); Agent runs are compared with the final only; expert ladder re-scored per case.
- **Zero-cost analyses.** Expert ladder and component swap — [`01_Expert_Experience_and_Checker.md`](../01_Expert_Experience_and_Checker.md).
- **Agent stages.** S0 `min` and S1 `tools` implemented; S2 `knowledge` and S3 `checker` designed ([research plan](../00_Research_Plan.md) §2.4–2.5), not implemented.
- **Formal runs** (Claude Code × GLM-5.3, one per case and stage): Prague, Magna, Maple Creek and Kīlauea S0/S1 scored; Kaikōura running; Ridgecrest queued. The four earlier Ridgecrest/Magna runs predate the output conventions and remain development runs.
- **Framework.** Task definitions, input mapping, Agent execution through adapters, run records and the external scorer are documented in [`docs/framework/`](../../framework/).

### Scored runs (metrics v2)

recall_norm against the primary detection reference (final in brackets); `recall_final` is the share of the final's events the run recovers. No run is usable yet.

| Run | recall_norm | recall_tight | recall_final | Main errors | Usability: failed criteria |
|---|---|---|---|---|---|
| Prague min | 0 (1.85) | — | — | outputs written outside the run folder | completed |
| Prague tools | 1.38 (1.85) | 0.70 (0.94) | 0.46 | depth +1.10 km vs final; magnitude −2.77 (unit error) | detection, detection_tight, completeness, depth, magnitude |
| Magna min | 0 (1.14) | — | — | session ended without outputs | completed |
| Magna tools | 0.87 (1.14) | 0.52 (0.78) | 0.51 | shift 2.50 km; depth −1.94 km vs final; magnitude +0.67 | detection, detection_tight, shift, depth, magnitude |
| Maple Creek min | 0.34 (0.99) | 0.04 (0.95) | 0.13 | 80 % of events outside the region; 56 % off structure; depths on model interfaces | 10 of 11 |
| Maple Creek tools | 0.96 (0.99) | 0.43 (0.95) | 0.22 | origin times +1.0 s; depth −2.18 km vs final; 12 % off structure | detection_tight, completeness, region, origin time, depth, structure |
| Kīlauea min | 0.90 (1.22) | 0.25 (0.57) | 0.42 | origin times 0.9 s off; magnitude −2.43; 17 % at one depth | 8 criteria |
| Kīlauea tools | 0.88 (1.22) | 0.42 (0.57) | 0.37 | detection only | detection, detection_tight, completeness |

Component swap (Agent picks, expert locator): the back-end errors largely disappear — Maple Creek tools depth −2.18 → −0.31 km and origin time 1.01 → 0.20 s; Prague tools depth +1.10 → 0.00 km; Magna tools depth −1.94 → −0.96 km, shift 2.50 → 1.61 km; Kīlauea min depth +1.29 → −0.03 km and origin time 0.90 → 0.19 s.

## 2. Work plan

| Phase | Work | Runs | Estimate |
|---|---|---:|---|
| A (now) | finish S0/S1 on six cases (Prague, Magna, Maple Creek, Kīlauea scored; Kaikōura running; then Ridgecrest); swap, blind audit (labels for Maple Creek and Kīlauea), second-rater check. In parallel without compute: tier table (research plan §2.2), intervention coding (`01_Expert_Experience_and_Checker.md` §5) | 4 left | ~1 week, single queue, 5–8 h per run |
| B | build the checker CLI and the knowledge skill; skill delivery in the runner; checker contract and scorer verification; debug on pilot runs (not counted) | 0 formal | 3–5 days |
| C | S2 and S3 on six cases; S1 repeats on Prague and Magna; second model S1/S3 on three cases; optional `tools + checker` on three | ~25 | ~7–8 days single queue |
| D | analysis, figures, writing | — | — |

## 3. Usability criteria

Fixed with metrics v2 on 2026-10-30: [`03_EVALUATION_METRICS.md`](../../framework/03_EVALUATION_METRICS.md) §7a. Each criterion is read against the final of the same case; the scorer writes the verdict into every run's `metrics.json` and the per-configuration `usable_runs` into `metrics_summary.json`.

## 4. Open items

- Second model and harness choice (research plan §2.6).
- Held-out case: whether, and which (research plan §2.6).
- Prompts state the time window but not the region, so out-of-region events are gated (usability) but not counted as false. Decide whether future task versions should state the region.
- The labelled audits of Prague tools and Magna tools keep their v1 samples (a subset of the v2 unsupported events); decide whether to add a v2 supplement.
- The task-level `VARIANTS.md` files still list `guided` as the knowledge arm (Q3). Update them when S2/S3 task files are added in Phase B.
