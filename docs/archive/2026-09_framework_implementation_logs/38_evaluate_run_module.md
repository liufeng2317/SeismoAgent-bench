# Stage 38: Dedicated evaluation workflow module

- **Commit:** `d4861d4` (`Extract evaluate run workflow module`)
- **Goal:** keep completed-run evaluation separate from the legacy combined task wrapper.
- **Implemented:** moved artifact validation, deterministic scoring, optional scientific scoring, and evaluation report updates into `workflow/evaluate_run.py`; kept `workflow/pipeline.py` as a compatibility wrapper exposing `run_task()` and re-exporting `evaluate_run()`.
- **Compatibility:** existing Python callers using `run_task()` continue to execute and evaluate in one call. The command-line workflow remains execute first, then external `evaluate`.
- **Validation:** focused workflow/CLI tests passed; full suite passed with 106 tests.
