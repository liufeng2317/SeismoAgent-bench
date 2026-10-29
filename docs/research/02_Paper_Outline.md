# Paper outline

Status: outline agreed 2026-10-29. This document holds the paper's question, its claims with the evidence each needs, and the section and figure plan. The design it relies on (case tiers, Agent stages, form of the knowledge and the checker, controls) is defined in the [research plan](./00_Research_Plan.md); progress and the work plan are in [`progress/STATUS_AND_PLAN.md`](./progress/STATUS_AND_PLAN.md).

## 1. Goal and core question

> **Can an agentic approach build high-precision earthquake catalogs automatically — and if not, is the missing piece tools, knowledge, or the ability to validate its own results?**

The paper answers it in four parts:

1. **Cases in tiers.** Six cases, from basic to hard, across induced, swarm, volcanic, moderate and large mainshock–aftershock, and complex multi-fault settings ([research plan](./00_Research_Plan.md) §2.2).
2. **Tools.** What a validated tool library adds to a general Agent (S0 → S1).
3. **Knowledge.** What case-agnostic expert knowledge, given up front, adds on top of tools (S1 → S2).
4. **Improving agentic catalogs.**
   - *Human-in-loop iteration*: the human-in-loop final is the upper bound; coding each human intervention shows which of them could be automated ([`01_Expert_Experience_and_Checker.md`](./01_Expert_Experience_and_Checker.md) §5).
   - *Expert experience as automated validation*: a reference-free checker run on the Agent's own products, with the Agent required to repair upstream (S2 → S3), and how much of the S1-to-final gap it closes.

## 2. Claims and the evidence each needs

| Claim | Evidence | Status |
|---|---|---|
| Difficulty rises across the tiers | tier features (research plan §2.2) and expert difficulty: rounds, blind → final gap, ceiling | features to tabulate |
| Tools are necessary | S0 vs S1 on six cases: completion, recall_norm, recall_tight, structure, pick timing | Prague, Magna, Maple Creek, Kīlauea scored; Kaikōura running |
| Tools are not sufficient | S1 vs final: no tools run reaches the trusted-catalog standard; space and strength fail on back-end choices the expert locator removes (swap); 22–51 % of the final's events recovered | four cases scored |
| Knowledge helps, and where | S2 vs S1 per dimension and tier | not started |
| Automated validation closes the gap | S3 vs S2; gap closure (S3 − S1)/(final − S1) per dimension | not started |
| Part of the final is unreachable without references | human-in-loop intervention coding (`01_Expert_Experience_and_Checker.md` §5); expert ladder | ladder done; coding not started |
| A trusted catalog is (or is not) reached | trusted-catalog verdict (metrics v2 §7a): reality, time, space, strength by accuracy and stability; completeness apart | none of 8 S0/S1 runs trusted; Kīlauea tools fails only on a −0.36 s time bias (audit pending) |

## 3. Sections and figures

1. **Introduction** — agentic science; earthquake catalogs as a complete, objectively testable task.
2. **Benchmark** — six tiered cases; multiple references and the ceiling; the human-in-loop final as the upper bound.
3. **Evaluation** ([`03_Scoring_Method.md`](03_Scoring_Method.md)) — catalog metrics v2 (gates at the sequence scale, chance correction, direct comparison with the final); shift/scatter decomposition; component swap; blind audit; trusted-catalog verdict by dimension, completeness apart. Include the v1 → v2 lesson: a headline that hides a scattered catalog.
4. **Results I: tools** — S0 vs S1 (necessary, not sufficient).
5. **Results II: knowledge** — S1 vs S2 by dimension and tier.
6. **Results III: human-in-loop iteration** — expert ladder; intervention coding.
7. **Results IV: automated validation** — S3; gap closure; checker use and dispositions; in-sample vs out-of-sample rules.
8. **Discussion** — which catalog dimensions an Agent can be trusted with, in which settings; what still needs a human or a reference.

| Figure | Content |
|---|---|
| 1 | benchmark overview and case map with tiers |
| 2 | heat map: case × stage × dimension, normalised to the final |
| 3 | gap-closure waterfall S1 → S2 → S3 → final per tier |
| 4 | component swap (front end vs back end) |
| 5 | human-in-loop ladder and intervention classes |
| 6 | checker use: flags raised, fixed, justified, missed |
