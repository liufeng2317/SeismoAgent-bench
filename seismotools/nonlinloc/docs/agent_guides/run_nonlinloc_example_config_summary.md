# Config Summary: Gamma Workflow

Default config file: `example/gamma_nonlinloc/nonlinloc_config.json`.
Primary config object: `nonlinlocpy.gamma_nonlinloc.ExampleRunConfig`.

```yaml
example_dir: ./inputs        # directory with velocity.txt, stations_gamma.csv, and phase_*.dat
run_dir: ./run_case          # clean output/run directory created by the workflow
nlloc_bin: ""                 # directory containing Vel2Grid, Grid2Time, and NLLoc; empty means resolve from PATH
phase_pattern: phase_*.dat   # Gamma event/pick file glob under example_dir
min_phases: 4                # minimum P/S picks required to keep an event
max_events: 200              # event limit for examples/testing; set higher or <=0 for larger catalogs
horizontal_pad_km: 10.0      # horizontal grid padding around stations/events
depth_top_km: -2.0           # top of search grid
depth_bottom_pad_km: 10.0    # depth padding below event/model range
horizontal_spacing_km: 1.0   # horizontal grid spacing
depth_spacing_km: 1.0        # depth grid spacing
utm_zone_number: null       # optional fixed UTM zone number for cross-zone regions, e.g. 54 for Japan Aomori
utm_zone_letter: null       # optional fixed UTM zone letter, e.g. N
pick_error_sec: 0.05         # timing uncertainty written to NLLOC_OBS
prepare_only: false          # prepare files but skip NLLoc when true
output_mode: production      # cleanup-oriented output mode after successful locations
skip_plots: false            # skip diagnostic PNG/txt outputs when true
chunk_size: 0                # >0 enables chunked runs for large catalogs
num_workers: 64              # workers for chunked/parallel execution
```
