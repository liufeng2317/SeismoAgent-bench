# hypoDD

hypoDD is a double-difference earthquake-relocation program. It refines the
relative locations of an event cluster from catalog differential times
(`dt.ct`) and, when available, waveform cross-correlation differential times
(`dt.cc`). The native solver is separate from the project Python interface,
which prepares phase/station inputs, runs `ph2dt` and hypoDD, optionally
prepares FDTCC inputs, and parses relocation outputs.

The shared tool directory contains source code, compiled programs and reusable
Python code only. Event files, differential-time files, control files, logs and
relocated catalogs must be written to a task or experiment output directory.

## Directory layout

```text
hypodd/
├── native/
│   ├── source/       # Native hypoDD/ph2dt Fortran/C source and manuals
│   ├── build/        # Local build tree; ignored and reproducible from source/
│   └── bin/          # Compiled hypoDD and ph2dt executables; ignored artifacts
├── HypoDDpy/
│   ├── hypodd_runner/ # Python package and packaged templates/FDTCC interface
│   ├── docs/          # Python interface card and usage notes
│   ├── examples/      # Example CT, CT+CC and FDTCC workflows
│   └── pyproject.toml # Local package definition
├── logs/             # Local build logs; ignored
└── README.md         # This overview and usage guide
```

### `native/`

The native source is the preserved implementation used to build
`native/bin/hypoDD`. The build tree and executable are host-specific and are
not committed to Git. Rebuild them with:

```bash
python seismotools/build_native.py --tool hypodd --jobs 4
```

The resulting executables are:

```text
seismotools/hypodd/native/bin/hypoDD
seismotools/hypodd/native/bin/ph2dt
```

The source distribution includes the original [README](native/source/README)
and [hypoDD manual](native/source/doc/hypoDD.pdf).

### `HypoDDpy/`

This is the project-local Python interface copied from TRACE-1.1. Its public
package is `hypodd_runner`. It provides catalog-only CT relocation,
waveform-based FDTCC relocation, CC-only relocation, input conversion,
time-window planning and output checks. The detailed interface card is
[HypoDDpy/docs/HYPODDPY_CARD.md](HypoDDpy/docs/HYPODDPY_CARD.md).

## Native command-line usage

A native run directory normally contains:

- an event catalog, commonly `event.dat`;
- a station table, commonly `station.dat`;
- catalog differential times in `dt.ct`;
- optional waveform cross-correlation times in `dt.cc`;
- a hypoDD control file, commonly `hypoDD.inp`.

Run the compiled solver from that directory:

```bash
PROJECT=/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench
BIN="$PROJECT/seismotools/hypodd/native/bin"
RUN=/path/to/a/hypodd/run

cd "$RUN"
"$BIN/hypoDD" hypoDD.inp
```

The control file specifies the input files, CT/CC weighting, iteration rows and
output names. Typical outputs include `hypoDD.loc`, `hypoDD.reloc`,
`hypoDD.res`, `hypoDD.stares` and `hypoDD.srcpar`. The native solver does
not measure waveform cross-correlation itself; `dt.cc` must be prepared
before the inversion.

When catalog differential times must be generated from phase picks, run the
native `ph2dt` program first with its own control file, then pass the generated
`dt.ct` to `hypoDD`:

```bash
"$BIN/ph2dt" ph2dt.inp
"$BIN/hypoDD" hypoDD.inp
```

## Python usage

Install the local package into the active environment, or add its directory to
the Python path for a source-tree run:

```bash
python -m pip install -e "$PROJECT/seismotools/hypodd/HypoDDpy" --no-build-isolation
```

or:

```bash
export PYTHONPATH="$PROJECT/seismotools/hypodd/HypoDDpy:$PYTHONPATH"
```

The public API is grouped by workflow:

- `run_catalog_only_relocation`: catalog differential times (`dt.ct`);
- `run_fdtcc_relocation`: catalog times plus waveform FDTCC times;
- `run_cc_only_relocation`: relocation from CC differential times;
- `build_hypodd_inputs`: prepare event, station and phase inputs;
- `plan_time_windows`: split larger catalogs into reproducible windows.

A minimal catalog-only call is:

```python
from hypodd_runner import (
    EventSelection,
    HypoDDInputs,
    HypoDDParams,
    Ph2dtParams,
    RuntimeOptions,
    run_catalog_only_relocation,
)

result = run_catalog_only_relocation(
    inputs=HypoDDInputs(
        hypo_root="/path/to/hypodd/native/build",
        phase_file="/path/to/events.pha",
        station_file="/path/to/stations.sta",
        output_folder="/path/to/run",
        catalog_code="ridgecrest_ct",
    ),
    selection=EventSelection(
        phase_format="auto",
        ot_range=("2019-07-04", "2019-07-07"),
        lat_range=(35.45, 36.05),
        lon_range=(-117.8, -117.25),
    ),
    ph2dt=Ph2dtParams(),
    hypodd=HypoDDParams(),
    runtime=RuntimeOptions(num_workers=1),
)
```

For CT+CC or CC-only workflows, provide waveform data and the FDTCC
configuration through `FDTCCParams`, then record the waveform window,
correlation threshold, velocity model and final CT/CC weights in the run
metadata.

The packaged examples under [HypoDDpy/examples](HypoDDpy/examples) include
Ridgecrest catalog-only and FDTCC workflows. They are examples, not universal
scientific settings; replace their paths, time ranges and model parameters for
a new case.

## Validation and references

Run the project-level validation suite:

```bash
bash seismotools/tools_usage_validation/run_all.sh
```

The hypoDD validation checks the native solver with synthetic input and a
bounded Ridgecrest CT replay. It also checks that the bundled Python package,
templates and public API can be imported without relying on an installed copy.

Further references:

- [HypoDDpy interface card](HypoDDpy/docs/HYPODDPY_CARD.md)
- [HypoDDpy package](HypoDDpy/hypodd_runner)
- [HypoDDpy examples](HypoDDpy/examples)
- [Native hypoDD README](native/source/README)
- [Native hypoDD manual](native/source/doc/hypoDD.pdf)
