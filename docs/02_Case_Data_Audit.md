# Phase I Six-Case Data Audit

This document audits cross-case files, catalogs, and data-preparation status. Paper-level method extraction is recorded in
`references/<SOURCE_ID>/paper/*__paper_reading.md`; catalog-level field audits are recorded in
`catalogs/<CATALOG_ID>/*__catalog_summary.md`; and frozen-window interpretation is recorded in each case's
`analysis/*_analysis.md`.

## Prague, Oklahoma — `2011_prague_oklahoma`

`COCHRAN2020_GJIGGAA153` is complete: the local catalog contains 8,811 rows and 8,811 unique IDs. In the frozen
window (`2011-11-11T00:00–2011-11-19T00:00 UTC`), the time-only selection contains 2,078 rows; applying the displayed
rounded spatial/depth bounds gives 2,076 rows. The full catalog magnitude range is −1.36–4.99, but the magnitude type
has not been confirmed from the release or SI and must not be labeled ML. The McMahon public release (5,446 rows) and
Isken Table S3 (13 manually relocated events) are retained as independent secondary/structural references and must
not be merged with Cochran. The 31-station mixed temporary/regional network and actual station-day availability still
require confirmation during waveform preparation; 25.71264 GB is the continuous-data upper bound for
31 × 3C × 100 Hz × int32 × 8 days, not a measured downloaded volume.

## Kaikōura, New Zealand — `2016_kaikoura_new_zealand`

The Lanza, Tan, and Chamberlain papers, supplements/catalogs, and local audits are archived. In the frozen window
(`2016-12-01–12-09 UTC`), the common-mask counts are Lanza 122, Tan S10 9,720, Tan S11 6,955 (6,973 time-only),
and Chamberlain 2,214. Tan's 1,165 phase files are also stored separately. The final 41,392-event cluster-filtered
set described by Tan is not released as a separate CSV, and the Wiley Movie SI-S01 remains an optional gap;
the Chamberlain CSV does not explicitly encode relocation membership. The 46 GeoNet/STREWN stations and 33.5 GB
continuous-data upper bound are recorded as design conditions, while actual station-day/channel availability is not
frozen yet.

## Maple Creek, Yellowstone — `2017_maple_creek_yellowstone`

The Shelly & Hardebeck paper, SI, USGS correlation-phase release, and official UUSS baseline are archived. The
8-day frozen window (`2017-06-11–06-19 UTC`) contains 23,660 phase-associated IDs; the historical 7-day convention
contains 22,858. The CSV/XML has no origin time, coordinates, or event-level uncertainty, so it must not be treated
as the article's 15,912/30,411-event table. The frozen phase release covers 27 network-station pairs, and 19.6 GB
is only the continuous-data design upper bound. The genuine Pang 3,345-event HYPOINVERSE + GrowClust paper has been
parsed, but its machine-readable event table has not been located; the Shelly release must not be substituted for it.

## Kīlauea, Hawaiʻi — `2018_kilauea_hawaii`

The Shelly S1/S2, Wei S1, Matoza 2021, Matoza 2014, and Lengliné products are archived separately by source. In
the frozen summit window (`2018-05-01–05-09 UTC`; 19.30–19.50°N, −155.40–−155.15°, 0–20 km), Shelly S1/S2 contain
1,883/1,877 common-mask rows (1,902/1,896 time-only), and Wei contains 2,369 rows, including 1,930 with numeric
magnitudes. The Matoza 2021 field definitions must be preserved: the `latR/lonR/depR` relocated-coordinate mask
contains 1,130 rows, of which 984 have `nbranch>1`; the `latC/lonC/depC` starting-coordinate mask contains 1,190
rows, of which 1,044 have `nbranch>1`. Lengliné has 6,049 temporally overlapping rows but only relative x/y;
Matoza 2014 is a historical LP catalog with zero rows in the frozen window. QuakeFlow has only the paper/evaluation
materials and code, with no verifiable Hawaiʻi event-catalog release. The HVO temporary-array station-day/channel
inventory and actual waveform volume remain to be frozen.

## Ridgecrest, California — `2019_ridgecrest_california`

Shelly Data S1 (34,091 rows), Liu Table S1 (15,445), Ross SCEDC QTM (111,918 rows, including 46,512 with
`nbranch>1`), and AWR v2 (222,864 hypocenters and 4,890 moment tensors) have all passed paper/catalog alignment
audits; the USGS/SCSN export is also preserved as the Q3 baseline. In the 72-hour frozen window
(`2019-07-04–07-07 UTC`; 35.45–36.05°N, −117.90–−117.20°, 0–20 km), common-mask counts are Shelly 7,716,
Liu 6,242, Ross 12,768 (6,463 relocated), AWR 5,737 hypocenters/254 moment tensors, and SCSN 6,566. The
products use different detection and station conditions, so they must not be ranked by event count. The Shelly
paper does not state a fixed station count; Liu reports 41 permanent plus 4 temporary stations, and AWR uses 66
broadband 3C stations. Ross Science DC1 is still missing, as are the station-day/channel manifest and the measured
waveform volume corresponding to the 28.3 GB continuous-data upper bound.

## Magna, Utah — `2020_magna_utah`

The Pang ISC event catalog (5,739 rows/unique IDs) and Baker ISC pick release (329,611 pick rows and 5,885 events)
have completed field audits. In the frozen 8-day window (`2020-03-18–03-26 UTC`), strict Pang parsing yields 4,163
time-only rows and 4,162 common-mask rows; the corresponding `Mc>-4` counts are 4,102 and 4,101. Baker yields
3,782/3,712 events and 164,276/161,567 picks for the time-only/common-mask selections. Pang's 39-station/226-channel
condition and Baker's 180-node condition must remain separate; the 62.5 GB Pang channel upper bound and Baker's
provisional nodal upper bound are not measured waveform volumes. The Pang S1 supplement and Baker article PDF are
still missing, so Baker remains partial.

## Overall conclusions

1. The canonical directory structure, paper-reading records, catalog summaries, and `analysis/` freeze records for
   all six cases are mutually aligned; the case analysis files are the source of truth for numerical details.
2. The references still missing a machine-readable primary catalog are Pang (Maple Creek) and QuakeFlow (Hawaiʻi);
   adjacent research catalogs must not be substituted.
3. The Magna Baker article PDF is still missing. Pang S1, Ross DC1, Tan Movie SI, and some station metadata are
   optional/reproduction-level gaps and must not be represented as downloaded.
4. All current waveform numbers are reproducible continuous-data upper bounds. Before waveform acquisition, generate
   station-day/channel availability, sample-rate, gap, and checksum manifests; this will not change the frozen time
   windows or reference roles.
