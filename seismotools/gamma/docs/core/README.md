# GaMMA core usage documents

This directory contains the curated Agent-facing usage documents for GaMMA.
Read the project-level [`../README.md`](../README.md) first, then select the
single guide that matches the required input source.

- `gamma_example_synthetic.md`: minimal synthetic association workflow.
- `gamma_example_phasenet.md`: picks produced by a PhaseNet-style workflow.
- `gamma_example_phasenet_ncedc.md`: NCEDC-style waveform and pick workflow.
- `gamma_example_seisbench.md`: SeisBench input preparation and association.
- `gamma_example_fastapi.md`: service/API usage, only when a service is required.

These documents explain method choices, input preparation, configuration and
quality checks. They are methodological guides, not case observations or
benchmark results. Execute the local benchmark adapter in `../../interface/`;
do not copy commands from a guide without checking its input and output
assumptions.
