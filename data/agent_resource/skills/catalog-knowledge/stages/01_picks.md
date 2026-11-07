# Stage 1: data and picks

Gate: `run.py --stage data` once, then `--stage picks` on the picks. Before association: every flag handled, every station without picks explained.

## Decisions

**Stations without picks.**
- *Applies:* `silent_stations` lists stations with data but no picks.
- *Do:* find the reason first: channel or location-code mismatch between data and metadata, a station missing from the picking list, a dead or noisy channel, a threshold too high for that station. A quiet record with clear events and no picks is a configuration problem; repair it and pick again.
- *Single-component stations:* a three-component picker gives them no picks. Picks from a P-only picker or a low threshold can be added, but only as a tested change (next rule). Leaving them unused is acceptable; say so in the disposition.

**Adding a group of picks** (another picker, a group of stations not used before, a lower threshold).
- *Do:* locate with the group, then run `scripts/compare_pick_groups.py --picks <picks with residual_s> --stations <group>` (or `--p-only`). Relocate the same events without the group and pass both catalogs (`--catalog-without`, `--catalog-with`) to see how far the group moves them.
- *Adopt only if* the group's residual spread is close to the other stations' and the events do not move by kilometres without an independent reason.
- *Why:* noise picks do not have to create events to do harm; the associator attaches them to real events and they pull the locations. An unused station is a smaller loss than a station that adds wrong times.
- *Example:* P picks of eight single-component stations at a low threshold had 46 % of residuals above 0.5 s against 15 % at the other stations (spread ratio 3.3); with them a quarter of the epicentres moved by more than 5 km; without them the catalog was close to the published one.

**Pick times on processed records.**
- *Do:* use zero-phase filtering (or none) on records you pick; check start times after every write.
- *Why:* a causal filter or a resampling step shifts every pick by its group delay (`processing_time_shift`).

## Flags of this stage

| Flag | Likely causes | Evidence | Repair |
|---|---|---|---|
| `processing_time_shift` | causal filter; non-zero-phase anti-alias filter; phase-changing instrument correction; wrong start time after writing | the shift is the same on every record and equals the filter's group delay; a resampling error scales with the rate change | zero-phase filtering; check start times |
| `duplicate_picks` | overlapping windows merged without de-duplication; one channel under two location codes | identical station, phase and time within a few samples | de-duplicate before association |
| `s_to_p_ratio` low | single-component stations; S threshold too high; horizontals not passed to the picker | count horizontals per station in the metadata | pass three components; P only for single-component stations (never S from a vertical) |
| `s_to_p_ratio` high | S on noise or P coda; P picks missing | S picks without a P at the same station and event; S picks off the event's Wadati line | raise the S threshold; check P detection |
| `pick_onset_offset` | the pick is the peak of a probability curve, not the onset; a processing time shift | the offset is the same at all stations and sizes (method) or differs by station (processing) | correct the method or the processing; this check cannot see a station clock error |

Input notes (`channel_sample_rates`, `data_gaps`, `stations_with_data`, `daily_station_count`) describe the data, not an error: use them to set expectations (fewer stations on some days lowers detection then).

**One station's amplitudes or noise far from its neighbours** (seen later as a magnitude station term): a round factor (×2 ≈ 0.3 magnitude units, ×10 = 1, ×1000 = 3) points to metadata units or a sensitivity at the wrong frequency. Repair the metadata or exclude the channel from amplitudes.

**Station delays** (`station_delays`, `station_residual_outliers`, after a first location): a delay equal in P and S (δS/δP ≈ 1) points to the station's clock or instrument; a delay about Vp/Vs larger in S points to the path or a position or elevation error. A step in a station's residuals over time, equal in P and S, points to a clock jump or instrument change. A constant clock offset and a constant site delay cannot be told apart from the catalog alone.
