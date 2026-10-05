# NonLinLoc directory guide

```text
nonlinloc/
├── source/       # Native NonLinLoc C source code
├── bin/          # Compiled Vel2Grid, Grid2Time and NLLoc executables
├── Nonlinlocpy/  # Python package, examples, templates and its documentation
├── docs/         # This short package-layout guide
└── README.md
```

Run-specific control files, velocity grids, travel-time grids, observations
and location outputs belong in a task or experiment output directory. They
must not be written into this shared tool package.
