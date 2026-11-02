# Offline replay (iteration tier A)

A formal Agent run takes 5–27 hours, mostly background computation, so a change to the checker, its comparison rule or the procedural knowledge cannot be tested by rerunning the Agent. Replay reuses what finished runs recorded (picks, catalog, waveforms) and asks a narrower question in minutes: had the Agent taken a given decision with the checker's help, would the checker have pointed the right way?

Each scenario names a recorded run, an intervention (a candidate product built from the run's own picks: relocation with another velocity model, removal of events, a depth or magnitude shift, or a catalog built elsewhere) and the kind of change. Replay then keeps two views apart:

- **Agent view** (no reference): the checker on the current and the candidate catalog, `seismotools/checker/interface/compare.py` on the two reports (verdict better / worse / mixed / uncertain / no_difference), and the median change of the catalog.
- **Benchmark view**: both catalogs scored with `SeismoAgentBench/scoring/catalog_metrics` and judged with the trusted-catalog criteria, restricted to the dimensions the change can affect (a velocity model affects time and space, not magnitude). The candidate is better if it fails fewer of those criteria, or as many but by a margin at least 10 % smaller. Agreement is right / wrong, or undecided when compare says mixed or uncertain.

**Pilot transfer.** With `pilots`, each scenario also applies the intervention to a pilot batch only (300 events by default), checks and compares it the same way, and predicts the full catalog's depth and time bias as the run's bias plus the median change of the pilot events. Rules: `best_recorded` (events picked at the most stations), `random`, `time_uniform` (equal numbers from 30 equal-duration windows), `pick_count_strata` (equal numbers from each decile of picks per event), `composite` (`seismotools/checker/interface/pilot.py events`: representative, busiest hour and largest events; the checker runs with `--pilot` and the catalog shift is measured on the representative part only). The summary reports whether the pilot reached the full catalog's verdict and how close its prediction came: the measure of whether a small batch can stand in for the full run.

## Use

```bash
python3 replay.py run scenarios/smoke.yaml                 # about a minute, no relocation
python3 replay.py run scenarios/velocity_swaps.yaml --only prague_tools_regional --workers 14
python3 replay.py rescore                                  # benchmark view again from the cached catalogs (after a scoring change)
python3 replay.py summary                                  # outputs/summary.md from every record
```

Scenario files are YAML: `defaults` plus a list of `scenarios`, each with `name`, `case`, `run` (`<variant>/<harness>/<model>/<run_id>` under `workflows/tasks/<case>/runs/`), `intervention`, `change` (as for compare), `stage` (checker stage, `location` by default; `magnitude` also reads waveforms) and optionally `pilots` and `pilot_events`.

Interventions: `relocate` (`model`: a key of `data/<case>/data/models/velocity_models.json`, or `litho1` / `crust1`; `datum_km`; `layering` step or linear; `usage` expert or checker; `unlocated` keep or drop), `catalog` (`path`), `drop_few_picks` (`min_p`), `drop_pileup`, `depth_shift` (`dz_km`), `magnitude_shift` (`dm`).

## Outputs

`outputs/` (not tracked): `records/<scenario>.json` (both views, pilot results and costs), `summary.md`, `logs/`, and `cache/<case>/<run>/` with the base checker reports and, per intervention, the candidate catalog, relocation files, checker reports and pilot subsets. Cached products are reused: delete a scenario's cache folder after changing the checker or the intervention code.

The references are read only by the benchmark view; nothing from them reaches the checker or compare.
