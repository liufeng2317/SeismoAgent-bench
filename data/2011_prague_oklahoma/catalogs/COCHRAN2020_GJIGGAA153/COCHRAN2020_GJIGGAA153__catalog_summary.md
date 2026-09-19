# COCHRAN2020_GJIGGAA153 — catalog summary

## Provenance

- Source: Cochran et al. (2020), DOI [10.1093/gji/ggaa153](https://doi.org/10.1093/gji/ggaa153)
- Catalog file: `COCHRAN2020_GJIGGAA153__catalog_primary.txt`
- Native format: whitespace-delimited text without a header row
- Local row count: 8,811 records (one event per row)
- Local checksum: generate with `sha256sum COCHRAN2020_GJIGGAA153__catalog_primary.txt` before benchmark release

## Reconstructed schema

The local file has eleven fields in this order:

```text
year month day hour minute second event_id latitude longitude depth_km magnitude
```

The file contains six time fields, one event identifier, latitude, longitude,
depth and magnitude. Seconds retain millisecond precision in the source rows
even though the first audit displayed integer seconds.

## Local audit

| Field | Value |
|---|---|
| Rows | 8,811 |
| Unique event IDs | 8,811 in the local audit |
| Time range | 2011-11-06 01:50:50 to 2012-01-31 23:50:19 UTC |
| Latitude | 35.45013–35.56470°N |
| Longitude | −96.87954–−96.72730°E |
| Depth | 0.261–13.280 km |
| Magnitude | 0.67–4.99 in the local file; confirm whether this field mixes ML and other source magnitudes before metric use |
| Missing values | None observed in the first schema audit; rerun validation before release |
| Duplicate rows | None observed by event ID; exact duplicate-row check should be retained in the audit script |

## Construction and quality interpretation

This is a template-matched catalog expanded from approximately 900 manually
reviewed/template events. The paper’s workflow uses channel-level correlation
screening, a nine-channel threshold, a 2 s duplicate suppression rule,
GrowClust relative relocation, and bootstrap uncertainties. The release is
therefore a mixed population of starting/template events and continuous-waveform
detections, not a homogeneous analyst-picked catalog.

The catalog is suitable as:

1. a Q2 enhanced detection and release-level QC reference;
2. a Q1 relative-location/structural reference when evaluated with differential
   geometry rather than absolute hypocenter error.

It is not suitable as a standalone completeness truth set or as an independent
reference for an agent that uses the same templates and waveform archive.

## Frozen benchmark mask

The Prague v1 benchmark uses the half-open UTC window
`2011-11-11T00:00:00Z ≤ origin_time < 2011-11-19T00:00:00Z`.
The case audit reports 2,078 events after the frozen spatial/time/depth mask:

- latitude: 35.4523–35.5576°N;
- longitude: −96.8723–−96.7334°E;
- depth: 1.02–9.62 km;
- magnitude: approximately ML −0.96 to 3.22.

The mask is a benchmark convention, not a replacement for the source catalog’s
full extent. Keep both counts in manifests and do not overwrite the full file.

## Required next checks

- Parse the fractional-second field without truncation.
- Confirm the magnitude type and units from the supplement or release metadata.
- Compute and record a SHA-256 checksum.
- Generate time–magnitude, map, depth-section, and daily-count plots under
  `raw/` (or the catalog’s designated plot directory), leaving the source text
  immutable.
- Cross-match the 2,078 frozen events against McMahon and the operational
  baseline only after applying identical masks.
