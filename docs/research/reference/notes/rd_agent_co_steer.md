# R&D-Agent and Co-STEER (Microsoft Research Asia)

This note covers three papers. arXiv 2310.11249 is NOT the Co-STEER paper; Co-STEER is arXiv 2407.18690 (see citation correction below).

## Papers

- **R&D-Agent (current).** "R&D-Agent: An LLM-Agent Framework Towards Autonomous Data Science". Xu Yang, Xiao Yang, Shikai Fang, et al. arXiv 2505.14738, version read: v2 (01 Oct 2025). https://arxiv.org/abs/2505.14738. Read in full: Sec. 3–4, App. C, App. E prompts.
- **R&D-Agent (v1).** Same arXiv id, v1 (20 May 2025), with a different title: "R&D-Agent: Automating Data-Driven AI Solution Building Through LLM-Powered Automated Research, Development, and Evolution". A short technical report, read in full.
- **Co-STEER.** "Collaborative Evolving Strategy for Automatic Data-Centric Development". Xu Yang, Haotian Chen, Wenjun Feng, Haoxue Wang, Zeqi Ye, Xinjie Shen, Xiao Yang, Shizhao Sun, Weiqing Liu, Jiang Bian. arXiv 2407.18690, version read: v1 (26 Jul 2024). https://arxiv.org/abs/2407.18690. Read in full: Sec. 3–4, App. B.
- **The paper at 2310.11249.** "Leveraging Large Language Model for Automatic Evolving of Industrial Data-Centric R&D Cycle". Xu Yang, Xiao Yang, Weiqing Liu, Jinhui Li, Peng Yu, Zeqi Ye, Jiang Bian. arXiv 2310.11249, version read: v1 (17 Oct 2023), the only version. https://arxiv.org/abs/2310.11249. Read in full for the knowledge-management section (Sec. 3.1, 4.2). This is the RD-Agent vision/precursor paper. It does not contain the name "Co-STEER" and does not describe Co-STEER's scheduler.

## What the papers say

### Knowledge base: what is stored

- **Co-STEER (Sec. 3.4.1).**
  - "This knowledge base archives all successfully completed tasks. Each entry in the database not only records the final outcome but also documents the iterative process of trials and feedback encountered along the way."
  - Stored unit: a successful task together with its full trial→feedback→fix trace. Failed tasks are not archived as entries, although their traces inside successful tasks capture errors and their fixes.
  - Warm start: "it begins with an initial phase that leverages a small-sized knowledge base filled with expert-crafted solutions" (Sec. 3.4.2).
- **2310.11249 (Sec. 4.2).**
  - "an experiment (referred to as a trial in R&D) is comprised of several key components: data, model, evaluation, and goal. Each component is transformed into embeddings and stored in an embedding space ... Each experiment generates a set of results. Results obtained under the same evaluation settings and metrics can be compared on a leaderboard."
  - It also keeps a general key-value knowledge store with embedded keys.
  - This is an experiment ledger: component embeddings plus results comparable on a leaderboard.
- **R&D-Agent v2.**
  - "FC-Memory Context ... manages how accumulated knowledge, such as historical solutions, evaluation results, and insights, is stored, retrieved, and reused" (Sec. 3.1).
  - Merge prompts carry, per solution, "Feedback to the Solution: Steps or changes that led to success, or failure analysis" and ask the agent to avoid "known failure patterns from the feedback history" (App. E).
  - v1 says only that "As new knowledge is gained, it is collected and organized into a knowledge base" (Sec. 2.1), and that a second exploration trace was given "access to the exploration history and failure cases from the first trace" (Sec. 3).

### Knowledge base: how it is retrieved

- **Co-STEER.**
  - Retrieval is keyed on feedback (error) similarity, not task similarity: "Instead of relying on task similarity, Co-STEER searches solutions based on feedback similarity within the practical knowledge base. The querying result is a list of steps to fix the current error."
  - Similarity uses an embedding model.
  - Worked example: a pandas MultiIndex `AttributeError` is fixed by retrieving `df.index.get_level_values('datetime')` from another task.
- **2310.11249.** Constraint queries (goal metric, model description, evaluation setting) return relevant past experiments. Differences between high- and low-scoring similar experiments are proposed as ideas to explore.
- **R&D-Agent v2 memory (Sec. 3.3).**
  - Each branch's context is augmented with "the best ideas across all branches and a probabilistically sampled subset from others. The sampling kernel favors ideas that are topically similar and have higher scores, with more recent ideas weighted higher."
  - Ablation "w/o Memory Context" lowers Any-Medal from 35.1% to 32.0%, the smallest of the four research-phase ablations (Table 3 text).
- **External RAG knowledge base hurt overall in R&D-Agent v2 (App. C.2).**
  - A KB of notebooks and forum posts from 85 Kaggle competitions: "incorporating external knowledge surprisingly harms overall performance". Overall 35.1 → 32.0; Lite tasks 68.2 → 54.6; high-difficulty 22.2 → 26.7 (Table 4).
  - Their reading: "RAG should be applied selectively based on task complexity".

### How Co-STEER schedules tasks from simple to complex (Sec. 3.3)

