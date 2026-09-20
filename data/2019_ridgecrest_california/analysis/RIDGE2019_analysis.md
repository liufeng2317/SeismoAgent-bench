# RIDGE2019 — Ridgecrest case analysis

> This file is the case-level synthesis. Paper-specific extraction is kept next to each paper and catalog-specific audits are kept next to each catalog; links below are the canonical entry points.

## Status and frozen benchmark rule

- **Case ID:** `2019_ridgecrest_california`
- **Phase:** reference calibration and data preparation
- **Status:** v1 time/space/depth rule frozen; station-day waveform manifest still pending
- **Scientific sequence:** Mw 6.4 foreshock on 2019-07-04, Mw 7.1 mainshock on 2019-07-06, dense foreshock–aftershock activity
- **Frozen window:** `2019-07-04T00:00:00Z <= origin_time < 2019-07-07T00:00:00Z` (72 h)
- **Common mask:** `35.45 <= latitude <= 36.05`, `-117.90 <= longitude <= -117.20`, `0 <= depth_km <= 20`
- **Depth convention:** each source keeps its native datum; the mask is a numerical comparison rule, not a claim that all absolute depths share the same reference surface.

The compact 72-hour window covers the foreshock, the Mw 6.4 event, the
inter-mainshock interval and the first ~21 hours after Mw 7.1. A 34-hour
inter-mainshock subset can be generated later, but it is not the frozen v1
window because it would exclude the initial foreshock and immediate post-mainshock
stress conditions.

## How references were selected

The selection is deliberate, not a list of arbitrary search hits. A product is
kept as a benchmark reference only when it satisfies all of the following:

1. the paper is a real research or data-release article that constructs, relocates,
   or explicitly publishes an event catalog;
2. the local file can be tied to an authoritative DOI, USGS/SCEDC/CaltechDATA
   release, or article-associated supplement;
3. the product's evaluation role is dimension-specific (detection, association,
   absolute location, relative geometry, focal mechanism or operational baseline);
4. shared waveform/template lineage and method overlap are recorded separately
   from the quality tier; and
5. article-reported populations are kept distinct from local release-version
   counts.

No catalog is treated as universal ground truth. The Q1–Q4 tiers in
[`docs/01_1_Case_details.md`](../../../docs/01_1_Case_details.md) are applied by
metric and role.

## Reference evaluation matrix

| Reference / local product | Evaluation role | Article / release scope | Common-mask count | Quality tier and limitations | Network condition / independence |
|---|---|---|---:|---|---|
| Shelly (2020) Data S1 | **Primary** dense detection, association and relative geometry | Article: 2019-07-04–07-16; 34,091 final events | **7,716** (7,773 time-only) | **Q1** relative/detection structure; **Q2** absolute location/completeness. Mostly unreviewed; mainshock centroids are not preferred absolute hypocenters. | SCSN/SCEDC; routine SCSN templates; medium independence from Ross/routine baseline |
| Liu et al. (2020) Table S1 | Independent-method secondary for raw-waveform detection and hypoDD geometry | 2019-07-04–07-09; article reports 16,563 REAL, 16,112 VELEST and 15,445 final hypoDD events | **6,242** (6,329 time-only) | **Q2** automatic independent catalog; strong method cross-check, but no event IDs/uncertainty columns and magnitude scale differs | 41 permanent + 4 temporary stations within 120 km; higher algorithmic independence because no routine event prior |
| Ross et al. (2019) SCEDC QTM | Secondary structural/relocation diagnostics | Archive 2019-07-04–07-25; 111,918 rows, 46,512 successfully relocated (`nbranch>1`) | **12,768** total / **6,463** relocated | **Q1** relative geometry/QC for relocated subset; Q2–Q3 for initial-only rows and Mw 7.1 depth | SCSN/SCEDC; medium independence. Science DC1 methods supplement is missing locally |
| Atterholt–Wilding–Ross (2025) Version 2 | Long-term relocation and moment-tensor auxiliary | Hypocenters 2019-04–2023-05; MT 2019-04–2023-04; local v2 222,864 / 4,890 | **5,737** hypo / **254** MT | **Q2** long-term methodological auxiliary; metric-specific Q1 for accepted relative/MT uncertainty fields. Article reports 214,467/4,892, so release version must be preserved. | 66 multi-network broadband 3C stations, changing availability; PhaseNO/GaMMA/HypoSVI/GrowClust overlap with future Agent methods |
| USGS/SCSN ComCat snapshot | **Q3 baseline** operational recovery and large-event anchor | Full 2019-07-04–07-17; benchmark CSV is already frozen | **6,566** | **Q3** routine operational catalog; not a high-resolution truth set | SCSN/CI operational network; independent release but same regional observations |

