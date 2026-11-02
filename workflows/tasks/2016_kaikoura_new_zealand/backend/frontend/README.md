# Front end for the back-end task

Phase picks and their association to events from an automatic picking and association run on this case's waveforms (PhaseNet picks; association by an automatic associator). They are fixed for the back-end task.

- `picks.csv`: 368,145 picks in the output-contract columns; `event_id` gives the association (empty: unassociated); rows with status `rejected` were rejected by that run. SHA-256 cdc0b1c3b67a51fd0520f1c5ef689c77dc0d7c9062d194367181247b644f2d1c.
- `events.csv`: the 9,152 associated events with their numbers of non-rejected picks. No locations, origin times or magnitudes are given.

Built by `workflows/development/backend_tier_b/build_backend_variants.py` from `runs/tools/claude/glm-5.3/20261029T183933Z/work/picks.csv` (the CSV files are not tracked).
