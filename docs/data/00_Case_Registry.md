# Case registry

The six Phase I cases: their role, difficulty tier, frozen evaluation window and primary references. This is the one place for these facts; per-case data and literature are in [`01_Case_Data_Inventory.md`](01_Case_Data_Inventory.md), candidate cases beyond these six in [`02_Case_Pool.md`](02_Case_Pool.md), and what each case record must contain in [`preparation/01_Case_Record_Standard.md`](preparation/01_Case_Record_Standard.md).

Sources: evaluation windows are half-open UTC intervals in each task's `workflows/tasks/<case>/expert/00_config/validation.yaml`; primary references and their roles are in `workflows/tasks/<case>/evaluation/metrics.yaml` and [`02_Catalog_Metrics.md`](../framework/02_Catalog_Metrics.md) §3; difficulty tiers are defined in the [research plan](../research/00_Research_Plan.md) §2.2.

| Case ID | Case | Regime | Difficulty tier | Evaluation window (UTC) | Primary detection reference | Primary location reference | Main role | Case analysis |
|---|---|---|---|---|---|---|---|---|
| `PRAGUE2011` | Prague 2011 | Induced/triggered aftershocks | basic | 2011-11-11 – 11-19 | Cochran 2020 | Cochran 2020 | Detection, location QC, changing network | [`PRAGUE2011_analysis.md`](../../data/2011_prague_oklahoma/analysis/PRAGUE2011_analysis.md) |
| `MAGNA2020` | Magna 2020 | Mainshock–aftershock | basic | 2020-03-18 – 03-26 | Pang 2020 | Pang 2020 | End-to-end catalog, relocation, picks (Baker) | [`MAGNA2020_analysis.md`](../../data/2020_magna_utah/analysis/MAGNA2020_analysis.md) |
| `MAPLE2017` | Maple Creek 2017 | Yellowstone swarm | intermediate | 2017-06-11 – 06-19 | ComCat (UUSS); ceiling from Shelly & Hardebeck 2019 | ComCat (UUSS) | Swarm detection, relative location, picks (Shelly) | [`MAPLE2017_analysis.md`](../../data/2017_maple_creek_yellowstone/analysis/MAPLE2017_analysis.md) |
| `KILAUEA2018` | Kīlauea 2018 | Volcanic caldera collapse | intermediate | 2018-05-01 – 05-09 | Shelly & Thelen 2019 | Shelly & Thelen 2019 | High-rate volcanic monitoring | [`KILAUEA2018_analysis.md`](../../data/2018_kilauea_hawaii/analysis/KILAUEA2018_analysis.md) |
| `RIDGE2019` | Ridgecrest 2019 | Foreshock–mainshock–aftershock | hard | 2019-07-04 15:35:29.4 – 07-07 | Shelly 2020 | Shelly 2020 | Dense detection, association, relative location | [`RIDGE2019_analysis.md`](../../data/2019_ridgecrest_california/analysis/RIDGE2019_analysis.md) |
| `KAIKOURA2016` | Kaikōura 2016 | Complex multi-fault aftershocks | hard | 2016-12-01 – 12-09 | Chamberlain 2021; ceiling from Tan 2024 | Lanza 2019 | 3-D location, relocation, regional network | [`KAIKOURA2016_analysis.md`](../../data/2016_kaikoura_new_zealand/analysis/KAIKOURA2016_analysis.md) |

Ridgecrest's data window starts at 2019-07-04 00:00; evaluation starts at the common start of the reference catalogs. The research plan v0.2 (2026-09-18) listed earlier windows and, for Prague, McMahon 2017 as primary; the table above supersedes them.

## Quality hierarchy

The quality tier is dimension-specific and does not imply absolute ground truth.

| Tier | Meaning | Typical use |
|---|---|---|
| **Q1** | High-confidence precision research catalog with strong QC, uncertainty, and transparent provenance | Primary target for a defined scientific dimension |
| **Q2** | Enhanced research catalog that improves on routine monitoring but has weaker review, completeness, absolute-location control, or independence | Detection enhancement, association, high-rate monitoring, cross-method comparison |
| **Q3** | Routine operational catalog | Baseline, operational recovery, large-event anchor |
| **Q4** | Preliminary, partial, derived, phase-only, or auxiliary product | Sanity checks and auxiliary diagnostics |

Quality tier, evaluation role, quality by dimension, and reference independence must be recorded separately in each case analysis file.

## Preparation status

All six cases are `window-frozen` since 2026-10-28: each `data/<case>/analysis/processing.yaml` records `window_status: frozen`, the date, and the evaluation window above. Counts computed with data-level masks remain descriptive; the evaluation cohort (time, region, depth) is the task's `validation.yaml`. The status vocabulary (`inventory`, `catalog-calibration`, `window-candidate`, `window-frozen`, `waveform-sampled`, `data-frozen`) is defined in [`preparation/01_Case_Record_Standard.md`](preparation/01_Case_Record_Standard.md) §4.
