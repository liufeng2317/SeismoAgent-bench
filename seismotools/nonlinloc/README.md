# NonLinLoc

NonLinLoc is the native absolute earthquake-location package used by this
project. It converts a velocity model and station travel-time grids into
probabilistic hypocenter solutions from phase observations. The package
contains the original C implementation, project-managed compiled executables,
and a local Python interface for preparing inputs, running the binaries and
parsing results.

The shared tool directory contains software and reusable resources only.
Control files, grids, observations, logs and location results belong in a
separate task or experiment run directory.

## Directory layout

```text
nonlinloc/
├── source/       # Native NonLinLoc C source, headers and build files
├── bin/          # Compiled Vel2Grid, Grid2Time and NLLoc executables
├── Nonlinlocpy/  # Python package, examples, templates and detailed docs
└── README.md     # This overview and usage guide
```

### `source/`

This is the native source snapshot. It is useful for inspecting the original
implementation or rebuilding the executables. It is not a run directory.

### `bin/`

This contains the host-built programs:

- `Vel2Grid`: generate velocity grids from control files;
- `Grid2Time`: generate station travel-time grids;
- `NLLoc`: locate events from phase observations and travel-time grids.

Rebuild them, when necessary, with:

```bash
python seismotools/build_native.py --tool nonlinloc --jobs 4
```

### `Nonlinlocpy/`

This is the project-local copy of the Python interface from TRACE-1.1. It
contains the `nonlinlocpy/` package, example workflows, templates,
requirements and detailed documentation. Its interface uses the sibling
`../bin/` executables when that directory is supplied explicitly.

Start with [Nonlinlocpy/README.md](Nonlinlocpy/README.md). The package-level
reference material is in [Nonlinlocpy/docs/README.md](Nonlinlocpy/docs/README.md)
and its workflow guidance is in [Nonlinlocpy/docs/SKILL.md](Nonlinlocpy/docs/SKILL.md).

## Native shell usage

The original NonLinLoc interface is a sequence of command-line programs. A
run directory should contain the relevant control files and should receive
all generated grids, logs and solutions.

For a prepared run directory:

```bash
PROJECT=/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench
BIN="$PROJECT/seismotools/nonlinloc/bin"
RUN=/path/to/a/task/run

cd "$RUN"
"$BIN/Vel2Grid" vel2grid.in
"$BIN/Grid2Time" grid2time.in
"$BIN/NLLoc" nlloc.in
```

The control files determine the input and output prefixes. A typical sequence
is:

1. `Vel2Grid` reads a velocity/control file and writes velocity grids;
2. `Grid2Time` propagates travel times for the configured stations;
3. `NLLoc` reads an `NLLOC_OBS` observation file and writes `.hyp`,
   `.loc.hyp`, residual and uncertainty products.

The exact control syntax is defined by the native source and its bundled
examples. The project Ridgecrest workflow records its case-specific settings
in [nonlinloc.yaml](../../workflows/tasks/2019_ridgecrest_california/expert/00_config/nonlinloc.yaml)
and runs the native interface from
[04_locate_nonlinloc.py](../../workflows/tasks/2019_ridgecrest_california/expert/01_pipeline/04_locate_nonlinloc.py).

## Python usage with Nonlinlocpy

Use the Python interface when the workflow needs to create or patch control
files, convert simple pick tables, run a prepared case, parse `.hyp`
solutions, or process many events in chunks.

Add the bundled package to the Python path when it has not been installed:

```bash
export PYTHONPATH="$PROJECT/seismotools/nonlinloc/Nonlinlocpy:$PYTHONPATH"
```

### Run a prepared directory

The `run_nlloc` helper expects a prepared run directory containing
`nlloc.in`, model/travel-time assets and station setup. It can convert a
simple pick table into `NLLOC_OBS`, run `NLLoc`, parse the resulting
solutions and write a compact CSV table.

```python
from nonlinlocpy import NLLocConfig, run_nlloc

solutions = run_nlloc(
    NLLocConfig(
        nlloc_bin="/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/nonlinloc/bin",
        control_dir="/path/to/a/task/run",
        picks="/path/to/picks_simple.txt",
        date="201907050000",
        output_csv="located_events.csv",
    )
)
print(f"located events: {len(solutions)}")
```

If the observation file is already prepared, set `skip_obs=True` and keep
the existing observation file in the run directory.

### Use the complete example workflows

For input preparation and static grid generation, use the high-level workflows:

```python
from nonlinlocpy import StandardRunConfig, run_standard_workflow

result = run_standard_workflow(StandardRunConfig(
    input_dir="./inputs",
    run_dir="./run_case",
    nlloc_bin="/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/nonlinloc/bin",
    use_native_obs=False,
))
```

Use `run_example_workflow(ExampleRunConfig(...))` for Gamma-associated
catalogs, especially when station aliases, event parsing and observation
conversion are needed. Use `run_standard_workflow` for native station tables,
simple picks and a conventional 1-D model.

For large event sets, the package also provides
`ParallelNLLocConfig` and `run_parallel_nlloc_workflow` for chunked runs.
Only use the parallel interface after the shared model and travel-time assets
have been prepared.

## Tool validation and references

Run the project validation suite with:

```bash
bash seismotools/tools_usage_validation/run_all.sh
```

The NonLinLoc check covers the native three-stage chain, a bounded Ridgecrest
event, Python package import, default sibling-binary resolution and the
packaged control template. Its results are written under the ignored
`seismotools/tools_usage_validation/outputs/` directory.

Further references:

- [Nonlinlocpy API and examples](Nonlinlocpy/README.md)
- [Nonlinlocpy detailed documentation](Nonlinlocpy/docs/README.md)
- [Nonlinlocpy workflow guidance](Nonlinlocpy/docs/SKILL.md)
- [Native source README](source/src/README.txt)
- [Native change notes](source/src/CHANGE_NOTES.txt)
