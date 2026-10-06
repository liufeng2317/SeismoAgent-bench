# CASE_CROSS_CORRELATION Plotting Summary

Plotting is post-processing. It is not proof that cross-correlation relocation succeeded.

## Built-In Figures

The package may call:

- `plot_hypodd_run_summary(catalog_code, output_folder)`
- `plot_hypodd_key_eval_metrics(catalog_code, output_folder)`

Typical PNG outputs follow the run prefix:

```text
{catalog_code}_hypodd_maps.png
{catalog_code}_residuals.png
{catalog_code}_eval_map_depth.png
{catalog_code}_eval_depth_mag.png
{catalog_code}_eval_residuals.png
```

These functions read `{catalog_code}.reloc` and `{catalog_code}.res`.

## Required Interpretation Checks

Before treating plots as scientific output, verify:

- `{catalog_code}.reloc` is non-empty;
- `{catalog_code}.res` is non-empty;
- `dt_*.ct` is non-empty;
- `dt_*.cc` is non-empty when claiming waveform CC;
- FDTCC and HypoDD logs show real execution.

## Full-Catalog Aggregate Figures

For batched/windowed full-catalog runs, per-unit plots are not enough. Create global figures from the consolidated table:

- input vs relocated map;
- relocation vectors or sampled displacement arrows;
- horizontal/depth shift histograms;
- depth before/after or depth-difference panels;
- residual summary across successful units;
- batch/window coverage and status map.

Label these as independent batch/window aggregates unless one global HypoDD inversion was actually run.
