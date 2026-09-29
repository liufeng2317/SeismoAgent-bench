### Objective

Process the declared waveform data for the time interval specified by the
input manifest. Produce reproducible preprocessing and P/S phase-pick results,
together with enough diagnostics to inspect the method and its limitations.

### Input scope

- Discover inputs from `BENCH_INPUT_MANIFEST`; do not hard-code alternative
  data locations.
- Use only waveform samples in the declared time window and use the declared
  station metadata for station coordinates. Record stations or traces that
  cannot be resolved.
- Treat all manifest inputs as read-only. Do not download, modify, rename or
  delete input files, and do not install packages or use network access.

### Required procedure

1. Before analysis, write a concise `task_plan.json` describing the selected
   window, discovered inputs, preprocessing operations, phase-picking method,
   quality checks, and output artifacts.
2. Save the complete reusable processing program as
   `$BENCH_OUTPUT/processing_script.py` before running the analysis. Execute
   that saved program to create the remaining outputs. The program must read
   the declared manifest and write outputs only below `$BENCH_OUTPUT`.
3. Apply transparent preprocessing and a stated P/S picking method. The
   method is not prescribed, but its parameters, thresholds, assumptions and
   known limitations must be recorded in `task_plan.json`.
4. Perform basic quality checks, including input selection, sample counts,
   sampling rates, missing data and pick plausibility. Preserve uncertainty,
   rejected picks and missing results explicitly; do not invent values to fill
   gaps.

### Output requirements

- Produce every artifact declared by the output contract. The contract is the
  source of truth for artifact paths and required CSV fields.
- The figure must contain a station-distribution panel and one representative
  waveform/preprocessing panel.
- Pick records must use `P` or `S` for phase and preserve uncertainty,
  rejected picks and missing results explicitly; do not invent values to fill
  gaps.
- Include a small inspectable set of accepted, rejected or missing examples,
  linked to their source trace where possible.

The final artifacts must be reproducible by rerunning the saved processing
program with the declared inputs and recorded runtime environment.
