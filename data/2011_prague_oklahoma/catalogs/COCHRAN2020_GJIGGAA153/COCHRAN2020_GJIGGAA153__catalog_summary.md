# COCHRAN2020_GJIGGAA153 — catalog summary and reproducible audit

## Provenance

- Source: Cochran et al. (2020), “Activation of optimally and unfavourably
  oriented faults in a uniform local stress field during the 2011 Prague,
  Oklahoma, sequence,” *Geophysical Journal International*, 222, 153–168.
- DOI / landing page: [10.1093/gji/ggaa153](https://doi.org/10.1093/gji/ggaa153)
- Catalog relationship: article-associated extended template-matched catalog;
  900 starting/template events plus 7,911 relocated detections.
- Catalog file: `COCHRAN2020_GJIGGAA153__catalog_primary.txt`
- Native format: whitespace-delimited text without a header row; one event per
  row; source file is preserved unchanged.
- Local row count: **8,811** records.
- SHA-256: `1b4fe6aee4bc6b5523dafeb36d1fc4ae9b8ceaa93fe24a93c9c37aa7c2076ca7`

## Reconstructed schema and parsing rules

The local file has eleven fields in this order:

```text
year month day hour minute second event_id latitude longitude depth_km magnitude
```

- `second` is parsed as a decimal number with three fractional digits; do not
  truncate it to integer seconds.
- The article describes event times in UTC. The local file has no explicit
  timezone column, so UTC is the working convention and should be retained in
  any normalized derivative.
- Latitude/longitude are decimal degrees; depth is treated as km below the
  reference surface because that is the convention used by the article's
  figures and text. The source file itself has no units header.
- Event IDs are unique within this file but have no documented cross-catalog
  namespace. They must not be used as join keys against McMahon, USGS, or other
  products without an explicit origin-time/space crosswalk.
- The magnitude column is numeric, but the article and headerless release do
  not identify its magnitude type or calibration. It is deliberately recorded
  as `magnitude_type = unresolved`, not assumed to be ML.

## Local audit

| Field | Value |
|---|---|
| Rows | 8,811 |
| Unique event IDs | 8,811 |
| Exact duplicate rows | 0 |
| Time range | 2011-11-06 01:50:50.880 to 2012-01-31 23:50:19.578 UTC |
| Latitude | 35.45013–35.56470°N |
| Longitude | −96.87954–−96.72730°E |
| Depth | 0.261–13.280 km (working unit: km) |
| Magnitude | **−1.36–4.99**; type/units unresolved |
| Missing/non-numeric fields | None observed in the current schema audit; rerun the validation script after any normalization |

The first local row predates the paper's 2011-11-07 template-search start
because the release includes starting/template events. This is not evidence that
the continuous search began on 2011-11-06.

## Construction and quality interpretation

The paper's workflow is:

```text
900 Sumy manually picked/relocated events
  → 2.0-s P/S templates (0.5 s pre-arrival; P shortened to S–P when needed)
  → day-long continuous matching on 2011-11-07–2012-01-31
  → ≥9 channels above 9×MAD; 2-s duplicate suppression
  → waveform differential times (CC ≥0.7)
  → GrowClust relative relocation; template-template weights ×100
  → 100 bootstrap uncertainty iterations
```

The article reports median relative uncertainties of 112 m horizontal and 133 m
vertical for relocated detections. These are not absolute errors and should not
be assigned to the 900 templates automatically. The release is a mixed
population of starting/template events and continuous-waveform detections, not
a homogeneous analyst-picked catalog.

Downstream FaultID parameters (DBSCAN distances 1,000/500/100 m; RANSAC plane
distances 300/150/100 m; 1,000 trials; stage-specific minimum inlier counts
500/100/20) describe fault interpretation, not event inclusion in this file.

## Benchmark role and limitations

1. **Primary role:** Q2 enhanced-detection and relative-location/release-QC
   reference.
2. **Metric-specific auxiliary role:** Q1 structural anchor for differential
   geometry and fault-plane comparisons, only when the score explicitly
   evaluates relative structure rather than independent event existence.
3. **Not suitable for:** a universal completeness truth set, independent
   absolute depth/location truth, or magnitude-completeness claims.
4. **Lineage warning:** an agent using the same LC waveforms, starting templates,
   or inherited velocity model is not independent of this reference. Shared
   waveform/template lineage must be reported with benchmark scores.

## Frozen benchmark selection audit

The current Prague v1 interval is the half-open UTC window
`2011-11-11T00:00:00Z ≤ origin_time < 2011-11-19T00:00:00Z`.
The event counts below are intentionally separated:

| Selection rule | Count | Exact audit ranges / interpretation |
|---|---:|---|
| Time-only window | **2,078** | Lat 35.45231–35.55757°N; lon −96.87233–−96.73343°E; depth 1.016–9.618 km; magnitude −0.96–3.22 |
| Time + rounded displayed envelope (`35.4523–35.5576`, `−96.8723–−96.7334`, `1.02–9.62 km`) | **2,076** | Two time-window rows are excluded solely by rounded bounds: ID 12367 at lon −96.87233 and ID 14642 at depth 1.016 km |

The canonical v1 selector is the **time-only** half-open interval, yielding
2,078 rows. The exact spatial/depth ranges are descriptive extrema of those
rows; the rounded 2,076 result is retained only as a sensitivity audit and must
not silently replace the canonical count.

## Required next checks

- Verify the official supplementary/catalog release URL and recover the
  magnitude type/calibration from release metadata or SI; retain
  `magnitude_type = unresolved` until verified.
- Extract the complete station/channel/sample-rate table from the cited Sumy
  supplementary material and build a station-day availability mask.
- Generate time–magnitude, map, depth-section, and daily-count plots under the
  catalog's plot/raw directory without modifying the source text.
- Cross-match the 2,078 time-window rows (or 2,076 explicitly masked rows)
  against McMahon and the operational baseline only after applying identical
  time/space/depth rules.
