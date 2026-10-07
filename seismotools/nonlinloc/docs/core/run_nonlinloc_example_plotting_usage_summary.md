# Plotting Usage Summary: Gamma Workflow

The Gamma workflow can generate diagnostics after successful location when `skip_plots` is `false`. Generated task scripts normally only need to call `run_example_workflow(config)`; plotting is handled inside the workflow.

Outputs under `run_dir`:
- `nonlinloc_summary.png`: map view, longitude-depth view, latitude-depth view, and horizontal-shift histogram comparing initial and relocated events.
- `nonlinloc_shift_vectors.png`: map vectors from initial event locations to relocated NonLinLoc solutions.
- `nonlinloc_plot_stats.txt`: compared-event count and shift statistics.

The plotting implementation is `nonlinlocpy.gamma_nonlinloc.write_diagnostic_plots(run_dir)`, but direct calls are only needed for custom post-processing.
