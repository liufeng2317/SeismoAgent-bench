# Case Registry and Cross-Case Summary

> Detailed case information is maintained in the corresponding `data/<case>/analysis/` file. This document is intentionally concise and is used for cross-case retrieval, statistics, prioritization, and status tracking.

## Case registry

| Case ID | Case | Regime | Frozen v1 benchmark window | Primary reference | Main role | Network / access | Priority | Detailed analysis |
|---|---|---|---|---|---|---|---|---|
| `RIDGE2019` | Ridgecrest 2019 | Foreshock–mainshock–aftershock | 2019-07-04–07-07 UTC; Shelly 7,716 / AWR 5,737 after QC | Shelly (2020) | Dense detection, association, relative location | SCSN/SCEDC public | A+ | [`RIDGE2019_analysis.md`](../data/2019_ridgecrest_california/analysis/RIDGE2019_analysis.md) |
| `PRAGUE2011` | Prague 2011 | Induced/triggered sequence | 2011-11-11–11-19 UTC; 2,078 Cochran events | Cochran et al. (2020) | Detection, location QC, network robustness | EarthScope/IRIS and mixed archives | A | [`PRAGUE2011_analysis.md`](../data/2011_prague_oklahoma/analysis/PRAGUE2011_analysis.md) |
| `MAGNA2020` | Magna 2020 | Mainshock–aftershock | 2020-03-18–03-26 UTC; Pang 4,102 valid-magnitude events | Pang et al. (2020) | End-to-end enhancement, relocation | EarthScope/IRIS + COSMOS | A+ | [`MAGNA2020_analysis.md`](../data/2020_magna_utah/analysis/MAGNA2020_analysis.md) |
| `MAPLE2017` | Maple Creek 2017 | Yellowstone swarm | 2017-06-11–06-19 UTC; 22,858 phase-associated IDs (not validated events) | Shelly & Hardebeck (2019) | Swarm detection, relative relocation | EarthScope/IRIS | A | [`MAPLE2017_analysis.md`](../data/2017_maple_creek_yellowstone/analysis/MAPLE2017_analysis.md) |
| `KILAUEA2018` | Kīlauea 2018 | Volcanic / caldera collapse | 2018-05-01–05-09 UTC; Shelly S1/S2 1,883/1,877 common-mask (time-only 1,902/1,896); Wei 2,369 rows (1,930 numeric-M) | Shelly & Thelen (2019) | Volcanic high-rate monitoring | HVO summit condition; local phase release has 25 HV codes (fixed station-day inventory pending) | A− | [`KILAUEA2018_analysis.md`](../data/2018_kilauea_hawaii/analysis/KILAUEA2018_analysis.md) |
| `KAIKOURA2016` | Kaikōura 2016 | Complex multi-fault aftershock | 2016-12-01–12-09 UTC; Lanza 122 / Tan S10 9,720 / S11 6,955 common-mask (6,973 time-only) | Lanza et al. (2019) | 3-D location, relocation, uncertainty | GeoNet public + temporary STREWN | A− / hard tier | [`KAIKOURA2016_analysis.md`](../data/2016_kaikoura_new_zealand/analysis/KAIKOURA2016_analysis.md) |

## Cross-case statistics

| Case | Full primary-reference size | Primary quality profile | Secondary / auxiliary products | Main reference risk |
|---|---:|---|---|---|
| Ridgecrest | 34,091 | Q1 detection/relative location; Q2 absolute location/completeness | Ross Q1 relative structure; SCSN Q3 baseline | Shared SCSN/template lineage |
| Prague | 8,811 local Cochran event rows | Q2 enhanced detection; metric-specific Q1 structural auxiliary | McMahon context; operational Q3 | Time-only core count 2,078; rounded spatial/depth mask 2,076; changing network |
| Magna | 5,623 relocated | Q1 relative location; Q2 detection/absolute location | Baker Q2 ML/nodal; UUSS Q3 baseline | Pang/Baker network mismatch |
| Maple Creek | 15,912 well located | Q1 relative location; Q2 enhanced detection | Routine Q3; phase products Q4 unless independent | Strong template lineage |
| Kīlauea | 44,188 summit events | Q1 summit relative geometry; Q2 summit detection | Wei Q2 broad detection/3-D location; HVO Q3 | Summit vs island-wide scope mismatch; changing network |
| Kaikōura | 2,013 final hypoDD | Q1 location/relocation/uncertainty; Q3 completeness | Tan Q2 detection; GeoNet Q3 baseline | Different event populations and network conditions |

## Frozen v1 benchmark windows

