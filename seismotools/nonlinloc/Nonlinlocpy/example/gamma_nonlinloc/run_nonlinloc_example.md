# Gamma Phase Blocks to NonLinLoc Location

This example shows how to locate Gamma-associated events with the local
`nonlinlocpy` package. The example script is intentionally thin: it reads a JSON
config and calls the reusable package workflow in
`nonlinlocpy.gamma_nonlinloc`.

Use this document as the main reference for the workflow, input formats, and
outputs. The implementation details live in the package, not in the example.

## Workflow

The package workflow is organized as explicit steps:

### Step 1: Load Config

Read `nonlinloc_config.json` into `ExampleRunConfig`. The config defines input paths, output paths, NonLinLoc binary location, filtering thresholds, grid spacing, plotting, and chunking.

### Step 2: Parse Gamma Inputs

Load Gamma phase-block files matching `phase_pattern` from `example_dir`. Parse each event header and its station pick rows. Skip missing P/S picks encoded as `-1`, and keep only events with at least `min_phases` valid observations.

### Step 3: Prepare Stations

Load `stations_gamma.csv`, keep only stations used by retained picks, and build NonLinLoc-safe station aliases. Save the alias mapping later as `station_alias_map.csv`.

### Step 4: Build Run Directory and Control File

Create a fresh `run_dir` with `model/`, `time/`, `obs/`, and `loc/`. Copy the package `nlloc.in` template, convert `velocity.txt` to `LAYER` lines, and patch `VGGRID`, `LOCGRID`, `LOCMETH`, and output settings.

### Step 5: Write Observations

Convert retained Gamma picks into native `NLLOC_OBS` lines using station aliases and `pick_error_sec`. Write all observations to `obs/All.obs`.

### Step 6: Build Static NonLinLoc Assets

Run `Vel2Grid` for P and S velocity grids, then run `Grid2Time` to create station travel-time tables under `model/` and `time/`.

### Step 7: Run Locations

Run `NLLoc` directly for small catalogs. If `chunk_size > 0` and the event count exceeds the chunk size, split events into `run_dir/chunks/`, run each chunk, and merge results.

### Step 8: Parse and Save Results

Parse NonLinLoc `.hyp` files into `located_events.csv`. Save `initial_events.csv`, `station_alias_map.csv`, and the compact relocated catalog.

### Step 9: Write Diagnostics

When `skip_plots=false`, write comparison plots and shift statistics: `nonlinloc_summary.png`, `nonlinloc_shift_vectors.png`, and `nonlinloc_plot_stats.txt`.

For large catalogs, set `chunk_size > 0`; events are split into chunk directories under `run_dir/chunks/`, and merged back into one `located_events.csv`.

## Minimal Usage

Run the example:

```bash
python run_nonlinloc_example.py
```

The script loads:

```text
nonlinloc_config.json
```

Equivalent Python usage:

```python
from nonlinlocpy.gamma_nonlinloc import config_from_json, run_example_workflow

config = config_from_json("/path/to/nonlinloc_config.json")
result = run_example_workflow(config)

print(result.run_dir)
print(result.located_csv)
print(result.n_input_events, result.n_located_events)
```

Direct config construction is also supported:

```python
from nonlinlocpy.gamma_nonlinloc import ExampleRunConfig, run_example_workflow

result = run_example_workflow(
    ExampleRunConfig(
        example_dir="/path/to/inputs",
        run_dir="/path/to/run_case",
        nlloc_bin="/path/to/NLL7.00_src/src",
        phase_pattern="phase_*.dat",
        min_phases=4,
        max_events=0,
        chunk_size=300,
        num_workers=8,
    )
)
```

## Config File

Default config:

```text
example/gamma_nonlinloc/nonlinloc_config.json
```

Main fields:

```json
{
  "example_dir": "./inputs",
  "run_dir": "./run_case",
  "nlloc_bin": "",
  "phase_pattern": "phase_*.dat",
  "min_phases": 4,
  "max_events": 200,
  "horizontal_pad_km": 10.0,
  "depth_top_km": -2.0,
  "depth_bottom_pad_km": 10.0,
  "horizontal_spacing_km": 1.0,
  "depth_spacing_km": 1.0,
  "utm_zone_number": null,
  "utm_zone_letter": null,
  "pick_error_sec": 0.05,
  "prepare_only": false,
  "output_mode": "production",
  "skip_plots": false,
  "chunk_size": 0,
  "num_workers": 64
}
```

