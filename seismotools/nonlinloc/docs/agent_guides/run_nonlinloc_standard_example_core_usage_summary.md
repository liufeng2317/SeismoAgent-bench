# Core Usage Summary: Standard Workflow

### Core API
Use the public workflow API for simple/native NonLinLoc inputs.

```python
import sys
from pathlib import Path

sys.path.insert(0, "seismotools/nonlinloc/runtime/python/Nonlinlocpy")
from nonlinlocpy.standard_nonlinloc import config_from_json, run_standard_workflow

config = config_from_json("/path/to/example/standard_nonlinloc/nonlinloc_config.json")
result = run_standard_workflow(config)
print(result.located_csv, result.n_located_events)
```

### Inputs
- `velocity_model_1d.txt`: whitespace table with `depth_km vp_kms vs_kms`.
- `stations_native.txt`: whitespace table with `station_id longitude latitude elevation_m`.
- `picks_simple.txt`: simple picks converted to `NLLOC_OBS` when `use_native_obs=false`.
- `event.obs`: native NonLinLoc observation file copied when `use_native_obs=true`.
- NonLinLoc binaries: `Vel2Grid`, `Grid2Time`, and `NLLoc` must be available through `nlloc_bin` or `PATH`.

### Step-by-step workflow
Step 1: Load JSON config with `config_from_json`.
Step 2: Validate velocity model, station file, and the observation input selected by `use_native_obs`.
Step 3: Load station metadata and create a seed event/grid estimate.
Step 4: Create a fresh `run_dir`, copy/patch `nlloc.in`, write velocity layers, and compute `VGGRID`/`LOCGRID`.
Step 5: If `use_native_obs=true`, copy `event.obs`; otherwise convert `picks_simple.txt` through the common `run_nlloc` path.
Step 6: Run `Vel2Grid`, `Grid2Time`, and `NLLoc`.
Step 7: Parse `.hyp` solutions and write `located_events.csv`.

### Outputs
`run_standard_workflow` returns a `StandardRunResult` with `run_dir`, `located_csv`, and `n_located_events`.
