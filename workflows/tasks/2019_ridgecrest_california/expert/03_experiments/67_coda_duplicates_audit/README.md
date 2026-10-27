# Coda-duplicate waveform review (2026-10-28)

Blind review behind stage 67 (`01_pipeline/67_coda_duplicates.py`).

- Sample: 40 Match&Locate detections of the `12_dense_layered` catalog, M >= 1.5,
  10 per group, seed 11: within 15 s of an event >= 0.5 units larger with CC
  <= 0.30, 0.30-0.40, > 0.40, and a control without a larger neighbour, CC 0.30-0.40.
  Plots were named a01-a40 in random order; the group (`audit_key.csv`) was
  read only after all 40 labels (`audit_labels.csv`) were written.
- Plot: `python -m SeismoAgentBench.scoring.catalog_metrics.audit_plots --task-dir
  workflows/tasks/2019_ridgecrest_california --events audit_events.csv --context
  <12_dense_layered catalog as event_id,origin_time_utc,latitude,longitude,depth_km,magnitude>
  --out-dir <dir>` (six nearest stations, 2-15 Hz, predicted P/S of the event and
  of every other catalog event; no reference catalog is shown).
- Label: earthquake = own P/S arrivals at >= 2 near stations; not_earthquake =
  none at the predicted times (the energy belongs to a neighbouring event).

| group | earthquake | not | undecidable |
|---|---|---|---|
| near larger, CC <= 0.30 | 2 | 7 | 1 |
| near larger, CC 0.30-0.40 | 3 | 6 | 1 |
| near larger, CC > 0.40 | 7 | 2 | 1 |
| control, CC 0.30-0.40 | 7 | 1 | 2 |

Near a larger event, CC <= 0.35 removes 16 (12 not, 3 earthquakes, 1
undecidable) and keeps 14 (9 earthquakes, 3 not); this is the stage-67 rule.
An automatic onset test (RMS jump at the predicted P) was tried first and
rejected: 39 % of M2-3 control detections failed it in the dense coda.
