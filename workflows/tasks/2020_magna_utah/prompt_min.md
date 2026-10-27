
## 2020 Magna, Utah sequence monitoring (minimal instructions)

### Objective

Using the supplied waveform data and station metadata, construct an earthquake catalog for the 2020 Magna, Utah earthquake sequence.

The run-local input is available under `input/waveforms/` (`data/` for waveforms, `stations/` for station metadata).

Process the half-open window `[2020-03-18T00:00:00Z, 2020-03-26T00:00:00Z)`; the catalog reports events with origin time inside it. The input may contain waveforms beyond the window.

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

Field conventions:

- UTF-8, comma-separated, the header rows above in exactly this order (followed only by the optional catalog columns below); the empty string for unavailable fields; no units inside cells.
- `station_id` is `NET.STA` (for example `UU.AVE`). `channel_id` is the full SEED channel `NET.STA.LOC.CHA` with an empty location code written as an empty segment (for example `UU.AVE.01.ENE`, or `XX.ABC..HNE` when the location code is empty).
- `phase` is `P` or `S`. `time_utc` and `origin_time_utc` are ISO 8601 UTC timestamps ending in `Z` or `+00:00`.
- `probability` is a detector-assigned quality score in [0, 1]; `uncertainty_s` is a pick-time uncertainty in seconds; both may be empty.
- `event_id` must match between the two files; an empty `event_id` marks an unassociated pick.
- `status` is `accepted`, `uncertain` or `rejected`; keep rejected rows in the files (they are not scored).
- `latitude` and `longitude` are decimal degrees (WGS84). `depth_km` is kilometres below sea level, positive down; it may be empty when depth is not resolvable.
- `magnitude` may be empty; `magnitude_type` is a short code such as `ML`, `Md`, `Mw` or `M`.
- `n_picks`, `n_p_picks` and `n_s_picks` count the non-rejected `picks.csv` rows of the event.
- `catalog.csv` may add, after the columns above, `horizontal_uncertainty_km`, `depth_uncertainty_km` and `origin_time_uncertainty_s` (1σ; may be empty).

### Validity conditions

- Do not use existing Magna 2020 earthquake catalogs, published phase picks, known event locations, or other reference earthquake products to construct or tune the result.
- Do not fabricate values; leave a field empty when it cannot be defensibly estimated.
