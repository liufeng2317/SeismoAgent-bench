# CHAMBERLAIN2021_JB022304 — catalog summary and reproducible audit

## Provenance and product lineage

- Source article: Chamberlain et al. (2021), DOI [10.1029/2021JB022304](https://doi.org/10.1029/2021JB022304).
- Official article data/code archive: [Zenodo 6763130](https://zenodo.org/record/6763130), cited in the paper's data-availability statement.
- Legacy public CSV: [Zenodo record 5035841](https://zenodo.org/records/5035841), local file `CHAMBERLAIN2021_JB022304__catalog_growclust.csv`.
- Canonical benchmark CSV: `CHAMBERLAIN2021_JB022304__catalog_growclust_corrected_focal_mechanisms.csv`, the corrected focal-mechanism release supplied with the local project materials.
- Both files are preserved. The corrected file is the benchmark input; the legacy file is a provenance/control product and must not be concatenated with it.

### Checksums

| File | Rows | SHA-256 | Use |
|---|---:|---|---|
| `CHAMBERLAIN2021_JB022304__catalog_growclust_corrected_focal_mechanisms.csv` | 33,328 | `6f00695585998c365a81132a60bc3c7ebe058abdd352e8d8d8f802489559137a` | **Canonical benchmark product** |
| `CHAMBERLAIN2021_JB022304__catalog_growclust.csv` | 34,704 | `b2f7c6e60198b309274051764b564a5a544ae039e45a142e2e31034e0068fc2b` | Legacy/provenance comparison only |

## Native schema and units

Both CSVs expose the same 37 column names, including `time`, `latitude`,
`longitude`, `depth`, `magnitude`, `local_magnitude`, phase/station counts,
uncertainties, `event_id`, `stations`, `template-id`, `strike`, `dip`, `rake`,
`kappa`, `scalar error`, and `Slip style`. The leading `Unnamed: 0.1` and
`Unnamed: 0` columns are export indices, not event identifiers.

- `time` is parseable as UTC-like ISO text with microsecond precision; no timezone
suffix is encoded in the CSV, so the audit treats it as UTC because the article's
workflow and case definition use UTC.
- `depth` is stored in metres in the CSV and is converted to kilometres in the
statistics below.
- `magnitude` and `local_magnitude` are numerically identical for the populated
rows and are labelled `ML` in 33,278 rows; 50 rows have no magnitude.
- `event_id` is a stable `smi:local/...` string in the corrected file. The
corrected file has 33,328 unique IDs and no duplicate IDs or times.
- `station_count`, phase-count and uncertainty fields are retained as published;
zero and missing values are not imputed.

## Corrected catalog audit

| Field | Full corrected product |
|---|---:|
| Rows / unique event IDs | 33,328 / 33,328 |
| Duplicate event IDs / duplicate origin times | 0 / 0 |
| Origin time | 2009-01-02 22:33:53.563403 to 2020-01-01 16:04:54.216000 UTC |
| Latitude | −43.878229–−39.975169° |
| Longitude | 171.971969–177.414826°E |
| Depth | −2.990234–97.898000 km |
| Local magnitude | 0.234392–6.312942; 50 missing; type `ML` where present |
| Associated phase count | 0–65 |
| Used phase count | 1–6,967 |
| Station count | 0–27 |
| Horizontal uncertainty | 1–2,292 (27,109 populated rows; source units not documented in CSV) |
| Vertical uncertainty | 0–36,871.2625 (source units not documented in CSV) |
| Complete strike/dip/rake mechanism rows | 1,756 |
| Slip-style labels | Strike-slip 17,172; Unknown 8,818; Reverse 4,267; Normal 3,071 |

The paper reports 33,328 final events and 27,431 GrowClust relocations. The CSV
does not expose a plainly named `relocated` flag, so the latter count should not
be reverse-engineered from `template-id`, focal-mechanism fields, or missing
values without the Zenodo code/QuakeML archive.

## Legacy-versus-corrected comparison

The legacy file has 34,704 rows but only 33,329 unique event IDs: 1,375 IDs are
duplicated, and one row is visibly malformed/column-shifted (`event_id = 0.0`,
`time = 201`, `magnitude_type = ML`). After deduplicating on `event_id`, all
33,328 corrected IDs are shared. For the shared IDs, the non-focal fields
(time, coordinates, depth, magnitudes, phase/station counts, uncertainties,
station lists and template IDs) match within numeric representation. The
correction changes focal-mechanism values (1,770 shared rows have changed
strike/dip/rake values; 7,013 have changed `Slip style` labels). Therefore:

1. use the corrected CSV for all benchmark statistics;
2. retain the legacy CSV only to document release lineage and the focal-mechanism
correction;
3. never count the two files together.

## Frozen Kaikōura benchmark window

Case rule: half-open UTC time interval
`2016-12-01T00:00:00Z <= time < 2016-12-09T00:00:00Z`, followed by the common
mask `−43.5 <= latitude <= −41.2`, `172.0 <= longitude <= 175.2`, and
`0 <= depth_km <= 60`.

| Field | Time-only selection | Common benchmark mask |
|---|---:|---:|
| Rows / unique IDs | 2,273 / 2,273 | 2,214 / 2,214 |
| Time range | 2016-12-01 00:03:58.705 to 2016-12-08 23:54:15.046341 UTC | same |
| Latitude | −43.878229–−40.889090° | −42.973046–−41.500135° |
| Longitude | 172.602810–175.183344°E | 172.602810–175.183344°E |
| Depth | −2.980469–96.687500 km | 0.007812–45.515625 km |
| Local magnitude | 0.475050–5.303747; 2 missing | 0.475050–5.303747; 2 missing |
| Complete focal mechanisms | 114 | 113 |

The common mask removes 59 time-window rows. This is a case-comparison rule,
not a claim that the removed catalog locations are all physically invalid.

## Benchmark role and limitations

- **Tier:** Q2 dense matched-filter / relative-location reference; use only the
reported high-quality GrowClust subset as a metric-specific Q1 location/
uncertainty anchor.
- **Best use:** compare detection expansion, event separation, relative fault
geometry and uncertainty calibration under a long-duration, changing-network
condition.
- **Not a universal truth catalog:** template inheritance from Lanza, variable
network coverage, and matched-filter morphology bias make completeness and
absolute-location comparisons conditional.
- **Catalog–paper alignment:** aligned at the headline 33,328-event count and
corrected release lineage; the 27,431 relocated subset and the one-row
1,755-versus-1,756 focal-mechanism discrepancy remain explicit unresolved
release metadata issues.

## Local outputs and next actions

- Paper reading: `../../references/CHAMBERLAIN2021_JB022304/paper/CHAMBERLAIN2021_JB022304__paper_reading.md`
- Case synthesis: `../../analysis/KAIKOURA2016_analysis.md`
- Raw/source CSVs are preserved in this directory; future plots should be
written under `raw/` or a dedicated `figures/` subdirectory without modifying
the two source files.
- If exact relocation membership or focal-mechanism provenance is required,
archive and parse the corrected QuakeML/software bundle from Zenodo 6763130.
