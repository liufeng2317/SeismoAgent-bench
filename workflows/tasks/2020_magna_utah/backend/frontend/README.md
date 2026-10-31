# Front end for the back-end task

Phase picks and their association to events from an automatic picking and association run on this case's waveforms (PhaseNet picks; association by an automatic associator). They are fixed for the back-end task.

- `picks.csv`: 145,677 picks in the output-contract columns; `event_id` gives the association (empty: unassociated); rows with status `rejected` were rejected by that run. SHA-256 a63dde58ed411cb620f2f9a16e3bfa34c7b87d540a0c2cfbf27471528f4f3f79.
- `events.csv`: the 3,861 associated events with their numbers of non-rejected picks. No locations, origin times or magnitudes are given.

Built by `workflows/tasks/build_backend_variants.py` from `runs/tools/claude/glm-5.3/20261028T135931Z/work/picks.csv` (the CSV files are not tracked).
