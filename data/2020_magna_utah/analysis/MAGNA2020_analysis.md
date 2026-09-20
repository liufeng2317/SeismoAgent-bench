# MAGNA2020 — Magna, Utah case analysis

> This is the case-level synthesis.  Paper reading and file-level catalog
> audits live beside their source products; this file records how to use them
> together without conflating event, pick, network, or quality populations.

## Status and case identity

- **Case ID:** `MAGNA2020`
- **Sequence:** 18 March 2020 (M_w 5.7) Magna mainshock and aftershocks,
  Salt Lake Valley, Utah, USA.
- **v1 benchmark window:** `2020-03-18T00:00:00Z <= origin_time <
  2020-03-26T00:00:00Z` (8 calendar days).
- **Common mask:** `40.69 <= lat <= 40.84`, `-112.14 <= lon <= -111.94`,
  `-1.3 <= depth_km <= 13.1`.
- **Audit status:** the Pang paper and ISC catalog are parsed and reconciled;
  the Baker ISC pick release is parsed.  The Pang S1 supplement and Baker
  article PDF are still missing, so method reproduction is not yet closed.

## Scientific role

This is a medium-scale mainshock–aftershock case with two complementary
research products:

1. **Pang et al. (2020):** permanent-network matched filtering followed by
   high-precision relative relocation.  It is the primary geometric target.
2. **Baker et al. (2021):** machine-learning picks and event locations under a
   dense temporary/nodal observation condition.  It is a secondary pick-level
   and network-condition target.
3. **UUSS/USGS operational export:** Q3 baseline only; it is not a substitute
   for either research catalog.

Pang and Baker must remain separate tasks.  Pang used 39 stations/226 channels
and explicitly did not use the 180-node deployment; Baker's release contains
repeated P/S picks from 205 `UU` station codes and two `GS` codes.  A raw row
count or station count cannot be compared across the two products.

## Reference evaluation matrix

| Reference | Evaluation role | Article / release span | Spatial/depth scope | Quality tier | Observation condition | Readiness |
|---|---|---|---|---|---|---|
| Pang et al. 2020, `PANG2020_GL089798` | **Primary:** matched-filter enhancement and relative relocation | Article processing 17 Mar–30 Apr 2020; local ISC rows extend 18 Mar–8 May | Article matched-filter radius ~40 km; frozen common mask above | Q1 relative geometry; Q2 detection; Q3 completeness | UUSS; 39 stations / 226 channels; nominal 100 Hz | Paper/catalog ready; S1 missing |
| Baker et al. 2021, `BAKER2021_0220200316` | **Secondary:** ML picks, association, dense nodal condition | Local origins 18 Mar–29 Apr 2020; paper describes 18 Mar–30 Apr | Local event extrema above; frozen common mask above | Q2 ML/pick-level; Q3 operational comparison | Local release: 326,969 `UU` + 2,642 `GS` pick rows; article inventory reports 180 temporary 3C 5-Hz geophones | Catalog ready; article PDF missing |
| UUSS/USGS operational snapshot | **Baseline:** routine operational catalog | Local full/benchmark exports in `USGS_UUSS_COMCAT_2020` | Query-defined case mask | Q3 | UUSS/ComCat source attribution | Ready as baseline |

Detailed source notes:

- [Pang paper reading](../references/PANG2020_GL089798/parsed/paper/PANG2020_GL089798__paper_reading.md)
  separates article-reported populations from local release counts.
- [Pang catalog audit](../catalogs/PANG2020_GL089798/PANG2020_GL089798__catalog_summary.md)
  records byte identity, timestamp anomalies, and strict/normalized window counts.
- [Baker catalog audit](../catalogs/BAKER2021_0220200316/BAKER2021_0220200316__catalog_summary.md)
  treats the CSV as pick-level and aggregates event counts explicitly.

## Paper-derived construction details

### Pang et al. (2020)

The article reports a UUSS urban–regional network of 203 stations (40 broadband,
97 strong-motion, 66 short-period) and five temporary telemetered additions.
For matched filtering it selected all available data within 40 km: 39 stations,
226 channels, nominally 100 Hz.  The paper's workflow was:

```text
UUSS routine picks/locations
  → 3–14 Hz detrend/filter and 100-Hz resampling
  → P templates (-0.2, +1.6 s), S templates (-0.2, +2.6 s)
  → channel-wise matched filtering
  → |correlation| threshold 0.6 (0.75–0.90 on selected channels)
  → DBSCAN (origin-time spread <=0.3 s; >=5 detections)
  → 4-s same-template suppression and ±5-s event/catalog suppression
  → correlation/RMS-ratio relative magnitudes
  → waveform differential times + hierarchical clustered relocation
```

The paper reports 56,679 P templates, 30,491 S templates, 5,501 new
aftershocks, and 5,623 relocated aftershocks.  The mainshock and many larger
aftershocks were not relatively relocated because of waveform complexity.  It
reports 2,103 routine UUSS locations by 30 April (2,077 with a magnitude type).
The local release's 3,595 `Template-Matching` rows and 2,144 blank-type rows
do not reproduce those article populations one-to-one; preserve both sets of
numbers and do not infer a relocation flag that is absent from the file.

### Baker et al. (2021)

