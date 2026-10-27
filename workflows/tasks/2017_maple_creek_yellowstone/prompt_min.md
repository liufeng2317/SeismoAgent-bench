
## 2017 Maple Creek, Yellowstone sequence monitoring (minimal instructions)

### Objective

Using the supplied waveform data and station metadata, construct an earthquake catalog for the 2017 Maple Creek, Yellowstone earthquake sequence.

The run-local input is available under `input/waveforms/` (`data/` for waveforms, `stations/` for station metadata).

### Required outputs

Write the following machine-readable files under the output directory.

`picks.csv` — one row per phase observation, header row exactly:
```text
pick_id,event_id,station_id,channel_id,phase,time_utc,probability,uncertainty_s,method,status
```

`catalog.csv` — one row per candidate earthquake, header row exactly:
```text
event_id,origin_time_utc,latitude,longitude,depth_km,magnitude,magnitude_type,n_picks,n_p_picks,n_s_picks,status
```

Use ISO 8601 UTC timestamps. `event_id` must match between the two files and may be empty for an unassociated pick. `depth_km` is kilometres below sea level, positive down. `status` is `accepted`, `uncertain` or `rejected`; keep rejected rows in the files (they are not scored). `catalog.csv` may add, after the columns above, `horizontal_uncertainty_km`, `depth_uncertainty_km` and `origin_time_uncertainty_s` (1σ; may be empty).

### Validity conditions

- Do not use existing Maple Creek 2017 earthquake catalogs, published phase picks, known event locations, or other reference earthquake products to construct or tune the result.
- Do not fabricate values; leave a field empty when it cannot be defensibly estimated.
