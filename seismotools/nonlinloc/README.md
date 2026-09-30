# NonLinLoc

Copied from the actual installed `NLL7.00_src/src` tree, including C headers, build files, README and change notes. Existing executable/object files were not copied; binaries are rebuilt for the current host in a separate `build/` tree.

```bash
python seismotools/build_native.py --tool nonlinloc --jobs 4
```

Outputs: `bin/Vel2Grid`, `bin/Grid2Time`, `bin/NLLoc`. Workflow: velocity/control inputs → velocity grids → station travel-time grids → phase observations/control files → hypocenters, residuals and conditional uncertainty products. This build check does not supply case grids or run a localization.

See the bundled [README](source/src/README.txt) and [change notes](source/src/CHANGE_NOTES.txt). The installed native tree has only source documentation; additional available manuals have now been copied from the local Nonlinlocpy documentation tree. The executed case interface is [04_locate_nonlinloc.py](../../workflows/tasks/2019_ridgecrest_california/expert/01_pipeline/04_locate_nonlinloc.py), with [nonlinloc.yaml](../../workflows/tasks/2019_ridgecrest_california/expert/00_config/nonlinloc.yaml). Its linear velocity interpolation, elevation datum and receiver corrections must be recorded explicitly in comparisons.

## Additional local manuals

- [Program index](docs/from_nonlinlocpy/Nonlinloc/markdown/index.md)
- [Control-file syntax](docs/from_nonlinlocpy/Nonlinloc/markdown/programs/control.ControlFile.md)
- [NLLoc](docs/from_nonlinlocpy/Nonlinloc/markdown/programs/core.NLLoc.md), [Vel2Grid](docs/from_nonlinlocpy/Nonlinloc/markdown/programs/core.Vel2Grid.md), [Grid2Time](docs/from_nonlinlocpy/Nonlinloc/markdown/programs/core.Grid2Time.md)
- [Local wrapper documentation](docs/from_nonlinlocpy/README.md) and its original `SKILL.md` are reference material; the wrapper itself is not the native implementation used by the expert pipeline.

Both the available RST sources and their Markdown conversions are preserved. The original [documentation notice](docs/from_nonlinlocpy/Nonlinloc/markdown/README.md) states that some referenced upstream introduction/installation/tutorial pages were absent from the local snapshot. This transfer cannot make those missing pages complete.
