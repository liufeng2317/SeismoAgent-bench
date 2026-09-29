# Stage 47: Folder-based phase-picking task

- **Goal:** turn the Ridgecrest phase-picking case into a one-day data-processing task instead of a fixed three-file smoke input.
- **Implemented:** added directory input support with `path_type: directory`; fixed the UTC window to `[2019-07-05T00:00:00Z, 2019-07-06T00:00:00Z)`; required an explicit planning output; replaced JSON picks with `picks.csv`; added a combined station/preprocessing figure and inspectable pick examples; updated the baseline and task documentation.
- **Validation:** the phase-picking task tests passed (2 tests); the full test suite passed (110 tests).
- **Git:** `e9ce886` (`Define folder-based phase picking task`).
