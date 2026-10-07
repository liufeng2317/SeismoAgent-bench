# Seismotools

`seismotools` contains the local seismological software used by benchmark
workflows. Each tool is kept as an independent package with its own source,
runtime resources, stable interface, examples and README. Case data, reference
catalogs and workflow outputs are stored outside this directory.

## Available tools

| Tool | Role | Standard entry point |
| --- | --- | --- |
| PhaseNet, EQTransformer, DPPPicker P | Phase probability inference | `phase_picking/interface/run.py` or `run_continuous.py` |
| GaMMA | Pick association | `gamma/interface/run.py` |
| NonLinLoc | Absolute location and travel-time grids | `nonlinloc/interface/run.py` |
| hypoDD | Relative relocation from catalog and/or cross-correlation times | `hypodd/interface/run.py` |

The three phase-picking models share one implementation package but remain
separate model choices. `hypoDD` CT and CT+CC are modes of the same program.
The standard interfaces define the reproducible input and output boundary;
advanced workflows may use the bundled Python or native interfaces directly.

## Common layout

```text
seismotools/
├── README.md
├── support/                         # integrity checks and tool validation
├── phase_picking/
│   ├── source/                      # model implementation
│   ├── runtime/weights/             # local model weights and metadata
│   ├── interface/                  # inference entry points and contracts
│   ├── examples/{smoke,workflow}/  # runnable examples
│   └── docs/{core,examples}/       # method notes and reference examples
├── gamma/{source,interface,examples,docs}/
├── nonlinloc/{source,runtime,interface,examples,docs}/
└── hypodd/{source,runtime,interface,examples,docs}/
```

Read the tool-specific README before using an interface. It records the
required input format, model or binary identity, important parameters and
generated products.

## Environment and validation

Run checks with the Python environment that provides the scientific
dependencies. The project evaluation environment is normally selected as
follows:

```bash
export PYTHON=/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python
"$PYTHON" seismotools/support/check_tools.py
"$PYTHON" seismotools/support/check_tools.py --imports
PYTHON="$PYTHON" bash seismotools/support/tools_usage_validation/run_all.sh
```

The integrity check verifies the tracked tool snapshot. The import check loads
the local Python packages and model weights on CPU. `run_all.sh` executes a
small synthetic check and a bounded Ridgecrest data check for each tool. These
checks verify that the local interfaces start and produce expected artifacts;
they do not establish scientific accuracy of a complete catalog.

Native tools can be rebuilt when a compiler toolchain is available:

```bash
"$PYTHON" seismotools/support/build_native.py --tool all --jobs 4
```

Generated binaries, build products, validation outputs and model weights are
runtime resources and are not intended to be committed as source code. A
checkout that excludes those resources must restore them before running the
corresponding validation.

## Interface conventions

Interfaces read declared inputs and write all generated products below a
caller-provided output directory. They record a versioned `run_result.json`,
return a nonzero status on failure, and protect existing outputs unless an
explicit overwrite option is supplied. Configuration files and command-line
arguments are documented by each interface; command-line values take
precedence when both are provided.

The interfaces do not decide case-level scientific policy. Preprocessing,
probability thresholds, pick extraction, association settings, velocity-model
choices and quality control must be stated by the calling workflow and recorded
with its results.

## Data and reproducibility boundary

Do not place waveform archives, StationXML, reference catalogs or experiment
outputs in this package. A workflow should record the selected tool metadata,
model weights or binary versions, effective parameters, input paths and output
paths. Shared tool source, weights, binaries and documentation must remain
unchanged during an agent run.

For implementation details and model-specific constraints, follow:

- [Phase picking](phase_picking/README.md)
- [GaMMA](gamma/README.md)
- [NonLinLoc](nonlinloc/README.md)
- [hypoDD](hypodd/README.md)
- [Validation tools](support/tools_usage_validation/README.md)
