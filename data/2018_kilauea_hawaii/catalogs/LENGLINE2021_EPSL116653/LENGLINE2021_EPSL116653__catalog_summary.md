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
- The paper reports the same 6,327 detections from 280 HVO templates. The
  local file's coordinates are a relative dike-study product, not a complete
  hypocenter table.
- Temporal overlap with the case v1 interval (`2018-05-01T00:00:00Z <= t <
  2018-05-09T00:00:00Z`) is 6,049 rows, but no common summit spatial mask is
  applied because this product targets the Middle East/Lower East Rift Zone.

## Benchmark role

- **Q2/Q4 auxiliary:** use for dike migration chronology and event recovery in a
  narrow template/channel condition.
- Do not compare its row count directly with Shelly S1/S2 or Wei S1, and do not
  derive depth/magnitude metrics from this file. Preserve the native coordinate
  frame and convert only with an explicitly documented local projection.
