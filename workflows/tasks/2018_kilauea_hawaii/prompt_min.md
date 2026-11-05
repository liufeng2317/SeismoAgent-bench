
## 2018 Kīlauea summit sequence monitoring (minimal instructions)

### Objective

Using the supplied waveform data and station metadata, construct an earthquake catalog for the 2018 Kīlauea summit earthquake sequence.

The run-local input is available under `input/waveforms/` (`data/` for waveforms, `stations/` for station metadata).

Process the half-open window `[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z)`; the catalog reports events with origin time inside it. The input may contain waveforms beyond the window.

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

- UTF-8, comma-separated, the header rows above in exactly this order (followed only by the optional columns below); the empty string for unavailable fields; no units inside cells.
- `station_id` is `NET.STA` (for example `HV.RIMD`). `channel_id` is the full SEED channel `NET.STA.LOC.CHA` with an empty location code written as an empty segment (for example `HV.RIMD..HHE`, whose location code is empty; `XX.ABC.00.HNE` when it is not).
- `phase` is `P` or `S`. `time_utc` and `origin_time_utc` are ISO 8601 UTC timestamps ending in `Z` or `+00:00`.
- `probability` is a detector-assigned quality score in [0, 1]; `uncertainty_s` is a pick-time uncertainty in seconds; both may be empty.
- `event_id` must match between the two files; an empty `event_id` marks an unassociated pick.
- `status` is `accepted`, `uncertain` or `rejected`; keep rejected rows in the files (they are not scored).
- `latitude` and `longitude` are decimal degrees (WGS84). `depth_km` is kilometres below sea level, positive down; it may be empty when depth is not resolvable.
- `magnitude` may be empty; `magnitude_type` is a short code such as `ML`, `Md`, `Mw` or `M`.
- `n_picks`, `n_p_picks` and `n_s_picks` count the non-rejected `picks.csv` rows of the event.
- `catalog.csv` may add, after the columns above, `horizontal_uncertainty_km`, `depth_uncertainty_km` and `origin_time_uncertainty_s` (1σ; may be empty).
- `picks.csv` may add, after the columns above, `residual_s`: the locator's arrival-time residual (observed minus predicted, seconds; may be empty). When the locator reports uncertainties and residuals, copy them into these optional columns.

### Validity conditions

- Do not use existing Kīlauea 2018 earthquake catalogs, published phase picks, known event locations, or other reference earthquake products to construct or tune the result.
- Do not fabricate values; leave a field empty when it cannot be defensibly estimated.
