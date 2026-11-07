# Run audit and process metrics

`audit_runs.py` reads every Agent run (execution log, work directory, final checker report, scores) and writes, in `outputs/` (not tracked):

- `runs.csv`: one row per run: cost, hours, web access, skill files read and skill scripts run, template matching run and detections merged, relative relocation run and submitted, checker runs, locator runs and their velocity-model files, the final flags and key measurements (single-depth pile, S−P depth offset, events beyond the stations, P-only pick-group spread), the scorer's audit, failed criteria (and the development-window rescore of formal runs);
- `process.md`: the process metrics per run: template matching merged, relocation run, reliable flags left, noisy pick group adopted, events beyond the network kept, dispositions accepted, products in place.

```bash
python workflows/development/run_audit/audit_runs.py [--variants dev_knowledge tools]
```

It takes about a minute and a half for all runs. Run it after every development round; the process metrics say whether a skill changed what the Agent did, with one run per case, before the outcome (failed criteria) can show it. Findings: [record 19](../../../docs/research/progress/records/19_run_audit.md).
