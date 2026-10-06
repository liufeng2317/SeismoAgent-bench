# hypoDD

hypoDD is a double-difference earthquake-relocation program. It refines an
event cluster from catalog differential times (`dt.ct`) and, when available,
waveform cross-correlation differential times (`dt.cc`). The native solver is
supplemented by a local Python interface for input conversion, FDTCC and
parallel workflows.

## Directory layout

```text
hypodd/
├── source/                 # Native hypoDD/ph2dt Fortran/C source and manuals
├── runtime/
│   ├── bin/                # Compiled hypoDD and ph2dt executables
│   ├── build/              # Host-specific ignored build tree
│   └── python/HypoDDpy/    # Python interface, templates and examples
├── interface/              # Stable native CT/CT+CC entry point and contracts
├── examples/smoke/          # Small executable CT relocation example
├── logs/                   # Ignored build logs
├── metadata.json
└── README.md
```

`runtime/bin`, `runtime/build` and `logs` are host-specific artifacts and are
not committed. Rebuild the native programs from `source/` with:

```bash
python seismotools/support/build_native.py --tool hypodd --jobs 4
```

## Standard interface

Use `interface/run.py` for a predictable native relocation call:

```bash
python seismotools/hypodd/interface/run.py \
  --input-dir /path/to/hypodd-inputs \
  --output-dir /path/to/writable-run \
  --mode ct \
  --bin-dir /liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/hypodd/runtime/bin
```

The input directory contains `hypoDD.inp`, `event.dat`, `station.dat` and
`dt.ct`. `--mode ct_cc` additionally requires `dt.cc`. Use `--run-ph2dt` only
when `ph2dt.inp` is provided and catalog differential times must be generated
first. The adapter copies inputs into the writable run directory, checks native
exit status, records `hypodd.log`, and requires `hypoDD.loc` before reporting
success.

Input and output details are defined in:

- [interface/input_schema.json](interface/input_schema.json)
- [interface/output_schema.json](interface/output_schema.json)

A minimal smoke test is:

```bash
bash seismotools/hypodd/examples/smoke/run.sh /tmp/hypodd-smoke
```

## Native command-line usage

For advanced controls, run the native programs directly in a writable run
directory:

```bash
BIN=/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/hypodd/runtime/bin
cd /path/to/writable-run
"$BIN/ph2dt" ph2dt.inp       # optional input-generation stage
"$BIN/hypoDD" hypoDD.inp
```

The native solver does not calculate waveform cross-correlation times itself;
`dt.cc` must be prepared before a CT+CC or CC-only relocation.

## Python interface

The project-local Python package is under
`runtime/python/HypoDDpy/`. Add it to `PYTHONPATH` or install it in the active
environment:

```bash
python -m pip install -e "$PWD/seismotools/hypodd/runtime/python/HypoDDpy" --no-build-isolation
```

Its public package is `hypodd_runner` and provides:

- catalog-only CT relocation;
- CT+CC and CC-only workflows;
- event/station/phase input conversion;
- FDTCC preparation;
- time-window planning and parallel execution.

Use the Python package for these advanced workflows, while using the standard
adapter for benchmark calls with a fixed input/output boundary. Its detailed
interface card is in
[`runtime/python/HypoDDpy/docs/HYPODDPY_CARD.md`](runtime/python/HypoDDpy/docs/HYPODDPY_CARD.md).

## Validation

Run the project validation with:

```bash
conda run -n seismoagent python seismotools/support/tools_usage_validation/validate_hypodd.py
```

The check covers the local Python package and templates, a synthetic native CT
relocation, and a bounded Ridgecrest CT replay. Passing verifies local
execution and file plumbing, not scientific accuracy of a full relocation
catalog.
