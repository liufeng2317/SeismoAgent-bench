# Literature reading notes (full text), 2026-10-31

These notes come from reading the full texts. They replace the earlier citations, which were based on abstracts only. Each note gives the full title, the authors, the arXiv id and the version read, and states whether the text was read in full. It separates "what the paper says" from "implication for us". PDFs and HTML were kept outside the repository, in the session scratchpad.

## Index

| Note | Paper(s) | arXiv (version read) | Read |
|---|---|---|---|
| [mle_star.md](mle_star.md) | MLE-STAR | 2506.15692 v3 (+ ADK code) | full |
| [ai_scientist_v2.md](ai_scientist_v2.md) | The AI Scientist-v2 | 2504.08066 v1 (+ GitHub code) | full |
| [aide.md](aide.md) | AIDE | 2502.13138 v1 (+ aideml code) | full |
| [rd_agent_co_steer.md](rd_agent_co_steer.md) | R&D-Agent (v1, v2); Co-STEER; RD-Agent precursor | 2505.14738 v2 and v1; 2407.18690 v1; 2310.11249 v1 | full |
| [multi_fidelity_proxies.md](multi_fidelity_proxies.md) | JoBS ("Chicken and Egg"); AutoLLMResearch; LABO | 2602.08351 v3 (v1 checked); 2605.11518 v2; 2605.22054 v1 | full (LABO regret appendix skimmed) |
| [critic.md](critic.md) | CRITIC | 2305.11738 v4 | full |
| [verifiagent.md](verifiagent.md) | VerifiAgent | 2504.00406 v2 | full |
| [scienceagentbench.md](scienceagentbench.md) | ScienceAgentBench; "Do LLMs Speak Scientific Workflows?" | 2410.05080 v3; 2412.10606 v3 | full |
| [beyond_execution_abe_ralph.md](beyond_execution_abe_ralph.md) | Beyond Execution (ABE-Ralph) | 2608.26753 v1 | full main text; code appendix skimmed |
| [trace.md](trace.md) | TRACE | 2603.21152 v4 | full main text and Methods; supplementary figures not inspected |
| [seismology_pilot_precedent.md](seismology_pilot_precedent.md) | QuakeFlow, FAST (Yoon 2019), Durrës, SeisBench picker benchmark, Kefalonia, plus unverified leads | 2208.14564, 2205.12033, 2110.13671, 2505.17221; Yoon 2019 BSSA PDF | full for those listed as read; others snippet-only |

No requested paper was unobtainable. The seismology note lists leads that were seen only as search snippets (LOC-FLOW SRL 2022, Mousavi & Beroza 2023, an OSTI report, a Marmara template-matching study). Read them, or ask the user to download them, before citing.

## Synthesis by design question

### (i) Small-batch-first protocol: precedent, novelty boundary, transfer-validation practice

**ML-agent precedent.** Several ML-engineering agents run something small first, but for different purposes:

- R&D-Agent is the strongest precedent. It debugs on "a small, representative subset" (10%, class-preserving, `--debug` mode). It estimates full runtime. "Only validated solutions proceed to full-scale evaluation". Its ablation drops Any-Medal from 34.7% to 24.0% without this.
- MLE-STAR caps training data at 30,000 rows in its prompts during refinement, and an LLM edit removes the cap at submission time.
- AI Scientist-v2 starts on a "simple dataset" and later pushes runs that are "too quick" to scale up.

**What none of them does.** None selects a pilot by stated representativeness criteria, uses pre-registered adoption rules, freezes the configuration, or checks that subset-level conclusions survive at full scale. MLE-STAR ranks candidates on the subsample with no transfer test. R&D-Agent uses the subset for correctness only and decides on full-data scores.

**Cautions from the multi-fidelity literature.**

