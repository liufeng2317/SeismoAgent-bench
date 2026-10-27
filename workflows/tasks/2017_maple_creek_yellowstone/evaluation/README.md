# Maple Creek 2017 evaluation figures

Compares catalog "reproductions" of the 2017 Maple Creek, Yellowstone swarm
over the fixed evaluation window **[2017-06-11T00:00:00Z, 2017-06-19T00:00:00Z)**:

1. **References** — the two gated sources of the case (cohort mask and hard
   count gates in `expert/00_config/validation.yaml`; no research event table
   is published for this sequence):
   - ComCat/UUSS operational events (626; located; depths below the local
     surface), query box corrected 2026-10-22 to the swarm footprint;
   - Shelly & Hardebeck (2019) detections derived from their phase release
     (18,062; origin times only, no locations; `data/2017_maple_creek_yellowstone/
     data/catalogs/SHELLY2019_GL081607/scripts/derive_detection_events.py`).
2. **Human-expert reproduction** — `expert/` round r9 complete catalog
   (`expert/export/r9/60_catalog/catalog_events.csv`, 12,602 events): the r8
   catalog moved to NonLinLoc EDT_OT_WT locations (stage 64: picked events
   relocated, Match&Locate events shifted with their templates; 0.28 % of
   events > 1 km from every ComCat event). r8 is the r7
   union (r5 NLL + stage-60 Match&Locate, N×MAD 9.25) with the location-quality
   rule of 2026-10-26 — a source event stays, and may place events as a
   template, only with ≥ 1 waveform CC link to a neighbour (ccdt), gap ≤ 150°
   and NLL σx ≤ 0.8 km. 1.5 % of events lie > 1 km from every ComCat event
   (r7: 3.5 %); ComCat recall 99.0 %, Shelly net 50.7 % (r7 99.4 / 52.1 %).
   Rounds registered in `EXPERT_ROUNDS` (r5–r9); depths below sea level
   converted to below-surface with the model datum (2.3 km).
   *Update 2026-10-28:* the expert population is now round `r11` = `r9` with stage-65 direct ML and stage-67 coda ghosts removed (expert/PLAN.md "Baseline corrections"); numbers below that name `r9` predate it. Benchmark scores: `metrics_v1_baseline.json`.
3. **Agent reproductions** — none completed yet; register arms in
   `AGENT_RUNS` inside `plot_evaluation_comparison.py` as runs finish.

## Event correspondence criteria

Greedy one-to-one pairing. Located pairs: **|Δt| ≤ 4 s and ≤ 15 km**, ranked
by (distance, Δt) — the Ridgecrest/Magna gates. Pairs with the time-only
Shelly reference: **|Δt| ≤ 1 s** alone; because the swarm peaks at one
Shelly detection every ~14 s, a **60 s shifted-reference** run of the same
matcher counts chance coincidences, reported as `chance_matches` and
`recall_net` = (matched − chance) / reference events. Both conventions equal
expert stage 05. Depth differences only between below-surface pairs
(ComCat, expert); agent depth datums are unknown and stay out of depth
statistics.

| Population | vs ComCat (R) | vs Shelly (R / net) | median \|Δt\| ComCat | epicentral ComCat | dZ vs ComCat (MAD) |
|---|---|---|---|---|---|
| **Expert (r9)** | 619 (98.9 %) | 10,269 (56.9 % / 51.1 %) | 0.09 s | 0.90 km | +1.46 (0.69) |
| Expert (r7) | 622 (99.4 %) | 10,526 (58.3 % / 52.1 %) | 0.10 s | 0.87 km | +1.43 (0.70) |
| Expert (r6) | 623 (99.5 %) | 9,825 (54.4 % / 48.5 %) | 0.10 s | 0.87 km | +1.43 (0.70) |
| agent arms | — no completed runs yet — | | | | |

Precision against ComCat is low by construction (r7 holds ~22× ComCat's
count); against Shelly 77 % of expert events have a detection within 1 s
(chance level ~8 %). The +1.4 km depth offset vs ComCat is a documented
input difference, not a locator artifact: our picks fit our hypocentres
better than ComCat's (expert PLAN.md, depth-offset diagnostic).

## Figures (`figures/`)

| File | Content |
|---|---|
| `01_reproduction_spatial_comparison` | Located populations only (ComCat, expert, agent arms): map density in 0.25 km cells, km east/north of the Mw 4.4 (star), and the along-strike depth section (axis = major axis of ComCat's epicentres), depth below the local surface. Shelly has no locations. |
| `02_reproduction_population_diagnostics` | (a) magnitude–frequency (Shelly included; magnitude types differ), (b) depth CDF (located populations), (c) cumulative detections with time (dotted line = Mw 4.4). |
| `03_agent_reference_correspondence` | Per focus agent arm: \|Δt\| vs expert, epicentral p50/p90 vs expert/ComCat, magnitude bias vs expert, depth vs ComCat. |


## Per-run scoring (metrics v1)

Runs are scored with the pre-registered metrics
(`docs/framework/03_EVALUATION_METRICS.md`), configured for this case in
`metrics_v1.yaml`. From the repository root, with the evaluation environment
(`/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python`):

```bash
# one run: output contract + metrics v1 (both declared in task_<variant>.json)
python -m SeismoAgentBench evaluate --run-dir workflows/tasks/2017_maple_creek_yellowstone/runs/<variant>/<harness>/<model>/<run_id>
# every run, per configuration (scores unscored runs; failed runs count as zero for detection)
python -m SeismoAgentBench.scoring.catalog_metrics summary --task-dir workflows/tasks/2017_maple_creek_yellowstone
# reference ceilings and the expert final / blind rows
python -m SeismoAgentBench.scoring.catalog_metrics baseline --task-dir workflows/tasks/2017_maple_creek_yellowstone
```

Per run: `<run>/evaluation/metrics_v1.json`, `location_diagnostics.png`,
`audit_sample.csv`; per case: `metrics_v1_summary.json`, `metrics_v1_baseline.json`.
The figures in this directory are descriptive; their matcher statistics are
not benchmark scores.

## Regenerating

```bash
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python plot_evaluation_comparison.py
```

Style: `data/2017_maple_creek_yellowstone/scripts/figures/figure_style.py`
(same publication style as Magna); ComCat green, Shelly blue, expert orange,
agent arms as in the Magna evaluation.
