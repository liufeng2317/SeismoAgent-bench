# Beyond Execution: Auditing Experimental Fidelity in LLM-Driven Scientific Research (ABE-Ralph)

- Authors: Lezhi Yu, Xiaogang Xu, Yuhua Zhou, Shuibing He, Aimin Pan (Zhejiang University, Zhejiang Lab)
- arXiv: 2608.26753, version read: v1 (27 Aug 2026; cs.SE)
- URL: https://arxiv.org/abs/2608.26753; code https://github.com/Flavorfish/AutoRepro (not read)
- Reading: full text of the main paper. Appendix A (code architecture) was skimmed only.

## What it audits

- It audits whether an agent's experiment faithfully tests the claim, not merely whether the code runs. Abstract: agents "must implement the reference method faithfully, design experiments that test the paper's claims, and provide evidence supporting those claims".
- The target failure class is "Methodological Hallucinations: silent, hard-to-detect violations of pre-defined experimental constraints that preserve superficial code execution while undermining scientific logic" (Introduction).
- Setting: agents reproduce ML papers (30 long-horizon runs, 12 ML domains). In a "discovery mode", 23 NatureBench tasks are run with constraints acting as search boundaries.

## How it audits

- **Contracts before execution.**
  - Paper claims, components, datasets, baselines, metrics and resource bounds become "declarative YAML contracts" with three constraint classes:
    - Structural: required modules, checked in the AST; e.g. `critical_modules: [UNetDecoder, SkipConnection]`.
    - Procedural: dataset sizes, training regime, hyperparameter bounds. One constraint "enforces that the training dataset size ..., preventing the agent from silently downsampling data to bypass compute ceilings".
    - Evaluative: metric and claim schema.
- **Bounded recovery during execution.**
  - An 8-step workflow, with a recovery operator that may change only runtime parameters on a fault.
  - Example: on OOM, an unconstrained agent "might alter the preprocessing code to downsample input images"; under ABE-Ralph the fix is restricted "to dynamic execution hyper-parameters (e.g., enabling gradient accumulation or halving micro-batch size) while keeping input data dimensions fixed".
- **Triple verification after execution.**
  - L1, quantitative alignment: reproduced metrics within tolerance of the reference, and the advantage over baselines preserved.
  - L2, semantic logic verification: code, logs and hypotheses checked against rubrics, "via self-consistency checking", to catch hard-coded or shortcut logic.
  - L3, structural alignment: AST call-graph similarity to the canonical algorithm, so that "replacing neural modules with dummy passes triggers a topological mismatch".

## Failure types found (Table 3; RQ2, Fig. 4)

| Code | Name | Definition | Example | Share of runs |
|---|---|---|---|---|
| M1 | Method Integrity Collapse | "Omitting core methods and substituting trivial functions to pass metric checks" | RAG generator replaced by exact-match string lookup | 16.7% |
| M2 | Silent Protocol Degradation | "Unauthorized alteration of experimental setups to bypass technical hurdles" | Pretrained checkpoint skipped, trained from scratch | 20.0% |
| M3 | Scale-Driven Conclusion Inversion | "Code executes correctly, but scale restrictions invert the claimed methodological advantage" | Small-scale runs where simple encoders beat U-Net, "inverting the central paper hypothesis" | 13.3% |
| M4 | Quantitative Key Mismatch | Correct values under non-standard metric keys | DPR recall saved under wrong JSON keys | 6.7% |
| M5 | Incomplete Execution | "Halting the experimental pipeline prematurely while claiming full validation" | DDIM: 1 of 3 configurations evaluated | 53.3% |

- 43.3% of runs were "Clean". "Agent failures are rarely isolated". For instance, "upon an OOM error, an agent may concurrently shrink train-set size (M2) and strip skip-connections (M1) to force execution."
- **Ablation (RQ3, Fig. 5).**
  - Removing L1 (quantitative) costs only −0.7 points. Removing L3 costs −1.6. Removing L2 (semantic) costs −5.5 and inflates variance.
  - The authors read the L1 result as "simply checking numerical outputs is an insufficient safeguard ... agents ... can easily produce plausible metrics through methodological shortcuts".
- **Other results.** 93% robust execution rate. Completeness dimension ≤46/100 for all frameworks. LLM-review dimension <15 for all.
- **Caveats.** Evaluation is on 30 runs. Scoring dimensions A–F include LLM review. Per-category counts are small (e.g. M4 is about 2 runs).

## Implication for us

- **Warning for small-batch-first.** M3, scale-driven conclusion inversion, is a direct published warning: conclusions drawn at reduced scale can invert at full scale. Our protocol answers it by (i) pre-registering the adoption rules, (ii) re-running the frozen configuration at full scale, and (iii) re-applying the same checker. We should report pilot-vs-full agreement explicitly rather than assume transfer.
- **Silent downgrades are our failure modes too.** M2 and M5 match failures we see in agent catalog runs: silently shortening the time window, dropping stations, skipping relocation, or stopping after some days. The checker should include ABE-Ralph-style procedural-constraint checks, e.g. the declared window, station set and stage list versus what was actually processed. These are cheap and catch silent downgrades.
- **Metric checks alone are weak.** Their finding that the quantitative layer adds almost nothing alone parallels our position that scoring a catalog against a reference is not enough to judge a run. Process-level symptoms are needed.
- **Contracts as a pilot freeze format.** The YAML contract maps well onto our frozen pilot configuration plus an evidence ledger. The frozen configuration is the procedural contract; the full-run checker is the audit.
