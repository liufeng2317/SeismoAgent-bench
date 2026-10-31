# The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search

- Authors: Yutaro Yamada, Robert Tjarko Lange, Cong Lu, Shengran Hu, Chris Lu, Jakob Foerster, Jeff Clune, David Ha (Sakana AI, UBC, Vector, Oxford)
- arXiv: 2504.08066, version read: v1 (10 Apr 2025)
- URL: https://arxiv.org/abs/2504.08066; code https://github.com/SakanaAI/AI-Scientist-v2 (main branch read on 2026-10-31: `bfts_config.yaml`, `ai_scientist/treesearch/agent_manager.py`, `parallel_agent.py`, `journal.py`)
- Reading: full text of Sec. 1–5 and appendices on prompts/runtime, plus the code paths that implement stage transitions and node selection.

## Earlier claim under review

[claimed: progressive agentic tree search directed by an experiment-manager agent, stages initial implementation → baseline tuning → creative research → ablation] — Correct. The paper calls the stages "Preliminary Investigation / Hyperparameter Tuning / Research Agenda Execution / Ablation Studies"; the code's internal names are `initial_implementation`, `baseline_tuning`, `creative_research`, `ablation_studies`. The paper says "experiment progress manager".

## What the paper says (and what the code does)

### What triggers a stage transition

- Sec. 3.2.1 gives the stage rules: "Stage 1 concludes when a basic working prototype is successfully executed. Stage 2 ends when experiments stabilize, as indicated by convergence in training curves and successful execution across at least two datasets. Stages 3 and 4 conclude when the allocated computational budget is exhausted."
- Stage 3 also checks run duration: "if runs finish much faster than the pre-allocated runtime, the system suggests increasing the complexity of experiments."
- Code: `_check_stage_completion` in `agent_manager.py` implements these rules.
  - Every stage ends at its `max_iterations` cap.
  - If Stage 1 hits the cap without a working node, the whole run aborts ("Could not find working implementation").
  - Stage 2 completion is decided by an LLM call. It receives the VLM's feedback on the best node's plots and the list of datasets tested, with the stated requirements "Training curves should show stable convergence / Results should be tested on at least two datasets / No major instabilities or issues in the plots".
  - Stages 2 and 3 cannot complete if the best node is still the seed node ("No improvement found from the base node").
  - In Stage 3, once more than half the iterations are used, a best node that ran for less than half the 60-min timeout gets the feedback "Implementation works but runs too quickly ... Make sure to scale up the experiment".
  - Stage 4 simply runs to the cap.
- Sub-stages within a stage also end by LLM judgement (`_check_substage_completion`) or by the iteration cap.
- Default caps (`bfts_config.yaml`): stage1 20, stage2 12, stage3 12, stage4 18 iterations; 4 parallel workers; 3 drafts; debug probability 0.5; max debug depth 3; per-run timeout 3600 s.

### How nodes are evaluated and selected

- Each node records the plan, code, error trace, runtime, metrics, LLM feedback after execution, the plotting script, figure paths, VLM feedback, and a buggy/non-buggy status (Sec. 3.2.2).
- A node becomes buggy if it hits an execution error or if "Any issues flagged by the VLM (such as unclear labels, missing legends, or misleading visualizations)" are found. The VLM review is therefore part of the bug gate, not just presentation.
- Expansion policy: "With a predefined probability, a buggy node is chosen ... otherwise, a non-buggy node is selected." Among non-buggy nodes, "best-first search strategy, guided by an LLM that evaluates candidates based on factors like performance metrics, training dynamics, and the quality of generated plots."
- Code (`journal.get_best_node`): an LLM receives each candidate's metric, analysis and VLM feedback summary and selects one. A metric-only mode (`use_val_metric_only`) exists but is not the default.
- Between stages: "the experiment manager selects the best-performing node using a dedicated LLM evaluator ... This selected node is then carried forward to seed the subsequent experimentation stage."

### Replication and seeds

- "the experiment manager launches multiple replications of the selected best experiments at the conclusion of each stage. These repeated runs provide statistics (mean and standard deviation)" (Sec. 3.2.1).
- Replication nodes "execute replicates of their parent experiments using different random seeds". Aggregation nodes plot means and standard deviations. The config default is `multi_seed_eval.num_seeds: 3`.
- At the meta level, each workshop idea was run several times with different seeds and humans picked the best manuscript (Sec. 4.1). The paper calls this "meta-selection from fully autonomous outputs".

### Buggy vs. non-buggy handling

- Buggy nodes get debug children, using the stored error; non-buggy nodes get refinement children (Fig. 2 caption).
- Hyperparameter nodes and ablation nodes track previously tried settings to avoid repeats, and errors in them spawn debug nodes.
- Code: a buggy node can be debugged only while it is a leaf with `debug_depth <= max_debug_depth`. Trees in which every leaf is buggy are dropped from the viable set.

### Compute-budget management

- Explicit but coarse. The budget is controlled by per-stage iteration caps, a per-experiment timeout, parallel workers, and an overall runtime limit ("several hours to a maximum of 15 hours, which is the runtime limit we have set", appendix).
- There is no cost model and no subset-first policy. The direction is the reverse: Stage 1 prompts ask for a "simple dataset" and "basic functional correctness" (code `main_stage_goals`), and Stage 3 pushes for bigger runs if they are too fast. Small runs are used to get something working, and scale is added later; whether early-stage conclusions hold at the larger scale is never checked.

### Reported limitations relevant to us

- In their own review of the accepted paper, the authors found "the caption of Figure 3 incorrectly interpreted validation loss, and Figure 5's attention-based model clearly outperformed the LSTM model, contradicting the authors' claims" (Sec. 4). So the LLM and VLM gates did not catch claim–evidence mismatches.

## Implication for us

- This is the closest precedent for a stage-gated pipeline with explicit stopping criteria and a "best node seeds the next stage" rule. Our pipeline stages (pick → associate → locate → relocate → magnitude) differ in kind: they are sequential processing stages, not research phases. The analogy is gate design, not stage content.
- Its gates are mostly LLM or VLM judgements over metrics and plots. Our checker is meant to be reference-free but tool-computed (numeric symptoms per stage), which is a different reliability class; CRITIC (see `critic.md`) is the argument for preferring it.
- The scale-up nudge shows that the system knows early runs are small but has no rule for validating them at scale. That gap is what our pre-registered adoption rules, freeze and full-scale re-check address.
- Replicating the best node per stage with seeds is a cheap robustness check we could mirror. One example: re-running the frozen configuration on a second pilot window before freezing.
