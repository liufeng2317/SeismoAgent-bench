# Multi-fidelity and cheap-proxy experimentation: JoBS ("Chicken and Egg"), AutoLLMResearch, LABO

## Papers

- **(a1) arXiv 2602.08351.** v1/v2 title: "The Chicken and Egg Dilemma: Co-optimizing Data and Model Configurations for LLMs". v3 title (28 Oct 2026, the version read): "Rethinking Bayesian Optimization for Co-Optimizing LLM Training Configurations". Zhiliang Chen, Alfred Wei Lun Leong, Shao Yong Ong, Apivich Hemachandra, Gregory Kang Ruey Lau, et al. (NUS, A*STAR). https://arxiv.org/abs/2602.08351. Full text of v3 read; v1 grepped for "AutoLLMResearch" and agent terms.
- **(a2) arXiv 2605.11518.** "AutoLLMResearch: Training Research Agents for Automating LLM Experiment Configuration — Learning from Cheap, Optimizing Expensive". Taicheng Guo, Nitesh V. Chawla, Olaf Wiest, Xiangliang Zhang (Notre Dame). Version read: v2 (17 May 2026). https://arxiv.org/abs/2605.11518. Read in full: Sec. 1–6 and the case-study appendix.
- **(b) arXiv 2605.22054.** "LABO: LLM-Accelerated Bayesian Optimization through Broad Exploration and Selective Experimentation". Zhuo Chen, Xinzhe Yuan, Jianshu Zhang, et al., corresponding authors Nanyang Ye and Qinying Gu (Shanghai AI Lab, SJTU, ...). Version read: v1 (21 May 2026). https://arxiv.org/abs/2605.22054. Read in full: Sec. 1–7; the regret appendix was skimmed. The alphaxiv overview id 2605.22054 is the arXiv id itself.

## (a1) arXiv 2602.08351: what it is actually about

- It is not about agents or "principles". It is a Bayesian-optimisation method (JoBS) for jointly optimising an LLM fine-tuning data mixture and the LoRA configuration. The "chicken-and-egg" is that "the optimal data configuration ... depends on the chosen model configuration ... but determining the optimal model configuration also depends on the chosen data configuration" (Sec. 1).
- Mechanism: spend part of the budget on full training runs to fit a neural "performance predictor that estimates fully trained LLM performance from only a small number of training steps". Then run BO in which each candidate is trained only for those few steps and scored by the predictor (Sec. 5). The paper reports that ~10% of the full steps "provides the best balance" (Sec. 6.4).
- AutoLLMResearch: not mentioned in v1 or v3. The earlier citation linking 2602.08351 to AutoLLMResearch was a misattribution.

### When low fidelity transfers, and failure modes (a1)

- Transfer works when an explicit learned mapping from early-training trajectories to final performance exists and is calibrated with some full-fidelity runs. Prediction error is treated as observation noise: "JoBS does not require a perfect performance predictor because the BO framework naturally treats the prediction error as observation noise" (Sec. 5).
- **Failure mode 1, non-monotone trajectories.** Fig. 3: "a good training configuration (green) yields improved performance as training steps increase, whereas a suboptimal training configuration (orange) causes performance to decrease." So freeze-thaw BO's assumption of monotone improvement "breaks down" (Sec. 2).
- **Failure mode 2, fixed-configuration extrapolators don't carry over.** Scaling-law formulas "do not transfer to our setting as they are defined w.r.t. a fixed training configuration" (Sec. 2).
- **Failure mode 3, budget trade-off.** Too few full runs give an inaccurate predictor, too many leave too few BO iterations (Sec. 5.3–5.4, Fig. 6a/b).
- **Failure mode 4, GP-coupled multi-fidelity is too weak.** GP-based multi-fidelity BO (MF-KG, MF-UCB) underperforms because "a GP is often not expressive enough to jointly model the relationship between fidelities" (App. B).

## (a2) AutoLLMResearch: checking the claim

[claimed: learns principles from low-fidelity experiments and extrapolates to expensive settings] — Correct as a description of this paper's stated aim. Abstract: "an agentic framework that mimics how human researchers learn generalizable principles from low-fidelity experiments and extrapolate to efficiently identify promising configurations in expensive LLM settings."

- **Mechanism.**
  - LLMConfig-Gym is "a multi-fidelity environment encompassing four critical LLM experiment tasks, supported by over one million GPU hours of verifiable experiment outcomes".
  - A Qwen3-4B agent is trained with trajectory simulation, policy distillation and multi-turn RL to propose high-fidelity configurations given low-fidelity results. Example: "extrapolating from 3B / 10B-token experiments to 7B / 20B-token ones".
  - It is a trained agent over a precomputed table of results, not a protocol applied to live runs.
