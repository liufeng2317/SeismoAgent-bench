# Standard NonLinLoc interface

`run.py` is the stable project entry point for a prepared 1-D NonLinLoc case. It
keeps inputs separate from the writable run directory and stops on the first
failed native stage.

```bash
python seismotools/nonlinloc/interface/run.py \
  --input-dir seismotools/nonlinloc/examples/smoke/inputs \
  --output-dir /tmp/nonlinloc-smoke \
  --bin-dir seismotools/nonlinloc/runtime/bin
```

Pass standard settings with `--config config.json`; command-line flags such as
`--date`, `--native-obs` and `--prepare-only` override the JSON values.

The input files and generated outputs are defined in
[input_schema.json](input_schema.json) and [output_schema.json](output_schema.json).
Optional standard settings are listed in [config_schema.json](config_schema.json).
The adapter is intentionally narrow: case workflows may use `Nonlinlocpy`
directly for advanced controls, but should preserve the same separation of
read-only inputs and writable run products.

The adapter refuses to use a non-empty output directory unless `--overwrite` is
provided. A successful run records the generated model, travel-time, observation
and location directories in `run_result.json`; a failed run records the error
when the output directory is available.

The adapter accepts `location_method` (`EDT_OT_WT` default, `EDT`,
`GAU_ANALYTIC`) and `grid_center` (`{latitude, longitude, depth_km}`; default:
a search grid spanning the station footprint). The smoke example pins its
`grid_center` in `examples/smoke/config.json`.

## Catalog locator: `locate.py` (interface version 3)

Locates many events at once: one `NLLoc` run per `event_id` (arrival group),
P and S travel-time grids computed once per station (`GRID2D`) in a local
azimuthal-equidistant frame, events run in a thread pool.

```bash
python seismotools/nonlinloc/interface/locate.py \
  --arrivals arrivals.csv --stations stations.csv --velocity-model model.txt \
  --output-dir OUT [--station-delays delays.csv] [--config config.json] \
  [--bin-dir DIR] [--workers 8] [--overwrite] [--quiet]
```

### Inputs

| File | Columns | Notes |
|---|---|---|
| `--arrivals` | `event_id, pick_id, station_id, phase, time_utc[, uncertainty_s]` | `phase` P or S; one row per (event, station, phase); `time_utc` ISO-8601 UTC; `uncertainty_s` overrides `pick_error_s` |
| `--stations` | `station_id, latitude, longitude, elevation_m` | sensor elevation (elevation minus burial depth) |
| `--velocity-model` | text `depth_km vp_km_s vs_km_s` | rows are layer tops; `velocity_layering` says whether they are constant layers (`step`) or nodes of a linear profile (`linear`) |
| `--station-delays` | `station_id, phase, delay_s[, n_picks]` | fixed NLL `LOCDELAY` (subtracted from observed times); iterating delays is case policy |

### Outputs

| File | Content |
|---|---|
| `events.csv` | `event_id, status (LOCATED/REJECTED/...), origin_time_utc, latitude, longitude, depth_km, rms_s, n_phases, n_stations, gap_deg, erh_km, erz_km, x_km, y_km, expect_{x,y,depth}_km, sigma_{x,y,depth}_km` |
| `arrivals.csv` | `event_id, pick_id, station_id, phase, residual_s, weight, predicted_travel_time_s` (weight 0: not used) |
| `failures.csv` | `event_id, error`; failed events keep their folder under `events_raw/` |
| `grids/` | velocity and travel-time grids |
| `config.json`, `run_result.json` | merged configuration; `status` success / partial (some events failed) / failed |

Depths are km below `reference_elevation_km`; station z = that reference minus
the station elevation. `erh_km` is the largest horizontal posterior standard
deviation, `erz_km` the vertical one.

### Configuration (deep-merged over the defaults)

| Key | Default | Meaning |
|---|---|---|
| `reference_elevation_km` | 0 | depth datum (km above sea level) |
| `projection_center` | station centroid | `[lon, lat]` of the local frame |
| `region` | station box + `region_pad_km`, depth from the mean station level (or 0, whichever is shallower) to 30 | search volume `{latitude: [a, b], longitude: [a, b], depth_km: [top, bottom]}`; depths relative to `reference_elevation_km`. `grid_depth_km` sets only the travel-time grid, not the search |
| `region_pad_km` | 20 | pad of the default region |
| `velocity_layering` | `step` | `step` (constant layers) or `linear` |
| `grid_spacing_km` | 0.5 | travel-time grid spacing |
| `grid_depth_km` | [-3, 40] | travel-time grid depth range; must contain the region and the stations |
| `location_method` | `EDT_OT_WT` | `GAU_ANALYTIC` (L2 Gaussian likelihood), `EDT` (equal differential time: robust to outlier picks, no origin-time term), `EDT_OT_WT` (EDT weighted by origin-time consistency) |
| `min_phases`, `min_s_phases` | 4, -1 | LOCMETH minimum phases / S phases (-1: none) |
| `pick_error_s` | P 0.10, S 0.20 | default Gaussian pick errors |
| `model_error_s` | 0.10 | LOCGAU travel-time error |
| `search` | min node 0.1 km, 50,000 nodes, 2,000 samples | octree search |
| `locgrid_counts` | [121, 121, 101] | initial search grid nodes |
| `per_event_timeout_s` | 180 | per-event NLLoc timeout |
| `keep_raw` | false | keep each event's NLLoc files |

### Choosing a method

Validation (`validate_nonlinloc.py`): with exact picks the three methods agree
(≤ 0.05 km); with one 2-s outlier pick `GAU_ANALYTIC` moved that event 0.4 km
(2.3 km in depth) while both EDT variants were unaffected. Run several methods
(or models) and compare per-event solutions to see how much a location
depends on the method.
