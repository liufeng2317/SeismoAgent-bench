# GrowClust relocation interface (version 1)

```bash
python seismotools/growclust/interface/run.py \
  --events events.csv --stations stations.csv --dtcc CCDT_OUT --velocity-model model.txt \
  --output-dir OUT [--config config.json] [--overwrite] [--quiet]
```

Requires the build (`python seismotools/support/build_native.py --tool growclust`).

## Inputs

| Input | Content | Notes |
|---|---|---|
| `--events` | CSV `event_id, origin_time_utc, latitude, longitude, depth_km[, magnitude]` | the catalog given to ccdt (same origin times: dt.cc times are relative to them); depth below the model datum |
| `--stations` | CSV `station_id (NET.STA), latitude, longitude` | station codes (after the network) unique, as in ccdt `dt.cc`; GrowClust ignores elevations: give event depths and the model from the station level when stations lie well above the catalog's datum, and convert back |
| `--dtcc` | ccdt output directory | `dt.cc` (DT = tt(id1) − tt(id2) → GrowClust `tdif_fmt 12`; weight = CC → `rxcor`) and `event_ids.csv`; run ccdt with `weight: cc` |
| `--velocity-model` | text `depth_km vp_km_s vs_km_s` | rows are layer tops; `step` writes repeated depths (GrowClust interpolates linearly) |

## Outputs

| File | Content |
|---|---|
| `relocated.csv` | `event_id, origin_time_utc, latitude, longitude, depth_km, cluster_id, n_branch, n_pairs, n_dt_p, n_dt_s, rms_p_s, rms_s_s, eh_km, ez_km, et_s, latitude_initial, longitude_initial, depth_km_initial, relocated` (`relocated`: in a cluster of ≥ 2 events; singletons keep their input position; `eh/ez/et` -1 without bootstrap) |
| `OUT/`, `IN/`, `TT/`, `growclust.inp`, `growclust.log` | native outputs (`out.growclust_cat`, `_clust`, `_log`, `_boot`), generated inputs (stations aliased `S0001`…, 5 characters), travel-time tables |
| `config.json`, `run_result.json` | merged configuration; counts |

## Configuration (deep-merged; upstream EXAMPLE values as defaults)

| Key | Default | Meaning |
|---|---|---|
| `velocity_layering` | `step` | rows constant (`step`) or linear nodes |
| `table.depth_min_km`, `depth_max_km`, `depth_step_km` | 0, 30, 1 | travel-time table depths (cover the catalog) |
| `table.distance_min_km`, `distance_max_km`, `distance_step_km` | 0, 200, 2 | travel-time table distances (cover all stations) |
| `table.rayparam_min` | 0 | GrowClust `rayparam_min` |
| `rmin` | 0.6 | minimum CC (`rxcor`) of a differential time |
| `delmax_km` | 80 | maximum station distance |
| `rmsmax_s` | 0.2 | maximum RMS residual to join clusters |
| `rpsavgmin`, `rmincut` | 0, 0 | minimum mean pair CC; CC cut for the link test |
| `ngoodmin` | 0 | minimum number of good differential times for a pair to link events |
| `iponly` | 0 | 1: P only |
| `nboot`, `nbranch_min` | 0, 1 | bootstrap resamples (≤ 100); minimum cluster size to report |

## Notes from validation

With sparse cross-correlation data, keep the upstream `ngoodmin 0` out: on six
hours of a dense local sequence (most event pairs with 1–2 CC differential
times) the default relocated 157 of 185 events but did not improve
inter-event distances against an independent relocated catalog
(0.47 → 0.45 km); `ngoodmin 4` relocated 110 and halved the error
(0.30 → 0.15 km), `ngoodmin 8` 51 events, 0.19 → 0.06 km.