- **Conditions for transfer.** Two kinds of cross-fidelity shift are defined (Sec. 1):
  - "Configuration Space Shift: The configuration space differs between training (low-fidelity) and target (high-fidelity) experiments";
  - "Optimization Landscape Shift: Even within the same configuration space, the optimization landscape changes across fidelity levels, and optimal configurations do not necessarily transfer monotonically."
  - What transfers is a trend rather than an optimum: "what transfers across the optimization-landscape shift is a fidelity-dependent scaling trend" (Case Study 2, e.g. the learning rate decreases with parameter count).
- **Failure modes reported.**
  - Directly reusing the low-fidelity optimum ("Top-k WS") "underperforms ... confirming that the landscape has shifted and simple configuration transfer is insufficient" (Sec. 5.1.1).
  - An untrained base LLM given low-fidelity context "extrapolates in the wrong direction ... incorrect extrapolation can be worse than no extrapolation at all" (App. C.3 / Sec. 5.2.2).
  - Stress tests: with too few low-fidelity experiments ("Ultra-low", 20%), or with low-fidelity optima reversed relative to the target, regret rises for all methods. Theirs "degrades at 'Ultra-low' but recovers quickly" once non-adversarial data are mixed in (Sec. 6, "Stress-Testing the Boundary of Low-to-High Extrapolation", Result 10).

## (b) LABO: gating rule for running an expensive real experiment

- **Setup.** Dual-fidelity BO. LLM predictions are a cheap fidelity f_L, and real experiments are the expensive fidelity. A Kennedy–O'Hagan surrogate is used, f_R(x) = ρ f_L(x) + δ(x), with δ a discrepancy GP (Sec. 4.1).
- **Gate (Sec. 4.2).** "discrepancy dominance ratio" p_Δ(x) = σ_δ²(x) / (ρ² σ_L²(x) + σ_δ²(x)). "If p_Δ(x) ≤ τ, the LLM-fidelity prediction is deemed reliable and used to update the joint surrogate ... Otherwise, LABO performs a real-fidelity experiment". Equivalently, "LABO triggers an experiment only when the surrogate uncertainty is dominated by the discrepancy".
- **Settings.** τ = 0.75, "the same fixed threshold across all main experiments". 50 LLM-fidelity evaluations at warm-up. Five seeds (Sec. 6.1).
- **Conditions for transfer.** Transfer holds when the LLM's predictions correlate with reality, so that the discrepancy variance stays small. ρ is re-estimated by least squares on paired observations, and the discrepancy GP absorbs input-dependent bias. "LABO finds better candidates under the same real-fidelity budget when LLM predictions are helpful, and matches vanilla BO when they are not" (Sec. 1). The regret guarantee holds "under the KOH modeling assumptions".
- **Failure modes and ablations (Sec. 6.3).**
  - Replacing LLM predictions with random values ("Random-fidelity") "leads to slower convergence and worse final performance".
  - Too high a τ "places too much trust in LLM outputs, which can mislead the search when the LLM predictions are inaccurate"; too low a τ "relies too heavily on real-fidelity evaluations".
  - High-dimensional tasks (COF, 14-D) "require more real-fidelity queries to compensate for LLM uncertainty".

## Implication for us

- **Two transfer paradigms.** These papers formalise two ways to use cheap results:
  - learn a calibrated mapping from cheap to expensive (JoBS predictor, LABO discrepancy model, AutoLLMResearch's learned trends);
  - gate expensive runs on uncertainty about that mapping (LABO).
  
  Our small-batch-first protocol is simpler and different. We do not extrapolate a performance number from pilot to full scale. We freeze parameters chosen on a pilot and then verify at full scale with the same checker. The relevant risk these papers name is landscape shift: a pilot optimum need not be the full-scale optimum, for example in event density, aftershock rate or station coverage.
- **What to report.** Report pilot-vs-full agreement of checker symptoms, not only final scores. Treat a disagreement as a gate in LABO's sense: re-tune at full scale only where pilot and full results disagree.
- **What to claim.** AutoLLMResearch's "trends transfer, optima may not" is a good framing. For example, the direction of a picker-threshold effect on the false-pick rate may transfer while the exact optimal value may not.
- **Novelty boundary.** None of these address processing pipelines or reference-free checking. They are configuration-optimisation methods over scalar objectives with known ground truth.

## Citation corrections

- Do not attribute "learns principles from low-fidelity experiments and extrapolates" to 2602.08351. It belongs to AutoLLMResearch, arXiv 2605.11518.
- 2602.08351 changed title in v3. Cite it with the version actually used: v1/v2 "The Chicken and Egg Dilemma: Co-optimizing Data and Model Configurations for LLMs" or v3 "Rethinking Bayesian Optimization for Co-Optimizing LLM Training Configurations".
- LABO is arXiv 2605.22054. The alphaxiv overview id is the same.
