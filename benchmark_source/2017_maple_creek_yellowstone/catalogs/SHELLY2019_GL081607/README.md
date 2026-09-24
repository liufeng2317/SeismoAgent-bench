# Shelly & Hardebeck (2019) Maple Creek phase-arrival release

- source_ref: SHELLY2019_GL081607
- Article: DOI https://doi.org/10.1029/2018GL081607.
- USGS release: DOI https://doi.org/10.5066/P13JCJ2I, ScienceBase item 667b1415d34e6151c9d6bcfd.
- Core local file: raw/Yellowstone_2017_correlation_phase_arrivals.csv.
- Companion XML: raw/Correlation-derived_seismic_phase_arrival_times_v2.xml.
- Local audit: README.md.
- CSV audit: 6,260,580 data rows; SHA-256 a1828099eb2a51339e01ffca191d6e4d98df27ad889c18837aa41278dd128d6c.
- Product meaning: correlation-derived P/S phase arrivals with template and match
  IDs; this is an auxiliary phase product, not an event-origin catalog.
- The article reports 15,912 well-located and 30,411 magnitude events, but those
  article-level event tables are not present in this directory.

## Local catalog audit

> Earlier window/mask statistics are exploratory. Current freeze status is defined by the case `analysis/processing.yaml`, which is `not_frozen`; retained historical “frozen” wording does not override it.

### Provenance and product identity

- Source reference: Shelly & Hardebeck (2019), DOI https://doi.org/10.1029/2018GL081607.
- Data release: USGS 10.5066/P13JCJ2I, ScienceBase item 667b1415d34e6151c9d6bcfd.
- Local product: raw/Yellowstone_2017_correlation_phase_arrivals.csv plus raw/Correlation-derived_seismic_phase_arrival_times_v2.xml.
- Product class: correlation-derived phase-arrival release; NOT the article's 15,912-event relocated catalog and NOT Pang et al.'s 3,345-event GrowClust catalog.
- SHA-256: CSV a1828099eb2a51339e01ffca191d6e4d98df27ad889c18837aa41278dd128d6c; XML 547cbc7e43b11d47b2c10098850904151b4b63de5b95dc6c2d1edb147f1a96e5.
- Local CSV scale: approximately 433 MiB, 6,260,580 data rows; raw file remains local-only under the repository ignore rule.

### Native schema

Header:

    template_id,match_id,network,station,phase,arrival,weight,mag,ccmax,ccdiff,chanloc

| Field | Meaning / audit |
|---|---|
| template_id | Assigned waveform-template ID |
| match_id | Assigned detected-event ID; repeated over many station/phase rows |
| network, station | Recording network and station code |
| phase | P or S |
| arrival | Epoch seconds UTC; template pick plus correlation-derived differential time |
| weight | Original correlation weight; XML gives (0.1 + 3*ccdiff)*ccmax^2 |
| mag | Magnitude associated with detected event; repeated on phase rows and contains invalid/extreme local values |
| ccmax | Signed peak absolute correlation coefficient |
| ccdiff | Difference between largest and second-largest absolute peaks |
| chanloc | Channel and location code joined by a period |

The file has no origin time, latitude, longitude, depth, location uncertainty, or
event-level quality flag. It cannot provide the spatial/depth event summary
needed for a standalone reference catalog without an event table.

### Full-file audit

| Field | Local result |
|---|---|
| Data rows / header | 6,260,580 / 1 |
| Malformed CSV rows | 0 under the 11-column parser |
| Unique match_id values | 115,448 |
| Unique template_id values | 1,147 |
| Phase rows | P 3,933,935; S 2,326,645 |
| Networks | WY 4,864,384; PB 1,394,725; US 872; TA 371; IW 228 |
| Unique network-station pairs | 29 |
| Arrival span | 2017-06-11T06:09:19.444800Z to 2017-09-17T16:13:09.091100Z |
| Finite mag values | 6,260,567 |
| Non-finite mag values | 9 rows encoded as -inf |
| Finite mag range | -6.99 to 5.17; four additional finite values are below -10 and should be flagged |
| chanloc cardinality | 15 |

The XML metadata declares a Yellowstone magnitude domain of 0.35 to 3.65,
which does not match local rows (5.17, negative extremes, and nine -inf
values). Preserve raw values and create a QC flag before magnitude metrics.

The XML describes Yellowstone coverage as 11 June to 6 September 2017, while
local arrivals extend to 17 September. The article itself reports scanning
through 14 September. Keep the discrepancy explicit; do not silently truncate.

### Frozen benchmark-window audit

Case-level spatial/depth mask:

    44.45 N <= latitude <= 44.75 N
    -110.55 E <= longitude <= -110.15 E
    0 km <= depth <= 15 km

This mask cannot be applied to the phase-only file because coordinates and depth
are absent. Only a time filter is reproducible:

| Half-open UTC window | Phase rows | Unique match_id | Unique template_id | Station pairs |
|---|---:|---:|---:|---:|
| 2017-06-11 <= t < 2017-06-18 (7 days) | 1,536,742 | 22,858 | not retained in prior audit | 27 |
| 2017-06-11 <= t < 2017-06-19 (8 days, frozen v1) | 1,591,090 | 23,660 | 1,119 | 27 |

These are phase observations and phase-associated IDs, not validated event counts.
Article-reported 15,912 and 30,411 populations remain separate.

### Quality tier and use

- Q4 auxiliary phase product by itself: phase timing, template/match lineage,
  and waveform detector diagnostics.
- Article-level Shelly catalog: Q1 relative geometry and Q2
  template-enhanced detection, but its event table is not staged locally.
- Independence: low against a matched-filter or correlation differential-time
  agent because the release shares the study lineage.
- Do not treat each CSV row as an event, use match_id as the article catalog
  count, or apply a spatial/depth mask without joining an event-origin product.

### Reproducibility and pending work

1. Keep the checksums above in any external data manifest.
2. Parse full USGS metadata if station-day availability or template/event
   crosswalks are needed.
3. Acquire or reconstruct the article event-level relocated table only with
   explicit provenance; never infer locations from phase arrivals.
4. Generate phase-count, correlation-quality, station-availability, and
   template-lineage plots under raw/ or a derived catalog directory.

## Generated analysis

[Product statistics and processing outputs](analysis/catalog_analysis.md) are generated by the catalog-local script; the provenance and scientific audit above are maintained here.
