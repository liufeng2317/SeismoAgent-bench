# Kaikōura 2016 evaluation figures

Compares catalog "reproductions" of the 2016 Kaikōura aftershock sequence over
the fixed evaluation window **[2016-12-01T00:00:00Z, 2016-12-09T00:00:00Z)** —
18 days after the 2016-11-13 Mw 7.8 (outside the window); the in-window
anchor is the GeoNet M5.5 2016p913880 (2016-12-04 03:15:47).

1. **References** (cohort mask and hard count gates in
   `expert/00_config/validation.yaml`: −43.5…−41.2 N, 172.0…175.2 E, depth
   −3…60 km):
   - Tan et al. (2024) SUGAR table S10 — detection primary (9,720);
   - Lanza et al. (2019) HypoDD preferred origins — location primary (122);
   - Chamberlain et al. (2021) corrected GrowClust catalog (2,260);
   - GeoNet operational, earthquake + unknown types (1,507).
2. **Human-expert reproduction** — `expert/` round r4 complete catalog
   (`expert/export/r4/60_catalog/catalog_events.csv`, 11,448 events): the r3
   NLL catalog (Chamberlain 1-D average of NZ3D, station delays, GaMMA DBSCAN
   eps 15 s) plus the stage-60 Match&Locate events (708 templates at 2 km
   cover, N×MAD 9.5; null-run false fraction 1.4 %), chained relative
   magnitudes. Rounds registered in `EXPERT_ROUNDS` (r3, r4). All depths are
   below sea level (model datum 0 km).
3. **Agent reproductions** — none completed yet; register arms in
   `AGENT_RUNS` inside `plot_evaluation_comparison.py`.

## Event correspondence criteria

Greedy one-to-one pairing by (distance, Δt) within **|Δt| ≤ 4 s and 15 km**
(the gates of every case). Populations are complete catalogs in the window.

| Population | vs Tan (R) | vs Lanza (R) | vs Chamberlain (R) | vs GeoNet (R) | epicentral Chamberlain | dZ vs Chamberlain (MAD) |
|---|---|---|---|---|---|---|
| **Expert (r4)** | 4,780 (49.2 %) | 120 (98.4 %) | 1,751 (77.5 %) | 1,379 (91.5 %) | 3.79 km | +0.34 (2.56) |
| agent arms | — no completed runs yet — | | | | | |

Epicentral differences are 3.1–3.8 km against every reference. The expert
locations sit 2–3 km north of the three 3-D-model relocations but not of
GeoNet (1-D, like the expert): a 1-D vs 3-D velocity-model difference,
documented in expert PLAN.md r2 and not tuned. The references disagree among
themselves at this level (GeoNet vs the others 3.2–4.3 km; Chamberlain vs
Lanza 1.2 km) and in origin time by up to 0.6 s, so |Δt| (0.42–0.63 s here)
is not a sharp diagnostic. GeoNet depths are ~6 km deeper than all other
catalogs (fixed-depth solutions are common in it).

## Figures (`figures/`)

| File | Content |
|---|---|
| `01_reproduction_spatial_comparison` | Tan, Lanza, Chamberlain, GeoNet, expert, agent arms: map density in 2 km cells, km east/north of the association projection centre (173.6 E, 42.35 S), star = M5.5 anchor, depth section along the major axis of Chamberlain's epicentres, depth below sea level. |
| `02_reproduction_population_diagnostics` | (a) magnitude–frequency (types differ; Lanza has none), (b) depth CDF, (c) cumulative detections (dotted line = M5.5). |
| `03_agent_reference_correspondence` | Per focus agent arm: \|Δt\| vs expert, epicentral p50/p90 vs expert/Lanza/Chamberlain/Tan, magnitude bias vs expert, depth vs Chamberlain. |

`match_statistics.json` records populations, provenance, criteria and all
pair statistics.

## Per-run evaluation

```bash
cd workflows/tasks/2016_kaikoura_new_zealand/evaluation/scripts
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python evaluate_run.py \
  --run-dir ../../runs/<variant>/<harness>/<model>/<RUN_ID>
```

writes `<run>/evaluation/{match_statistics.json, figures/01_run_vs_references,
figures/02_run_correspondence}` with the same matcher (`evaluate_run.py` is
identical across Prague, Kīlauea and Kaikōura and was smoke-tested on the
first two).

## Implementation

References are read and masked by the expert stage-05 module
(`expert/04_comparison/05_match_references.py`) — one implementation for
round feedback and evaluation. `plot_evaluation_comparison.py` is shared with
Prague and Kīlauea except for its settings block.

## Regenerating

```bash
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python plot_evaluation_comparison.py
```

Style: `data/2016_kaikoura_new_zealand/scripts/figures/figure_style.py` (same
publication style as Prague/Maple/Magna); references in Okabe–Ito blue,
purple, vermillion and green, expert orange.
