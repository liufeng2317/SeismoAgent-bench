# Ridgecrest earthquake-catalog task

This package defines the catalog-construction task for the 2019 Ridgecrest
sequence. It is separate from the lightweight phase-picking workflow test in
`workflows/workflow_tests/2019_ridgecrest_california_phasepicking/`.

The task input is described by `input.json`. At runtime the declared source
folder is linked read-only as:

```text
$BENCH_OUTPUT/input/waveforms/
├── data/       waveform files
└── stations/   StationXML and station metadata
```

The Agent explores the available data, records its selected time coverage and
processing decisions in its task output, and writes a candidate earthquake
catalog. The human-readable instructions are in `task_prompt.md`. The optional
`output_contract.json` declares the required `catalog.json` artifact for
external artifact validation and catalog scoring.

`baseline_agent.py` is the deterministic infrastructure baseline. It exercises
the task, output validation and scoring path; it is not a scientific detector,
phase picker or location solution. The expert scientific workflow and its
intermediate analyses are kept under `expert/`.

Large waveform files, source catalogs and generated analysis products remain in
the external data store and are not copied into Git.
