# HypoDDpy

This directory contains the project-local `hypodd_runner` Python package for
catalog differential-time, waveform FDTCC and CC-only HypoDD workflows.

Import the package with:

```bash
export PYTHONPATH=/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/hypodd/runtime/python/HypoDDpy:$PYTHONPATH
```

The main public entry points are:

- `run_catalog_only_relocation`;
- `run_fdtcc_relocation`;
- `run_cc_only_relocation`;
- `build_hypodd_inputs`;
- `plan_time_windows`.

The package expects the native hypoDD source/build root and task-specific input
paths to be supplied explicitly. It does not use the example paths as defaults
for a scientific run. Templates are under
[hypodd_runner/template](hypodd_runner/template), examples are under
[../examples](../examples), and the detailed interface contract is in
[docs/HYPODDPY_CARD.md](docs/HYPODDPY_CARD.md).

For the complete package and native-tool overview, see the parent
[hypoDD README](../README.md).

