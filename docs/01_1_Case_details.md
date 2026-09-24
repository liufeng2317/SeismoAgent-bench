# Case registry

This is the navigation and scientific-role index. Case-specific interpretation and processing notes live in the linked analysis; numerical audits belong to each catalog README and its generated outputs.

| Case ID | Case | Regime | Reference focus | Main role | Design priority | Case analysis |
|---|---|---|---|---|---|---|
| `RIDGE2019` | Ridgecrest 2019 | Foreshock–mainshock–aftershock | Shelly (2020) | Dense detection, association, relative location | A+ | [`RIDGE2019_analysis.md`](../data/2019_ridgecrest_california/analysis/RIDGE2019_analysis.md) |
| `PRAGUE2011` | Prague 2011 | Induced/triggered sequence | Cochran et al. (2020) | Detection, location QC, network robustness | A | [`PRAGUE2011_analysis.md`](../data/2011_prague_oklahoma/analysis/PRAGUE2011_analysis.md) |
| `MAGNA2020` | Magna 2020 | Mainshock–aftershock | Pang et al. (2020) | End-to-end enhancement, relocation | A+ | [`MAGNA2020_analysis.md`](../data/2020_magna_utah/analysis/MAGNA2020_analysis.md) |
| `MAPLE2017` | Maple Creek 2017 | Yellowstone swarm | Shelly & Hardebeck (2019) | Swarm detection, relative relocation | A | [`MAPLE2017_analysis.md`](../data/2017_maple_creek_yellowstone/analysis/MAPLE2017_analysis.md) |
| `KILAUEA2018` | Kīlauea 2018 | Volcanic / caldera collapse | Shelly & Thelen (2019) | Volcanic high-rate monitoring | A− | [`KILAUEA2018_analysis.md`](../data/2018_kilauea_hawaii/analysis/KILAUEA2018_analysis.md) |
| `KAIKOURA2016` | Kaikōura 2016 | Complex multi-fault aftershock | Lanza et al. (2019) | 3-D location, relocation, uncertainty | A− / hard tier | [`KAIKOURA2016_analysis.md`](../data/2016_kaikoura_new_zealand/analysis/KAIKOURA2016_analysis.md) |

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

| Status | Meaning |
|---|---|
| `inventory` | Reference and case information collected; no catalog freeze |
| `catalog-calibration` | Catalog files downloaded and schemas/release counts being reconciled |
| `window-candidate` | Candidate time/space window proposed but not frozen |
| `window-frozen` | Exact time, spatial, and event-inclusion rules frozen |
| `waveform-sampled` | Representative waveform requests successfully tested |
| `data-frozen` | Catalog, metadata, and waveform manifest versioned for experiments |

Current status for all six cases: `window_status: not_frozen` in the case processing configuration. Existing time/space selections and derived counts are exploratory; they do not establish waveform readiness or a formal evaluation freeze.

Detailed readiness and unresolved literature gaps are maintained once in the [reference manifest](../data/REFERENCES_MANIFEST.md). Product counts and units are generated in the [catalog manifest](../data/CATALOGS_MANIFEST.md).

## Case-analysis requirements

Each detailed analysis file must maintain:

- case scientific context and regime;
- primary, secondary, baseline, and auxiliary catalogs;
- Q1–Q4 quality tier and dimension-specific quality profile;
- evaluation role and reference independence;
- full and benchmark time/space scope;
- network and station/channel conditions;
- catalog schema, event counts, and release reconciliation;
- candidate and frozen benchmark windows;
- waveform access, data gaps, and volume estimates;
- allowed metrics, excluded interpretations, risks, and final freeze decision.
