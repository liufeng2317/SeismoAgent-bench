# NonLinLoc

Copied from the actual installed `NLL7.00_src/src` tree, including C headers, build files, README and change notes. The source tree and runtime binaries are kept separate: `source/` contains the C sources and `bin/` contains the host-built executables.

```bash
python seismotools/build_native.py --tool nonlinloc --jobs 4
```

Outputs: `bin/Vel2Grid`, `bin/Grid2Time`, `bin/NLLoc`. Workflow: velocity/control inputs → velocity grids → station travel-time grids → phase observations/control files → hypocenters, residuals and conditional uncertainty products. This build check does not supply case grids or run a localization.

See the bundled [README](source/src/README.txt) and [change notes](source/src/CHANGE_NOTES.txt). The executed case interface is [04_locate_nonlinloc.py](../../workflows/tasks/2019_ridgecrest_california/expert/01_pipeline/04_locate_nonlinloc.py), with [nonlinloc.yaml](../../workflows/tasks/2019_ridgecrest_california/expert/00_config/nonlinloc.yaml). Its linear velocity interpolation, elevation datum and receiver corrections must be recorded explicitly in comparisons.

The project-local Python library is [Nonlinlocpy](Nonlinlocpy/). It provides control, velocity, station, observation, runner and result-parsing helpers. It uses the compiled programs in `../bin` when an explicit binary directory is supplied.

## Python library documentation

The Python package, examples, templates, requirements and its associated
documentation are kept together under `Nonlinlocpy/`. The top-level `docs/`
directory only explains the tool-package layout.
