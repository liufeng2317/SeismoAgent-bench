# NonLinLoc workflow example

This example supplies a synthetic layered velocity model, four synthetic
stations and an eight-pick event observation set. It calls the standard
NonLinLoc adapter, which runs `Vel2Grid`, `Grid2Time` and `NLLoc` in order.

The implementation is in `run_workflow.py`; `run.sh` is only a thin shell wrapper.

Run it with:

```bash
bash seismotools/nonlinloc/examples/workflow/run.sh /tmp/nonlinloc-workflow
```

The output directory contains `run_result.json`, `located_events.csv` and the
native model, travel-time and location products. This is a locator interface
example; the coordinates and picks are synthetic and are not a validated
location benchmark.

The output path must not already exist; choose a new temporary path for each run.
