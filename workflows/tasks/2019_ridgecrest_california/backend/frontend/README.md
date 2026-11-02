# Front end for the back-end task

Phase picks and their association to events from an automatic picking and association run on this case's waveforms (PhaseNet picks; association by an automatic associator). They are fixed for the back-end task.

- `picks.csv`: 446,388 picks in the output-contract columns; `event_id` gives the association (empty: unassociated); rows with status `rejected` were rejected by that run. SHA-256 020321ed7830beb23bff038477ab6b8c0139b72d876dfdb7478f637d871a65c6.
- `events.csv`: the 14,164 associated events with their numbers of non-rejected picks. No locations, origin times or magnitudes are given.

Built by `workflows/development/backend_tier_b/build_backend_variants.py` from `runs/tools/claude/glm-5.3/20261029T203757Z/work/picks.csv` (the CSV files are not tracked).
