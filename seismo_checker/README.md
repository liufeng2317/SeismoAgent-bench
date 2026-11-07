# Catalog checker

The checker measures the products of an earthquake-catalog workflow stage by stage — station data, picks, association, absolute location, relative relocation, magnitudes — using only the products themselves, the station metadata and the waveforms. It needs no reference catalog. Each check compares one property with a case-agnostic expected range and, when the property falls outside, states the **symptom**: what was measured and by how much it is out of range. It never names a cause or a repair; deciding what a symptom means and what to change is up to you.

## Commands

```bash
python CHECKER_PATH/interface/run.py --stage <stage> --stations <StationXML file or folder> --output-dir <dir> [inputs]
python CHECKER_PATH/interface/compare.py --before <dir>/checker_report.json --after <dir2>/checker_report.json --change <kind>
python CHECKER_PATH/interface/pilot.py events|windows ...
```

| Stage | Inputs | Also runs |
|---|---|---|
| `data` | `--waveforms` (folder of `NET.STA.LOC.CHA__start__end.mseed`), optional `--processed-waveforms` (your processed records, same naming) | — |
| `picks` | `--picks picks.csv` (associated or not), optional `--waveforms` | — |
| `association` | `--catalog events.csv --picks picks.csv` (locations may be missing) | picks |
| `location` | `--catalog catalog.csv --picks picks.csv`, optional `--location-setup setup.json`, optional `--model-ensemble` | picks, association |
| `relocation` | `--catalog relocated.csv --catalog-before located.csv --picks picks.csv`, optional `--dtcc dt.cc` | picks, association, location (on the relocated catalog) |
| `magnitude` | `--catalog --picks --waveforms` (StationXML with responses) | picks, association, location |
| `all` | everything the given inputs allow | |

