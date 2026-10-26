# REAL association interface (version 1)

```bash
python seismotools/real/interface/run.py \
  --picks picks.csv --stations stations.csv --velocity-model model.txt \
  --output-dir OUT [--config config.json] [--workers 8] [--overwrite] [--quiet]
```

Requires the build (`python seismotools/support/build_native.py --tool real`).

## Inputs

| File | Columns | Notes |
|---|---|---|
| `--picks` | `pick_id, station_id, phase, time_utc[, probability]` | `phase` P or S; probability is written as REAL's pick weight (1 if absent) |
| `--stations` | `station_id, latitude, longitude, elevation_m` | ids `NET.STA` (REAL files are `NET.STA.P.txt`); ≤ 500 stations |
| `--velocity-model` | text `depth_km vp_km_s vs_km_s` | rows are layer tops; see `velocity_layering` |

## Outputs

| File | Content |
|---|---|
| `events.csv` | `event_index, time_utc, latitude, longitude, depth_km, num_picks, num_p_picks, num_s_picks, std_s, gap_deg` (REAL's refined grid location; a starting point for a locator) |
| `assignments.csv` | one row per input pick: `pick_index, pick_id, event_index, assignment_probability (empty), assignment_status, residual_s` (GaMMA interface columns + residual) |
| `ttdb.txt` | travel-time table in REAL's format |
| `chunks/<start>/` | REAL inputs, `real.log`, `catalog_sel.txt`, `phase_sel.txt` per time chunk |
| `config.json`, `run_result.json` | merged configuration; status, counts, table geometry |

## How the adapter runs REAL

- **Travel-time table:** first arrivals from a fast-marching solution (pyrocko
  eikonal, `table.fmm_spacing_km`) of the 1-D model — head waves included —
  sampled at REAL's `-G` grid (depth outer, distance inner, both from 0) with
  `dt/dΔ` (s/deg) and `dt/dz` (s/km) by central differences. REAL predicts
  `t = ptime + ΔGCarc·prayp + Δdep·phslow + elev/v_surface`.
- **Elevations:** station elevation relative to `reference_elevation_km`,
  corrected with the first model row's velocities (`-V…/1`).
- **Time chunks:** REAL runs on `chunk_hours` with `buffer_s` of picks on both
  sides; an event is kept only by the chunk containing its origin, so events
  across chunk boundaries (e.g. midnight) appear once.

## Configuration (deep-merged; keys map to REAL flags)

| Key | Default | REAL | Meaning |
|---|---|---|---|
| `reference_elevation_km` | 0 | | depth datum |
| `velocity_layering` | `step` | | rows constant (`step`) or linear nodes |
| `region` | none | | optional output filter `{latitude, longitude, depth_km}` |
| `search.rx_deg`, `rh_km`, `dx_deg`, `dh_km` | 0.1, 20, 0.04, 2 | `-R` | half-width (deg) and depth range around the initiating station; grid steps |
| `search.event_interval_s` | 5 | `-R` tint | minimum event separation |
| `search.max_gap_deg`, `max_distance_deg` | 360, 1.4 | `-R` gap, GCarc0 | largest azimuthal gap; largest station distance |
| `thresholds.np0`, `ns0`, `nps0`, `npsboth0` | 3, 2, 12, 3 | `-S` | min P, S, P+S picks; stations with both |
| `thresholds.std0` | 0.5 | `-S` | max travel-time residual std (s) |
| `thresholds.dtps` | 0.2 | `-S` | min S−P interval (s) |
| `thresholds.nrt`, `drt` | 1.0, 0.25 | `-S` | window length factor; initiating-pick removal |
| `thresholds.nxd` | 0.2 | `-S` | discard events whose nearest station is beyond `nxd × max_distance_deg` |
| `thresholds.rsel`, `ires` | 4, 0 | `-S` | residual outlier factor; resolution output |
| `table.max_distance_deg`, `max_depth_km` | 1.5, 30 | `-G` | must cover `search.max_distance_deg` + 0.05 and `search.rh_km` |
| `table.dist_step_deg`, `depth_step_km`, `fmm_spacing_km` | 0.01, 1, 0.1 | `-G` | table steps; eikonal grid spacing |
| `chunk_hours`, `buffer_s` | 24, 120 | | run length and pick buffer |

Defaults are the upstream `demo_real` values; tune them per case (the
upstream `runREAL.pl` lists the trade-offs). Note `nxd`: with a small
`max_distance_deg` the nearest-station cut becomes strict (validation uses
0.5 for a 40-km synthetic network with `max_distance_deg` 0.5).
