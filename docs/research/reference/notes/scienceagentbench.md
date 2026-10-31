# ScienceAgentBench (and the misattributed arXiv 2412.10606)

## Papers

- **ScienceAgentBench.** "ScienceAgentBench: Toward Rigorous Assessment of Language Agents for Data-Driven Scientific Discovery". Ziru Chen, Shijie Chen, Yuting Ning, Qianheng Zhang, Boshi Wang, et al., Huan Sun (OSU, UW–Madison, ...); ICLR 2025. arXiv 2410.05080, version read: v3 (31 Mar 2025). https://arxiv.org/abs/2410.05080. Read in full: Sec. 1–5, App. H.
- **arXiv 2412.10606.** "Do Large Language Models Speak Scientific Workflows?". Orcun Yildiz, Tom Peterka (Argonne National Laboratory); SC'25 workshops, DOI 10.1145/3731599.3767578. Version read: v3 (09 Oct 2025). https://arxiv.org/abs/2412.10606. Read in full.

## Earlier claim under review

[claimed: calls for assessing agents on individual workflow tasks before claiming end-to-end automation, with step rubrics] — The claim is in ScienceAgentBench, nearly verbatim. It is not in 2412.10606, so citing 2412.10606 for it is a misattribution. "Step rubrics" needs qualifying: ScienceAgentBench's rubrics are per-task, graded in five program stages, and used for human evaluation of generated programs. They do not score each step of a scientific workflow.

## What ScienceAgentBench says

### The call for individual-task assessment

- Abstract: "In this work, we call for rigorous assessment of agents on individual tasks in a scientific workflow before making bold claims on end-to-end automation."
- Sec. 1: "we contend that for a language agent to fully automate data-driven discovery, it must be able to complete all essential tasks in the workflow, such as model development, data analysis, and visualization. Thus, we advocate careful evaluations of the agents' performance on these tasks, before claiming they can automate data-driven discovery end-to-end. Such an assessment strategy helps grasp a more solid understanding of an agent's strengths and limitations than purely relying on end-to-end evaluations, e.g., using an LLM-based reviewer to assess generated papers (Lu et al., 2024)."
- Sec. 2: "Before automating the entire workflow end-to-end, we envision language agents to first serve as science co-pilots that can write code to process, analyze, and visualize data."

### Rubrics

- Sec. 2.3, "Rubric-Based Evaluation": "we structure the rubrics into five stages: Data Loading, Data Processing, Modeling or Visualization, Output formatting, and Output Saving." GPT-4o drafts each rubric, experts refine it (App. H), and it is applied by human raters. The authors note: "automating this rubric-based evaluation approach, such as developing an LLM-based judge, is a meaningful future direction."
- Sec. 4.2 caveat: "Since each rubric is derived from a gold program and reflect its implementation, there are chances that the evaluator overlooks such equivalence". For example, a random forest that works as well as the gold program's neural network may be under-credited.

### Scale and headline numbers

- 102 tasks from 44 peer-reviewed papers in four disciplines, validated by nine subject-matter experts. Each task's target is one self-contained Python program.
- "the best-performing agent can only solve 32.4% of the tasks independently and 34.3% with expert-provided knowledge". o1-preview reaches 42.2% "but with more than 10 times the cost".
- Conclusion: "our results underscore the limitations of current language agents in generating code for data-driven discovery, let alone end-to-end automation for scientific research."

## What arXiv 2412.10606 is

- An HPC scientific-workflow-systems study. It asks whether LLMs can configure workflows, annotate task code, and translate task code between workflow systems (Wilkins, ADIOS2, PyCOMPSs, Parsl, Henson). Generated code is scored against reference code with BLEU and ChrF (Sec. 3).
- Findings: "LLMs face challenges in the context of scientific workflows, as LLMs are primarily trained for general tasks and lack the domain knowledge required for scientific workflows". "incorporating external knowledge as context significantly improves the performance" (few-shot for configuration). Iterative error correction is suggested as future work (Sec. 5).
- It makes no argument about individual-task vs. end-to-end evaluation of science agents and has no rubrics. "Workflow" there means workflow-management systems (task graphs and I/O coupling), not a scientific analysis workflow.

## Implication for us

- **What ScienceAgentBench supports.** It is the right citation for our tiered evaluation: offline replay of recorded intermediate products, back-end-only tasks, then full runs. It also supports measuring agents per stage before claiming end-to-end catalog automation. The quote is strong and can be used verbatim.
- **Rubric stages are program anatomy, not pipeline stages.** Their five stages (load / process / model / format / save) describe the anatomy of one program. Our stages (detection, picking, association, location, relocation, magnitude) are pipeline stages with their own physical outputs. Cite them as precedent for staged partial credit, not as precedent for a stage checker.
- **Lesson from the gold-program caveat.** Rubrics derived from one gold implementation under-credit equivalent alternatives. This argues for our reference-free, symptom-based checker over "matches the expert pipeline" rubrics.
- **Possible legitimate use of 2412.10606.** It could be cited for "LLMs lack domain knowledge for (HPC) scientific workflows; external context helps". It is weak and off-topic for our claims.

## Citation correction

- Replace the citation of arXiv 2412.10606 for the individual-task-before-end-to-end claim with arXiv 2410.05080 (Chen et al., ScienceAgentBench, ICLR 2025).
- Describe its rubrics as "expert-refined, per-task rubrics in five program stages used for human grading", not "step rubrics".