Options:
- `--pilot`: the products come from a pilot batch (a part of the data). Checks of scope `population` are reported without a verdict.
- `--location-setup setup.json`: your location set-up in km below sea level, `{"interfaces_km_bsl": [...], "search_depth_km_bsl": [top, bottom], "grid_spacing_km": g, "grid_origin_km_bsl": z0, "trial_depth_km_bsl": z}` (any subset). The report then states where the most common depth lies relative to each of these.
- `--model-ensemble`: also relocates a sample of 100 events with six generic velocity models and reports how the catalog compares (10–45 minutes; reported only).
- `--config config.json`: override expected ranges (keys as printed in the report's `config`); the overrides are recorded in the report.
- `--no-figures`.

Run time: seconds to a few minutes per stage; the magnitude stage reads waveforms for about 30 events.

## Output

`<output-dir>/checker_report.json` and figures (PNG). Exit code 0 whether or not flags are raised, 2 on unreadable inputs.

| Section | Holds |
|---|---|
| `flags` | products outside their expected range: `flag_id`, `dimension`, `symptom`, `measured`, `unit`, `expected`, `scope` |
| `input_notes` | properties of the input data outside the usual range (station coverage, gaps, sample rates). They describe what the data allow; they are not errors of the workflow |
| `measurements` | values reported without an expected range, with the reason (`why_not_judged`): they did not separate correct from faulty catalogs when the checker was validated, or they only describe the data |
| `checks` | every check: measured value, expected range, number of items, flag, details |
| `figures`, `data`, `picks`, `association_figures`, `location_figures`, `magnitude_figures`, `relocation`, `model_ensemble` | figure names and the numbers behind each figure |
| `counts`, `summary`, `inputs` (with SHA-256), `config`, `stage`, `pilot` | bookkeeping |

`scope`: `item` checks measure single picks, events or stations, so a pilot batch estimates them as well as the full run; `population` checks measure the distribution of the whole catalog and are judged on the full run only.

## Checks

Dimensions: `data` (input), `reality` (are the events real and complete), `time` (origin and pick times), `space` (locations), `strength` (magnitudes). The expected range of each check is printed in the report.

| Stage | Check | Measures | Judged |
|---|---|---|---|
| data | `stations_with_data`, `daily_station_count`, `channel_sample_rates`, `data_gaps`, `network_geometry` | metadata and waveform coverage | input notes |
| data | `processing_time_shift` | time shift of your processed records against a zero-phase filter of the same records | yes |
| data | representative windows | the most energetic network-wide windows, raw against processed records (figures, SNR, peak frequency) | figures |
| picks | `silent_stations`, `station_day_gaps` | stations or station-days with data but no picks | yes |
| picks | `duplicate_picks`, `s_to_p_ratio` | repeated picks; S picks per P pick | yes |
| picks | `pick_onset_offset` | P picks against the AIC onset on a sample of clear picks (S reported; details: share of picks with a low amplitude ratio across the pick) | yes |
| association | `associated_share`, `association_busy_hours` | share of picks in events, overall and in the busiest hours | yes |
| association | `duplicate_events` | events within 1.5 s and 3 km of another (details: pairs sharing picks) | yes |
| association | `events_with_few_picks` | events with picks that have fewer than 4 P picks; events without any pick (template-matching detections) are counted apart (`events_without_picks`) | yes |
| location | `isolated_events` | events far from all others | yes |
| location | `events_beyond_stations` | located events more than 10 km outside the hull of the stations (details: count, aperture) | reported |
| location | `location_uncertainty` | the locator's horizontal and depth uncertainties (optional catalog columns `horizontal_uncertainty_km`, `depth_uncertainty_km`): distribution, and the events above 3 times the median horizontal uncertainty | reported |
| location | `station_residual_spread` | the locator's residuals (optional picks column `residual_s`) per station and phase with at least 10 picks: median and spread (MAD); station-phases whose spread exceeds max(0.2 s, 3 times the median spread of the stations with S picks) | reported |
| location | `wadati_origin_spread`, `wadati_origin_offset` | origin times from each event's own S−P times against the catalog origin times (spread; median offset, flagged only beyond 1.5 s) | yes |
| location | `travel_time_intercept`, `station_residual_outliers`, `station_residual_azimuth` | P travel times against distance; residuals by station and azimuth | reported |
| location | `depth_single_value`, `depth_at_edges`, `depth_layers` | events at one depth, at the shallowest or deepest depth, in thin depth slices | yes |
| location | `sp_depth_offset` | depths implied by S−P times at stations closer than the source depth against catalog depths | yes |
| location | `depth_constraint` | station geometry per event (azimuthal gap, nearest station); share of events with an S pick within 1.4 focal depths; make-up of the most common depth | reported |
| location | `pile_against_setup` | distance of the most common depth to the features of `--location-setup` | reported |
| location | `station_delays` | P and S delays per station and their ratio | reported |
| location | `model_ensemble_depth`, `model_ensemble_time` | catalog against relocations with generic models (`--model-ensemble`) | reported |
| relocation | `relocation_shift`, `relocation_large_moves`, `relocation_thinning` | overall shift; large moves; thinning of local structure | yes |
| relocation | `relocated_share` | share of events with enough picks that relocation moved | reported |
| magnitude | `magnitude_range`, `magnitude_detection` | plausible magnitudes; amplitude implied at the farthest detecting station | yes |
| magnitude | `magnitude_recompute` | catalog magnitude against a standard local magnitude recomputed from the records for 20 events (details: station terms, trend with distance, spread) | yes |
| magnitude | `largest_events_magnitude` | the same for the largest events, from unclipped records over a long window | yes |
| magnitude | `b_positive` | b-value from magnitude differences of consecutive events (details: the standard b-value and its completeness) | reported |

Each stage also runs the cheaper checks of the stages before it.

## What the checker's own models and formulas are for

The checker carries generic velocity models (CRUST1.0, LITHO1.0 and global 1-D models, `runtime/velocity_models/`, used by `--model-ensemble`) and recomputes magnitudes with the IASPEI standard relation (`magnitude_recompute`). Both are references for comparison: they show how much a result depends on the model, and whether a magnitude code has a unit or response error. They are not recommended location models or magnitude formulas for any region: generic models miss near-surface structure (sediments, basins), and the standard magnitude relation differs from regional calibrations by a few tenths. Choose the location model and the magnitude calibration for the region yourself, and say which and why.

The checks and measurements are not criteria for choosing a velocity model either. The model that brings `sp_depth_offset`, `travel_time_intercept`, `wadati_origin_offset`, the station residuals or the depth distribution closest to their expected values is not, in general, the one that places events best: in validation, choosing among a generic model and the same model under slow surface layers by any one of these measures chose a wrong model in one or two of the three sequences where a right candidate existed, and their values at the right model differed from sequence to sequence. A flag that disappears after a model change says something about the new products, not that the new model is better.

## Comparing two products

`compare.py` takes the reports of a current product and a candidate built from the same input (run the checker with the same stage and inputs on both) and returns `better`, `worse`, `mixed`, `uncertain` or `no_difference` under a rule fixed in advance (printed in the output's `rule` field). `--change` names what differs (`velocity_model`, `location_method`, `picks`, `association`, `event_selection`, `relocation`, `magnitude`, `other`); checks that cannot rank that kind of change are listed but not counted. The verdict says which product the checks prefer, not that either is right.

## Pilot batches

`pilot.py events --catalog --picks --output-dir` writes a pilot batch of about 300 events (representative 60 %, busiest hour 20 %, largest events 20 %) with `pilot.json` naming the events of each part. `pilot.py windows --waveforms --stations [--picks] --output-dir [--extract]` chooses time windows before any catalog exists (representative windows, the busiest window, the window of the strongest network-wide transient) and can extract their records. Run the checker on a pilot with `--pilot`.

## Region

`region.py --stations [--catalog] [--region LAT_MIN LAT_MAX LON_MIN LON_MAX] [--buffer-km 10] --output-dir` writes `region.json` with the station coverage (the convex hull of the stations widened by the buffer, in latitude/longitude and km about the network centre, and the aperture) and the given region if any; with `--catalog` also `events_region.csv` (`event_id, km_outside_station_hull, inside_station_coverage[, inside_given_region]`). Outside the coverage the network sees an event from one side only, so its distance and depth are poorly constrained. Inside the coverage a catalog can still hold real earthquakes from elsewhere in the network; a region given by the user (for example the task's study region) separates those. The tool does not remove events: whether to keep events outside the coverage or the given region is a decision for the catalog, and the rule should be stated.

## Validation

The checks, their ranges and the report-only list were validated on human-in-loop catalogs and Agent runs of several earthquake sequences and on synthetic regression scenarios (`examples/smoke/run.sh`).