### Why Shelly is primary

Shelly is the best Phase-I target because it has a verified article-associated
34,091-event release, explicit matched-filter and hypoDD criteria, public
waveform lineage, and a compact high-rate sequence. It is not “best” for every
metric: Liu is the key independent raw-waveform check, Ross is the strongest
structural/QTM diagnostic, and AWR is valuable for long-term and moment-tensor
comparisons.

## Article–catalog alignment audit

| Source | Is the paper genuinely a catalog-construction paper? | Local product alignment | Decision |
|---|---|---|---|
| Shelly 2020 | Yes: template matching + hypoDD relative relocation | Article 34,091 matches Data S1 34,091; phase CSV is a separate auxiliary product | Use Data S1 as primary; never count phase rows as events |
| Liu 2020 | Yes: PhaseNet → REAL → VELEST → hypoDD | Article final 15,445 matches Table S1 15,445; REAL/VELEST intermediates are not local | Use Table S1 as final hypoDD secondary |
| Ross 2019 | Yes: high-resolution template-matched/relocated seismicity catalog | Official QTM archive has 111,918 rows, but only `nbranch>1` (46,512) are successful relocations; article DC1 absent | Use relocated subset for Q1 structure; obtain DC1 before exact reproduction |
| AWR 2025 | Yes: PhaseNO → GaMMA → HypoSVI → GrowClust + Bayesian MT inversion | Local v2 has 222,864 hypocenters and 4,890 MT vs article 214,467/4,892 | Keep local v2 intact and record article/release discrepancy; do not trim by guesswork |
| USGS SCSN | No research construction article is attached | Official operational query snapshot only | Baseline, not a research truth catalog |

## Catalog comparison under the common rule

| Product | Full rows / span | Time-only | Common mask | Common-mask time / spatial / depth / magnitude range |
|---|---:|---:|---:|---|
| Shelly Data S1 | 34,091; 2019-07-04–07-16 | 7,773 | 7,716 | 2019-07-04 15:35:29.400–07-06 23:59:47.320; 35.4852–36.0128, −117.8192–−117.2557, 0.159–19.953 km, M −0.10–7.10 |
| Liu Table S1 | 15,445; 2019-07-04–07-09 | 6,329 | 6,242 | 2019-07-04 00:56:37.520–07-06 23:59:30.040; 35.5040–36.0473, −117.8836–−117.2759, 0.002–14.126 km, M −0.20–5.50 |
| Ross QTM all rows | 111,918; 2019-07-04–07-25 | 12,806 | 12,768 | 2019-07-04 03:26:19.848–07-06 23:59:47.190; 35.5017–36.0496, −117.8955–−117.2225, 0.018–19.700 km, M −0.82–7.10 |
| Ross QTM relocated only | 46,512 | 6,470 | 6,463 | Same mask; filter `nbranch>1` before relative-location metrics |
| AWR v2 hypocenters | 222,864; 2019-04–2023-05 | 5,842 | 5,737 | 2019-07-04 04:03:01.162–07-06 23:59:20.494; 35.5052–36.0500, −117.8779–−117.2677, 0.692–14.732 km, gamma-M 0.056–4.585 |
| AWR v2 moment tensors | 4,890; 2019-04–2023-04 | 258 | 254 | 2019-07-04 16:13:43.096–07-06 23:56:34.234; 35.5484–36.0389, −117.8478–−117.3660, 0.921–12.866 km, M 1.874–4.115 |
| USGS/SCSN benchmark | 6,566; 2019-07-04–07-07 | 6,566 | 6,566 | 35.4935–36.0495, −117.8912–−117.2680, 0–19.09 km, M 0.14–7.10 |