Notes:

- `nlloc_bin` should point to the directory containing `Vel2Grid`,
  `Grid2Time`, and `NLLoc`. If empty, the package tries known fallback paths.
- `max_events=0` means no event limit.
- `prepare_only=true` writes inputs but does not run NonLinLoc.
- `output_mode="production"` removes bulky per-event location files after
  successful parsing.

## Input Directory

`example_dir` must contain:

```text
inputs/
  velocity.txt
  stations_gamma.csv
  phase_*.dat
```

### `velocity.txt`

Whitespace table with three numeric columns:

```text
depth_km vp_kms vs_kms
```

Example:

```text
0.0 5.20 3.01
2.0 5.50 3.18
5.0 5.90 3.41
```

The workflow converts these rows to NonLinLoc `LAYER` lines and patches the
control file.

### `stations_gamma.csv`

CSV station metadata. Required columns:

```text
station_id,longitude,latitude,elevation_m
```

Extra columns such as `network` or `station` are allowed and preserved in
`station_alias_map.csv` when present.

Example:

```csv
station_id,longitude,latitude,elevation_m
N.S3N02,142.7918,39.3746,-1622.0
N.S3N03,143.1206,39.3231,-1890.0
```

### `phase_*.dat`

Gamma event-block file. Each event starts with one event header row:

```text
origin_time,latitude,longitude,depth_km,magnitude
```

Followed by station pick rows:

```text
station_id,p_pick_time,s_pick_time,s_amplitude
```

Example:

```text
2025-12-08T00:02:29.367000,39.6428,143.2800,24.01,2.26
N.S3N02,2025-12-08T00:02:36.060000,2025-12-08T00:02:37.290000,0.086
N.S4N23,2025-12-08T00:02:38.260000,-1,0.055
```

Rules:

- `-1` means the P or S pick is missing.
- Missing picks are skipped.
- One station row can produce zero, one, or two NonLinLoc observations.
- Events with fewer than `min_phases` retained observations are dropped.

## Output Structure

`run_dir` is recreated and populated as:

```text
run_case/
  nlloc.in
  initial_events.csv
  station_alias_map.csv
  located_events.csv
  nonlinloc_summary.png
  nonlinloc_shift_vectors.png
  nonlinloc_plot_stats.txt
  obs/
    All.obs
  model/
    ...
  time/
    ...
  loc/
    ...
  chunks/
    chunk_0000/
    chunk_0001/
```

Some files appear only after execution. `chunks/` appears only when
`chunk_size > 0` and the event count exceeds the chunk size.

## Main Outputs

- `nlloc.in`: patched NonLinLoc control file.
- `obs/All.obs`: converted `NLLOC_OBS` picks.
- `initial_events.csv`: parsed Gamma initial catalog used by the workflow.
- `station_alias_map.csv`: mapping from original station IDs to NonLinLoc-safe
  aliases.
- `located_events.csv`: compact relocated catalog parsed from `.hyp` files.
- `model/`: velocity-grid files from `Vel2Grid`.
- `time/`: station travel-time grids from `Grid2Time`.
- `loc/`: raw NonLinLoc location products, retained or cleaned depending on
  `output_mode`.

## Diagnostic Outputs

When `skip_plots=false` and locations are available:

- `nonlinloc_summary.png`: map view, longitude-depth section,
  latitude-depth section, and horizontal-shift histogram.
- `nonlinloc_shift_vectors.png`: initial-to-relocated map vectors.
- `nonlinloc_plot_stats.txt`: number of compared events and shift statistics.

## Return Object

`run_example_workflow(config)` returns `ExampleRunResult`:

```python
ExampleRunResult(
    run_dir="...",
    located_csv="...",
    n_input_events=0,
    n_located_events=0,
    chunk_count=1,
    summary_plot="...",
    shift_plot="...",
    stats_file="...",
)
```

## When To Use

Use this workflow when:

- the input catalog comes from Gamma or a Gamma-like associator;
- phase picks are grouped by event blocks;
- station names need safe NonLinLoc aliases;
- a complete absolute-location run is needed, including input preparation,
  NonLinLoc execution, parsed results, and diagnostics.

For already-native `NLLOC_OBS` inputs, use the standard NonLinLoc example
instead.