The Baker PDF is not present locally.  The ISC README identifies the CSV as a
machine-learning-derived catalog containing P, S, first-motion, location, and
magnitude fields.  The file-level audit confirms approximately 142k P and 188k
S picks, consistent with the rounded counts recorded in the project inventory.
The article inventory records a 180-station three-component 5-Hz nodal
deployment, but exact detector/association/QC parameters and sample-rate
metadata must be verified from the paper before reproduction.  Until then,
Baker is a data-backed secondary target, not a fully extracted literature
reference.

## Frozen-window catalog comparison

The following counts use the source-native files and explicit aggregation rules.
Pang counts are event rows; Baker counts are one event per `event_number` plus
separate pick rows.  Pang's strict parser excludes seven in-window rows whose
seconds field is written as `-0.xxx` or `60.xxx`; a normalized sensitivity is
kept in the catalog summary.

| Product | Time-only | Common mask | Magnitude sensitivity | Notes |
|---|---:|---:|---:|---|
| Pang ISC | 4,163 rows; 4,102 with `Mc > -4` | **4,162 rows; 4,101 with `Mc > -4`** | normalized parser: 4,169 / 4,108 | 5,739 total; 3,595 source-labelled Template-Matching |
| Baker ISC | 3,782 events / 164,276 picks | **3,712 events / 161,567 picks** | 3,351 events / 150,379 picks with `magnitude > -4` | 329,611 picks; 5,885 total events |
| UUSS/USGS baseline | See baseline README | See baseline README | Source magnitude scale | Q3 only |

For the recommended common mask, Pang event ranges are 40.6933–40.8368°N,
−112.1375–−111.9413°E, −1.28–13.02 km, and `Mc > -4` values −3.9–5.67.
Baker event ranges are 40.6905–40.8285°N, −112.1396667–−111.9463333°E, and
0.1–13.1 km; source `magnitude > -4` values span −1.0888675–5.70.
The magnitude fields are not equivalent and should not be used for a direct
catalog ranking without a separate calibration.

## Network and waveform preparation

### Comparable primary condition

For the core Pang task, retrieve the 39-station/226-channel UUSS-compatible
waveforms from the IRIS/EarthScope DMC (and optional COSMOS strong-motion data)
for the frozen window.  Preserve network, station, channel, sample rate, and
availability flags.  The paper's matched-filter processing span begins one day
before the mainshock, so a reproduction may need a 17 March pre-roll even though
the scoring window starts on 18 March.

### Separate Baker nodal condition

Treat Baker as a separate observation regime.  Keep the 180-node deployment
metadata distinct from the permanent UUSS network and do not mix Baker picks
into the Pang target.  The local CSV alone cannot establish station-day
availability or waveform completeness.

### Storage upper bounds (not downloaded waveforms)

These are raw int32 continuous-data upper bounds, not measured file sizes:

- Pang channel-based upper bound: `226 channels × 100 Hz × 4 bytes × 8 days`
  ≈ **62.5 GB decimal** (58.2 GiB).  A 39×3-component approximation is
  ≈32.3 GB because the paper's 226 channels are not exactly 39×3.
- Baker nodal upper bound, if the inventory's 250 samples/s value is confirmed:
  `180 × 3 × 250 Hz × 4 bytes × 8 days` ≈ **373.2 GB decimal**.  This is
  provisional while the Baker PDF and station/sample-rate metadata are missing.

No waveform archive is counted as complete until station-day availability and
actual downloaded byte manifests are recorded.

## Benchmark decisions, risks, and next actions

| Decision / risk | Handling |
|---|---|
| Article versus ISC population mismatch | Keep article-reported 2,103/5,501/5,623 and local 2,144/3,595/5,739 values side by side; build an event crosswalk before scoring |
| Pang timestamp anomalies | Preserve raw text; strict and normalized policies are both recorded; use strict policy for v1 counts |
| Pick rows versus events | Aggregate Baker by `event_number`/`catalog_evid`; retain P/S rows for pick metrics |
| Magnitude scales | Treat Pang `Mc` and Baker `Mxc`/`d`/`l`/`h`/`w` as source-native, not interchangeable |
| Network confounding | Score Pang permanent-network and Baker nodal conditions separately |
| Missing literature | Download Pang S1 and Baker article PDF; only then finalize exact reproducibility parameters |
| Baseline | Use UUSS/USGS snapshot as Q3 operational context, never as a replacement for research references |

**Recommended v1 target:** Pang's common-mask event geometry under the 39-station
permanent-network condition.  Baker's pick/event product is a secondary
comparison track after the missing article and nodal metadata are recovered.

## Sources and local files

- Pang paper: [`../references/PANG2020_GL089798/paper/PANG2020_GL089798__paper.pdf`](../references/PANG2020_GL089798/paper/PANG2020_GL089798__paper.pdf)
- Pang reading note: [`../references/PANG2020_GL089798/parsed/paper/PANG2020_GL089798__paper_reading.md`](../references/PANG2020_GL089798/parsed/paper/PANG2020_GL089798__paper_reading.md)
- Pang catalog: [`../catalogs/PANG2020_GL089798/`](../catalogs/PANG2020_GL089798/)
- Baker catalog: [`../catalogs/BAKER2021_0220200316/`](../catalogs/BAKER2021_0220200316/)
- Baker reference status: [`../references/BAKER2021_0220200316/README.md`](../references/BAKER2021_0220200316/README.md)
- UUSS/USGS baseline: [`../catalogs/USGS_UUSS_COMCAT_2020/`](../catalogs/USGS_UUSS_COMCAT_2020/)
