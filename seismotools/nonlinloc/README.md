# NonLinLoc

NonLinLoc is the native probabilistic earthquake-location tool used by this
project. It builds velocity and travel-time grids and then locates events from
phase observations. This directory keeps the source, host-built executables,
Python helpers and a small reproducible example separate from case data and
run outputs.

## Directory layout

```text
nonlinloc/
├── source/                 # Native NonLinLoc C source and build files
├── runtime/
│   ├── bin/                # Vel2Grid, Grid2Time and NLLoc for this host
│   └── python/Nonlinlocpy/ # Project-local Python interface and references
├── interface/              # Stable project CLI and input/output contracts
├── examples/{smoke,workflow}/ # Executable examples, no case catalog data
├── docs/{core,examples}/  # Curated method guides and workflow notes
├── metadata.json           # Tool and interface identity
└── README.md
```

`runtime/bin` is host-specific and may be rebuilt from `source/`. The Python
package is a local copy of the interface used by the project; its detailed API
and examples are documented in
[`runtime/python/Nonlinlocpy/README.md`](runtime/python/Nonlinlocpy/README.md).

## Standard project interface

Use the stable adapter when an agent or workflow needs a predictable command:

```bash
python seismotools/nonlinloc/interface/run.py \
  --input-dir /path/to/nonlinloc-inputs \
  --output-dir /path/to/writable-run \
  --bin-dir /liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/nonlinloc/runtime/bin
```

The input directory contains `velocity_model_1d.txt`, `stations_native.txt` and
`picks_simple.txt`. The adapter creates all controls, grids, logs and location
products below the writable output directory. `--native-obs` can be used when
`event.obs` is already in NonLinLoc's `NLLOC_OBS` format. Input and output
contracts are recorded in [`interface/input_schema.json`](interface/input_schema.json)
and [`interface/output_schema.json`](interface/output_schema.json).

The adapter validates required files and executables, runs `Vel2Grid`,
`Grid2Time` and `NLLoc` in order, and exits non-zero if a stage fails. It does
not silently turn a failed grid or locator run into an empty catalog.

A complete local smoke test is:

```bash
bash seismotools/nonlinloc/examples/smoke/run.sh /tmp/nonlinloc-smoke
```

For a complete offline prepared-input workflow, see [examples/workflow](examples/workflow).

### Catalog locator (many events)

`interface/locate.py` (interface version 3) locates a whole catalog of arrival
groups: travel-time grids once per station, one NLLoc run per event in a thread
pool, optional fixed station delays, selectable location method
(`GAU_ANALYTIC`, `EDT`, `EDT_OT_WT`). Inputs are plain CSV/text (arrivals,
stations with latitude/longitude/elevation, a 1-D model); outputs are
`events.csv` and `arrivals.csv` with residuals. See
[`interface/README.md`](interface/README.md#catalog-locator-locatepy-interface-version-3).


## Native command-line usage

For advanced case-specific controls, run the native programs directly in a
writable run directory. The control file syntax is defined by the bundled
source and Nonlinlocpy templates:

```bash
BIN=/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/nonlinloc/runtime/bin
cd /path/to/writable-run
"$BIN/Vel2Grid" vel2grid.in
"$BIN/Grid2Time" grid2time.in
"$BIN/NLLoc" nlloc.in
```

Each command must be checked by the caller; generated model, travel-time,
observation and location files belong to the run directory, never this shared
tool directory.

## Python interface

For prepared directories and advanced workflows, add the bundled package to
`PYTHONPATH` or install it in the active environment:

```bash
export PYTHONPATH="$PWD/seismotools/nonlinloc/runtime/python/Nonlinlocpy:$PYTHONPATH"
```

Additional generic examples and Agent-oriented summaries are in [docs/README.md](docs/README.md).

The package exposes `run_nlloc`, `run_standard_workflow`,
`run_example_workflow` and the parallel workflow helpers. Use the standard
interface above for benchmark calls; use these Python APIs when a case needs
custom control generation, Gamma observation conversion, parsing, or chunked
execution. See the package README and its `docs/` material for the API and
native control reference.

## Validation

The project validation checks package import, bundled template resolution, the
three native stages on a tiny synthetic grid, one bounded Ridgecrest event, the
adapter's smoke solution under all three location methods, the catalog locator
on a synthetic half-space case (known hypocentres; one outlier pick) and its
reproduction of 50 Prague expert (r2) locations:

```bash
python seismotools/support/tools_usage_validation/validate_nonlinloc.py
```

This verifies executability and input/output plumbing. It is not a claim that a
new case catalog is scientifically equivalent to an expert catalog.
