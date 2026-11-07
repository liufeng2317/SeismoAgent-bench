# Stage 7: submission

All paths are relative to the output directory `$BENCH_OUTPUT`: `catalog.csv`, `picks.csv` and `checker/` sit at its top, not in a subdirectory.

## Steps

1. Write the final `catalog.csv` and `picks.csv` (output convention of the task; optional columns: the locator's `horizontal_uncertainty_km`, `depth_uncertainty_km`, picks `residual_s`). Events beyond the network are `rejected`; template detections are in the catalog.
2. Run the checker on exactly these files: `run.py --stage all --catalog catalog.csv --picks picks.csv --stations ... --waveforms ... [--catalog-before located.csv] --output-dir checker/final`.
3. Write `checker/dispositions.json`: one entry per flag of `checker/final/checker_report.json` (format in the catalog-checker skill).
   - `fixed`: the flag is gone in the final report; `what_changed` says what and in which step; `report_before` is the report (path relative to `$BENCH_OUTPUT`) in which the flag was raised.
   - `justified`: the flag remains; `evidence` gives numbers, files or an experiment that shows the flagged property is not an error. A flag the stage files say to repair (for example a pile of unconstrained events, a depth flag above its limit) is not justified by describing it. Which flags must be fixed and which can be justified after one experiment: `../reference/flag_reliability.md`.
4. Run `python <catalog-checker skill>/scripts/check_submission.py --output-dir $BENCH_OUTPUT` and fix everything it reports.
5. In your record: the decisions of every stage with their evidence, the velocity model and its source, what was left out and why (stations, events beyond the network, stages not run), and the uncertainties you could not resolve (`../reference/not_visible.md`: model sensitivity, frame, magnitude calibration level, coda completeness).

A run that ends early is fine once these steps pass; remaining time is not a reason to add steps that the stage files do not call for.
