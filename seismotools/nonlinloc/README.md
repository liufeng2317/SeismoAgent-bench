# NonLinLoc

Copied from the actual installed `NLL7.00_src/src` tree, including C headers, build files, README and change notes. The source tree and runtime binaries are kept separate: `source/` contains the C sources and `bin/` contains the host-built executables.

```bash
python seismotools/build_native.py --tool nonlinloc --jobs 4
```

Outputs: `bin/Vel2Grid`, `bin/Grid2Time`, `bin/NLLoc`. Workflow: velocity/control inputs → velocity grids → station travel-time grids → phase observations/control files → hypocenters, residuals and conditional uncertainty products. This build check does not supply case grids or run a localization.

See the bundled [README](source/src/README.txt) and [change notes](source/src/CHANGE_NOTES.txt). The executed case interface is [04_locate_nonlinloc.py](../../workflows/tasks/2019_ridgecrest_california/expert/01_pipeline/04_locate_nonlinloc.py), with [nonlinloc.yaml](../../workflows/tasks/2019_ridgecrest_california/expert/00_config/nonlinloc.yaml). Its linear velocity interpolation, elevation datum and receiver corrections must be recorded explicitly in comparisons.

The project-local Python entry point is [python/nonlinloc_runner.py](python/nonlinloc_runner.py). It only runs prepared controls in the order `Vel2Grid`, `Grid2Time`, and `NLLoc`; it does not provide a model or hide run-specific files.

## Additional local manuals

- [Program index](docs/python_reference/Nonlinloc/markdown/index.md)
- [Control-file syntax](docs/python_reference/Nonlinloc/markdown/programs/control.ControlFile.md)
- [NLLoc](docs/python_reference/Nonlinloc/markdown/programs/core.NLLoc.md), [Vel2Grid](docs/python_reference/Nonlinloc/markdown/programs/core.Vel2Grid.md), [Grid2Time](docs/python_reference/Nonlinloc/markdown/programs/core.Grid2Time.md)
- [Python reference notes](docs/python_reference/README.md) describe an external helper package; the maintained project entry point is the thin runner under `python/`.

Both the available RST sources and their Markdown conversions are preserved. The original [documentation notice](docs/python_reference/Nonlinloc/markdown/README.md) states that some referenced upstream introduction/installation/tutorial pages were absent from the local snapshot. This transfer cannot make those missing pages complete.
