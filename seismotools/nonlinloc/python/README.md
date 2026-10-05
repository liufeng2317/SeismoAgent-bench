# NonLinLoc Python runner

`nonlinloc_runner.py` is a thin project-local wrapper around the three native
programs in `../bin`. It does not choose a velocity model or generate control
files. A task must prepare those files in its own run directory, then execute
the stages in this order:

```text
Vel2Grid → Grid2Time (one or more controls) → NLLoc
```

Example:

```bash
python seismotools/nonlinloc/python/nonlinloc_runner.py \
  --work-dir /path/to/run \
  --velocity-control /path/to/run/grids/P.in \
  --travel-time-control /path/to/run/grids/P.in \
  --travel-time-control /path/to/run/grids/S.in \
  --location-control /path/to/run/event/control.in
```

The wrapper captures each command's output and stops immediately if a stage
fails. It never writes to `seismotools/nonlinloc`; all generated files belong
to the caller's run directory.
