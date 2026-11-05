# Research documents

Reading order:

| Document | Holds | Changes when |
|---|---|---|
| [`00_A_Research_Plan_Benchmark.md`](00_A_Research_Plan_Benchmark.md) | research plan A, the fallback line: a benchmark of Agents and models on earthquake-catalog construction and of how much tools and knowledge matter; needs breadth (at least 10 cases, several models and harnesses) (Chinese) | the benchmark design changes |
| [`00_B_Research_Plan_Checker.md`](00_B_Research_Plan_Checker.md) | research plan B, the main line: encoding seismologists' experience as automated checks (and knowledge) so that a general Agent checks and repairs the catalogs it builds, toward high-precision catalogs; why such catalogs matter, applications, lessons for similar work; needs depth (the six cases, Claude Code only) (Chinese); the evidence tables are in [`progress/expert_experience_evidence.md`](progress/records/00_expert_experience_evidence.md) | the checker plan changes |
| [`01_Register.md`](01_Register.md) | the register: every piece of work the two plans need (shared basis C1–C9, plan B B1–B17, plan A A1–A9) with what it produces and its status; the formal experiment plan to be frozen; open decisions; deviation log (Chinese) | as work is done; the experiment plan only through the deviation log once frozen |
| [`02_Checker_Design.md`](02_Checker_Design.md) | the reference-free checker as it stands: principles, every check with its computation, threshold and the evidence behind it, what it can and cannot see, lessons, versions (Chinese) | the checker changes |
| [`reference/notes/`](reference/notes/README.md) | full-text reading notes on agent research (MLE-STAR, AI Scientist-v2, R&D-Agent, CRITIC, VerifiAgent, ScienceAgentBench, ABE-Ralph, TRACE, …) and a synthesis for the pilot protocol, the checker organisation and replay | new papers are read |
| [`reference/seismology_qc/`](reference/seismology_qc/README.md) | literature reviews of how seismologists judge each stage (data, picking, association and detection, location and relocation, magnitude and catalog) and whether anomalies can be attributed (tiers A/B/C), with the checks the checker lacks and the papers to download | new papers are read |
| [`progress/`](progress/README.md) | results and validation records: the current results summary, the generated score table and overview, checker validation rounds 01–10, back-end audits, topical analyses, archived status documents (Chinese) | as results come in |

[`research_map.html`](research_map.html) is a one-page Chinese overview (research questions, stage ladder, case progress, work plan) for viewing in a browser; it predates the register (`01_Register.md`) and is not kept up to date.

`assets/` holds figures used by these documents and the repository README.

Elsewhere: case and data documents in [`../data/`](../data/), evaluation metrics and run contracts in [`../framework/`](../framework/).

Writing rule: one line per paragraph or list item; no manual line wrapping.
