# Research documents

Reading order:

| Document | Holds | Changes when |
|---|---|---|
| [`00_Research_Plan.md`](00_Research_Plan.md) | the benchmark design, defined once: core questions, case tiers, Agent stages S0–S3, form of the knowledge and the checker, controls, leakage rules, reference principles, expected outputs | the design changes |
| [`01_Expert_Experience_and_Checker.md`](01_Expert_Experience_and_Checker.md) | evidence that expert catalogs need experience (expert ladder, out-of-range choices, component swap), the reference-free checker rules, human-in-loop intervention coding | new evidence or checker rules |
| [`02_Paper_Outline.md`](02_Paper_Outline.md) | the paper's question, claims with the evidence each needs, sections and figures | the paper plan changes |
| [`03_Scoring_Method.md`](03_Scoring_Method.md) | how a catalog is scored, step by step, from completion to the trusted-catalog verdict, with a worked example; the evaluation section of the paper | the metrics change |
| [`progress/STATUS_AND_PLAN.md`](progress/STATUS_AND_PLAN.md) | current status with the trusted-catalog verdicts, work plan, open items | continuously |
| [`progress/SCORE_TABLE.md`](progress/SCORE_TABLE.md) | the complete score table for every case and run, generated from the tracked score files (`catalog_metrics table`) | after every scored run |
| [`progress/`](progress/) `YYYY-MM-DD_progress_summary.md` | dated progress summaries (Chinese) | one per report, not edited afterwards |

[`research_map.html`](research_map.html) is a one-page Chinese overview (research questions, stage ladder, case progress, work plan) for viewing in a browser; update it together with `progress/STATUS_AND_PLAN.md`.

`assets/` holds figures used by these documents and the repository README.

Elsewhere: case and data documents in [`../data/`](../data/), evaluation metrics and run contracts in [`../framework/`](../framework/).

Writing rule: one line per paragraph or list item; no manual line wrapping.
