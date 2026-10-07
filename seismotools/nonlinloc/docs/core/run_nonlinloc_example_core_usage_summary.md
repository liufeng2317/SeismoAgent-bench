# Core Usage Summary: Gamma Workflow

### Core API
Use the public workflow API. Do not rebuild the pipeline from low-level helpers unless you are customizing internals.

```python
import sys
from pathlib import Path

sys.path.insert(0, "seismotools/nonlinloc/runtime/python/Nonlinlocpy")
from nonlinlocpy.gamma_nonlinloc import config_from_json, run_example_workflow

config = config_from_json("/path/to/example/gamma_nonlinloc/nonlinloc_config.json")
result = run_example_workflow(config)
print(result.located_csv, result.n_input_events, result.n_located_events)
```

### Inputs
- `velocity.txt`: whitespace table with `depth_km vp_kms vs_kms`.
- `stations_gamma.csv`: CSV station metadata including `station_id`, `longitude`, `latitude`, `elevation_m`.
- `phase_*.dat`: Gamma event blocks. Event header lines contain origin time, latitude, longitude, depth, and magnitude; pick lines contain station id plus P/S pick times.
- NonLinLoc binaries: `Vel2Grid`, `Grid2Time`, and `NLLoc` must be available through `nlloc_bin` or `PATH`.
- For study areas crossing automatic UTM zone boundaries, set `utm_zone_number` and `utm_zone_letter` in the JSON config instead of monkey-patching projection code. Japan Aomori can use `utm_zone_number: 54` and `utm_zone_letter: N`.

### Step-by-step workflow
Step 1: Load JSON config with `config_from_json`.
Step 2: Validate `example_dir`, velocity model, station CSV, and phase files.
Step 3: Parse events and picks, filter by `min_phases` and `max_events`.
Step 4: Build NonLinLoc-safe station aliases and station objects.
Step 5: Create a fresh `run_dir`, copy/patch `nlloc.in`, write velocity layers, and compute `VGGRID`/`LOCGRID`.
Step 6: Convert Gamma picks to `NLLOC_OBS` and write run metadata such as station aliases and initial events.
Step 7: Run `Vel2Grid`, `Grid2Time`, and `NLLoc`.
Step 8: Parse `.hyp` solutions and write `located_events.csv`.
Step 9: Optionally write diagnostic plots and stats when `skip_plots=false`.

### Outputs
`run_example_workflow` returns an `ExampleRunResult` with `run_dir`, `located_csv`, `n_input_events`, `n_located_events`, `chunk_count`, `summary_plot`, `shift_plot`, and `stats_file`.
