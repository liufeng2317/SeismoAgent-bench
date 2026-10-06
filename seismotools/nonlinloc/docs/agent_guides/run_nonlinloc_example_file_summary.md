# File Summary: nonlinlocpy Gamma Workflow

nonlinlocpy is a local Python workflow wrapper around the external NonLinLoc programs. It does not replace `Vel2Grid`, `Grid2Time`, or `NLLoc`; instead, it prepares their control files and inputs, launches the binaries, and parses `.hyp` outputs into easier-to-use CSV/result objects.

This case demonstrates how to locate an earthquake catalog that has already been associated by Gamma or a Gamma-like picker/associator. Its purpose is to convert `phase_*.dat` event blocks and `stations_gamma.csv` metadata into a complete NonLinLoc absolute-location run, then compare the original event guesses with the relocated solutions.

For broad regions that cross automatic UTM zone boundaries, set `utm_zone_number` and `utm_zone_letter` in the JSON config so the grid and station projection use one fixed zone.

Main steps:
1. Load `nonlinloc_config.json` with `nonlinlocpy.gamma_nonlinloc.config_from_json`.
2. Call `run_example_workflow(config)` from `nonlinlocpy.gamma_nonlinloc`; the example script itself should stay thin.
3. Read `velocity.txt`, `stations_gamma.csv`, and `phase_*.dat` from `example_dir`.
4. Filter events by phase count, create NonLinLoc-safe station aliases, and convert Gamma picks to `NLLOC_OBS`.
5. Build a clean `run_dir`, copy and patch `nlloc.in`, write velocity/grid settings, and compute `VGGRID`/`LOCGRID`.
6. Run `Vel2Grid`, `Grid2Time`, and `NLLoc` using the configured NonLinLoc binary path.
7. Parse `.hyp` solutions, write `located_events.csv`, and optionally write summary/shift diagnostic plots.

Generated task scripts should use this high-level workflow first. Only inspect lower-level modules such as `workflows.py`, `velocity.py`, `observations.py`, or `runner.py` when a task explicitly requires custom NonLinLoc preparation logic.
