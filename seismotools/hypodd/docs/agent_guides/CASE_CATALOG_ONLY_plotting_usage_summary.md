# CASE_CATALOG_ONLY Plotting Summary

Plotting is optional post-processing for catalog-only HypoDD outputs. It is not the relocation success criterion.

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

## Required Interpretation Checks

Before using plots as results, verify:

- `{catalog_code}.reloc` is non-empty;
- `{catalog_code}.res` is non-empty;
- `dt_*.ct` is non-empty;
- native `ph2dt` and `hypoDD` logs show real execution.

`dt_*.cc` and FDTCC logs are not required for catalog-only plots.

## Full-Catalog Aggregate Figures

For batched/windowed full-catalog runs, create global figures from the consolidated table:

- input vs relocated map;
- relocation vectors or sampled displacement arrows;
- horizontal/depth shift histograms;
- depth before/after or depth-difference panels;
- residual summary across successful units;
- batch/window coverage and status map.

Use the task-level consolidated relocated catalog and event-accounting table that preserve window/unit ids and original event ids. Do not plot final products from per-window iteration snapshots such as `hypoDD_0-0.reloc.001.NNN`, and do not treat non-empty snapshots as a substitute for empty `{catalog_code}.reloc` outputs. If some windows failed, show relocated results from successful final native outputs and explicitly annotate/account for failed or unrelocated events rather than rerunning only to satisfy plotting.

Label these as independent batch/window aggregates unless one global HypoDD inversion was actually run.
