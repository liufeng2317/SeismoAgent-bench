# Stage 51: Unique default run ID

- **Goal:** allow repeated `bash run.sh` invocations without overwriting a previous run.
- **Implemented:** the phase-picking task script now uses a UTC-timestamped default `run_id`; users can still set `RUN_ID` explicitly for a stable identifier.
- **Validation:** shell syntax and diff checks passed.
- **Git:** `d9890f1` (`Use unique default task run ids`).
