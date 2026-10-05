# NonLinLoc Python Helpers

This is the project-local copy of the Nonlinlocpy library from TRACE-1.1. Its
native executables are provided separately in the sibling `../native/bin/` directory;
pass that directory explicitly as `nlloc_bin` or `--nlloc-bin` when running a
workflow. Generated grids, observations and location products belong in the
caller-provided run directory.

## Overview

This package provides Python helpers and example workflows for [NonLinLoc](http://alomax.net/nlloc/). It focuses on three tasks:

- preparing control files and input data
- running `Vel2Grid`, `Grid2Time`, and `NLLoc`
- exporting compact event tables from `.hyp` results

Most users should start from one of the two example workflows:

- `example/standard_nonlinloc/`: minimal native/simple-pick NonLinLoc workflow
- `example/gamma_nonlinloc/`: Gamma-associated phase catalog to NonLinLoc location workflow

The example scripts are designed around Python configuration objects and JSON-compatible settings. Agent, notebook, and pipeline usage should prefer the programmatic workflow functions instead of calling low-level helpers directly.

Both examples default to:

- input directory: `./inputs`
- output run directory: `./run_case`

## Repository Layout

| Path | Purpose |
| --- | --- |
| `nonlinlocpy/` | Core Python package |
| `nonlinlocpy/workflows.py` | User-facing `NLLocConfig` / `run_nlloc` helper for prepared run directories |
| `nonlinlocpy/control.py` | Control-file patch helpers |
| `nonlinlocpy/velocity.py` | 1-D velocity model to `LAYER` helpers |
| `nonlinlocpy/stations.py` | Station table, `GTSRCE`, and `Grid2Time` helpers |
| `nonlinlocpy/observations.py` | Pick table and `NLLOC_OBS` helpers |
| `nonlinlocpy/runner.py` | Run-directory cleanup and `NLLoc` binary execution |
| `nonlinlocpy/hyp.py` | `.hyp` result parsing |
| `nonlinlocpy/parallel.py` | Chunked/parallel `NLLoc` helpers |
| `nonlinlocpy/utils.py` | Shared filesystem, grid, binary-resolution, and CSV helpers |
| `nonlinlocpy/template/` | Control-file and input templates |
| `../native/bin/` | Project-managed compiled NonLinLoc binaries |
| `example/gamma_nonlinloc/` | Gamma-based example workflow |
| `example/standard_nonlinloc/` | Native-format example workflow |
| `pyproject.toml` | Local package configuration |

## Installation

### Core Package

```bash
python -m pip install -e seismotools/nonlinloc/Nonlinlocpy --no-build-isolation
```

### With Example Dependencies

```bash
python -m pip install -e "seismotools/nonlinloc/Nonlinlocpy[examples]" --no-build-isolation
```

## Package Entry Points

### Python API

```python
import nonlinlocpy
from nonlinlocpy import NLLocConfig, run_nlloc
```

The package root intentionally exposes a small user-facing API:

- `run_nlloc` for an already prepared run directory plus a simple pick table or existing observations
- `run_parallel_nlloc_workflow` for chunked catalog runs
- `parse_hyp_solutions`, `Station`, and `PhasePick` for common data handling

Advanced control-file, observation-format, and grid-building helpers remain
available from focused modules such as `nonlinlocpy.control`,
`nonlinlocpy.velocity`, `nonlinlocpy.stations`, `nonlinlocpy.observations`,
`nonlinlocpy.runner`, `nonlinlocpy.hyp`, and `nonlinlocpy.utils`.

For complete end-to-end examples, prefer the case workflows:

```python
run_standard_workflow(StandardRunConfig(...))
run_example_workflow(ExampleRunConfig(...))
```

## Core Features

### Control and Model Preparation

The package can:

- copy the shared `nlloc.in` template
- replace `LAYER`, `VGGRID`, `LOCGRID`, and related control lines
- insert `LOCMETH` when needed

### Observation Preparation

The package supports:

- native `NLLOC_OBS` input
- conversion from simple pick tables

### Station and Travel-Time Preparation

The package can:

- read native station tables
- write `GTSRCE` sections
- generate `Zone_info.pickle`
- run `Grid2Time` for both `P` and `S`

### Result Parsing

After `NLLoc` completes, the package can:

- parse `.hyp` files
- recover stable geographic coordinates in `TRANS NONE` workflows
- extract common quality and uncertainty fields
- export compact event tables with a single `origin_time` column

### Parallel Execution

Recommended parallel entry points include:

- `run_parallel_nlloc_workflow`
- `ParallelNLLocConfig`
- `ParallelNLLocResult`

Lower-level chunk helpers are available from `nonlinlocpy.parallel` for advanced
workflows. The high-level parallel workflow is intended for large event sets
that reuse common static assets such as `model/` and `time/`.

## Templates

The `nonlinlocpy/template/` directory contains:

| File | Purpose |
| --- | --- |
| `nlloc.in` | Main NonLinLoc control-file template |
| `stations_native.example.txt` | Native station table example: `station_id lon lat elev_m` |
| `picks_simple.example.txt` | Simple pick table example: `station_id phase time_sec [first_motion]` |
| `event.obs.example` | Native `NLLOC_OBS` example |
| `velocity_model_1d.example.txt` | 1-D velocity model example: `depth_km vp_kms vs_kms` |

## Input Formats

### Native Station Table

```text
station_id  longitude  latitude  elevation_m
```

### Simple Pick Table

```text
station_id  phase  time_sec  [first_motion]
```

Notes:

- `time_sec` is measured after the reference `HHMM`
- `first_motion` is optional and may be `U`, `D`, or `?`

### 1-D Velocity Model

```text
depth_km  vp_kms  vs_kms
```

This format is treated as an editable source file and converted into `LAYER` lines before being written into `nlloc.in`.

## Example Workflows

Choose the example by input type:

| Case | Use When | Main Entry |
| --- | --- | --- |
| Standard/native | Data are already close to NonLinLoc format: 1-D velocity model, native station table, simple picks or `NLLOC_OBS` | `run_standard_workflow(StandardRunConfig(...))` |
| Gamma-to-NonLinLoc | Picks come from Gamma association files and need event parsing, station aliasing, and observation conversion | `run_example_workflow(ExampleRunConfig(...))` |

### Gamma-Based Example

Script:

- `example/gamma_nonlinloc/run_nonlinloc_example.py`

Purpose:

- Converts Gamma-associated event/pick files to NonLinLoc `NLLOC_OBS`
- Builds station aliases for NonLinLoc-safe station labels
- Prepares `nlloc.in`, model grids, travel-time grids, and location inputs
- Supports optional chunked execution for larger catalogs
- Writes relocation diagnostics when enabled

Recommended Python usage:

```python
from nonlinlocpy.gamma_nonlinloc import config_from_json, run_example_workflow

config = config_from_json("example/gamma_nonlinloc/nonlinloc_config.json")
result = run_example_workflow(config)
```

Config-driven alternatives:

- edit `example/gamma_nonlinloc/nonlinloc_config.json` for a local run
- construct `ExampleRunConfig(...)` directly for programmatic use

Default paths:

- input directory: `./inputs`
- output run directory: `./run_case`

Main outputs:

- `run_case/obs/All.obs`
- `run_case/station_alias_map.csv`
- `run_case/initial_events.csv`
- `run_case/located_events.csv`
- optional `run_case/nonlinloc_summary.png`
- optional `run_case/nonlinloc_shift_vectors.png`
- optional `run_case/nonlinloc_plot_stats.txt`

### Standard Native-Format Example

Script:

- `example/standard_nonlinloc/run_nonlinloc_standard_example.py`

Purpose:

- Demonstrates a minimal native/simple-pick NonLinLoc workflow
- Uses station labels that are already suitable for NonLinLoc
- Converts `picks_simple.txt` to `obs/All.obs`, or copies an existing `event.obs`
- Runs static preprocessing and delegates final location/parsing/export to `run_nlloc`
- Writes a compact `located_events.csv` table

Recommended Python usage:

```python
from run_nonlinloc_standard_example import StandardRunConfig, run_standard_workflow

result = run_standard_workflow(
    StandardRunConfig(
        input_dir="./inputs",
        run_dir="./run_case",
        nlloc_bin="/path/to/NonLinLoc/src/bin",
        use_native_obs=False,
    )
)
```

Config-driven alternatives:

- edit `DEFAULT_RUN_CONFIG` in the example file for a local run
- load a JSON object with `config_from_json("nonlinloc_standard_config.json")`

Default paths:

- input directory: `./inputs`
- output run directory: `./run_case`

Notes:

- Both example scripts import `nonlinlocpy` directly. They can use an installed package from the active environment or the local source tree fallback used by the example files.
- The standard/native case is intentionally minimal: no Gamma parsing, no station alias map, no chunked execution, and no plotting.

## Common Python Usage

### Run NLLoc In A Prepared Directory

Use `run_nlloc` only after the run directory already has a valid `nlloc.in`, model/travel-time assets, and station setup. For a complete from-inputs example, use `run_standard_workflow(...)` or `run_example_workflow(...)`.

```python
from nonlinlocpy import NLLocConfig, run_nlloc

solutions = run_nlloc(
    NLLocConfig(
        nlloc_bin="/path/to/NonLinLoc/src",
        control_dir="run_case",
        picks="template/picks_simple.example.txt",
        date="199402172216",
        output_csv="located_events.csv",
    )
)
```

### Run Chunked Parallel `NLLoc`

Chunked execution is usually used inside the Gamma case for larger catalogs. Use it directly only when you already know how to prepare per-chunk `All.obs` files.

```python
from pathlib import Path
from nonlinlocpy import ParallelNLLocConfig, run_parallel_nlloc_workflow

def prepare_chunk_inputs(chunk_run_dir: Path, chunk_items):
    # Write All.obs and any chunk-local metadata here
    ...

config = ParallelNLLocConfig(
    base_run_dir="run_case",
    nlloc_bin_dir="",
    chunk_size=200,
    num_workers=8,
    output_mode="production",
)

result = run_parallel_nlloc_workflow(
    items=events,
    config=config,
    prepare_chunk_inputs=prepare_chunk_inputs,
)
```

## Output Table

The default exported event table is compact and uses a single `origin_time` column.

| Column | Meaning |
| --- | --- |
| `event_id` | Event identifier, usually derived from the `.hyp` filename |
| `origin_time` | Origin time in a compact ISO-like format |
| `lat` | Latitude |
| `lon` | Longitude |
| `depth_km` | Depth in km |
| `rms_sec` | RMS residual in seconds |
| `used_phase_count` | Number of used phases |
| `used_station_count` | Number of used stations |
| `gap_deg` | Azimuthal gap |
| `min_dist_km` | Minimum station distance |
| `max_dist_km` | Maximum station distance |
| `median_dist_km` | Median station distance |
| `min_horizontal_uncertainty_km` | Minimum horizontal uncertainty |
| `max_horizontal_uncertainty_km` | Maximum horizontal uncertainty |
| `semi_major_axis_km` | Semi-major axis of the confidence ellipsoid |
| `semi_minor_axis_km` | Semi-minor axis of the confidence ellipsoid |
| `semi_intermediate_axis_km` | Intermediate ellipsoid axis |
| `coord_source` | Coordinate extraction source |

## Notes

- In `TRANS NONE` workflows, the package prefers `HYPOCENTER x/y/z + Zone_info.pickle` over the raw `GEOGRAPHIC` line when the `GEOGRAPHIC` values are clearly internal grid coordinates.
- Chunked workflows keep detailed event files under each chunk directory instead of merging all per-event `.hyp/.hdr` files into a single top-level `loc/`.
- If you need reproducible runtime behavior across machines, set `nlloc_bin` explicitly in the workflow configuration.
