# Results overview

Generated 2026-10-30 23:23 UTC by `python -m SeismoAgentBench.scoring.catalog_metrics table` together with [`SCORE_TABLE.md`](SCORE_TABLE.md) (every metric, by dimension); do not edit by hand. A run is judged against the human-in-loop final of its case (catalog metrics v2, trusted-catalog standard §7a of `docs/framework/02_Catalog_Metrics.md`).

## 1. Cases × configurations

Latest formal run per cell: verdict · number of failed trusted-catalog criteria · recall against the final.

| Tier | Case | min | tools |
|---|---|---|---|
| basic | Prague 2011 | no valid catalog (artifact_invalid) | not trusted · 2 failed · recall 0.46 |
| basic | Magna 2020 | no valid catalog (artifact_invalid) | not trusted · 3 failed · recall 0.51 |
| intermediate | Maple Creek 2017 | not trusted · 12 failed · recall 0.13 | not trusted · 6 failed · recall 0.22 |
| intermediate | Kīlauea 2018 | not trusted · 6 failed · recall 0.42 | not trusted · 1 failed · recall 0.37 |
| hard | Ridgecrest 2019 | not trusted · 7 failed · recall 0.30 | not trusted · 6 failed · recall 0.39 |
| hard | Kaikōura 2016 | not trusted · 8 failed · recall 0.04 | not trusted · 7 failed · recall 0.43 |

## 2. Runs

Values against the human-in-loop final; ✗ marks a value that fails its criterion. Δt origin time (s), Δz depth (km), shift = median horizontal offset (km), scatter = spread about it (km), Δmag against the primary magnitude reference, depth pile = share in the densest 1-km slice. Figures: the scorer's standard spatial comparison (reference, final, run on one extent) and offset diagnostics.

