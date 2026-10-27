# Kīlauea 2018 evaluation figures

Compares catalog "reproductions" of the 2018 Kīlauea summit sequence over the
fixed evaluation window **[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z)** — the
onset of the summit collapse, spanning the 2018-05-04 Mw 6.9 south-flank
earthquake (inside the window, outside the summit box):

1. **References** (cohort mask and hard count gates in
   `expert/00_config/validation.yaml`: summit box 19.30–19.50 N,
   −155.40…−155.15, depth −3…20 km):
   - Shelly & Thelen (2019) data S1 hypocentroids — primary (1,902);
   - Wei et al. (2022) data S1, 3-D NonLinLoc (3,627);
   - Matoza et al. (2021) GrowClust relocations, nbranch > 1 (1,020);
   - ComCat/HVO operational (496).
2. **Human-expert reproduction** — `expert/` round r7 complete catalog
   (`expert/export/r7/60_catalog/catalog_events.csv`, 8,223 events): the r4
   catalog moved to NonLinLoc EDT_OT_WT locations (stage 64: picked events
   relocated, Match&Locate events shifted with their templates). r4 is the r3
   NLL catalog (HVO linear-gradient model, 1 Hz Wood–Anderson prefilter) plus
   the stage-60 Match&Locate events (480 templates, N×MAD 9.5; null-run false
   fraction 0.8 %), chained relative magnitudes. Rounds registered in
   `EXPERT_ROUNDS` (r3, r4, r7). Expert depths are converted from sea level to
   below the surface with the model datum (1.07 km).
   *Update 2026-10-28:* the expert population is now round `r9` = `r7` with stage-65 direct ML and stage-67 coda ghosts removed (expert/PLAN.md "Baseline corrections"); numbers below that name `r7` predate it. Benchmark scores: `metrics_v1_baseline.json`.
3. **Agent reproductions** — none completed yet; register arms in
   `AGENT_RUNS` inside `plot_evaluation_comparison.py`.

## Event correspondence criteria

Greedy one-to-one pairing by (distance, Δt) within **|Δt| ≤ 4 s and 15 km**
(the gates of every case). Reference depth datums are unstated or mixed; all
are compared as below-surface depths. Populations are complete catalogs in
the window, so the expert's 8,223 rows include events outside the summit box
(east rift, south flank, GaMMA bound artifacts — "outside view" in figure 01).

| Population | vs Shelly (R) | vs Wei (R) | vs Matoza (R) | vs ComCat (R) | epicentral Shelly | dZ vs Shelly (MAD) |
|---|---|---|---|---|---|---|
| **Expert (r7)** | 1,234 (64.9 %) | 2,479 (68.3 %) | 915 (89.7 %) | 461 (92.9 %) | 0.76 km | +0.54 (0.49) |
| Expert (r4) | 1,221 (64.2 %) | 2,480 (68.4 %) | 913 (89.5 %) | 461 (92.9 %) | 0.89 km | +0.55 (0.58) |
| agent arms | — no completed runs yet — | | | | | |

Median |Δt|: 0.21 s (Shelly), 0.24 s (Wei), 0.26 s (Matoza), 0.11 s (ComCat).
Recall vs Shelly splits sharply at the Mw 6.9: 0.95 after, 0.20 before — the
pre-mainshock events are small (Shelly median M 0.49) and r3 located few
there, so stage 60 has few templates for them (expert PLAN.md r4).

## Figures (`figures/`)

| File | Content |
|---|---|
| `01_reproduction_spatial_comparison` | Shelly, Wei, Matoza, ComCat, expert, agent arms: map density in 0.25 km cells, km east/north of the summit (association projection centre, −155.28 / 19.40), depth section along the major axis of Shelly's epicentres, depth below the surface. |
| `02_reproduction_population_diagnostics` | (a) magnitude–frequency (types differ), (b) depth CDF, (c) cumulative detections (dotted line = Mw 6.9). |
| `03_agent_reference_correspondence` | Per focus agent arm: \|Δt\| vs expert, epicentral p50/p90 vs expert/Shelly/Wei, magnitude bias vs expert, depth vs Shelly. |

`match_statistics.json` records populations, provenance, criteria and all
pair statistics.

## Per-run evaluation

```bash
cd workflows/tasks/2018_kilauea_hawaii/evaluation/scripts
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python evaluate_run.py \
  --run-dir ../../runs/<variant>/<harness>/<model>/<RUN_ID>
```

writes `<run>/evaluation/{match_statistics.json, figures/01_run_vs_references,
figures/02_run_correspondence}` with the same matcher. Smoke-tested
2026-10-24 with the r3 NLL catalog as a pseudo run (Shelly 51.7 %, Wei
58.6 %, Matoza 87.9 %, ComCat 92.1 %).

## Implementation

References are read and masked by the expert stage-05 module
(`expert/04_comparison/05_match_references.py`) — one implementation for
round feedback and evaluation. `plot_evaluation_comparison.py` is shared with
Prague and Kaikōura except for its settings block; `evaluate_run.py` is
case-independent.

## Regenerating

```bash
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python plot_evaluation_comparison.py
```

Style: `data/2018_kilauea_hawaii/scripts/figures/figure_style.py` (same
publication style as Prague/Maple/Magna); references in Okabe–Ito blue,
vermillion, purple and green, expert orange.
