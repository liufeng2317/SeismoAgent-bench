# Ridgecrest phase-picking workflow test case

This task takes the approved waveform and StationXML manifest and asks an
agent to produce two JSON artifacts:

- `preprocessing.json`: the input traces and preprocessing operations applied;
- `picks.json`: phase-pick records with station, channel, phase, arrival time
  and confidence fields.

The task stops at phase picking. It does not require event association,
location, magnitude estimation or a reference catalog. The included baseline
uses a simple STA/LTA trigger for pipeline validation; it is not a scientific
replacement for PhaseNet.

This workflow test case is maintained separately from the scientific Ridgecrest case package. It exists to validate the benchmark execution and evaluation path.

## Run results

The `runs/` entry is a relative symbolic link to the durable run store for
this task. It exposes completed and in-progress runs without copying their
files into the repository. The link target is grouped by the task's stable
`task_id`, while the physical run store remains outside the source tree.
