# AWR2025_CALTECHDATA — Version 2 catalog summary and reproducible audit

## Provenance and files

- Source article: Atterholt, Wilding & Ross (2025), DOI [10.1093/gji/ggaf001](https://doi.org/10.1093/gji/ggaf001).
- Current local release: CaltechDATA DOI [10.22002/5af05-cah73](https://doi.org/10.22002/5af05-cah73), Version 2 as staged in this project.
- Article text also cites catalog DOI [10.22002/f40da-hww21](https://doi.org/10.22002/f40da-hww21); it is retained as a separate provenance reference because the local files do not include a release manifest proving identity.

| File | Format / role | Bytes | Data rows | SHA-256 |
|---|---|---:|---:|---|
| `AWR2025_CALTECHDATA__catalog_hypocenters_v2.csv` | CSV hypocenters | 19,728,609 | 222,864 | `fa87745528bddc66e7b1d25a94cba8d2448d38f67c6157c566ae451a84fa3ea8` |
| `AWR2025_CALTECHDATA__catalog_moment_tensors_v2.csv` | CSV moment tensors | 1,956,794 | 4,890 | `0746e6bbc694cf63d06112517305e91bf282a80833e660d6e6b0ea77578a33e7` |

## Native schema

### Hypocenters

Columns: `evid,time,latitude,longitude,depth_km,magnitude_gamma,qnpair,qndiffP,qndiffS,rmsP,rmsS`.
`evid` is unique in the local file. `magnitude_gamma` is a release-specific
amplitude/gamma magnitude; no standard ML/Mw label is supplied. `qnpair` is
positive for all rows, while differential P/S counts can be zero.

### Moment tensors

Columns include `evid,time,latitude,longitude,depth_km,magnitude,moment`, six
moment-tensor components, isotropic/CLVD terms and uncertainties, two nodal
planes, strike/dip/rake standard deviations, and `n_picks_used`. All 4,890 local
rows have at least 15 picks and angular standard deviations below 7.5°.

## Full release audit

| Field | Hypocenters v2 | Moment tensors v2 |
|---|---:|---:|
| Rows / unique IDs | 222,864 / 222,864 | 4,890 / 4,890 |
| Duplicate origin times | 2 | 0 |
| Time range | 2019-04-04 01:47:41.335–2023-05-01 20:55:26.801 UTC | 2019-04-07 18:52:58.223–2023-04-21 07:11:10.306 UTC |
| Latitude | 34.910170–36.573010°N | 35.196190–36.462740°N |
| Longitude | −118.612600–−116.740580°E | −118.598140–−117.023630°E |
| Depth | −0.599–19.539 km | −0.210–13.573 km |
| Magnitude | γ −0.723–4.585 | 1.366–4.115 |
| Negative depth rows | 78 | 4 |
| Angular-uncertainty criterion | Not applicable | all rows: strike/dip/rake std <7.5° |

## Frozen benchmark-window audit

Rule: half-open UTC 2019-07-04 through 2019-07-07; latitude 35.45–36.05°N;
longitude −117.90–−117.20°; depth 0–20 km.

| Product | Time-only | Common mask | Common-mask time range |
|---|---:|---:|---|
| Hypocenters | 5,842 | 5,737 | 2019-07-04 04:03:01.162–2019-07-06 23:59:20.494 UTC |
| Moment tensors | 258 | 254 | 2019-07-04 16:13:43.096–2019-07-06 23:56:34.234 UTC |

Hypocenter common-mask ranges: latitude 35.505180–36.050000°N, longitude
−117.877930–−117.267740°, depth 0.692–14.732 km, gamma magnitude 0.056–4.585.
Moment-tensor common-mask ranges: latitude 35.548390–36.038930°N, longitude
−117.847810–−117.366030°, depth 0.921–12.866 km, magnitude 1.8739–4.1146.

## Article-versus-release reconciliation

The article reports 214,467 retained relocated hypocenters and 4,892 accepted
moment tensors. The local Version 2 release has 222,864 and 4,890 rows. No
single obvious threshold on the local `qndiffP/qndiffS` fields reproduces the
article count, so these are recorded as release/version differences. Do not
trim the local files to the article counts without obtaining the exact article
supplementary ZIP or release manifest.

## Benchmark role and limitations

- **Tier:** Q2 long-term methodological auxiliary; metric-specific Q1 for the
  accepted relative-location and moment-tensor uncertainty subsets.
- The catalog spans a changing 66-station, multi-network deployment and is not
  a stationary July-2019 observation condition.
- `magnitude_gamma` must remain distinct from ML/Mw; it is unsuitable for direct
  magnitude comparisons without calibration.
- The workflow uses PhaseNO, GaMMA, HypoSVI and GrowClust, so method overlap
  with a future Agent implementation can create leakage; use AWR primarily as
  an auxiliary cross-check, not the sole hidden target.

## Local outputs

- Paper reading: `../../references/AWR2025_CALTECHDATA/paper/AWR2025_CALTECHDATA__paper_reading.md`
- Case synthesis: `../../analysis/RIDGE2019_analysis.md`
- Source README: `README.md`
