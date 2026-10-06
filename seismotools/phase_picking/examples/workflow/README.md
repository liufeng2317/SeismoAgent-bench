# Phase-picking workflow example

This example creates a deterministic three-component waveform array, runs the
local CPU PhaseNet interface, and checks the probability output. The adapter
returns model probabilities; thresholding and conversion to arrival picks are
left to the surrounding workflow.

The implementation is in `run_workflow.py`; `run.sh` is only a thin shell wrapper.

Run it with:

```bash
bash seismotools/phase_picking/examples/workflow/run.sh /tmp/phase-picking-workflow
```

The synthetic impulse is only an interface demonstration. It is not a trained
model accuracy test or a substitute for waveform quality control.

The output path must not already exist; choose a new temporary path for each run.
