---
name: catalog-checker
description: The reference-free catalog checker (seismo_checker, at CHECKER_PATH given in the task) - what it measures at each stage of an earthquake-catalog workflow, how to run it, and what the output contract requires (the checker report on the submitted products and a disposition for every flag). Use after each processing stage and before submitting a catalog.
---

# Catalog checker

The checker (`CHECKER_PATH`, given in the task) measures your products stage by stage — data, picks, association, location, relocation, magnitudes — against case-agnostic expected ranges, without any reference catalog, and reports symptoms: what was measured and how far it is out of range. It does not say why or what to change. Full description of every check, its inputs and its output: `checker/README.md` under the tools base directory given in the task (`TOOLS_BASE_PATH/checker/README.md`).

## When to run it

Run the checker on each stage's products as soon as they exist (`--stage data`, `picks`, `association`, `location`, `relocation`, `magnitude`), before the next stage uses them, and on the final products before you submit. A stage run takes seconds to minutes.

## What the output contract requires

Two items are added to the submission:

1. `work/checker/final/checker_report.json`: the checker run with `--stage all` (or the latest stage you produced) on the submitted `catalog.csv` and `picks.csv`, with `--waveforms` and the StationXML you were given, and `--catalog-before` if you relocated. The scorer re-runs the checker on the submitted files and verifies this report.
2. `work/checker/dispositions.json`: one entry for every entry in that report's `flags`:

```json
[
  {"flag_id": "space.depth_single_value", "disposition": "fixed",
   "what_changed": "what you changed and in which step", "report_before": "work/checker/<run>/checker_report.json"},
  {"flag_id": "strength.magnitude_recompute", "disposition": "justified",
   "evidence": "the measurement or experiment that shows the flagged property is not an error, with file paths"}
]
```

- `fixed`: the product was changed and the flag is gone in the final report; say what changed and point to the report in which the flag was raised.
- `justified`: the flag remains; give evidence (numbers, files, an experiment), not an explanation in words alone.

`input_notes` (properties of the input data) and `measurements` (reported without a verdict) need no disposition.

## Rules

- Do not change a product only to make a check pass (shifting depths, deleting events, rescaling magnitudes without a reason). The evaluation reads your record of changes and counts such changes separately from real fixes.
- Keep every checker report you produce (`work/checker/<stage or step>/`); they are part of the record.
