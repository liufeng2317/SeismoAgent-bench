# Ridgecrest phase-picking workflow test case

This task takes a one-day waveform directory and StationXML manifest and asks
an agent to plan, preprocess and pick phases for the half-open UTC window
`[2019-07-05T00:00:00Z, 2019-07-06T00:00:00Z)`.

The required outputs are:

- `processing_script.py`: the saved executable processing logic used to create
  the other artifacts;
- `task_plan.json`: the selected window, processing steps and method;
- `preprocessing_figure.png`: station distribution and one representative
  preprocessing view;
- `picks.csv`: P/S phase-pick records with station, channel, arrival time and
  confidence. The scorer interchange fields are `station`, `phase` and
  `arrival_time_utc`; status, method and uncertainty may be included;
- `pick_examples.json`: a small inspectable subset of picks.

The task stops at phase picking. It does not require event association,
location, magnitude estimation or a reference catalog. The included baseline
uses a simple STA/LTA trigger for pipeline validation; it is not a scientific
replacement for PhaseNet.

The processing script is part of the output contract. Temporary exploratory
code may be used during development, but the final artifacts must be
reproducible by running the saved script from the declared inputs.

This workflow test case is maintained separately from the scientific Ridgecrest case package. It exists to validate the benchmark execution and evaluation path.

The task definition is split for readability: `task.json` contains structured
metadata and points to `task_prompt.md`, which contains the human-readable task
instructions. `task_prompt.md` is the only supported source for the Agent-facing
task prompt.

## Input manifest vocabulary

The task declares semantic input roles in `task.json` under
`input_requirements`. Each
manifest entry repeats its role in `data_type` and separately records the
physical file representation in `format`. For example, a waveform entry uses
`data_type: waveform` and `format: miniSEED`, while station metadata uses
`data_type: station_metadata` and `format: StationXML`. This distinction keeps
the task meaning independent of a particular file format.

The output requirements are defined in `task_prompt.md`. The Agent may choose
the internal layout and file types required by that task description. An input
manifest is supplied here as an optional detailed description of the waveform
directory and station metadata; the task can also describe inputs directly in
the prompt.

For Codex runs, the framework renders `task.json` and, when supplied,
`input_manifest.json` into `control/agent_prompt.md`. This is a convenience
view; `task_prompt.md` remains the Agent-facing task description.

The task-local `run_config.yaml` defines the runtime input view separately from
the data manifest. Its `input_links` mapping uses the run-local link path as
the key and an input-manifest `id` as the value. For this task, the Agent sees
`work/input/waveforms` and `work/input/stationxml`; the large source files are
not copied into the run.

## Run

Use the task-local script:

```bash
bash run.sh
```

Each invocation gets a UTC-timestamped `run_id`. Set `RUN_ID` when a stable
custom identifier is needed. Set `PYTHON` or `CODEX_BIN` only when the default
executable locations are not available.

## Run results

The `runs/` entry is a relative symbolic link to the durable run store for
this task. It exposes completed and in-progress runs without copying their
files into the repository. The link target is grouped by the task's stable
`task_id`, while the physical run store remains outside the source tree.

Each run has four framework-level directories:

```text
<run_id>/
├── control/       # task and input snapshots supplied to the Agent
├── work/          # the only Agent work root; its internal layout is Agent-defined
├── record/        # execution log, commands and run metadata
└── evaluation/    # external artifact-contract score and report
```

The framework records the files written under `work/`. Scientific evaluation
is performed by a task-specific external scorer rather than by this run
script. Runtime HOME and temporary files are kept outside the run directory.
