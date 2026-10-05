# Japan JMA CC-only examples

This directory keeps one recommended CC-only relocation example:

`run_jma_cc_only.py`
  Auto-windowed CC-only relocation example. It splits the selected catalog into
  manageable independent event-count windows before CC-only relocation. If the
  selected catalog is small, the planner may produce a single window.

Both examples are function-parameter driven. They do not parse command-line
arguments and does not require external JSON config files as user inputs. The
case-specific script prepares JMA catalog/station/phase inputs, then uses the
public `hypodd_runner.build_cc_only_relocation_kwargs` helper to build the common
CC-only HypoDD/FDTCC parameter set.

Input QC plotting is disabled by default (`no_plot=True`) to keep the example
project compact. Set `no_plot=False` in the script settings if a selected
event/station map is needed.