- A scheduling agent uses a guided chain of thought to draw a task DAG in Mermaid: "if acquiring the knowledge to complete task A could assist in completing task B, and task A is simpler than task B, we then establish a directed edge from A to B", with a rationale per edge.
- The schedule adapts: "repeated failures on the same task signal its difficulty, prompting the scheduler to prioritize simpler tasks to accumulate more knowledge efficiently."
- Evidence (Table 3, RD2Bench, 40 candidate factors of which 13 are unimplementable): the evolving scheduler beats a random scheduler at Top-5 (execution 0.765 vs 0.522; avg. corr. 0.280 vs 0.211). The paper concludes "the order of method implementation plays an important role".

### How feedback is structured (Co-STEER Sec. 3.4.2)

- **Unsupervised feedback.** "LLM-based feedback, generated by LLM, evaluates the current solution and task ... tool-based feedback utilizes a Python compiler to run the proposed solutions, providing practical feedback on their execution."
- **Supervised feedback**, when expert solutions exist:
  - LLM-written differences between the agent's code and the expert code;
  - quantitative comparison of outputs ("correlation coefficient and value accuracy").
- Evaluation metrics: average execution rate, format correctness, average and maximum correlation with ground truth (Sec. 4.2).

### Subset-first in R&D-Agent: the strongest precedent in this batch

- v1 (Sec. 2.1): "the process is divided into two phases: 1) developing a runnable solution and 2) running the solution. In the first phase, the development agent creates a runnable solution by iteratively debugging on a sampled dataset ... In the second phase, the development agent runs the solution on the full dataset to evaluate its performance."
- v2 (Sec. 3.3, MD-Coding Workflow): "first samples a small, representative subset of the training data and enters a rapid prototyping loop ... This cycle continues until achieving a runnable and logically sound solution on the subset. Only validated solutions proceed to full-scale evaluation."
- The prompt protocol (App. E.5) runs `python main.py --debug` and specifies:
  - "Sample 10% of the training data";
  - "Run minimum epochs";
  - inference only on the first test sample;
  - "Maintain identical label class numbers between debug and full modes";
  - the script must print `debug_time` and `estimated_time` for the full run.
- A checker prompt verifies "Debug Mode Compliance" ("Exactly 10% training data sampling with maintained class distributions", "Timing Accuracy", "Output Consistency: Identical submission format between debug and full modes") and "Submission Authenticity" (rejects constant, random or hard-coded outputs).
- Ablation (Sec. 4.3.2, Fig. 3): "W/o Coding Workflow ... forces the system to use full-dataset debugging ... Performance drops immediately to 24.0% Any Medal Rate" (vs 34.7% for the full system).
- Important boundary: the subset is used for correctness and runtime estimation, NOT for choosing between candidates. Scores that select solutions come from "full-scale evaluation". The paper does not test whether subset-level judgements, such as "logically sound", predict full-scale behaviour.
- Related budget idea (MD-Planning): "In the early stage (e.g., the first hour), the agent is given a limited computational budget, which discourages the use of heavy techniques such as ensembles or cross-validation. As promising directions emerge, the budget gradually increases". Removing it lowers Any-Medal 35.1 → 26.7.
- Ablations are single runs: "ablation results report single representative runs due to computational constraints" (Table 3 caption).

## Implication for us

- **Small-batch-first.** R&D-Agent is the closest ML-agent precedent: debug on a 10% stratified subset, estimate full runtime, then run at full scale, with an ablation showing it pays off. Our novelty boundary is that we also tune parameters on the pilot under pre-registered adoption rules, freeze, and re-validate at full scale with the same checker. R&D-Agent uses the subset only to reach "runnable and logically sound" and makes all selection decisions on full data.
- **Representativeness.** R&D-Agent's only representativeness constraint is class preservation. Our pilot must preserve seismicity regime (rate, magnitude range, network geometry, mainshock vs. background), which is harder and worth making explicit.
- **Runtime estimate.** The `estimated_time` requirement is a cheap addition we could copy: the pilot reports a projected full-run cost before the freeze.
- **Ledger.** For the knowledge base / experiment ledger, 2310.11249 gives the "trial = components + results on a common leaderboard" design, and Co-STEER gives "store successful traces with their error→fix history; retrieve by symptom similarity".
- **Symptom-keyed retrieval.** Retrieving by symptom maps directly onto our checker: a checker symptom such as "Wadati ratio out of range" or "depth pile-up at model interface" should key into playbook entries, rather than retrieval by case name.
- **Caution on generic knowledge.** R&D-Agent v2's negative RAG result is a caution for our resource/knowledge layer. Generic external knowledge can hurt; curated, symptom-keyed procedural knowledge is a different claim and needs its own ablation.

## Citation correction

- Cite Co-STEER as arXiv 2407.18690 (Yang, Chen, Feng et al., 2024). arXiv 2310.11249 is the 2023 RD-Agent vision paper on industrial data-centric R&D, with an embedding-based experiment knowledge base. It can be cited for "trial = data/model/evaluation/goal stored as embeddings and compared on a leaderboard", but not for Co-STEER's scheduler or its feedback-keyed knowledge base.
- R&D-Agent v1 and v2 differ substantially in title and content. Cite v2 for the six-component framework, the debug-mode subset and the ablations.