The counts target different populations: Shelly and Ross are template/correlation
products, Liu is pick-based and independent of the routine event prior, AWR is a
long-term modern workflow, and SCSN is operational. Event-count ranking without
conditioning on method and network is invalid.

## Catalog construction and quality notes

### Shelly primary

- 13,525 SCSN template events → daily 100-Hz template scans → correlation and
  differential-time weighting → hypoDD.
- Detection thresholds: 8× daily MAD for summed correlation and 7× MAD for
  individual differential-time correlations; max differential times 0.5 s (P)
  and 0.85 s (S).
- Final event criterion: at least 12 P and 12 S correlation differential times.
- Magnitudes combine SCSN preferred values and calibrated ML for newly detected
  events. Small-event completeness changes strongly after each mainshock.

See [`SHELLY2020_0220190309__paper_reading.md`](../references/SHELLY2020_0220190309/parsed/paper/SHELLY2020_0220190309__paper_reading.md) and
[`SHELLY2020_0220190309__catalog_summary.md`](../catalogs/SHELLY2020_0220190309/SHELLY2020_0220190309__catalog_summary.md).

### Liu independent secondary

- PhaseNet probability picks (0.5) → REAL grid association (≥5 P and ≥13 total
  picks, 0–20 km) → VELEST (<200° gap, <0.6 s residual) → hypoDD (stations
  <80 km, phase probability >0.7).
- SI Text S3 documents 884 routine events missed by strict thresholds, depth
  truncation, close-event suppression, coda burial and poor geometry.
- The paper reports 7,425 routine events in Section 2 but 7,743 in the Conclusion; this internal discrepancy is retained and is not used to alter Table S1.

See [`LIU2020_GL086189__paper_reading.md`](../references/LIU2020_GL086189/parsed/paper/LIU2020_GL086189__paper_reading.md) and
[`LIU2020_GL086189__catalog_summary.md`](../catalogs/LIU2020_GL086189/LIU2020_GL086189__catalog_summary.md).

### Ross QTM secondary

- The SCEDC schema retains initial and relocated locations plus differential-time
  counts, RMS residuals, errors and cluster IDs.
- Use `nbranch>1` as the relocation flag. The Mw 7.1 QTM depth is explicitly
  poorly constrained; use SCSN for the mainshock absolute anchor.
- The missing Science DC1 is a real gap in method reproducibility, not evidence
  that the QTM archive is absent.

See [`ROSS2019_SCIENCE__paper_reading.md`](../references/ROSS2019_SCIENCE/parsed/paper/ROSS2019_SCIENCE__paper_reading.md) and
[`ROSS2019_SCIENCE__catalog_summary.md`](../catalogs/ROSS2019_SCIENCE/ROSS2019_SCIENCE__catalog_summary.md).

### AWR long-term auxiliary

- PhaseNO → GaMMA → HypoSVI → GrowClust; accepted MT rows require at least 15
  P-amplitude picks and angular uncertainties below 7.5°.
- Local Version 2 is authoritative for the files in this repository, but its
  row counts differ from the article. `magnitude_gamma` remains a native field,
  not ML/Mw.

