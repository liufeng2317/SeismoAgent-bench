# PANG2019_GL082376 - catalog readiness and audit

## Provenance

- Source article: Pang et al. (2019), DOI https://doi.org/10.1029/2019GL082376.
- Article-reported product: 3,345-event Maple Creek absolute catalog with 3,257
  GrowClust relative relocations.
- Local reference files: paper PDF and publisher SI PDF are present under
  references/PANG2019_GL082376/.
- Local machine-readable event catalog: **not present**.
- Catalog status: **missing**, not partial. No row count, schema, checksum,
  coordinate range, or frozen-window event count can be asserted locally.
- Do not substitute catalogs/SHELLY2019_GL081607/raw/Yellowstone_2017_correlation_phase_arrivals.csv:
  that file is a Shelly/USGS phase-arrival release and has no event coordinates.

## What is known from the article (not a local-file audit)

| Field | Article-reported value |
|---|---|
| Event count | 3,345 absolute locations |
| Relative relocations | 3,257 of 3,345 |
| Time range | 2017-06-12 through 2018-03-13 |
| Absolute location method | UUSS HYPOINVERSE with regional 1-D model |
| Relative method | BCSEIS differential times plus GrowClust |
| Differential times | About 4.4 million; 73 percent P and 27 percent S |
| Relocation network | 22 local + 2 regional stations |
| Median absolute errors | About 500 m horizontal, 730 m depth |
| Median relative errors | About 62 m horizontal, 86 m vertical from 100 bootstrap runs |
| Coda magnitude | Mc -1.7 to 4.4; Mc completeness about 0.5 |
| Depth population | More than 97 percent at 6-14 km beneath surface |

These values are evidence for article design only. They must be replaced or
confirmed by a local event-table audit after the catalog is acquired.

## Frozen benchmark mask to apply after acquisition

The case-level frozen v1 selection is:

    2017-06-11T00:00:00Z <= origin_time < 2017-06-19T00:00:00Z
    44.45 <= latitude <= 44.75
    -110.55 <= longitude <= -110.15
    0 <= depth_km <= 15

Expected output fields for a future normalized copy:

    event_id, origin_time_utc, latitude, longitude, depth_km,
    magnitude, magnitude_type, location_method, relocation_status,
    horizontal_error_km, vertical_error_km, source_row_hash

Until a source table with explicit column definitions is found, do not infer
relocation membership, uncertainty units, or magnitude scale from figures.

## Acquisition guidance

The article states that data are openly available from IRIS, but the waveform
archive is not an event-catalog download. A valid catalog acquisition must meet
all of these checks:

1. A stable author/publisher/Zenodo/USGS URL or DOI explicitly identifies the
   Pang 3,345-event table.
2. The file includes origin time and coordinates, and identifies whether each
   row is absolute, GrowClust-relocated, or both.
3. The event count and key ranges can be reconciled with the article.
4. The checksum and source URL are added here before marking the manifest ready.

Until then this source remains the independent-reference gap, not a reason to
label the Shelly phase CSV as Pang data.
