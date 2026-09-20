# LENGLINE2021_EPSL116653 — dike-propagation catalog summary

## Provenance and schema

- Source: Lengliné et al. (2021), DOI [10.1016/j.epsl.2020.116653](https://doi.org/10.1016/j.epsl.2020.116653).
- File: `raw/loc_events.txt`; 6,327 data rows plus one description line.
- SHA-256: `556f4d6f5ba8c6688f5c36c165c94b12c0c623e5d3f33183911aca2888ed18ca`.
- Native columns: `time_days_since_2018-04-29`, `x_m`, `y_m`.
- Reference point: latitude 19.3864°, longitude −155.1050°; the file does not
  define a universal depth, magnitude, or event identifier.

## Local audit

- Rows: 6,327; exact duplicate triplets: none detected.
- Relative-day range: 0.00456–5.99930 days, corresponding to
  2018-04-29 00:06:33.984–2018-05-04 23:58:59.520 UTC.
- Native x range: −358 to 24,140 m; native y range: −506.0241 to 10,000 m.
- Native coordinate frame: `x` and `y` are metres relative to 19.3864°N,
  −155.1050°E; they are not latitude/longitude and do not encode a universal
  depth. The full-file native ranges are `x = −358–24,140 m` and
  `y = −506.0241–10,000 m`.
- The paper reports the same 6,327 detections from 280 HVO templates. The
  local file's coordinates are a relative dike-study product, not a complete
  hypocenter table.
- Temporal overlap with the case v1 interval (`2018-05-01T00:00:00Z <= t <
  2018-05-09T00:00:00Z`) is 6,049 rows. The common summit spatial/depth mask
  is **not applicable**: native `x/y` cannot be compared to the case
  latitude/longitude/depth bounds, and the release has no depth or magnitude.

### Frozen-window fields

| Field | Value |
|---|---|
| UTC rule | `2018-05-01T00:00:00Z <= t < 2018-05-09T00:00:00Z` |
| Time-only rows | 6,049 |
| Time range | 2018-05-01 00:01:16.896–2018-05-04 23:58:59.520 UTC (native relative-day conversion) |
| Native x range in time window | −358–24,140 m |
| Native y range in time window | −506.0241–10,000 m |
| Latitude / longitude / depth / magnitude | **N/A — not present in the native release** |
| Common summit-mask rows | **N/A — no defensible spatial/depth mask in native coordinates** |

Network conditions are documented in the paired paper-reading note:
[`LENGLINE2021_EPSL116653__paper_reading.md`](../../references/LENGLINE2021_EPSL116653/parsed/paper/LENGLINE2021_EPSL116653__paper_reading.md).
The detector used 280 shallow HVO templates and four selected channels (three
components at JOKA plus the vertical component of KUPD or KLUD), with HVO
waveforms accessed through IRIS; this is a focused network condition, not the
full HVO station set.

## Benchmark role

- **Q2/Q4 auxiliary:** use for dike migration chronology and event recovery in a
  narrow template/channel condition.
- Do not compare its row count directly with Shelly S1/S2 or Wei S1, and do not
  derive depth/magnitude metrics from this file. Preserve the native coordinate
  frame and convert only with an explicitly documented local projection.
