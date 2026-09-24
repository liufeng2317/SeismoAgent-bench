# MAPLE2017 - 2017 Maple Creek, Yellowstone case analysis

> Current preparation state: `window_status: not_frozen` in [processing.yaml](processing.yaml). Earlier “frozen/v1” windows and counts below are retained as exploratory audit history, not approved evaluation inputs.


> This is the detailed case audit. Cross-case summary belongs in
> docs/01_1_Case_details.md; source-specific reading and file-level audits live
> beside each paper or catalog.


## 1. Case identity and benchmark purpose

| Field | Frozen/working value |
|---|---|
| Canonical case ID | 2017_maple_creek_yellowstone |
| Sequence | Maple Creek earthquake swarm, Yellowstone region, Wyoming/Montana |
| Main activity | 2017-06-12 onward; article follows the 2017-2018 sequence |
| Largest event | Mw 4.4 on 2017-06-16 |
| Scientific role | Swarm detection, relative location, migration, and fault-network geometry |
| v1 benchmark window | 2017-06-11T00:00:00Z <= t < 2017-06-19T00:00:00Z |
| Frozen spatial/depth mask | 44.45 <= latitude <= 44.75; -110.55 <= longitude <= -110.15; 0 <= depth_km <= 15 |
| Network design | Yellowstone/UUSS plus EarthScope/IRIS; preserve station and template lineage |
| Waveform design upper bound | About 19.6 GB for 27 stations x 3 components x 100 Hz x int32 x 8 days; actual volume depends on gaps and selected channels |

The eight-day interval is frozen for consistency with the official baseline query.
The older inventory also records a compact seven-day interval ending 2017-06-18;
both phase-only counts are retained below so that the historical choice remains
traceable.

## 2. Reference evaluation matrix

| Source | What it really is | Role | Quality tier | Independence | Readiness |
|---|---|---|---|---|---|
| Shelly & Hardebeck 2019, DOI 10.1029/2018GL081607 | Genuine enhanced catalog paper; local USGS file is phase-only | Primary article-level target for template-enhanced detection and relative geometry | Q1 relative geometry; Q2 detection; Q3 absolute location | Low-Medium against matched-filter agents | Paper, SI, phase release ready; article event table not locally staged |
| Pang et al. 2019, DOI 10.1029/2019GL082376 | Genuine 3,345-event HYPOINVERSE + GrowClust paper | Independent high-resolution secondary location reference | Q1/Q2 | Medium-High method independence; shared UUSS/IRIS waveforms | Paper and SI ready; machine-readable event catalog missing |
| USGS/UUSS ComCat snapshot | Official operational export, not research truth | Q3 baseline and interoperability check | Q3 | Higher operational independence, but not independent of routine network | Full and frozen CSV snapshots ready; only 9/5 rows returned |
| MAPLE_RELATED_OPEN | Sheldon, Nevada 2023 paper, not Yellowstone | Context only; exclude from benchmark | N/A for Maple | N/A | Kept only to document misclassification |

### Interpretation

Shelly is the best local primary reference for a template-enhanced swarm
benchmark, but the event-level relocated table is not present in the staged
USGS release. Pang is the key independent location reference and should not be
dropped merely because its table is currently missing. The official ComCat
snapshot provides a reproducible low-resolution baseline, but its five events
in the frozen mask must not be interpreted as catalog completeness.

## 3. Shelly article and local phase release

### Article-reported populations

- 2,289 routinely cataloged events supplied waveform templates from 11 June to
  6 September 2017.
- Continuous scanning covered 11 June to 14 September.
- 34.1 million correlation-derived differential times and 1.3 million
  routine-catalog differential times entered hypoDD.
- 15,912 events retained at least 50 P and 50 S correlation observations and
  were considered well located.
- A less stringent threshold (at least 15 P and 30 S) yielded a 30,411-event
  magnitude catalog.
- The article states nearly 2,500 routine events and magnitudes up to Mw 4.4.

These are article values, not local CSV row counts.

### Local USGS phase release audit

File:
catalogs/SHELLY2019_GL081607/raw/Yellowstone_2017_correlation_phase_arrivals.csv

- 6,260,580 data rows, no malformed rows under the 11-column parser.
- 115,448 unique match IDs and 1,147 unique template IDs.
- P rows 3,933,935; S rows 2,326,645.
- Networks: WY 4,864,384; PB 1,394,725; US 872; TA 371; IW 228.
- 29 network-station pairs in the full file; 27 in the frozen eight-day time
  interval.
- Arrival span 2017-06-11T06:09:19.444800Z to 2017-09-17T16:13:09.091100Z.
- SHA-256 CSV:
  a1828099eb2a51339e01ffca191d6e4d98df27ad889c18837aa41278dd128d6c.
- The companion XML SHA-256 is
  547cbc7e43b11d47b2c10098850904151b4b63de5b95dc6c2d1edb147f1a96e5.

The phase file has no origin time, latitude, longitude, depth, or event-level
uncertainty. match_id is repeated across station/phase rows and cannot be
treated as an independently located event count. The local magnitude column
contains nine -inf values and four finite values below -10; finite values span
-6.99 to 5.17. This conflicts with the XML's declared magnitude domain and
requires QC before any magnitude metric.