| Case | Config | State | Verdict | Recall | Δt | Δz | Shift | Scatter | Δmag | Depth pile | Failed criteria | Figures |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Prague 2011 | min | artifact_invalid | no valid catalog | — | — | — | — | — | — | — | — | — |
| Prague 2011 | tools | completed | not trusted | 0.46 | 0.06 | 1.10 ✗ | 0.03 | 0.26 | -2.77 ✗ | 0.02 | depth_bias, magnitude_offset | [map](../../../workflows/tasks/2011_prague_oklahoma/evaluation/agents/tools__claude__glm-5.3__20261028T043719Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2011_prague_oklahoma/evaluation/agents/tools__claude__glm-5.3__20261028T043719Z/figures/location_diagnostics.png) |
| Magna 2020 | min | artifact_invalid | no valid catalog | — | — | — | — | — | — | — | — | — |
| Magna 2020 | tools | completed | not trusted | 0.51 | -0.19 | -1.94 ✗ | 2.35 ✗ | 0.51 | 0.67 ✗ | 0.02 | horizontal_shift, depth_bias, magnitude_offset | [map](../../../workflows/tasks/2020_magna_utah/evaluation/agents/tools__claude__glm-5.3__20261028T135931Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2020_magna_utah/evaluation/agents/tools__claude__glm-5.3__20261028T135931Z/figures/location_diagnostics.png) |
| Maple Creek 2017 | min | completed | not trusted | 0.13 | 0.39 ✗ | -3.81 ✗ | 1.02 ✗ | 3.95 ✗ | 0.66 ✗ | 0.27 ✗ | inside_region, time_bias, time_spread, after_large_events, horizontal_shift, depth_bias, horizontal_scatter, off_structure, depth_pileup, magnitude_offset, magnitude_spread, magnitude_scale | [map](../../../workflows/tasks/2017_maple_creek_yellowstone/evaluation/agents/min__claude__glm-5.3__20261028T220720Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2017_maple_creek_yellowstone/evaluation/agents/min__claude__glm-5.3__20261028T220720Z/figures/location_diagnostics.png) |
| Maple Creek 2017 | tools | completed | not trusted | 0.22 | 1.15 ✗ | -2.18 ✗ | 0.91 | 1.90 ✗ | 0.19 | 0.04 | inside_region, time_bias, depth_bias, horizontal_scatter, off_structure, magnitude_scale | [map](../../../workflows/tasks/2017_maple_creek_yellowstone/evaluation/agents/tools__claude__glm-5.3__20261028T220746Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2017_maple_creek_yellowstone/evaluation/agents/tools__claude__glm-5.3__20261028T220746Z/figures/location_diagnostics.png) |
| Kīlauea 2018 | min | completed | not trusted | 0.42 | -0.96 ✗ | 1.29 ✗ | 0.13 | 1.31 ✗ | -2.43 ✗ | 0.17 ✗ | inside_region, time_bias, depth_bias, horizontal_scatter, depth_pileup, magnitude_offset | [map](../../../workflows/tasks/2018_kilauea_hawaii/evaluation/agents/min__claude__glm-5.3__20261029T084653Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2018_kilauea_hawaii/evaluation/agents/min__claude__glm-5.3__20261029T084653Z/figures/location_diagnostics.png) |
| Kīlauea 2018 | tools | completed | not trusted | 0.37 | -0.36 ✗ | 0.45 | 0.07 | 0.38 | -0.06 | 0.04 | time_bias | [map](../../../workflows/tasks/2018_kilauea_hawaii/evaluation/agents/tools__claude__glm-5.3__20261029T084718Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2018_kilauea_hawaii/evaluation/agents/tools__claude__glm-5.3__20261029T084718Z/figures/location_diagnostics.png) |
| Ridgecrest 2019 | min | completed | not trusted | 0.30 | 0.25 | -1.37 ✗ | 1.01 ✗ | 0.60 | 0.30 ✗ | 0.01 | inside_region, horizontal_shift, depth_bias, off_structure, magnitude_offset, magnitude_spread, large_events_present | [map](../../../workflows/tasks/2019_ridgecrest_california/evaluation/agents/min__claude__glm-5.3__20261029T203728Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2019_ridgecrest_california/evaluation/agents/min__claude__glm-5.3__20261029T203728Z/figures/location_diagnostics.png) |
| Ridgecrest 2019 | tools | completed | not trusted | 0.39 | 0.05 | -2.31 ✗ | 0.59 | 0.83 | -1.21 ✗ | 0.36 ✗ | inside_region, depth_bias, off_structure, depth_pileup, magnitude_offset, large_events_present | [map](../../../workflows/tasks/2019_ridgecrest_california/evaluation/agents/tools__claude__glm-5.3__20261029T203757Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2019_ridgecrest_california/evaluation/agents/tools__claude__glm-5.3__20261029T203757Z/figures/location_diagnostics.png) |
| Kaikōura 2016 | min | completed | not trusted | 0.04 | 2.56 ✗ | 0.06 | 2.73 ✗ | 4.44 ✗ | -0.26 | 0.50 ✗ | time_bias, time_spread, after_large_events, horizontal_shift, horizontal_scatter, off_structure, depth_pileup, large_events_present | [map](../../../workflows/tasks/2016_kaikoura_new_zealand/evaluation/agents/min__claude__glm-5.3__20261029T123602Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2016_kaikoura_new_zealand/evaluation/agents/min__claude__glm-5.3__20261029T123602Z/figures/location_diagnostics.png) |
| Kaikōura 2016 | tools | completed | not trusted | 0.43 | 0.63 ✗ | 0.54 | 3.70 ✗ | 3.69 ✗ | -0.60 ✗ | 0.13 ✗ | time_bias, time_spread, horizontal_shift, horizontal_scatter, depth_pileup, magnitude_offset, large_events_present | [map](../../../workflows/tasks/2016_kaikoura_new_zealand/evaluation/agents/tools__claude__glm-5.3__20261029T183933Z/figures/spatial_comparison.png) · [offsets](../../../workflows/tasks/2016_kaikoura_new_zealand/evaluation/agents/tools__claude__glm-5.3__20261029T183933Z/figures/location_diagnostics.png) |

## 3. Not formal results

Reference-only rescues (outputs recovered outside work/) and runs excluded for a harness defect.

| Case | Run | State | Note |
|---|---|---|---|
| Prague 2011 | min | rescue, reference only | not trusted; failed: inside_region, time_bias, after_large_events, depth_bias, horizontal_scatter, magnitude_offset, magnitude_spread, magnitude_scale |
| Kaikōura 2016 | runs/tools/claude/glm-5.3/20261029T123626Z | excluded | Excluded 2026-10-30: harness defect, not a formal result. The runner passed the task prompt on the Claude process's argv; the tools prompt names MatchLocate2, so the Agent's own `ps | grep MatchLocate2 | ... kill -9` (its last command, 17:01:15 UTC) matched and killed its Claude session (exit -9, state execution_failed, 4.4 h). work/catalog.csv is an intermediate version from 16:19 UTC. The runner now passes the prompt on stdin; the run is repeated with the fixed runner. |

