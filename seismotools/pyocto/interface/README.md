# PyOcto association interface (version 1)

```bash
python seismotools/pyocto/interface/run.py \
  --picks picks.csv --stations stations.csv --velocity-model model.txt \
  --config config.json --output-dir OUT [--workers 8] [--overwrite] [--quiet]
```

Requires the build (`python seismotools/support/build_native.py --tool pyocto`).

## Inputs

| File | Columns | Notes |
|---|---|---|
| `--picks` | `pick_id, station_id, phase, time_utc[, probability]` | `phase` P or S; ISO-8601 UTC; probability is not used by PyOcto |
| `--stations` | `station_id, latitude, longitude, elevation_m` | sensor elevation; every pick's station must be listed |
| `--velocity-model` | text `depth_km vp_km_s vs_km_s` | rows are layer tops; see `velocity_layering` |
| `--config` | JSON | must contain `region` |

## Outputs

| File | Content |
|---|---|
| `events.csv` | `event_index, time_utc, latitude, longitude, depth_km, num_picks, num_p_picks, num_s_picks, x_km, y_km` (depth below `reference_elevation_km`; positions are PyOcto's node locations, a starting point for a locator) |
| `assignments.csv` | one row per input pick: `pick_index, pick_id, event_index, assignment_probability (empty), assignment_status (assigned/unassigned), residual_s` — same columns as the GaMMA interface plus `residual_s` |
| `travel_time_table.bin` | the 1-D travel-time table (PyOcto format: `nx, nz, delta` then P and S grids) |
| `config.json`, `run_result.json` | merged configuration; `status` success / failed, counts, table geometry |

## Configuration

| Key | Default | Meaning |
|---|---|---|
| `region` | required | `{latitude: [a, b], longitude: [a, b], depth_km: [top, bottom]}`; top ≥ 0 (no search above the datum) |
| `reference_elevation_km` | 0 | depth datum; station z = datum − elevation, handled by PyOcto's surface-velocity elevation correction (first model row) |
| `velocity_layering` | `step` | `step`: rows are constant layers (a node is inserted just above each layer top, since PyOcto interpolates linearly between rows); `linear`: rows are nodes |
| `travel_time_table.delta_km` | 0.25 | table spacing |
| `travel_time_table.max_distance_km`, `max_depth_km` | region-station extent + 10, region bottom + 5 | table extent |
| `travel_time_table.tolerance_s` | 2.0 | PyOcto velocity-model tolerance |
| `travel_time_table.association_cutoff_distance_km`, `location_cutoff_distance_km` | none | only use stations up to this distance |
| `time_before_s` | 300 | overlap of consecutive time slices; must exceed the largest travel time in the region |
| `associator` | upstream defaults | any `OctoAssociator` keyword, e.g. `n_picks` 10, `n_p_picks` 3, `n_s_picks` 3, `n_p_and_s_picks` 3, `pick_match_tolerance` 1.5, `min_interevent_time` 3, `time_slicing` 1200; `n_threads` defaults to `--workers` |

## Notes from validation

- The travel-time table is a first-order fast-marching solution: never faster
  than the exact time, up to ~0.065 s (P) slower along grid diagonals at
  0.25 km spacing over 65 km. A smaller `delta_km` reduces it.
- With the default `pick_match_tolerance` (1.5 s), random false picks near
  events get absorbed (6.7 % of synthetic false picks); 0.5 s lowered that to
  4.4 % with no loss of true picks or events.
