# Research documents

Reading order:

| Document | Holds | Changes when |
|---|---|---|
| [`00_Research_Plan_Benchmark.md`](00_Research_Plan_Benchmark.md) | research plan A, the fallback line: a benchmark of how far Agents build earthquake catalogs on their own (question, cases and tiers, Agent stages, scoring, validity, outputs, status) (Chinese) | the benchmark design changes |
| [`01_Research_Plan_Checker.md`](01_Research_Plan_Checker.md) | research plan B, the main line: expert experience written as a reference-free checker and knowledge skill (question, grounds, design, how it is tested, status, risks) (Chinese); the evidence tables are in [`progress/expert_experience_evidence.md`](progress/expert_experience_evidence.md) | the checker plan changes |
| [`02_Paper_Outline.md`](02_Paper_Outline.md) | the paper's question, claims with the evidence each needs, sections and figures, a summary of current results, progress, and the pre-registered analysis plan (Chinese) | the paper plan changes, results come in, or the analysis plan is frozen |
| [`03_Scoring_Method.md`](03_Scoring_Method.md) | how a catalog is scored, step by step, from completion to the trusted-catalog verdict, with a worked example; the evaluation section of the paper | the metrics change |
| [`04_Checker_Design.md`](04_Checker_Design.md) | the reference-free checker as it stands: principles, every check with its computation, threshold and the evidence behind it, what it can and cannot see, lessons, versions (Chinese) | the checker changes |
| [`reference/notes/`](reference/notes/README.md) | full-text reading notes on agent research (MLE-STAR, AI Scientist-v2, R&D-Agent, CRITIC, VerifiAgent, ScienceAgentBench, ABE-Ralph, TRACE, …) and a synthesis for the pilot protocol, the checker organisation and replay | new papers are read |
| [`reference/seismology_qc/`](reference/seismology_qc/README.md) | literature reviews of how seismologists judge each stage (data, picking, association and detection, location and relocation, magnitude and catalog) and whether anomalies can be attributed (tiers A/B/C), with the checks the checker lacks and the papers to download | new papers are read |
| [`progress/STATUS_AND_PLAN.md`](progress/STATUS_AND_PLAN.md) | current status with the trusted-catalog verdicts, work plan, open items | continuously |
| [`progress/checker_validation/`](progress/checker_validation/README.md) | each round of checker validation with its method, data and readings, numbered by date (Chinese); the design document links here | after each validation round |
| [`progress/RESULTS_OVERVIEW.md`](progress/RESULTS_OVERVIEW.md) | one page: the case × configuration matrix and one row per run with its headline numbers and standard figures, generated with the score table | after every scored run |
| [`progress/SCORE_TABLE.md`](progress/SCORE_TABLE.md) | the complete score table for every case and run, generated from the tracked score files (`catalog_metrics table`) | after every scored run |
| [`progress/`](progress/) `YYYY-MM-DD_progress_summary.md` | dated progress summaries (Chinese) | one per report, not edited afterwards |

[`research_map.html`](research_map.html) is a one-page Chinese overview (research questions, stage ladder, case progress, work plan) for viewing in a browser; update it together with `progress/STATUS_AND_PLAN.md`.

`assets/` holds figures used by these documents and the repository README.

Elsewhere: case and data documents in [`../data/`](../data/), evaluation metrics and run contracts in [`../framework/`](../framework/).

Writing rule: one line per paragraph or list item; no manual line wrapping.
