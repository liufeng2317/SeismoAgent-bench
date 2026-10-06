# Config Summary: Standard Workflow

Default config file: `example/standard_nonlinloc/nonlinloc_config.json`.
Primary config object: `nonlinlocpy.standard_nonlinloc.StandardRunConfig`.

```yaml
input_dir: ./inputs          # directory with velocity_model_1d.txt, stations_native.txt, and pick/obs input
run_dir: ./run_case          # clean output/run directory created by the workflow
nlloc_bin: ""                 # directory containing Vel2Grid, Grid2Time, and NLLoc; empty means resolve from PATH
date: "201907040234"         # YYYYMMDDHHMM reference time used when converting picks_simple.txt
utm_zone_number: null       # optional fixed UTM zone number for broad/cross-zone regions
utm_zone_letter: null       # optional fixed UTM zone letter
use_native_obs: false        # false: convert picks_simple.txt; true: copy event.obs directly
prepare_only: false          # prepare files but skip NLLoc when true
```

When `use_native_obs=false`, `picks_simple.txt` is required. When `use_native_obs=true`, `event.obs` is required.
