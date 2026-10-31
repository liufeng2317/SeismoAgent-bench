# Front end for the back-end task

Phase picks and their association to events from an automatic picking and association run on this case's waveforms (PhaseNet picks; association by an automatic associator). They are fixed for the back-end task.

- `picks.csv`: 138,483 picks in the output-contract columns; `event_id` gives the association (empty: unassociated); rows with status `rejected` were rejected by that run. SHA-256 707843556342f1c00b6cc9ff7d43502d1694b4f08004005603aa673ab029669f.
- `events.csv`: the 2,710 associated events with their numbers of non-rejected picks. No locations, origin times or magnitudes are given.

Built by `workflows/tasks/build_backend_variants.py` from `runs/tools/claude/glm-5.3/20261029T084718Z/work/picks.csv` (the CSV files are not tracked).
