# CASE_CC_ONLY Plotting Summary

Plotting is optional post-processing for CC-only relocation. It is not proof that CC-only relocation succeeded.

## Built-In And Task-Level Figures

The same generic package plot names may be produced when merged native files exist:

```text
{catalog_code}_hypodd_maps.png
{catalog_code}_residuals.png
{catalog_code}_eval_map_depth.png
{catalog_code}_eval_depth_mag.png
{catalog_code}_eval_residuals.png
```

For auto-window CC-only runs, task-level plots should usually be built from the merged output and `cc_window_status.csv`.

## Recommended Figures

- input vs relocated map for successful windows;
- relocation vectors or sampled displacement arrows;
- horizontal/depth shift histograms;
- residual summary from `{catalog_code}.res`;
- window coverage/status map;
- CC link diagnostics by window, using `dt_cc_pair_headers`, `dt_cc_data_lines`, `events_after_dtime_match`, and `clusters`.

## Required Interpretation Checks

Before using plots as scientific output, verify:

- merged `{catalog_code}.reloc` is non-empty;
- merged `{catalog_code}.res` is non-empty;
- at least one successful window has non-empty `dt_*.cc`;
- `cc_window_status.csv` / manifest show successful windows and acceptable failed-window behavior;
- native HypoDD logs show CC observations were read.

Do not use plots to hide failed windows, empty `dt.cc`, or insufficient CC connectivity.
