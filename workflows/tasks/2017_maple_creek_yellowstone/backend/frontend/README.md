# Front end for the back-end task

Phase picks and their association to events from an automatic picking and association run on this case's waveforms (PhaseNet picks; association by an automatic associator). They are fixed for the back-end task.

- `picks.csv`: 89,447 picks in the output-contract columns; `event_id` gives the association (empty: unassociated); rows with status `rejected` were rejected by that run. SHA-256 3e7b81fc17f2e19d14a75d20f88dba6998ef8f920417905ae201c60e3d007b27.
- `events.csv`: the 3,906 associated events with their numbers of non-rejected picks. No locations, origin times or magnitudes are given.

Built by `workflows/development/backend_tier_b/build_backend_variants.py` from `runs/tools/claude/glm-5.3/20261028T220746Z/work/picks.csv` (the CSV files are not tracked).