- JoBS: low-fidelity signals transfer only through a calibrated mapping, and trajectories can be non-monotone.
- AutoLLMResearch: "optimal configurations do not necessarily transfer monotonically"; what transfers are fidelity-dependent trends, and naive reuse of the cheap optimum underperforms.
- LABO: gate the expensive run on how much predictive uncertainty is due to cheap-vs-real discrepancy.
- ABE-Ralph documents "Scale-Driven Conclusion Inversion" in 13.3% of 30 agent runs: small-scale runs inverted a paper's central claim.

**Seismology.** A bounded search found catalog workflows that tune by "trial and error", "several tests", visual inspection or defaults:

- QuakeFlow names the hyperparameter trade-off as future work.
- FAST tuned its most sensitive parameter on the full multi-year dataset and notes that the acceptable value depends on duration.
- No written pilot-window protocol was found, and no measurement of pilot-to-full transfer.

**Novelty boundary.** Our contribution is not "use a subset first". It is the systematised protocol for long, parameter-heavy processing pipelines with no reference:

1. representative pilot;
2. checker-guided tuning under pre-registered adoption rules;
3. freeze;
4. full run;
5. the same checker at full scale, reporting pilot-vs-full agreement.

Duration-dependent parameters are explicitly flagged for re-checking.

### (ii) Checker organisation: tool-grounded verification, two-level checks, knowledge base / experiment ledger

**Tool-grounded evidence.**

- CRITIC is the core citation.
  - LLM self-evaluation discriminates poorly: hallucination-detection AUROC 0.67–0.73, against 0.81–0.83 with tools.
  - Self-correction without external feedback is "marginal" and "unstable" (−0.03 / +2.33 F1; −1.8 on GSM8k for davinci).
  - Self-Refine without an oracle collapsed GSM8k from 71.3 to 26.7.
  - Use the measured form, not "self-correction always fails". Tools can also hurt (SVAMP −3.3).
- The CRITIC vs. CRITIC* (oracle) gap shows that most of the value lies in detecting which outputs are wrong. This argues for the checker as a separate symptom detector.
- AIDE and AI Scientist-v2 decide bug status and quality largely by LLM/VLM reading of stdout and plots. In its own review, AI Scientist-v2 still produced figure claims that contradicted its own results. This is the contrast class for a tool-computed checker.

**Two-level structure.**

- VerifiAgent gives the template: meta verification (completeness, consistency) first, then tool-based verification.
- Ablation: tools add accuracy and precision, meta checks add recall. Without tools, performance is near baseline.
- The gating is prompt-level; we should gate in code.
- ABE-Ralph adds a third axis we need: procedural-contract checks for silent downgrades (data shrunk, components replaced, runs stopped early; M1/M2/M5 occur in 17–53% of runs).
  - Its quantitative-only layer contributed almost nothing (−0.7 when removed). This matches our view that metric agreement alone is insufficient.
  - TRACE's Result Checking Agent supplies the generic seismological check list (file validity, numerical ranges, completeness, spatio-temporal consistency, convergence, plausible statistics). It validates its catalog against existing catalogs, i.e. with a reference.
  - Our checker makes this list stage-specific and reference-free.
- MLE-STAR's leakage and data-usage checkers show the "extract the relevant block, judge narrowly, trigger before execution / once before refinement" pattern for cheap static checks.

**Knowledge base / ledger.**

- Co-STEER stores successful tasks with their full trial→feedback→fix traces and retrieves "based on feedback similarity", not task similarity. This maps directly onto keying our playbooks by checker symptom.
- The RD-Agent precursor (2310.11249) stores each trial as data/model/evaluation/goal embeddings with results on a shared leaderboard. This is a template for the experiment ledger of pilot iterations.
- R&D-Agent v2 found that a generic external RAG knowledge base hurt overall (35.1 → 32.0). Curated, symptom-keyed procedural knowledge must be shown to help by ablation, not assumed.

### (iii) Fast iteration and replay

**Partial precedent in the ML-agent literature.**

- R&D-Agent's debug mode (10% data, minimum epochs, inference on one test sample, printed full-run time estimate) is a cheap correctness tier. Removing it costs a lot.
- AI Scientist-v2 and AIDE keep a node journal (code, logs, metrics, feedback) that allows re-selection without re-running. Neither replays recorded intermediate products to test a downstream change.
- AIDE's "exactly one atomic change ... so that its effect on performance is directly measurable" supports one-factor-at-a-time pilot iterations.

