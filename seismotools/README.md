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
| PyOcto | Pick association (octree space-time partitioning) | `pyocto/interface/run.py` |
| REAL | Pick association (pick counting on a grid around the initiating station) | `real/interface/run.py` |
| NonLinLoc | Absolute location and travel-time grids (methods GAU_ANALYTIC / EDT / EDT_OT_WT) | `nonlinloc/interface/run.py` (one event), `locate.py` (catalog) |
| HypoInverse | Absolute location, linearised with distance/residual weighting (USGS network locator) | `hypoinverse/interface/run.py` |
| VELEST | Minimum 1-D velocity model: joint inversion of hypocentres, layered P/S velocities and station corrections | `velest/interface/run.py` |
| hypoDD | Relative relocation from catalog and/or cross-correlation times | `hypodd/interface/run.py` |
| GrowClust | Relative relocation, L1 hierarchical cluster growth on cross-correlation times | `growclust/interface/run.py` |
| MatchLocate2 | Template detection with grid-search location (Match&Locate; matched filter as the zero-grid case) | `match_and_locate/interface/prepare.py` then `run.py` |
| ccdt | Waveform cross-correlation differential times (`dt.cc` for hypoDD / GrowClust) | `cross_correlation/interface/run.py` |

The three phase-picking models share one implementation package but remain
separate model choices. `hypoDD` CT and CT+CC are modes of the same program.
Association and location tools share one input contract (stations with latitude/longitude/elevation,
picks or arrivals with `time_utc`, a `depth_km vp_km_s vs_km_s` model with explicit layering), so
methods can be swapped and compared on the same data. MatchLocate2 is built from the upstream source with local patches
(`match_and_locate/source/patches/`) that fix a thread race and unchecked
buffers and speed up the grid stack without changing its output.
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
├── hypodd/{source,runtime,interface,examples,docs}/
├── cross_correlation/{runtime,interface,examples}/   # project-local Python, no native code
├── pyocto/{source/{upstream,patches},runtime,interface,examples}/
├── real/{source/upstream,runtime,interface,examples}/
├── growclust/{source/upstream,runtime,interface,examples}/
├── hypoinverse/{source/upstream,runtime,interface,examples}/
└── match_and_locate/{source/{upstream,patches},runtime,interface,examples,docs}/
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
small synthetic check for each tool, plus the upstream example where one
exists. These
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
- [Match&Locate](match_and_locate/README.md)
- [ccdt cross-correlation](cross_correlation/README.md)
- [PyOcto](pyocto/README.md)
- [REAL](real/README.md)
- [GrowClust](growclust/README.md)
- [HypoInverse](hypoinverse/README.md)
- [Validation tools](support/tools_usage_validation/README.md)
