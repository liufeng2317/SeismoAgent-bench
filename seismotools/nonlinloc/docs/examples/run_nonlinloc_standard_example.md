# Standard Native NonLinLoc Location

This example shows the shortest native-format NonLinLoc workflow in the local
`nonlinlocpy` package. It is for data that already look close to NonLinLoc
inputs: a 1-D velocity model, a native station table, and either simple relative
pick times or an existing `NLLOC_OBS` file.

The example script is intentionally thin. It reads `nonlinloc_config.json` and
calls the reusable package workflow in `nonlinlocpy.standard_nonlinloc`.

## Workflow

The package workflow is organized as explicit steps:

### Step 1: Load Config

Read `nonlinloc_config.json` into `StandardRunConfig`. The config defines input paths, output path, NonLinLoc binary location, reference date, observation mode, and whether to stop after preparation.

### Step 2: Validate Inputs

Check that `velocity_model_1d.txt` and `stations_native.txt` exist. Then check observation input: use `picks_simple.txt` when `use_native_obs=false`, or `event.obs` when `use_native_obs=true`.

### Step 3: Build Run Directory and Control File

Create a fresh `run_dir` with `model/`, `time/`, `obs/`, and `loc/`. Copy the package `nlloc.in` template, convert `velocity_model_1d.txt` to `LAYER` lines, and patch `VGGRID`, `LOCGRID`, `LOCMETH`, and output settings.

### Step 4: Load Stations

Load `stations_native.txt` as station definitions. Station IDs are expected to already be NonLinLoc-safe; this workflow does not create aliases.

### Step 5: Write Observations

Prepare `obs/All.obs`. If `use_native_obs=false`, convert `picks_simple.txt` using the config `date` as the `YYYYMMDDHHMM` reference time. If `use_native_obs=true`, copy `event.obs` directly.

### Step 6: Build Static NonLinLoc Assets

Run `Vel2Grid` for P and S velocity grids, then run `Grid2Time` to create station travel-time tables under `model/` and `time/`.

### Step 7: Run Location

Run `NLLoc` using the prepared control file and `obs/All.obs`.

### Step 8: Parse and Save Results

Parse NonLinLoc `.hyp` files and write the compact relocated catalog to `located_events.csv`.

This standard case does not do Gamma block parsing, station aliasing, chunked parallel execution, production cleanup policy, or relocation diagnostic plots. Use the Gamma-to-NonLinLoc example for those features.

## Minimal Usage

Run the example:

```bash
python run_nonlinloc_standard_example.py
```

The script loads:

```text
nonlinloc_config.json
```

Equivalent Python usage:

```python
from nonlinlocpy.standard_nonlinloc import config_from_json, run_standard_workflow

config = config_from_json("/path/to/nonlinloc_config.json")
result = run_standard_workflow(config)

print(result.run_dir)
print(result.located_csv)
print(result.n_located_events)
```

Direct config construction is also supported:

```python
from nonlinlocpy.standard_nonlinloc import StandardRunConfig, run_standard_workflow

result = run_standard_workflow(
    StandardRunConfig(
        input_dir="/path/to/inputs",
        run_dir="/path/to/run_case",
        nlloc_bin="/path/to/NLL7.00_src/src",
        date="201907040234",
        use_native_obs=False,
    )
)
```

## Config File

Default config:

```text
example/standard_nonlinloc/nonlinloc_config.json
```

Fields:

```json
{
  "input_dir": "./inputs",
  "run_dir": "./run_case",
  "nlloc_bin": "",
  "date": "201907040234",
  "utm_zone_number": null,
  "utm_zone_letter": null,
  "use_native_obs": false,
  "prepare_only": false
}
```

Notes:

- `nlloc_bin` should point to the directory containing `Vel2Grid`,
  `Grid2Time`, and `NLLoc`. If empty, the package tries known fallback paths.
- `date` is the `YYYYMMDDHHMM` reference time used when converting
  `picks_simple.txt`; each `time_sec` is relative to this reference minute.
- `use_native_obs=false` converts `picks_simple.txt` to `obs/All.obs`.
- `use_native_obs=true` copies `event.obs` to `obs/All.obs`.
- `prepare_only=true` writes inputs but does not run NonLinLoc.

## Input Directory

`input_dir` must contain:

```text
inputs/
  velocity_model_1d.txt
  stations_native.txt
  picks_simple.txt
  event.obs
```

`event.obs` is only required when `use_native_obs=true`. `picks_simple.txt` is
required when `use_native_obs=false`.

### `velocity_model_1d.txt`

Whitespace table with three numeric columns. Comment lines beginning with `#`
are allowed.

```text
depth_km vp_kms vs_kms
```

Example:

```text
# depth_km  vp_kms  vs_kms
0.0    4.74    2.739
1.0    5.01    2.895
2.0    5.35    3.092
```

### `stations_native.txt`

Whitespace station table. Comment lines beginning with `#` are allowed.

```text
station_id longitude latitude elevation_m
```

Example:

```text
# station_id  longitude  latitude  elevation_m
CLC   -117.597510  35.815740   775.0
TOW2  -117.764880  35.808560   685.0
WRC2  -117.650380  35.947900   943.0
```

Station IDs should already be NonLinLoc-safe. This standard workflow does not
build station aliases.

### `picks_simple.txt`

Simple relative pick table. Comment lines beginning with `#` are allowed.

```text
station_id phase time_sec [first_motion]
```

Example:

```text
# station_id  phase  time_sec  [first_motion]
CLC   P  37.7083  ?
CLC   S  42.2283  ?
TOW2  P  37.2883  ?
```

`time_sec` is relative to the config `date` value. For example, with
`date="201907040234"`, a pick time of `37.7083` means
`2019-07-04T02:34:37.7083`.

### `event.obs`

Native `NLLOC_OBS` file. Use this path by setting `use_native_obs=true`.

Example:

```text
CLC    ?    ?    ? P      ? 20190704 0234   37.7083 GAU  2.00e-02 -1.00e+00 -1.00e+00 -1.00e+00
CLC    ?    ?    ? S      ? 20190704 0234   42.2283 GAU  2.00e-02 -1.00e+00 -1.00e+00 -1.00e+00
!END_EVENT
!END_FILE
```

## Output Structure

`run_dir` is recreated and populated as:

```text
run_case/
  nlloc.in
  located_events.csv
  obs/
    All.obs
  model/
    ...
  time/
    ...
  loc/
    ...
```

Some files appear only after execution. If `prepare_only=true`, the run
directory and observations are prepared, but `located_events.csv` is not created.

## Main Outputs

- `nlloc.in`: patched NonLinLoc control file.
- `obs/All.obs`: native observation file used by NonLinLoc.
- `model/`: P/S velocity-grid files from `Vel2Grid`.
- `time/`: station travel-time grids from `Grid2Time`.
- `loc/`: raw NonLinLoc location products.
- `located_events.csv`: compact relocated catalog parsed from `.hyp` files.

## Return Object

`run_standard_workflow(config)` returns `StandardRunResult`:

```python
StandardRunResult(
    run_dir="...",
    located_csv="...",
    n_located_events=0,
)
```

## When To Use

Use this workflow when:

- station IDs are already NonLinLoc-safe;
- picks are already simple relative picks or native `NLLOC_OBS` exists;
- the run is a small native-format test or a minimal absolute-location case;
- you do not need Gamma parsing, station aliasing, chunking, or diagnostic plots.

Use the Gamma-to-NonLinLoc example when the input comes from Gamma event blocks
or when many events need chunked execution and relocation diagnostics.