### Time-only window counts

| Window | Phase rows | Unique match IDs | Interpretation |
|---|---:|---:|---|
| 2017-06-11 <= t < 2017-06-18 | 1,536,742 | 22,858 | Historical seven-day compact window; phase-associated IDs |
| 2017-06-11 <= t < 2017-06-19 | 1,591,090 | 23,660 | Frozen eight-day v1 window; phase-associated IDs |

The spatial/depth mask cannot be applied to this release. The article-level
15,912 and 30,411 event populations must be reported separately.

## 4. Pang article and missing event table

Pang genuinely constructs a 3,345-event catalog over 2017-06-12 to 2018-03-13.
It uses UUSS HYPOINVERSE absolute locations, about 4.4 million BCSEIS
differential times, and GrowClust relocation of 3,257 events. Twenty-two local
and two regional stations were used; median absolute errors are about 500 m
horizontal and 730 m depth, while bootstrap relative errors are about 62 m
horizontal and 86 m vertical. Coda magnitudes span Mc -1.7 to 4.4 with
completeness near Mc 0.5.

The local supplementary PDF is method/figure material, not a CSV, QuakeML, or
spreadsheet event table. No verified public machine-readable 3,345-row table
has been staged. Therefore:

- Pang remains a real, important secondary reference.
- The Pang catalog column is missing, not partial.
- No Pang row count, coordinate range, or frozen-window count is asserted as a
  local audit.
- The Shelly USGS phase release cannot be relabeled as Pang.
- The next acquisition action is to find an author/publisher/repository release
  whose provenance explicitly identifies the 3,345-event table and relocation
  status.

## 5. Official baseline audit

Query definition is versioned in
scripts/00_catalog_downloading/official_baseline_windows.json.

| Snapshot | Rows | Local range | Notes |
|---|---:|---|---|
| Full 2017-06-11 to 2017-09-15 | 9 | M 0.16-1.86; depth 2.08-5.97 km | All reviewed, network uu |
| Frozen 2017-06-11 to 2017-06-19 and spatial/depth mask | 5 | M 1.01-1.86; depth 2.20-4.67 km | All reviewed, network uu |

The low count likely reflects the exact ComCat/UUSS query and source filters;
it is not a statement that the swarm had five events. Preserve the snapshots
for reproducibility but do not use them as a completeness truth set.

## 6. Catalog comparability and valid metrics

| Comparison | Valid now? | Rationale |
|---|---|---|
| Shelly article event catalog vs Pang event catalog | Not yet | Pang machine-readable table missing; acquire before event-level overlap |
| Shelly phase release vs waveform phase picker | Yes, with lineage labels | Both are phase observations; evaluate timing/association, not locations |
| Shelly phase release vs ComCat events | Limited | Requires explicit phase-to-origin association; no coordinates in phase release |
| Pang article-reported counts vs ComCat rows | No | Different populations and detection thresholds |
| Common spatial/depth event benchmark | Only for ComCat currently | Shelly local phase release and Pang local table lack event coordinates |

Do not collapse phase rows, article event counts, and official baseline rows into a
single leaderboard. Keep event detection, phase timing, absolute location, and
relative location as separate tasks.

## 7. Remaining data-preparation actions

1. Acquire and checksum Pang's 3,345-event machine-readable table, preferably
   from an author/publisher/repository DOI.
2. Locate the Shelly article's event-level relocated/magnitude table, if it is
   distinct from the USGS phase release; record whether it contains 15,912,
   30,411, or another filtered population.
3. Obtain station metadata and station-day availability for the 27-station
   Shelly setup and the 24-station Pang relocation setup.
4. Download the common eight-day waveforms only after station/channel selection
   is frozen; retain network and template lineage.
5. Generate derived plots under each catalog directory: daily phase/event rate,
   station availability, spatial/depth map when event tables are available,
   magnitude-frequency curves with QC flags, and phase-quality distributions.

## Catalog processing

Processing entry points and product declarations are in [processing.yaml](processing.yaml). Shared identifier and output rules are maintained in [data organization](../../README.md#processing-and-output-policy). File-level counts, schemas and figures belong to the catalog README and its generated analysis, rather than a second case index.

### Next preparation steps

1. Acquire and checksum Pang's 3,345-event machine-readable table before any
   event-level Shelly–Pang comparison.
2. Keep phase timing, event detection, absolute location and relative location
   as separate benchmark tasks.
3. Build station-day/channel manifests for the 27-station Shelly phase release
   and the 24-station Pang relocation design before waveform download.
4. Create an explicit cross-catalog event crosswalk; never join local
   `event_id` values directly.

### Re-run commands

From the repository root:

```bash
python3 data/2017_maple_creek_yellowstone/catalogs/SHELLY2019_GL081607/scripts/run_catalog_analysis.py
python3 data/2017_maple_creek_yellowstone/catalogs/USGS_UUSS_COMCAT_2017/scripts/run_catalog_analysis.py
```
