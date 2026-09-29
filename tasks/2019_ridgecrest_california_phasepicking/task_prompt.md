### Objective

Process the declared waveform data for the time interval specified by the
input manifest. Produce reproducible preprocessing and P/S phase-pick results,
together with enough diagnostics to inspect the method and its limitations.

### Input scope

- Use the following input locations. They are read-only:
  - Waveform directory: `/ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/data/2019_ridgecrest_california/waveforms/data`
  - Station metadata: `/ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/data/2019_ridgecrest_california/waveforms/stations/earthscope.stationxml`
- When `BENCH_INPUT_MANIFEST` is available, use its entries to obtain the same
  paths together with detailed metadata; the variable points to the run's
  manifest, not directly to waveform data.
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

- Save the complete reusable program as `processing_script.py`.
- Save the plan and quality-control record as `task_plan.json`.
- The figure must contain a station-distribution panel and one representative
  waveform/preprocessing panel in `preprocessing_figure.png`.
- Save pick records as `picks.csv` with `station`, `phase` and
  `arrival_time_utc` columns. Include channel and confidence when available.
- Save a small inspectable set of examples as `pick_examples.json`.
- Pick records must use `P` or `S` for phase and preserve uncertainty,
  rejected picks and missing results explicitly; do not invent values to fill
  gaps.
- Link examples to their source trace where possible.

The final artifacts must be reproducible by rerunning the saved processing
program with the declared inputs and recorded runtime environment.
