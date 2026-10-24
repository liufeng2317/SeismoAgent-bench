# Prague 2011 evaluation figures

Compares catalog "reproductions" of the 2011 Prague, Oklahoma aftershock
sequence over the fixed evaluation window **[2011-11-11T00:00:00Z,
2011-11-19T00:00:00Z)** — the stable-network interval five days after the
2011-11-06 Mw 5.7 mainshock (which is outside the window):

1. **References** (cohort mask and hard count gates in
   `expert/00_config/validation.yaml`; the Cochran window envelope widened to
   three decimals):
   - Cochran et al. (2020) template-enhanced relocated catalog — primary (2,078);
   - McMahon et al. (2017) subspace-detection release (2,343);
   - Isken & Mooney (2017) Table S3, M>3 manual relocations (6) — origin
     times to the minute, matched at 60 s / 5 km: a location anchor;
   - ComCat operational (11; sparse in 2011).
2. **Human-expert reproduction** — `expert/` round r3 complete catalog
   (`expert/export/r3/60_catalog/catalog_events.csv`, 7,156 events): the r2
   NLL catalog (Keranen 2013 model, step layers, station delays) plus the
   stage-60 Match&Locate events (N×MAD 9.5; null-run false fraction 0.7 %),
   chained relative magnitudes. Rounds registered in `EXPERT_ROUNDS` (r2,
   r3). Expert depths are converted from sea level to below the surface with
   the model datum (0.28 km).
3. **Agent reproductions** — none completed yet; register arms in
   `AGENT_RUNS` inside `plot_evaluation_comparison.py`.

## Event correspondence criteria

Greedy one-to-one pairing by (distance, Δt) within **|Δt| ≤ 4 s and 15 km**
(Ridgecrest/Magna/Maple gates); a reference's own `gates` override (Isken
60 s / 5 km). Reference depth datums are unstated; all are compared as
below-surface depths (±0.3 km caveat). Populations are complete catalogs in
the window (Magna convention), so recall here can exceed stage 05/60, which
count box-filtered expert events (r3: Cochran 0.967 here vs 0.952).

| Population | vs Cochran (R) | vs McMahon (R) | median \|Δt\| Cochran | epicentral Cochran | dZ vs Cochran (MAD) |
|---|---|---|---|---|---|
| **Expert (r3)** | 2,010 (96.7 %) | 2,281 (97.4 %) | 0.10 s | 0.49 km | −0.05 (0.63) |
| agent arms | — no completed runs yet — | | | | |

Isken: 6/6, epicentral 0.32 km, depth −1.61 km (Isken deeper — gradient
half-space model there; Cochran agrees with the expert). ComCat 11/11.

Magnitudes: expert ML runs **0.22 below Cochran** (MAD 0.23), the same for
picked (−0.22) and Match&Locate rows (−0.24) — a constant calibration offset
(provisional Hutton–Boore ML vs Cochran's magnitudes), not a scatter. It does
not affect detection or location scores; magnitude comparisons should allow
for it.

## Figures (`figures/`)

| File | Content |
|---|---|
| `01_reproduction_spatial_comparison` | Cochran, McMahon, ComCat, expert, agent arms (Isken omitted: 6 events): map density in 0.25 km cells, km east/north of the Mw 5.7 epicentre (star, Cochran location), depth section along the major axis of Cochran's epicentres (pointing NE), depth below the surface. |
| `02_reproduction_population_diagnostics` | (a) magnitude–frequency (types differ), (b) depth CDF, (c) cumulative detections (the mainshock precedes the window; no marker). |
| `03_agent_reference_correspondence` | Per focus agent arm: \|Δt\| vs expert, epicentral p50/p90 vs expert/Cochran/McMahon, magnitude bias vs expert, depth vs Cochran. |

## Per-run evaluation

```bash
cd workflows/tasks/2011_prague_oklahoma/evaluation/scripts
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python evaluate_run.py \
  --run-dir ../../runs/<variant>/<harness>/<model>/<RUN_ID>
```

Smoke-tested 2026-10-23 with the r2 catalog as a pseudo run (Cochran
63.0 %, McMahon 73.4 %, epicentral 0.49 km).

## Implementation

References are read and masked by the expert stage-05 module
(`expert/04_comparison/05_match_references.py`) — one implementation for
round feedback and evaluation. `plot_evaluation_comparison.py` is shared with
Kīlauea and Kaikōura except for its settings block (title, primary
reference, view, rounds); `evaluate_run.py` is case-independent.

## Regenerating

```bash
/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python plot_evaluation_comparison.py
```

Style: `data/2011_prague_oklahoma/scripts/figures/figure_style.py` (copied
from the Maple/Magna style module).
