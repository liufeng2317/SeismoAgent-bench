# TRACE: A Multi-Agent System for Autonomous Physical Reasoning for Seismology

- Authors: Feng Liu, Xin Cui, Jian Xu, Wang Xinghao, Zijie Guo, et al. (Harvard, Shanghai AI Lab, USTC, McGill, ...)
- arXiv: 2603.21152, version read: v4 (30 Sep 2026; physics.geo-ph)
- URL: https://arxiv.org/abs/2603.21152
- Reading: full text of the main paper and Materials and Methods. The supplementary figures were not inspected.

## What it does

- TRACE turns open-ended mechanism questions into executable seismological workflows and an auditable evidence chain. It has three modules: Planning and Task Decomposition; Automated Execution and Diagnostics; Scientific Integration and Inference.
- The resource layer has two parts:
  - a Structured Knowledge Library, which "encodes methodological rules, parameter ranges, workflow templates and documented failure modes ... defines when a method is appropriate, what input data it requires, what assumptions it makes and what diagnostics should be checked";
  - a Validated Scientific Tools Library, with ObsPy, PhaseNet, GaMMA, HypoDD, EQcorrscan, SeismoStats, ETAS and others.
- Tasks:
  - 104 benchmark tasks (74 basic plus 30 multi-step) across three backbones (GPT-5.1, Claude Sonnet 4, Gemini 3 Flash);
  - two end-to-end applications. 2019 Ridgecrest starts from waveforms and finds delayed cascading activation between the M6.4 and M7.1. The 2025–2026 Sanriku sequence starts from JMA phases and covers shallow-interface activation, repeaters and b-value changes.

## Checks of intermediate outputs, concretely

- **Result Checking Agent** (Methods): "evaluates the intermediate and final products against predefined computational and physical criteria. These checks include file validity, numerical ranges, catalog completeness, spatial and temporal consistency, convergence of inversion or relocation routines, and plausibility of derived seismicity statistics."
- **Visualization diagnostics:** "checks whether figures contain the expected data layers, labels and physically meaningful ranges."
- **On failure:** "TRACE revises the workflow within allowed operations, for example, by adjusting a parameter, repairing code, changing a data subset or selecting an alternative tool. Persistent differences among valid alternatives are retained as separate evidence branches". "Only outputs satisfying the applicable diagnostic criteria ... are passed to evidence synthesis; unresolved failures remain in the provenance record".
- **Catalog validation in the Ridgecrest application:** cross-catalog consistency with ComCat and Ross et al. (event counts in magnitude bins, spatial and temporal distributions). This is a reference-based check.
- **Sanriku:** "Human-supervised quality control revealed numerous implausible arrivals" in the deep-learning-pick route, so the JMA arrivals were retained. Catalog quality control was partly human.

## How it differs from building a catalog (SeismoAgentBench)

- In TRACE the catalog is an intermediate product on the way to a physical interpretation. Catalog quality is checked by generic diagnostics and agreement with existing catalogs, and nothing scores the catalog itself as the final deliverable.
- SeismoAgentBench makes the high-precision catalog the target. It needs:
  - a stage-resolved, reference-free checker whose symptoms are specific to catalog processing (picks, association, location, relocation, magnitude), tied to playbooks;
  - an explicit protocol for parameter-heavy long runs (pilot, freeze, full run, re-check), which TRACE does not have. TRACE's loop revises "within allowed operations" without pre-registered adoption rules or pilot-to-full validation.
- TRACE's check list is the right generic skeleton (validity, ranges, completeness, consistency, convergence, plausibility). Our checker can be presented as making this list stage-specific, quantitative and independent of a reference.

## Citation note

- No earlier claim was given to check. This is the user's own group's paper; the description above is drawn from v4.