**Evaluation tiers.**

- ScienceAgentBench supplies the argument for evaluation below end-to-end: "we call for rigorous assessment of agents on individual tasks in a scientific workflow before making bold claims on end-to-end automation". Our tiers (offline replay of recorded products → back-end-only tasks → full runs) extend this from single programs to pipeline stages.

**Not found.** No paper in this set builds offline replay of recorded intermediate products as an iteration or evaluation tier. Among these sources it appears novel; a targeted search on "record and replay" in agent evaluation is still advisable.

**Two cautions.**

- Multi-fidelity results warn that cheap tiers must be validated against the full tier on at least some cases.
- ABE-Ralph's M3 shows conclusions can invert with scale.

## Citation corrections

1. **Co-STEER.** Co-STEER is arXiv 2407.18690 (Yang, Chen, Feng et al., 2024, "Collaborative Evolving Strategy for Automatic Data-Centric Development"). arXiv 2310.11249 is a different paper: the 2023 RD-Agent vision paper "Leveraging Large Language Model for Automatic Evolving of Industrial Data-Centric R&D Cycle". It never mentions Co-STEER.
2. **AutoLLMResearch.** "Learns generalizable principles from low-fidelity experiments and extrapolates" belongs to AutoLLMResearch, arXiv 2605.11518 (Guo, Chawla, Wiest, Zhang). arXiv 2602.08351 does not mention AutoLLMResearch. It is a Bayesian-optimisation method (JoBS) for joint data-mixture and LoRA configuration with a learned early-training performance predictor. Its title changed between v2 ("The Chicken and Egg Dilemma: Co-optimizing Data and Model Configurations for LLMs") and v3 ("Rethinking Bayesian Optimization for Co-Optimizing LLM Training Configurations").
3. **ScienceAgentBench, not 2412.10606.** The claim "assess agents on individual workflow tasks before claiming end-to-end automation" is in ScienceAgentBench (arXiv 2410.05080), nearly verbatim. arXiv 2412.10606 (Yildiz & Peterka, "Do Large Language Models Speak Scientific Workflows?") is about LLMs configuring, annotating and translating code for HPC workflow-management systems (Wilkins, ADIOS2, PyCOMPSs, Parsl, Henson) and makes no such argument. Also, ScienceAgentBench's rubrics are per-task, in five program stages (load, process, model/visualise, format, save), and used for human grading. They are not "step rubrics" for workflow steps.
4. **MLE-STAR subset.** The claim is correct but should be stated precisely: the subset is a prompt-level cap ("If there are more than 30,000 training samples, you must subsample to 30,000"), removed by an LLM code edit only when the submission is produced. The paper reports no test that conclusions on the subset transfer to full data. The validation-up/test-down example (Table 5) is a leakage failure, not a subset failure.
5. **CRITIC.** "LLMs unreliable at self-verification" is supported (AUROC table). "Self-correction without tools fails" is overstated: the effect is marginal and mixed, sometimes positive (e.g. ChatGPT +4.5 on GSM8k without the interpreter).
6. **AI Scientist-v2.** The description is correct. The paper's stage names are "Preliminary Investigation / Hyperparameter Tuning / Research Agenda Execution / Ablation Studies" (code: initial_implementation / baseline_tuning / creative_research / ablation_studies), and the component is the "experiment progress manager". Transitions are set by iteration caps plus LLM judgement; for Stage 2, an LLM reads VLM plot feedback.
7. **VerifiAgent.** The two-level description is correct. Note that the "meta first, then tools" order is enforced by the prompt within a single agent, not by a programmatic gate.
8. **LABO.** The arXiv id is 2605.22054, the same as the alphaxiv overview id. Gate: run a real experiment when p_Δ(x) = σ_δ² / (ρ²σ_L² + σ_δ²) > τ, with τ = 0.75 fixed.
