# Ridgecrest phase-picking task

This task takes the approved waveform and StationXML manifest and asks an
agent to produce two JSON artifacts:

- `preprocessing.json`: the input traces and preprocessing operations applied;
- `picks.json`: phase-pick records with station, channel, phase, arrival time
  and confidence fields.

The task stops at phase picking. It does not require event association,
location, magnitude estimation or a reference catalog. The included baseline
uses a simple STA/LTA trigger for pipeline validation; it is not a scientific
replacement for PhaseNet.
