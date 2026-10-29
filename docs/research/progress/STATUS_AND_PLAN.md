# Status and work plan

Living document: what is done, what runs, what comes next. The design is defined in the [research plan](../00_Research_Plan.md); the paper's claims are in the [paper outline](../02_Paper_Outline.md). Weekly summaries are kept next to this file (`YYYY-MM-DD_progress_summary.md`).

## 1. Status (2026-10-29)

- **Metrics.** Metrics v1 frozen ([`03_EVALUATION_METRICS.md`](../../framework/03_EVALUATION_METRICS.md)); single scoring path `python -m SeismoAgentBench evaluate` (catalog-metrics@1), blind review of unsupported events, L5 picks for Magna and Maple Creek.
- **Human-in-loop baselines.** Corrected and fixed for all six cases (final and blind rows in each `evaluation/human_in_loop/metrics_v1_baseline.json`; Agent runs are compared with the final only); expert ladder recorded per case.
- **Zero-cost analyses.** Expert ladder (what each expert step adds) and component swap (Agent front end versus model/locator choice) — [`01_Expert_Experience_and_Checker.md`](../01_Expert_Experience_and_Checker.md).
- **Agent stages.** S0 `min` and S1 `tools` implemented; S2 `knowledge` and S3 `checker` designed ([research plan](../00_Research_Plan.md) §2.4–2.5), not implemented.
- **Formal runs** (Claude Code × GLM-5.3, one per case and stage): Prague, Magna and Maple Creek S0/S1 done and scored; Kīlauea running; Kaikōura and Ridgecrest queued. The four earlier Ridgecrest/Magna runs predate the output conventions and remain development runs.
- **Framework.** Task definitions, input mapping, Agent execution through adapters, run records and the external scorer are documented in [`docs/framework/`](../../framework/). The deterministic `main.py` baseline verifies task execution and artifact generation.

## 2. Work plan

| Phase | Work | Runs | Estimate |
|---|---|---:|---|
| A (now) | finish S0/S1 on six cases (Prague, Magna, Maple Creek done; Kīlauea running; then Kaikōura, Ridgecrest); score, swap, blind audit, second-rater check. In parallel without compute: tier table (research plan §2.2), freeze the usability criteria (below), intervention coding (`01_Expert_Experience_and_Checker.md` §5) | 6 left | ~1 week, single queue, 5–8 h per run |
| B | build the checker CLI and the knowledge skill; skill delivery in the runner; checker contract and scorer verification; debug on pilot runs (not counted) | 0 formal | 3–5 days |
| C | S2 and S3 on six cases; S1 repeats on Prague and Magna; second model S1/S3 on three cases; optional `tools + checker` on three | ~25 | ~7–8 days single queue |
| D | analysis, figures, writing | — | — |

## 3. Usability criteria (draft — freeze before the first S2 run)

Summary layer over metrics v1 outputs; no metric definition changes. A case × stage run is **usable** when all hold against the primary references:

| Dimension | Criterion |
|---|---|
| completion | contract-valid catalog |
| detection | `recall_norm` ≥ 0.9 × final |
| precision | `audited_false_rate` ≤ 2 % |
| absolute location | `shift` ≤ 1 km and ≤ final + 0.5 km |
| depth | \|`dz_median`\| ≤ 0.5 km; `depth_mode_share` ≤ 5 % |
| magnitude | \|median `dmag`\| ≤ 0.2; all M ≥ 4 events present |

Per-case exceptions are allowed only where the final itself fails a criterion. Example: Kaikōura's frame offset makes the location criteria relative to the final. Exceptions are written down when the criteria are frozen. Frozen criteria are added to `03_EVALUATION_METRICS.md` §11 as a reporting convention.

## 4. Open items

- Second model and harness choice (research plan §2.6).
- Held-out case: whether, and which (research plan §2.6).
- The task-level `VARIANTS.md` files still list `guided` as the knowledge arm (Q3). Update them when S2/S3 task files are added in Phase B.
- Data-level `processing.yaml` files still record `window_status: not_frozen`; the evaluation windows are fixed by metrics v1 ([`CASE_REGISTRY.md`](../../data/CASE_REGISTRY.md)). Decide whether to mark the data windows frozen.
