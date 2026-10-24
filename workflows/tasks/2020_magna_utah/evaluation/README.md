# Magna 2020 evaluation figures

Compares catalog "reproductions" of the 2020 Magna, Utah sequence over the
fixed evaluation window **[2020-03-18T00:00:00Z, 2020-03-26T00:00:00Z)**:

1. **Published reference catalogs** — the three gated sources of the case
   (`data/2020_magna_utah`, cohort mask and hard count gates in
   `expert/00_config/validation.yaml`): Pang et al. (2020) relocated
   (4,169), Baker & Whidden (2021) picks collapsed to events (3,712), and
   the UUSS/ComCat operational benchmark (1,432).
2. **Human-expert reproduction** — this repository's `expert/` workflow,
   round r8 complete catalog (`expert/export/r8/60_catalog/catalog_events.csv`,
   5,522 events): round events with DD positions where relocated and
   accepted (else the stage-45 depth-prior NLL position) plus the
   Match&Locate events of stage 60, shifted with their templates, with
   chained relative magnitudes. Rounds are registered in `EXPERT_ROUNDS`
   (`load_expert(round_)`; r6, r7, r8); stage 60 scores against r6.
3. **Agent reproductions** — none completed yet; arms are registered in
   `AGENT_RUNS` inside `plot_evaluation_comparison.py` as runs finish
   (`min`, `tools`, `guided`).

## Figures (`figures/`)

