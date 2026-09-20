# Shelly & Thelen (2019) — paper reading and catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | David R. Shelly and Weston A. Thelen | PDF title block |
| Title | *Anatomy of a Caldera Collapse: Kīlauea 2018 Summit Seismicity Sequence in High Resolution* | PDF p. 1 / MinerU content-list p. 0 |
| Journal | *Geophysical Research Letters*, 46, 14,395–14,403 (2019) | PDF citation block |
| DOI | [10.1029/2019GL085636](https://doi.org/10.1029/2019GL085636) | DOI / article PDF |
| Article type | Research article that constructs a waveform-detection and double-difference summit catalog, then applies correlation-derived polarity clustering | Abstract; §§2–3 |
| Public data release | USGS [10.5066/P9DMIFMW](https://doi.org/10.5066/P9DMIFMW); local S1/S2 products and metadata are preserved | Article reference/data release; local files |
| Supporting information | `supplement/Shelly2019_Kilauea_Figure_SI.pdf` is present; it is figure-based and has not been treated as a machine-readable catalog | Local provenance |
| Local paper parse | `paper/SHELLY2019_GL085636__paper__mineru.md`; methods anchors below use MinerU content-list pages because concatenated Markdown has no page breaks | Local parse audit |

This is a genuine catalog-construction paper and the strongest summit-relative
reference in this case. It is not an island-wide completeness truth set: the
catalog is template-conditioned, focused on the summit, and the authors caution
that the derived magnitudes are only approximate.

## Scientific scope and observation conditions

- Sequence: Kīlauea's 2018 eruption and incremental summit caldera collapse,
including the 4 May 2018 Mw 6.9 south-flank earthquake and repeated Mw~5.2–5.4
collapse events.
- Article span: 2018-04-29 through 2018-08-06 UTC (PDF pp. 1–2; metadata XML).
- Target region: shallow summit seismicity, mostly <2.5 km below the Kīlauea
summit datum; the catalog is not intended to represent the lower East Rift Zone,
offshore flank, or island-wide seismicity.
- Initial templates: 2,823 HVO-cataloged earthquakes spanning the full study
period. During May Run 1, both automatic and analyst-refined events were used;
later runs used analyst-refined templates only because of their higher quality
(PDF p. 3 / MinerU content-list p. 3).
- Waveforms and routine catalog: HVO stations and phase picks supplied by HVO;
waveforms retrieved through the IRIS Data Management Center (PDF p. 12 / data
acknowledgements).
- Fixed station count: the paper's figure depicts the full network but the
article does not state one fixed count. The local correlation-phase CSV has 25
unique `HV` station codes. Do not replace this measured release fact with the
older case-level estimate of 66 stations without a station inventory from the
supporting material.

## Catalog-construction workflow

```text
HVO catalog templates (2,823 events)
    -> waveform cross-correlation detection during rolling processing runs
    -> correlation-derived P/S phase arrivals and differential times
    -> double-difference (hypoDD) relocation
    -> retain events with >=10 P and >=10 S differential-time constraints
    -> estimate approximate relative magnitudes
    -> group events by correlation-derived phase-polarity patterns
    -> 50 hierarchical polarity clusters (S2 product)
```

### Detection and relative location

- The method follows the integrated detection/precise-location workflow of
Shelly, Ellsworth & Hill (2016). The paper emphasizes that manual P/S picking
was infeasible during the intense summit sequence and that routine locations
were too uncertain to resolve the compact structures (PDF p. 3).
- The final catalog contains 44,188 earthquakes from 29 April to 6 August 2018
that retained at least 10 P and 10 S correlation-derived differential times
after the hypoDD inversion (PDF p. 3; Figure 1 caption). Exact run-by-run
correlation thresholds and station masks are in the supporting material; the
local Figure SI PDF has not been converted into a parameter table here.
- The release includes both location products with and without local x/y/z
coordinates. Depths are nominally referenced to the Kīlauea summit, about 1.2
km above sea level, not a universal sea-level depth datum.

### Magnitudes and polarity grouping

- Newly detected magnitudes are estimated from waveform amplitude ratios to HVO
catalog earthquakes and their catalog magnitudes. The authors report broad
scatter and a systematic near-source bias, and explicitly recommend against
using these magnitudes for detailed b-value analysis (PDF p. 3).
- The same correlation measurements were used to derive relative phase polarity.
Approximately 25 million measurements were grouped into 50 hierarchical
clusters. The paper uses the clusters to distinguish source/mechanism families;
it does not invert focal mechanisms for the groups (PDF p. 3; Figure 2).

## Reported products and quality controls

| Product/stage | Article or local value | Evidence |
|---|---:|---|
| HVO template events | ~2,823 | PDF p. 3 |
| Final S1 high-resolution catalog | 44,188 events | PDF p. 3 / local file |
| S2 polarity-cluster catalog | 43,950 events; 50 cluster labels | Local S2 and metadata |
| S1→S2 event difference | 238 S1 IDs do not receive an S2 cluster label | Local ID audit |
| Retention criterion | At least 10 P and 10 S correlation-derived differential times after hypoDD | PDF p. 3 |
| Correlation-phase auxiliary release | 8,582,492 data rows; 7,460,986 P and 1,121,506 S rows; 25 HV stations | Local USGS CSV audit |
| Approximate magnitude range in S1/S2 | −1.17–5.4 | Local catalog audit |
| Negative summit-referenced depths | 254 in S1; 253 in S2 | Local catalog audit |

The phase-arrival CSV is a pick-level/association auxiliary product, not a
replacement for the S1/S2 event catalogs. Its `template_id` and `match_id`
fields are not the same as the S1/S2 event IDs, and it includes many phase rows
per event.

## Benchmark interpretation

| Dimension | Decision |
|---|---|
| Quality tier | **Q1** relative summit geometry for retained hypoDD events; **Q2** dense summit detection/completeness; **Q3** only for island-wide or offshore claims |
| Primary role | High-rate summit event recovery, relative location, sequence geometry, and polarity-cluster structure |
| Suitable metrics | Event matching within the summit mask, relative epicenter/depth error, cluster/sequence geometry, detection support conditional on HVO/IRIS network availability |
| Unsuitable metrics | Absolute-location truth for the whole island, uniform completeness through the eruption, or fine magnitude/b-value scoring without calibration |
| Dependence | Medium: templates and initial picks come from HVO; waveform archive and USGS phase release are shared with operational products |
| Main biases | Template conditioning, changing processing runs/network availability, summit-only geometry, approximate magnitudes, summit-referenced depths |

## Frozen Kīlauea summit benchmark window

The case-level v1 rule is the half-open UTC interval
`2018-05-01T00:00:00Z <= origin_time < 2018-05-09T00:00:00Z`, with the common
summit mask `19.30 <= latitude <= 19.50`, `-155.40 <= longitude <= -155.15`,
and `0 <= depth_km <= 20`.

| Product | Time-only rows | Common summit-mask rows | Common-mask ranges |
|---|---:|---:|---|
| S1 high-resolution catalog | 1,902 | **1,883** | lat 19.329439–19.469961; lon −155.365674–−155.193571; depth 0.010–15.103 km; magnitude −0.72–4.80 |
| S2 polarity-cluster catalog | 1,896 | **1,877** | lat 19.32944–19.46996; lon −155.36567–−155.19357; depth 0.010–15.103 km; magnitude −0.72–4.80 |
| Wei S1 (secondary) | 2,369 | 2,369 under its own summit/depth mask | See Wei catalog summary; 1,930 rows have numeric magnitudes |

The time-only counts are useful for reproducing the article's temporal subset;
the common-mask counts are the comparable benchmark values. Negative depths
are retained in the source but excluded by the common depth rule. S1 and S2
share 43,950 event IDs; the 238 S1-only IDs explain why their window counts are
not identical.

## Local provenance and open actions

- Paper PDF: `data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/paper/SHELLY2019_GL085636__paper.pdf`
- Parsed paper: `data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/paper/SHELLY2019_GL085636__paper__mineru.md`
- Figure SI: `data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/supplement/Shelly2019_Kilauea_Figure_SI.pdf`
- Canonical event products: `data/2018_kilauea_hawaii/catalogs/SHELLY2019_GL085636/SHELLY2019_GL085636__catalog_S1.txt` and `...__catalog_S2.txt`
- Raw USGS phase release: `data/2018_kilauea_hawaii/catalogs/SHELLY2019_GL085636/raw/Kilauea_2018_correlation_phase_arrivals.csv` (607,958,927 bytes; SHA-256 `be6bab5bca8dff5355d763495ac2f9a5c54d157f80b0f315095e3d3caf1d8dc4`; local-only due size)
- Metadata: `raw/Kilauea_metadata_v2_clustersS2.xml` and the source-spelled `raw/Kileauea_metadata_v2_hyposS1.xml`
- Required follow-up: extract Figure SI/Table S1 run-specific thresholds and station masks before claiming exact reproducibility; keep station deployment and HVO/temporary network labels in waveform manifests.
