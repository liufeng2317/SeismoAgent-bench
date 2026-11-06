# End-to-end smoke test without a model

Checks the whole path of a run once the checker, the knowledge skill, the runner or the scorer has changed, without spending a model run: the runner builds a real run directory for a back-end arm, `scripted_agent.py` takes the Agent's place, and the scorer scores the run with its checker audit.

`scripted_agent.py` lists what the run gives the Agent (`work/smoke/inputs.json`: input entries, the skills reachable through them, the `BENCH_*` variables), submits the catalog and picks of an earlier completed run unchanged, runs the checker as the catalog-checker skill asks (`--stage all` with waveforms and StationXML) and `region.py`, and writes a `justified` disposition for every flag.

```bash
bash workflows/development/smoke_end_to_end/run.sh [CASE] [VARIANT] [SOURCE_RUN]
# defaults: 2018_kilauea_hawaii, backend_knowledge, its run of 2026-11-03; SOURCE_RUN is the full path of the run directory
```

Runs go to `workflows/tasks/<case>/runs_smoke/<variant>/scripted/none/<run_id>/` (not tracked; scorable, never in the summary). What to read afterwards:

- `record/run_result.json`: state `completed`;
- `evaluation/metrics.json`: `completion.completed`; `checker` (`flags_agree`, `report_on_submission`, `complete`); `process.leakage` (no flag); `headline` and `trust` equal to the source run's, since the products are the same;
- `work/checker/final/checker_report.json`: the checks of the current version are present (for 1.3: `wadati_origin_offset` judged, `events_beyond_stations` reported; for 1.4 also `location_uncertainty` and `station_residual_spread` reported).

The generic `run-agent` path does not apply the environment configuration (package policy and environment fingerprint) that `run-claude` and `run-codex` apply; those are covered by `tests/execution/test_environment.py`.

Log:

- 2026-11-05, checker 1.3 freeze: Kīlauea `backend_knowledge` (source run 20261103T010127Z): the scripted Agent took 4.5 minutes (the checker with waveforms), scoring a few minutes more. Run completed, contract met, the scorer's re-run gave the same two flags as the submitted report, both disposed, no leakage flag; headline and failed criteria identical to the source run (`depth_pileup`); `wadati_origin_offset` 0.017 s (judged, passes), `events_beyond_stations` 6.5 % (the scorer's `out_of_coverage_fraction` 6.5 %).
- 2026-11-05, after moving the checker to `seismo_checker/`: Kīlauea `backend_knowledge` again (passed; provenance records seismotools and seismo_checker; contract report type `seismo-checker-report`). Then the first full-pipeline package, Maple `knowledge` (source: the formal tools run 20261028T220746Z): run completed, prompt carries `TOOLS_BASE_PATH` and `CHECKER_PATH`, both skills visible, the scorer's re-run agreed with the submitted report (three flags), no leakage flag, headline and failed criteria equal to the source run.
- 2026-11-06, checker 1.4 freeze: Maple `knowledge` (source: the formal tools run 20261028T220746Z): run completed, the prompt carries the optional picks column `residual_s`, the scorer's re-run agreed with the submitted report (three flags), no leakage flag, failed criteria equal to the source run (`time_bias`, `horizontal_scatter`, `off_structure`, `magnitude_scale`); `location_uncertainty` reported (median horizontal uncertainty 2.28 km, 10.6 % of events above 3 times the median), `station_residual_spread` skipped (the source run's picks have no residuals). Its behaviour with residuals was checked separately on the same picks with one station's P residuals made noisy: only that station was listed. Unit tests: 148 pass (four runner tests timed out under a load of about 37 and passed when run alone).
- 2026-11-07, development loop: Maple `dev_knowledge` (source: the formal knowledge run 20261105T225355Z): the prompt carries the development window, the scorer cut the references and the catalog to it (1,716 of 5,481 events, 218 location pairs), the checker re-run agreed with the submitted report, no leakage flag; the window reproduces the full-window failures (origin time +1.30 s, horizontal shift 1.89 km, normalised recall 0.74).