See [`AWR2025_CALTECHDATA__paper_reading.md`](../references/AWR2025_CALTECHDATA/parsed/paper/AWR2025_CALTECHDATA__paper_reading.md) and
[`AWR2025_CALTECHDATA__catalog_summary.md`](../catalogs/AWR2025_CALTECHDATA/AWR2025_CALTECHDATA__catalog_summary.md).

## Network and waveform preparation

- Shelly, Ross, Liu and SCSN all use the SCSN/SCEDC regional archive, but their
  station subsets and processing windows differ.
- Liu reports 41 permanent + 4 temporary stations within 120 km; AWR reports 66
  broadband 3C stations selected in a 200 × 200 km region over four years.
- Shelly's article does not state a fixed station count; the auxiliary phase CSV
  has 30 network-station pairs (5,703,270 rows), which is not a station inventory.
- A provisional continuous-waveform storage upper bound for a future 72-hour
  39-station/3C/100-Hz/int32 condition is ~28.3 GB, but this is a design bound,
  not a frozen observed volume. The station-day/channel manifest must be built
  from SCEDC availability before waveform volume is used as a benchmark metric.

## Readiness and open actions

- [x] Shelly article, Data S1, XML metadata and auxiliary phase CSV staged and hashed.
- [x] Liu article, SI DOCX and final Table S1 staged and hashed.
- [x] Ross article and official SCEDC QTM archive staged and field-audited.
- [x] AWR article and local Version 2 hypocenter/MT files staged and hashed.
- [x] USGS/SCSN full and benchmark operational snapshots staged.
- [ ] Download/attach Ross Science DC1 and extract exact template/relocation parameters.
- [ ] Obtain an exact AWR article-supplement/release manifest to explain 214,467 vs 222,864 and 4,892 vs 4,890.
- [ ] Build station-day/channel availability and waveform-volume manifest for the frozen 72-hour window.
- [ ] Normalize event IDs only in derived files; never edit source catalogs.
- [ ] Generate comparable map/time/depth/magnitude plots under each catalog's `raw/` or `figures/` directory.

## Local source index

- [`references/SHELLY2020_0220190309/parsed/paper/SHELLY2020_0220190309__paper_reading.md`](../references/SHELLY2020_0220190309/parsed/paper/SHELLY2020_0220190309__paper_reading.md)
- [`catalogs/SHELLY2020_0220190309/SHELLY2020_0220190309__catalog_summary.md`](../catalogs/SHELLY2020_0220190309/SHELLY2020_0220190309__catalog_summary.md)
- [`references/LIU2020_GL086189/parsed/paper/LIU2020_GL086189__paper_reading.md`](../references/LIU2020_GL086189/parsed/paper/LIU2020_GL086189__paper_reading.md)
- [`catalogs/LIU2020_GL086189/LIU2020_GL086189__catalog_summary.md`](../catalogs/LIU2020_GL086189/LIU2020_GL086189__catalog_summary.md)
- [`references/ROSS2019_SCIENCE/parsed/paper/ROSS2019_SCIENCE__paper_reading.md`](../references/ROSS2019_SCIENCE/parsed/paper/ROSS2019_SCIENCE__paper_reading.md)
- [`catalogs/ROSS2019_SCIENCE/ROSS2019_SCIENCE__catalog_summary.md`](../catalogs/ROSS2019_SCIENCE/ROSS2019_SCIENCE__catalog_summary.md)
- [`references/AWR2025_CALTECHDATA/parsed/paper/AWR2025_CALTECHDATA__paper_reading.md`](../references/AWR2025_CALTECHDATA/parsed/paper/AWR2025_CALTECHDATA__paper_reading.md)
- [`catalogs/AWR2025_CALTECHDATA/AWR2025_CALTECHDATA__catalog_summary.md`](../catalogs/AWR2025_CALTECHDATA/AWR2025_CALTECHDATA__catalog_summary.md)
- [`catalogs/USGS_SCSN_COMCAT_2019/README.md`](../catalogs/USGS_SCSN_COMCAT_2019/README.md)