| File | Content |
|---|---|
| `01_reproduction_spatial_comparison` | One column per catalog (Pang, Baker, UUSS, expert, then agent arms) on shared axes and one log colour scale: top, map of event-count density in 0.25 km cells, km east/north of the M 5.7 mainshock (star); bottom, depth section along the sequence axis (major axis of Pang's epicentres, + toward N70°W). Events outside the shared view are counted per column. Baker's section is drawn but its depth datum differs. |
| `02_reproduction_population_diagnostics` | (a) magnitude–frequency (cumulative counts, Baker's −10 "no magnitude" sentinels excluded), (b) depth distribution (CDF, km below sea level), (c) cumulative detections with time (dotted line = mainshock) — the completeness differences between catalogs read directly as the gaps between curves. One shared legend. |
| `03_agent_reference_correspondence` | Matched-pair diagnostics for the focus agent arm: (a) \|Δ origin time\| vs expert, (b) epicentral p50/p90 vs expert/pang/uuss, (c) magnitude bias vs expert magnitude with running median, (d) depth-vs-depth vs pang with 1:1 line. Written per-run (and cross-run once agent runs are registered). |

`match_statistics.json` records the populations, provenance, matching
criteria and all pair statistics shown in the figures.

## Event correspondence criteria

Greedy one-to-one pairing (nearest epicentral distance, then Δt) within
**|Δ origin time| ≤ 4 s** and **epicentral separation ≤ 15 km** — the same
gates as the expert stage-05 primary matcher and the Ridgecrest evaluation,
so per-run numbers are comparable across cases. The matcher is validated
against stage 05: on the same r6 catalog it reproduces the Hungarian-based
stage-05 counts to within 0.5–0.9 % (2,374 vs 2,354 pang; 2,307 vs 2,294
baker; 1,331 vs 1,328 uuss) and the round dZ median exactly (−0.08 km).
Headline numbers:

| Population | vs Pang | vs Baker | vs UUSS | median \|Δt\| | median epicentral |
|---|---|---|---|---|---|
| **Expert (r8)** | 3,407 (P 61.7%, R 81.7%) | 3,153 (P 57.1%, R 84.9%) | 1,405 (P 25.4%, R 98.1%) | 0.13 s | 1.09 km |
| Expert (r7, previous) | 3,407 (P 61.8%, R 81.7%) | 3,152 (P 57.2%, R 84.9%) | 1,404 (P 25.5%, R 98.0%) | 0.14 s | 0.88 km |
| Expert (r6) | 2,374 (P 85.1%, R 56.9%) | 2,307 (P 82.7%, R 62.1%) | 1,331 (P 47.7%, R 92.9%) | 0.15 s | 1.47 km |
| agent arms | — no completed runs yet — | | | | |

Precision P = matched / population events in window; recall R = matched /
masked reference cohort. Medians are vs Pang. Depth-difference statistics
are computed only between sea-level-datum pairs (expert/pang/uuss); Baker's
depth convention differs (visible as its shifted depth CDF in figure 02b)
and is excluded from depth claims, as throughout the case.

Reading r8: precision against any single reference is low by construction —
the expert catalog holds ~1.3× Pang's event count, and a channel-shuffled
null run puts noise-driven false detections at 1.4–2.3% at the adopted
threshold (see `expert/PLAN.md` r7), so most unmatched expert events are
events the references do not list rather than noise. Depth vs Pang: median
+0.09 km, MAD 0.73 km. The r7 catalog showed a band at 0–5 km below sea level
along strike (528 rows) that looked like a new structure; it was a location
artifact (weak events trading depth for origin time in NLL, plus hypoDD
trapping events under the velocity contrast at ~2 km bsl) and r8 cuts it to
224 rows (`expert/PLAN.md` r7 known issue and r8). The remaining short streaks
at 1–3 km bsl in figure 01 are Match&Locate families of a few templates that
are themselves mislocated shallow; depths shallower than ~4 km bsl are not to
be interpreted. The r8 epicentral median (1.09 vs 0.88 km in r7) reflects a
rigid offset of the DD cluster, not added scatter.

## Per-run evaluation

This directory holds the **cross-run** comparison. Each run additionally
gets its own evaluation next to its record, produced by
`scripts/evaluate_run.py`:

```text
<run>/evaluation/match_statistics.json      per-run stats (same schema and
                                            matcher as the cross-run file)
<run>/evaluation/figures/01_run_vs_references   same layout as figure 01 with
                                                 three columns: pang | expert | run
<run>/evaluation/figures/02_run_correspondence  matched-pair diagnostics
```

```bash
cd workflows/tasks/2020_magna_utah/evaluation/scripts
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python evaluate_run.py \
  --run-dir ../../runs/tools/claude/<model>/<RUN_ID>
# every run that produced a catalog:
for d in ../../runs/*/*/*/*/; do
  [ -f "$d/work/catalog.csv" ] && \
    /liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python evaluate_run.py --run-dir "$d"
done
```

The per-run numbers use the same greedy matcher (4 s / 15 km) as the
cross-run statistics, so a run's block in its own `match_statistics.json`
is identical to the one this directory would print for it. This is
deliberately separate from the package's formal scorer path
(`python -m SeismoAgentBench evaluate --run-dir …`), which writes contract/
scientific score JSONs, uses different matching criteria, and only accepts
runs in terminal success-ish states.

### Where the code lives (cross-case convention)

Per-case evaluation code stays under `workflows/tasks/<case>/evaluation/scripts/`;
the cross-case contract is the convention, not a shared package: a script
named `evaluate_run.py`, CLI `--run-dir <run>`, outputs
`<run>/evaluation/{match_statistics.json, figures/}`. The Magna comparison
module is self-contained (stdlib + numpy + matplotlib + PyYAML); its
reference readers are ports of the expert stage-05 readers and any reader
fix must be applied in both places. If a third case gains references, lift
the shared core (population records, greedy matcher, statistics, compact
figure set) into `SeismoAgentBench/evaluation/` driven by per-case config;
the `evaluate_run.py --run-dir` CLI contract survives that move unchanged.

## Style and palette

Figures reuse the case's audited publication style
(`data/2020_magna_utah/scripts/figures/figure_style.py`: 180 mm width, PNG
320 dpi + PDF, DejaVu Sans, panel letters). The three references keep
their stage-05 colors (Pang `#0072B2`, Baker `#D55E00`, UUSS `#009E73`);
the new populations follow the Ridgecrest evaluation palette: Expert
`#E69F00`, agent tools `#56B4E9`, agent min `#F0E442` (dash-dot, the only
free Okabe-Ito slot, disambiguated from the expert orange by line style).
The categorical palette is numerically validated (OKLab CVD ΔE; every
adjacent pair ≥ 15 — the weakest is baker-vs-expert at 15.6); it is used
for the line plots (figure 02), where a shared legend names every curve.
Spatial figures do not overlay catalogs: each has its own column, drawn as
event-count density with one single-hue blue ramp and a shared log scale,
so identity comes from the column header, never from colour. The white star
marks the M 5.7 mainshock anchor.

## Regenerating

```bash
cd workflows/tasks/2020_magna_utah/evaluation/scripts
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python plot_evaluation_comparison.py
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python evaluate_run.py --run-dir <run>
```

Reference cohorts are gated by the expert validation config (masked counts
4,169/3,712/1,432 asserted); agent runs are picked up via the paths in
`AGENT_RUNS` — extend that dict when arms complete.
