# File Summary: nonlinlocpy Standard Workflow

nonlinlocpy is a local Python workflow wrapper around the external NonLinLoc programs. It prepares NonLinLoc run directories, control files, velocity/travel-time grids, observation inputs, binary execution, and `.hyp` result parsing, while leaving the actual location calculation to the original `Vel2Grid`, `Grid2Time`, and `NLLoc` executables.

This case demonstrates the compact standard/native workflow for inputs that are already close to NonLinLoc format. Its purpose is to show the minimal absolute-location path from a 1-D velocity model, a native station table, and either simple picks or a native `event.obs` file to a parsed `located_events.csv` table.

For broad regions that cross automatic UTM zone boundaries, set `utm_zone_number` and `utm_zone_letter` in the JSON config so the grid and station projection use one fixed zone.

Main steps:
1. Load `nonlinloc_config.json` with `nonlinlocpy.standard_nonlinloc.config_from_json`.
2. Call `run_standard_workflow(config)` from `nonlinlocpy.standard_nonlinloc`; the example script itself should stay thin.
3. Read `velocity_model_1d.txt`, `stations_native.txt`, and the observation input selected by `use_native_obs`.
4. If `use_native_obs=false`, require and convert `picks_simple.txt`; if `use_native_obs=true`, require and copy `event.obs`.
5. Build a clean `run_dir`, copy and patch `nlloc.in`, write velocity/grid settings, and compute `VGGRID`/`LOCGRID`.
6. Run `Vel2Grid`, `Grid2Time`, and `NLLoc` using the configured NonLinLoc binary path.
7. Parse `.hyp` solutions and write `located_events.csv`.

This workflow intentionally avoids Gamma parsing, station alias mapping, chunked execution, and plotting. Use it as the first reference for simple single-case NonLinLoc runs or native-format tests.
