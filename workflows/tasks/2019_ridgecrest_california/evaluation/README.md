# Ridgecrest evaluation figures

Compares three kinds of catalog "reproductions" of the 2019 Ridgecrest
sequence over the fixed evaluation window
**[2019-07-04T00:00:00Z, 2019-07-07T00:00:00Z)**:

1. **Published reference catalogs** — the five audited sources of the case
   (`data/2019_ridgecrest_california`, gated by `reference_audit.json`):
   Shelly 2020 (template matching), Liu 2020 (ML picker + GaMMA),
   Ross 2019 QTM relocated subset, AWR 2025 v2 (long-term GaMMA), and the
   USGS/SCSN ComCat operational snapshot.
2. **Human-expert reproduction** — this repository's `expert/` workflow,
   round `12_dense_layered` (`expert/export/12_dense_layered/60_catalog/
   catalog_events.csv`, 18,537 events): stage-52 joint-DD events plus
   Match&Locate events from 1,932 templates (0.5 km cover of events passing
   the location-quality rule: ≥ 1 stage-52 CC link, gap ≤ 150°, NLL σx ≤ 0.8 km;
   N×MAD 9.5, null false fraction 0.5 %; 4 s separation, closer events only
   with ≥ 6 templates), the same rule applied to picked events, moved into the
   frame of Shelly Table 1 as published (constant layers) by stage 63.
   Recall vs Shelly 93.3 %, Ross 94.1 %, Liu 95.9 %, ComCat 89.0 %; median
   epicentral 0.44 / 0.79 / 0.46 / 0.60 km; depth vs Shelly −0.09 km (MAD
   0.56); 0.5 % of events > 1 km from every Shelly/Ross/Liu event (ComCat
   1.5 %). Round history in expert/PLAN.md (stages 60, 62, 63).
   *Update 2026-10-28:* the expert population is now round `57_coda_duplicates` = `12_dense_layered` with stage-65 direct ML, the depth-bound large events restored by stage 66 (M7.1, M6.4, M5.4) and stage-67 coda ghosts removed (expert/PLAN.md "Baseline corrections"); numbers below that name `12_dense_layered` predate it. Benchmark scores: `metrics_v1_baseline.json`.
3. **Agent reproductions** — completed Claude Code × GLM-5.3 runs:
   `runs/min/claude/glm-5.3/20261013T215003Z` (the Q1 `min` arm),
   `runs/tools/claude/glm-5.3/20261015T020300Z` (the Q2 `tools` arm;
   11,611 events in window, runner session lost at 6.5 h but the agent
   finished — record closed via `finalize`), and the historical
   legacy-baseline run `runs/base/claude/glm-5.3/20261013T043225Z`
   (retired prompt; shown for strategy-variance context only).

## Figures (`figures/`)

| File | Content |
|---|---|
| `01_reproduction_spatial_comparison` | Depth-colored maps for all nine populations (3×3) + full-width record-count bar. Agent panels widen to their data extent (dashed box = shared reference bounds) and annotate how many events fall outside the reference box. |
| `02_reproduction_population_diagnostics` | (a) magnitude CCDF, (b) depth CDF, (c) stage-specific rate heatmap (five mainshock-relative stages × nine populations), (d) `tools`-arm recall of reference events by magnitude band, (e) hourly event rates. |
| `03_agent_reference_correspondence` | Matched-pair diagnostics for the `tools` arm: (a) \|Δ origin time\|, (b) epicentral difference p50/p90 vs Expert and Shelly, (c) magnitude bias vs expert magnitude with running median, (d) depth-vs-depth scatter with 1:1 line. |
| `04_reproduction_hourly_rates` | Single-panel hourly-rate timeline, all populations, symlog scale. |
| `05_three_way_comparison` | Focused six-panel comparison of Shelly, the expert reproduction, and one agent run (`--agent`, default `tools`), displayed as `reference`, `expert`, and `claude glm5.3 (tools)`. All three maps share the fixed reference-box extent; agent events outside the box are clipped and only counted in the red annotation. |

`match_statistics.json` records the populations, provenance, matching
criteria and all pair statistics shown in the figures; the recall and
matched-pair panels feature the arm named by `FOCUS_AGENT` (`agent_tools`).

## Event correspondence criteria

Greedy one-to-one pairing (nearest distance, then Δt) within
**|Δ origin time| ≤ 4 s** and **epicentral separation ≤ 15 km**, applied
independently for each agent run against the expert, Shelly and ComCat
populations. Headline numbers:

