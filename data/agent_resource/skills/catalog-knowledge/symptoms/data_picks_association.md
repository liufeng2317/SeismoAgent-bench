# Data, picks, association and detection

## Data and preprocessing

**`processing_time_shift` — processed records are shifted in time against a zero-phase filter of the same records.** Tier A.
- Causes: a causal (one-pass) filter; resampling or decimation with a non-zero-phase anti-alias filter; an instrument-correction step that changes phase; trimming that shifts the start time; a wrong sample-rate or start-time field after writing.
- Evidence: the shift is the same on every record and close to the group delay of the filter used (a causal Butterworth filter delays by a fraction of its period); a resampling error scales with the rate change.
- Repair: zero-phase filtering (forward and backward), or no filtering of the records used for picking; check start times after every write.

**`channel_sample_rates`, `data_gaps`, `stations_with_data`, `daily_station_count` (input notes).** These describe the data, not an error of the workflow. Use them to set expectations (fewer stations on some days lowers detection then) and to explain later symptoms (a rate change on a day with fewer stations).

**Gain or unit errors at one station** (seen later as one station's magnitude term far from the others, `magnitude_recompute` details, or noise far above or below its neighbours). Tier A if the offset is a round factor (×2 ≈ 0.3 magnitude units, ×10 = 1, ×1000 = 3): metadata units (m/s vs nm/s, counts vs volts) or a sensitivity at the wrong frequency. Repair the metadata or exclude the channel from amplitudes.

## Picks

**`silent_stations` — stations with data but no picks.** Tier A/B.
- Causes: a channel naming or location-code mismatch between data and metadata; a station outside the picking window list; dead or noisy channel; picker threshold too high for that station's noise.
- Evidence: look at the record and its noise level; a quiet record with clear events and no picks is a configuration problem; a record without signal is a dead channel.

**`duplicate_picks` — the same station, phase and time picked more than once.** Tier A: overlapping processing windows merged without de-duplication, or the same channel under two location codes. Repair: de-duplicate on (station, phase, time within a few samples) before association.

**`s_to_p_ratio` below its range — few S picks.** Tier A/B.
- Causes: vertical-only stations (no horizontals to pick S); S threshold too high; horizontals not passed to the picker; picker model trained on a different instrument type.
- Evidence: count horizontals per station in the metadata; stations with horizontals and P picks but no S picks point to the configuration.
- Repair: pass three components; for vertical-only stations use P only (do not fabricate S from the vertical).

**`s_to_p_ratio` above its range — more S than P picks.** Tier B: S picks on noise or on P coda (picker threshold too low on horizontals), or P picks missing. Evidence: S picks without a P at the same station and event; S picks that fall off their event's Wadati line (plot S−P against P time for single events).

**`pick_onset_offset` — picks systematically early or late relative to the waveform onset.** Tier A/B.
- Causes: the pick is the maximum of a probability curve, not the onset (machine-learning pickers trained on one network's habits); a time shift in preprocessing (see above); picks on filtered records with a causal filter.
- Evidence: the offset is similar at all stations and for large and small events → method; it differs by station → station-specific processing.
- Note: this check cannot see a clock error of the station, because the pick and the onset come from the same record. Clock errors show in `station_delays` (equal in P and S) and as steps in a station's residuals over time.

**Station delays (`station_delays` details, `station_residual_outliers`).** Tier B.
- A delay that is the same in P and S (δS/δP ≈ 1) points to the station's clock or instrument; a delay about Vp/Vs times larger in S (≈ 1.7) points to the path (slow or fast ground under the station) or to an elevation or position error.
- A step in a station's residuals over time, equal in P and S (plot its residuals against time), points to a clock jump or instrument change; a gradual change, larger in S, to seismicity moving.
- A constant clock offset and a constant site delay cannot be told apart from the catalog alone (tier C); station corrections absorb both.

## Association

**`duplicate_events` — origins within a second or two and a few km of each other.** Tier A/B.
- If the pairs share picks (`details.pairs_sharing_picks`): the same event entered twice — overlapping association windows merged without de-duplication, or two associators' outputs concatenated. Repair: merge on shared picks.
- If they share no picks: possibly real doublets (common early in sequences) or one event split in two (picks divided between two origins). Evidence: the union of their picks fits one origin; the two halves come from different stations.

**`events_with_few_picks` — many events with fewer than 4 P picks.** This measures how well events are constrained, not whether they are correct. Tier B.
- Causes: a low association threshold (events from coincident noise); a small network; real small events near one station.
- Evidence: few-pick events concentrated near one or two stations, at times of high noise, or outside the network point to false associations; inspect a random sample of their waveforms.
- Repair: raise the minimum picks and stations per event (common practice: ≥ 4 P and ≥ 7 picks in total, or ≥ 4 stations with both P and S), and keep the few-pick events in a separate list rather than deleting them silently.

**`associated_share` low.** Not an error by itself (published workflows associate as few as 12–19 % of their picks with a low picker threshold). Very low values with a high picker threshold point to an associator configured for the wrong region, velocity or time window.

**`association_busy_hours` — fewer events per pick in the busiest hours.** Tier B.
- Causes: the associator saturates at high event rates (it merges or drops events when events are seconds apart); picker misses in coda.
- Evidence: in busy hours, picks per event rises and the share of unassociated picks rises; rerun the association of one busy hour with a smaller time window or a different associator and compare the number of events.

**Picks off their event's travel-time curve (no check; read the residuals of single events).** Tier B: picks from another event (association across overlapping events), wrong phase label, or a station with a wrong position. Evidence: the outlier picks belong to one station (position or clock) or are spread (association); relocate a few events without the outlier picks.

## Detection beyond picking (template matching, matched filtering)

Before running template matching on the full data:

- **Null test:** run the same templates on time-reversed or time-shifted data; detections there are false. Set the threshold so the false rate is below 1–2 % of detections. Published thresholds are 8–15 × MAD; the false rate depends on the number of templates, channels and the bandwidth, so a threshold does not transfer between setups. The false rate falls steeply with the threshold (from most detections to about 1 % within one or two MAD units), and so does the number of real detections above it: a threshold set well above the point where the null test passes can give up half or more of the real events. Run the null test over a range of thresholds and keep the lowest one that passes, rather than a high value chosen to be safe.
- **Detections per template:** a template with far more detections than the others (often a template with a noise burst, a teleseism or a blast) dominates the false detections. Check its waveform; drop or re-cut it.
- **Ghosts near large events:** in the coda of a large event many templates correlate with the coda itself. Detections within the coda of a larger event with low correlation are suspect; detections larger than their own template need their own magnitude and location.
- **Blasts:** many detections of one template in daytime working hours, few at night or at weekends; a high high-to-low-frequency amplitude ratio is typical of earthquakes, a low ratio of blasts.