| Case | UTC window and event count | Spatial / depth / magnitude rule | Network condition | Waveform upper bound | Reference role |
|---|---|---|---|---:|---|
| Prague | 2011-11-11–11-19; Cochran 2,078 time-only (2,076 rounded mask) | 35.45231–35.55757°N, −96.87233–−96.73343°E; 1.016–9.618 km; magnitude type unresolved | 31-station RAMP/USArray/Oklahoma heterogeneous network | 25.71264 GB decimal (23.95 GiB) | Cochran Q2 primary; Isken metric-specific structural anchor |
| Kaikōura | 2016-12-01–12-09; Lanza 122 / Tan S10 9,720 / S11 6,955 common-mask (6,973 time-only) | −43.5–−41.2°S, 172.0–175.2°E; 0–60 km; Tan S11 M −0.53–4.87 | 46 GeoNet/STREWN stations, permanent/temporary flags retained | 33.5 GB | Lanza Q1 location; Tan Q2 high-rate detection |
| Maple Creek | 2017-06-11–06-19; 22,858 phase IDs (not validated events) | 44.45–44.75°N, 110.55–110.15°W; 0–15 km; magnitude unavailable from phase-only release | 27-station Yellowstone/EarthScope–IRIS setup | 19.6 GB | Shelly Q1/Q2; phase release Q4 auxiliary |
| Kīlauea | 2018-05-01–05-09; Shelly S1/S2 1,883/1,877 common-mask (time-only 1,902/1,896); Wei 2,369 rows (1,930 numeric-M) | Summit: 19.30–19.50°N, −155.40–−155.15°W; 0–20 km; Shelly S1 M −0.72–4.80 | Shelly local phase release: 25 HV station codes; Wei HV/PT/Z1/Z6/4S/AM deployments separate | Not frozen; derive station/channel/day manifest | Shelly Q1/Q2 summit; Wei Q2 cross-check |
| Ridgecrest | 2019-07-04–07-07; Shelly 7,716 / AWR 5,737 | 35.45–36.05°N, −117.90–−117.20°W; 0–20 km; Shelly M −0.10–7.10 | 39-station CI/SCSN 3C subset within ~100 km | 28.3 GB | Shelly Q1 primary; AWR/Liu Q1–Q2 cross-check |
| Magna | 2020-03-18–03-26; Pang 4,102 valid-magnitude events | 40.69–40.84°N, −112.14–−111.94°W; −1.3–13.1 km; Mc −3.9–5.67 | Pang 39 stations/226 channels; Baker 180-node condition separate | 28.3 GB Pang; 130.6 GB Baker upper bound | Pang Q1/Q2 primary; Baker Q2 nodal/pick-level |

Waveform volumes are reproducible continuous-data upper bounds using `stations × 3 components × 100 Hz × 4-byte samples × window duration`; they are not claims about the final downloaded byte count. Actual manifests must apply station-day availability, channel response policy, gaps, and compression.

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

Current status for all six cases: `window-frozen`; waveform sampling and final catalog-gap resolution remain pending. Maple Pang and QuakeFlow Hawaiʻi still lack their dedicated public event catalogs, and Magna Baker still lacks the local paper PDF.

## Literature and catalog gap-audit summary

| Case | Audit result | Sufficiency status | Highest-priority addition |
|---|---|---|---|
| Ridgecrest | Core set strong but missing an independent raw-waveform ML catalog | Conditionally sufficient after Liu | Liu et al. (2020), DOI 10.1029/2019GL086189 |
| Prague | Material catalog omission | Conditionally sufficient after Cochran | Cochran et al. (2020) 8,811-event catalog, DOI 10.1093/gji/ggaa153 |
| Magna | Core catalog set currently sufficient | Sufficient after local acquisition/validation | Baker ISC catalog and article |
| Maple Creek | Material independent-location omission | Conditionally sufficient after Pang | Pang et al. (2019), DOI 10.1029/2019GL082376 |
| Kīlauea | Core pair strong; spatial-role gaps remain | Conditionally sufficient after scope freeze | Lengliné et al. (2021) and Matoza et al. (2021) |
| Kaikōura | Strong core pair but missing a major dense catalog | Sufficient after Chamberlain | Chamberlain et al. (2021), Zenodo record 5035841 |

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

The detailed records are:

- [RIDGE2019 analysis](../data/2019_ridgecrest_california/analysis/RIDGE2019_analysis.md)
- [PRAGUE2011 analysis](../data/2011_prague_oklahoma/analysis/PRAGUE2011_analysis.md)
- [MAGNA2020 analysis](../data/2020_magna_utah/analysis/MAGNA2020_analysis.md)
- [MAPLE2017 analysis](../data/2017_maple_creek_yellowstone/analysis/MAPLE2017_analysis.md)
- [KILAUEA2018 analysis](../data/2018_kilauea_hawaii/analysis/KILAUEA2018_analysis.md)
- [KAIKOURA2016 analysis](../data/2016_kaikoura_new_zealand/analysis/KAIKOURA2016_analysis.md)