| Arm | vs Expert | vs Shelly | vs ComCat | median \|Δt\| | median epicentral |
|---|---|---|---|---|---|
| `tools` | 8,015 (P 69.0%, R 48.0%) | 6,060 (78.5%) | 5,317 (81.0%) | 0.95 s | 1.4 km |
| `min` | 2,910 (P 28.2%, R 17.4%) | 2,620 (34.0%) | 2,518 (38.4%) | 0.42 s | 5.0 km |
| `legacy` | 1,208 (P 68.6%, R 7.2%) | 1,147 (14.9%) | 1,108 (16.9%) | 0.30 s | 2.5 km |

Medians are vs Expert. Since 2026-10-25 the expert is the stage-60 union
(16,686 events), so recall *vs Expert* fell for every arm (tools: 85.9 % →
48.0 % against the 6,520-event stage-52 catalog) while precision rose; the
reference columns are unchanged. The `tools` arm still roughly doubles both
precision and recall over `min` against every population.

## Per-run evaluation

This directory holds the **cross-run** comparison. Each run additionally
gets its own evaluation next to its record, produced by
`scripts/evaluate_run.py`:

```text
<run>/evaluation/match_statistics.json      per-run stats (same schema and
                                            matcher as the cross-run file)
<run>/evaluation/figures/01_run_vs_references    reference vs expert vs run
                                                 (maps at the fixed reference-box extent)
<run>/evaluation/figures/02_run_correspondence   matched-pair diagnostics
```

```bash
cd workflows/tasks/2019_ridgecrest_california/evaluation/scripts
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python evaluate_run.py \
  --run-dir ../../runs/tools/claude/glm-5.3/20261015T020300Z
# every run that produced a catalog:
for d in ../../runs/*/*/*/*/; do
  [ -f "$d/work/catalog.csv" ] && \
  /liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python evaluate_run.py --run-dir "$d"
done
```

The per-run numbers are computed by the same greedy matcher (4 s / 15 km)
as the cross-run statistics, so the `agent_tools` block of the tools run's
`match_statistics.json` is identical to the one in this directory. This is
deliberately separate from the package's formal scorer path
(`python -m SeismoAgentBench evaluate --run-dir …`), which writes contract/
scientific score JSONs, uses different matching criteria, and only accepts
runs in terminal success-ish states.

### Where the code lives (cross-case convention)

Per-case evaluation code stays under `workflows/tasks/<case>/evaluation/scripts/`;
the cross-case contract is the convention, not a shared package: a script
named `evaluate_run.py`, CLI `--run-dir <run>`, outputs
`<run>/evaluation/{match_statistics.json, figures/}`, plus a cross-run
comparison script at case level. Reasons not to put an engine in the
`SeismoAgentBench` package today: the package is matplotlib-free (only the
eval environment installs plotting), and this is currently the only case
with gated reference catalogs and a house comparison-figure API. When a
second case gains references, lift the shared core (population records,
greedy matcher, statistics, compact figure set) into
`SeismoAgentBench/evaluation/` driven by per-case config; the
`evaluate_run.py --run-dir` CLI contract survives that move unchanged.

## Style and palette

Figures reuse the audited publication style of
`data/2019_ridgecrest_california/scripts/figures/plot_catalog_comparison.py`
(180 mm width, PNG 320 dpi + PDF, DejaVu Sans, panel letters). The five
published sources keep their house colors; the new populations are
Expert `#E69F00`, Agent tools `#56B4E9`, Agent min `#F0E442`
(dash-dot), Agent legacy `#000000` (dashed). Under a Viénot deutan
simulation the adjacent-pair OKLab ΔE spans 0.09–0.65; the weakest pair
is Expert orange vs Agent-min yellow (the yellow is the only unused
Okabe-Ito slot), which is why agent min also carries a dash-dot line
style, and every population stays identifiable from panel titles and
the population bar regardless of color.

## Regenerating

```bash
cd workflows/tasks/2019_ridgecrest_california/evaluation/scripts
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python plot_evaluation_comparison.py
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python plot_evaluation_comparison_three_way.py [--agent agent_tools]
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python evaluate_run.py --run-dir <run>
```

Requires the reference-audit gate to be current
(`reference_audit.json` hash-matched to `processing.yaml`); agent runs
are picked up by the paths in `AGENT_RUNS` — extend that dict when new
arms (`guided`, …) complete.
