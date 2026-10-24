# ccdt interface (version 1)

```bash
python interface/run.py --events E.csv --arrivals A.csv --waveforms DIR --output-dir OUT \
    [--pairs P.csv] [--config C.json] [--workers N] [--overwrite] [--quiet]
```

## Inputs (CSV with header)

| File | Columns | Notes |
|---|---|---|
| events | `event_id, origin_time_utc, latitude, longitude, depth_km` | unique ids; ISO 8601 UTC (`Z`, `+00:00`, space separator and nanoseconds accepted); depth on any one datum (only used for neighbour search) |
| arrivals | `event_id, station_id, phase, time_utc[, source]` | `station_id` = `NET.STA`; phase `P` or `S`; pick or prediction — it positions the window only; first row wins per event/station/phase |
| pairs (optional) | `event_id_1, event_id_2` | default: `pairs.max_neighbors` nearest within `pairs.max_distance_km` |
| waveforms | directory | searched recursively for `*.mseed/.miniseed/.ms/.msd`; channels chosen per station by `channels.families` order |

## Outputs (`OUT/`)

| File | Content |
|---|---|
| `dt.cc` | `# id1 id2 0.0` per pair, then `STA DT WEIGHT PHASE`; DT = tt(id1) − tt(id2) in s; weight = CC (or CC² with `"weight": "cc2"`); accepted only |
| `event_ids.csv` | `cusp_id` (integer written to dt.cc, 1-based input order) ↔ `event_id` |
| `measurements.csv` | `event_id_1, event_id_2, station_id, phase, dt_s, cc, lag_s, n_components, snr_1, snr_2, status` |
| `run_result.json` | status, counts by measurement and window status, timing |
| `config.json` | the merged configuration |

Measurement status: `accepted`, `low_cc`, `low_snr`, `edge_peak`,
`anticorrelated`, `ambiguous`, `self_overlap`, `no_common_data`.
Window status (run_result): `ok`, `no_data`, `gap_or_edge`, `zero_signal`.

## Configuration (JSON, deep-merged over the defaults)

| Key | Default | Meaning |
|---|---|---|
| `channels.families` | HH, EH, BH, HN, EN | preference order per station |
| `channels.P` / `channels.S` | Z / N, E, 1, 2 | components per phase |
| `filter` | 2–15 Hz, 4 corners | zero-phase Butterworth on the long trace |
| `window.P` / `window.S` | 0.2 + 0.6 s / 0.3 + 1.0 s | before/after the arrival |
| `max_lag_s` | P 0.3, S 0.4 | half search range; must exceed the arrival error |
| `pad_s`, `edge_guard_s`, `taper_s` | 30, 3, 2 s | neighbour data read, distance from trace ends/gaps, taper |
| `snr` | noise 2 s, min 3 | RMS ratio, both events |
| `accept` | min_cc 0.7, ambiguity_ratio 0.9, guard 0.1 s | see README |
| `pairs` | 3 km, 30 neighbours | default pair selection |
| `phases` | P, S | |
| `weight` | cc | or cc2 |
| `write_rejected` | true | rejected rows in measurements.csv |
