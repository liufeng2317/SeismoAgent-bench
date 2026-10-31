# AIDE: AI-Driven Exploration in the Space of Code

- Authors: Zhengyao Jiang, Dominik Schmidt, Dhruv Srikanth, Dixing Xu, Ian Kaplan, Deniss Jacenko, Yuxiang Wu (Weco AI)
- arXiv: 2502.13138, version read: v1 (18 Feb 2025)
- URL: https://arxiv.org/abs/2502.13138; code https://github.com/WecoAI/aideml (`aide/agent.py`, main branch read on 2026-10-31)
- Reading: full text (Sec. 1–5 and appendices). Code checked for how bugs and metrics are decided, because the paper does not spell this out.

## Earlier claim under review

None was specified. Questions: Draft/Debug/Improve policy, use of the evaluation signal, data subsets or cheap proxies.

## What the paper says

### Draft / Debug / Improve policy (Sec. 3.2)

- "the search policy ... follows a simple hard-coded rule". It chooses:
  - "Drafting if we have not yet reached the desired number of initial solutions."
  - "Debugging if a buggy node remains within a certain debug depth."
  - "Improving otherwise, typically targeting the best (non-buggy) solution."
- Rationale: "1) first exploring a set of diverse initial solutions and continuously improving the best one, and 2) constraining the number of debug attempts for a broken solution."
- Improve step: "the LLM proposes exactly one 'atomic' change, such as switching optimizers or adding a regularization technique, so that its effect on performance is directly measurable." This is a one-factor-at-a-time discipline.
- Code (`search_policy`): fill `num_drafts` first; then, with probability `debug_prob`, pick a random buggy leaf with `debug_depth < max_debug_depth`; otherwise improve the greedy best node (`journal.get_best_node()`).

### How the evaluation signal is used

- Each node is scored by a scalar validation metric that the generated script itself computes on its own train/validation split (Sec. 3.1, 4.1).
- The summarisation operator feeds back "Performance metrics", "Hyperparameter settings if a solution involves a hyperparameter sweep" and "Relevant hints for debugging" rather than full logs (Sec. 3.2).
- Code (`parse_exec_result`): an LLM reads the code and terminal output and returns `is_bug`, a summary, the validation `metric` and `lower_is_better` (function `submit_review`). A node counts as buggy if the LLM says so, if an exception occurred, or if the metric is missing or NaN. Buggy nodes get the worst metric value.
- So the metric is the LLM's reading of stdout from a split chosen by the agent. Nothing independent checks that the split or metric is sound.
- The authors note the risk: hyperparameter search by brute force carries "a risk of overfitting to the validation set" (Sec. 2).
- In their own benchmark, the evaluation holdout is separate from the agent's internal split: "our holdout test set is also distinct from the train-validation split that AIDE itself generates as part of its internal node evaluation protocol" (Sec. 4.1).

### Subsets and cheap proxies

- None in the method. The only related mechanism is a static "data preview" in prompts (rows, columns, splits), which "helps AIDE guide key code decisions ... selecting a validation split or scaling hyperparameters" (Sec. 3.2).
- Prompts tell the coder that the script "should complete within" the execution timeout (code), which acts as an implicit cost cap.
- "Weco-Kaggle Lite" (16 tasks) and "MLE-bench Lite" are benchmark subsets used for evaluation, not proxies used inside the agent.
- Cost: under ~$2.50 per task with GPT-4 Turbo (App., Fig. 7).

### Reported failure mode

- On METR's RE-Bench, "AIDE managed to surpass human scientists within six hours ... However, human scientists eventually caught up, as AIDE adopts a simple greedy policy that may lead to local optima on challenging R&D tasks" (Fig. 4 caption).

## Implication for us

- AIDE is the baseline design that MLE-STAR, AI Scientist-v2 and R&D-Agent all extend: a tree of scripts, greedy improvement on one validation number, and a capped debug depth.
- The "one atomic change per step so its effect is measurable" rule is a useful citation for our pilot-tuning discipline: change one parameter group per pilot iteration and record the checker delta.
- AIDE's bug and metric decisions come from an LLM reading stdout. Our checker computes symptoms with tools from intermediate products. That is the contrast to draw, with CRITIC for why it matters.
- AIDE offers no precedent for small-batch-first. It runs everything at full data size within a timeout.
