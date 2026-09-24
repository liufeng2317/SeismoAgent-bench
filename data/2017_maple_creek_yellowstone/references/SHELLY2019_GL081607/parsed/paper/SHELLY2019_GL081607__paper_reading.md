# Shelly & Hardebeck (2019) — paper reading and catalog-construction audit

## Identity and evidence status

| Field | Extracted information | Evidence / status |
|---|---|---|
| Authors | David R. Shelly and Jeanne L. Hardebeck | PDF title block; MinerU text |
| Title | Illuminating Faulting Complexity of the 2017 Yellowstone Maple Creek Earthquake Swarm | PDF title block |
| Journal / citation | *Geophysical Research Letters*, 46, 2544–2552 (2019) | PDF citation block |
| DOI | [10.1029/2018GL081607](https://doi.org/10.1029/2018GL081607) | Article and source README |
| Article type | Research letter that constructs an enhanced detection, magnitude, relative-location, and focal-mechanism catalog | Abstract and Methods |
| Local paper parse | `parsed/SHELLY2019_GL081607__paper__mineru.md` | MinerU output; source PDF is preserved beside it |
| Associated release | USGS [10.5066/P13JCJ2I](https://doi.org/10.5066/P13JCJ2I) | Local XML metadata and article data statement |

This is a genuine catalog-construction paper. The article's event catalog is
not the same object as the local USGS CSV: the article describes relocated event
populations, whereas the downloaded CSV contains correlation-derived phase
arrivals only. The distinction is material for benchmark scoring.

## Scientific scope

- **Sequence:** the 2017 Maple Creek earthquake swarm in the Yellowstone region,
  with a largest event of \(M_w 4.4\) on 2017-06-16.
- **Study activity:** the paper discusses the June–September 2017 swarm and
  plots detections through 14 September. Templates were selected from
  2017-06-11 through 2017-09-06; continuous data were scanned from 11 June
  through 14 September (Methods, MinerU content-list pages 2–3).
- **Published populations:** nearly 2,500 routine events; 15,912 well-located
  events; magnitudes estimated for 30,411 events. These are article-reported
  populations, not counts recoverable from the local phase-only CSV.
- **Spatial context:** a swarm zone recorded by 27 seismic stations within
  approximately 70 km. The paper does not publish a machine-readable event
  polygon in the local release.
- **Scientific role:** dense swarm detection, relative hypocenter geometry,
  temporal migration, and correlation-based focal-mechanism clustering.

## Observation and network conditions

| Item | Article-reported value | Local audit / limitation |
|---|---|---|
| Waveform source | Continuous EarthScope/IRIS data plus the University of Utah routine catalog and phase picks | Exact station-day availability is not in the local CSV |
| Published network | 27 stations within 70 km; multiple three-component broadband upgrades after 2013 | The 27-station value is the paper's processing setup |
| Sampling / filtering | 100 Hz; 2–15 Hz bandpass for template matching | Keep these parameters when preparing waveforms |
| Template population | 2,289 routinely cataloged events, 11 June–6 September 2017 | Local phase CSV contains 1,147 unique `template_id` values; this is a release-level subset/identifier count and must not replace the article value |
| Local phase release | Networks WY, PB, US, TA, IW; 29 network–station pairs over the full file, 27 in the frozen 8-day time span | Phase release has no latitude, longitude, depth, or event-origin table |

The paper notes a polarity reversal at station YMC that was corrected for focal
mechanism work. Station availability and template lineage should be retained as
covariates; a fixed “27 stations continuously available” assumption is not
justified for every day.

## Catalog-construction workflow

~~~text
UUSS routine catalog and phase picks
    → 2,289 waveform templates (100 Hz; 2–15 Hz)
    → continuous matched-filter scanning (0.01 s increments)
    → correlation quality weighting and differential-time measurement
    → 34.1 million correlation-derived + 1.3 million catalog-derived differential times
    → hypoDD double-difference relocation
    → retain ≥50 P and ≥50 S correlation observations: 15,912 well-located events
    → relative-amplitude magnitude estimates; retain ≥15 P and ≥30 S: 30,411-event magnitude catalog
    → polarity clustering / composite focal mechanisms (100 clusters)
~~~

Key method details:

- Detection and differential-time weights use the correlation coefficient, daily
  median absolute deviation, and nearby-peak separation (Methods).
- Magnitudes for new detections are inferred from template amplitudes and UUSS
  coda magnitudes \(M_c\); the small-event scale is intentionally \(M_c\)-like,
  not a uniform \(M_w\) scale.
- Correlation-derived signed polarities are clustered hierarchically and passed
  to a weighted HASH variant for composite mechanisms. This product is an
  interpretation layer, not an independent event catalog.

## Article-reported quality and limitations

| Product | Count / criterion | Benchmark meaning |
|---|---:|---|
| Routine catalog templates | 2,289 | Seed population, not the enhanced catalog |
| Well-located catalog | 15,912 | Relative-location target; at least 50 P and 50 S correlation observations |
| Magnitude superset | 30,411 | More permissive location/magnitude population; at least 15 P and 30 S observations |
| Differential times | 34.1 million correlation + 1.3 million routine-catalog | Strongly correlation/template dependent |
| Focal-mechanism clusters | 100 specified clusters; 95% of located events in top eight | Do not treat cluster labels as independent truth |

The article is high quality for relative geometry (Q1) and template-enhanced
detection (Q2), but lower for absolute location (Q3) and completeness outside
template-supported waveform families. It is not an independent reference for an
agent that uses the same matched-filter/differential-time lineage.

## Local release interpretation

The USGS release is explicitly titled a dataset of correlation-derived seismic
phase arrival times for developing phase-picking neural networks. Its Yellowstone
CSV schema is:

`template_id, match_id, network, station, phase, arrival, weight, mag, ccmax, ccdiff, chanloc`.

`arrival` is epoch seconds calculated from a template phase pick plus a
correlation-derived differential time. `match_id` is an assigned detected-event
identifier, but rows are phase/station observations and do not constitute a
complete origin catalog. The XML metadata says the Yellowstone component covers
11 June–6 September 2017; the local CSV has arrivals through 17 September,
which is recorded as a release discrepancy in the catalog summary.

## Benchmark decision

- **Primary article target:** Shelly & Hardebeck enhanced event catalog
  (15,912 well-located and 30,411 magnitude populations; article-reported).
- **Local machine-readable product:** phase-arrival auxiliary only; do not call
  it a downloaded Shelly event catalog.
- **Independent secondary:** Pang et al. (2019) is methodologically distinct
  and genuinely constructs a 3,345-event GrowClust catalog, but its event table
  is not present locally and remains an acquisition gap.
- **Baseline:** the local USGS/UUSS ComCat snapshot is Q3 operational context;
  its five-event frozen-window result is not a completeness estimate.
- **Valid metrics:** phase-pick timing, matched-event recovery, relative
  geometry, and method-specific catalog overlap after explicit lineage labels.
- **Invalid shortcut:** comparing all phase-row counts to event-row counts or
  treating correlation arrivals as an independent event truth set.

## Local paths

- Paper PDF: `data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/paper/SHELLY2019_GL081607__paper.pdf`
- Parsed paper: `data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/parsed/SHELLY2019_GL081607__paper__mineru.md`
- Supplement: `data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/supplement/Shelly2019_MapleCreek_SI.pdf`
- Phase release and XML metadata: `data/2017_maple_creek_yellowstone/catalogs/SHELLY2019_GL081607/raw/`
- Catalog-level audit: `../../../catalogs/SHELLY2019_GL081607/README.md` (created alongside this note)
