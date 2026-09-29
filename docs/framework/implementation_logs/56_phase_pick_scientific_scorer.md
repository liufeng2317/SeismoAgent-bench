# Implementation 56: Phase-pick scientific scorer

- Git commit: `a003e0f`
- Goal: add a small deterministic scientific score for `picks.csv` without inventing a reference when none is available.
- Change: added one-to-one station/phase matching with configurable time tolerance, P/S precision, recall, F1, absolute arrival-time error, missing/extra counts and station coverage. Added the external `evaluate --pick-reference` option and a JSON record at `evaluation/pick_scientific_score.json`.
- Check: six focused unittest cases passed; `git diff --check` passed. A reference CSV is required for scientific scoring; artifact-contract scoring remains independent.
- Limitation: this stage does not create a Ridgecrest truth-pick file. It only provides the scorer and an explicit reference-file interface.
