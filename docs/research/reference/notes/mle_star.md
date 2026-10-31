# MLE-STAR: Machine Learning Engineering Agent via Search and Targeted Refinement

- Authors: Jaehyun Nam, Jinsung Yoon, Jiefeng Chen, Jinwoo Shin, Sercan Ö. Arık, Tomas Pfister (Google Cloud, KAIST)
- arXiv: 2506.15692, version read: v3 (28 Aug 2025)
- URL: https://arxiv.org/abs/2506.15692 (HTML https://arxiv.org/html/2506.15692v3; PDF used for the prompt figures, which are images in the HTML)
- Reading: full text (main text, appendices A, E, F; prompt Figures 10–27 from the PDF). Cross-checked against the Google ADK reference implementation (google/adk-samples, commit 9bf35ee, `python/agents/machine-learning-engineering`).

## Earlier claim under review

[claimed: uses a subset of training samples for faster refinement, removes subsampling for the final submission] — Correct, but the claim is thinner than it sounds: the subset is a hard-coded size cap written into a prompt, not a designed pilot, and nothing checks that conclusions drawn on the subset hold on full data.

## What the paper says

### How the subset is chosen and sized

- The only sizing rule is in the prompt for the candidate-evaluation agent (Fig. 10, App. A.2) and the merging prompt (Fig. 11): "If there are more than 30,000 training samples, you must subsample to 30,000 for a faster run."
- The prose of App. A.2 says only: "if there are too many training samples, A_init uses the subset of training sample for faster execution."
- There is no stratification, no representativeness criterion and no seed control. The LLM writes the subsampling code itself, so how the 30,000 rows are drawn (random, head of file, etc.) is left to the generated script.
- Later prompts keep the subset in place. The refinement coder prompt (Fig. 15) says "Implement the improvement plan on the above code block. But do not remove subsampling if exists." The debugging prompt (Fig. 19) says "Do not remove subsampling if exists."
- The ensemble-implementation prompt points the other way: "Do not subsample or introduce dummy variables" (Fig. 18). The paper does not discuss whether ensemble scores are therefore on full data while the refinement scores were on the subset.

### When and how subsampling is removed

- Removal happens only at submission time (App. E.3, "Removing subsampling"): "MLE-STAR uses the subset of training sample for faster refinement (since evaluating the solution candidate can take a lot of time). However, in order to get a better performance, when generating a submission file MLE-STAR removes such subsampling code."
- The mechanism has two LLM steps. One prompt extracts "a code block where subsampling of training samples is used" (Fig. 26). A second rewrites it to "Remove the subsampling and make it to use full training samples" (Fig. 27).
- The paper reports no validation score after subsampling is removed. The final full-data model is scored only by the Kaggle test grader.

### Does the paper test transfer from subset to full data?

- No. The paper has no ablation of subsampling (on vs. off, or different sizes) and no report of how often the ranking of candidates on the subset matched their ranking on full data. Subsampling appears only in Appendices A and E.
- It does document a related generalisation failure, but one caused by leakage rather than subsampling. Table 5 (spaceship-titanic) shows validation accuracy 0.8188→0.8677 while test accuracy fell 0.8033→0.7343, "attributed to the LLM performing feature engineering using the target variable Transported" (Sec. 5). The text cites this as "Table 6", which is a labelling slip in the paper.

### Other verification modules and their triggers (Sec. 3.4)

- **Debugging agent.** Triggered by an execution error (traceback). Runs "until either the script executes successfully, or a predefined maximum number of debugging rounds is reached". If the bug persists, "MLE-STAR proceeds to the next task using the latest version of the script that is known to be executable."
- **Data leakage checker.** Runs on every solution before it executes: "All generated solutions are passed through a data leakage checker ... prior to their execution for evaluation." To keep it targeted, it first extracts the preprocessing code block, asks whether it leaks, and replaces the block with a corrected one if so (App. A.12, Figs. 20–21).
- **Data usage checker.** Runs once, "before MLE-STAR starts refinement". It compares the initial script with the task description and revises the script if provided data is unused. Table 6 (nomad2018): RMSLE improves 0.0591→0.0559 when the checker is on, because `geometry.xyz` had been ignored.
- **Ablation-study agent (targeted refinement, Sec. 3.2).** Not a checker, but closely related to our design. In each outer step the agent writes and runs an ablation script that disables or modifies pipeline components. It then summarises the results and picks "the code block ... whose modification had the most significant impact on performance" as the next block to refine. Earlier ablation summaries and already-refined blocks are passed in so that the agent explores different parts of the pipeline.
- **Compute.** Four retrieved models, four inner and four outer loops, and five ensemble rounds take 14.1 h per solution on average, against 15.4 h for AIDE, under a 24 h cap (App. F).

## Implication for us

- MLE-STAR is precedent for running a cheap subset during search and then the full data for the final product. It is not precedent for a validated pilot protocol. Its subset rule is a size cap in a prompt; it has no representativeness criterion, no frozen parameter set and no full-scale validation step. Our small-batch-first protocol adds exactly these: a representative pilot, pre-registered adoption rules, a freeze, and the same checker re-run at full scale.
- In MLE-STAR, removing the subsample is itself an unverified LLM code edit. In our protocol, moving from pilot to full run should change only the input window, not code or parameters, so that the pilot-to-full step is replayable.
- The leakage checker is a good model for one checker pattern: extract the relevant block, then judge it narrowly. Its trigger rule, "always before execution", is a reasonable template for cheap static checks in our stage checker.
- The ablation agent picks which block to refine by measured sensitivity. This parallels using the checker's per-stage symptoms to decide which pipeline stage to retune.
- The leakage case (validation up, test down) is a usable citation for "optimising the in-loop metric can silently diverge from the held-out target". It is a leakage failure, not a subset-transfer failure.
