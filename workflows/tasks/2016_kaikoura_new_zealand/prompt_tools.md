
## 2016 Kaikōura sequence monitoring (minimal instructions, expert tools)

### Objective

Using the supplied waveform data and station metadata, construct an earthquake catalog for the 2016 Kaikōura aftershock sequence. Local expert tools for the canonical processing stages are available and may be used (see Tools).

The run-local input is available under `input/waveforms/` (`data/` for waveforms, `stations/` for station metadata).

Process the half-open window `[2016-12-01T00:00:00Z, 2016-12-09T00:00:00Z)`; the catalog reports events with origin time inside it. The input may contain waveforms beyond the window.

### Tools

The tools base directory is TOOLS_BASE_PATH=`/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/`. The supplied implementations may be used through their standard execution paths. Before calling a tool, read its README, the relevant guidance under its `docs/` directory and the validated executable examples under its `examples/` directory, and use those materials to determine the method, parameters, input preparation and output interpretation.

1. Phase picking: PhaseNet produces P/S probability output and extracted phase observations. Tool resources and documentation are under `TOOLS_BASE_PATH/phase_picking/`.
PhaseNet usage must follow the validated example at `TOOLS_BASE_PATH/phase_picking/examples/phasenet.py`: construct an ObsPy `Stream` with the PhaseNet component order `E,N,Z`, use `model.classify` as the preferred method for direct P/S picks and peak probabilities, or use `model.annotate` when probability sequences are required and then interpret channels as `N,P,S`. Resample waveform data to the validated 100 Hz model input before inference. The bundled `run.py` and `run_continuous.py` interfaces return model probabilities; they do not perform resampling, threshold selection or pick extraction, and `run_continuous.py` only applies overlapping windows to a long input. Do not use an unvalidated sampling rate or infer PhaseNet behavior from another picker.
2. Association: GaMMA, PyOcto and REAL produce candidate events and pick-to-event assignments with different algorithms (GaMMA: Bayesian Gaussian mixture; PyOcto: octree space-time partitioning; REAL: pick counting on a grid around the station with the initiating pick). Tool resources and documentation are under `TOOLS_BASE_PATH/gamma/`, `TOOLS_BASE_PATH/pyocto/` and `TOOLS_BASE_PATH/real/`.
3. Absolute location: NonLinLoc and HypoInverse produce absolute locations using an explicit velocity model. NonLinLoc is a probabilistic grid search with selectable likelihood methods (`GAU_ANALYTIC`, `EDT`, `EDT_OT_WT`) and has a single-event and a catalog interface; HypoInverse is a linearised locator with distance and residual weighting. Tool resources and documentation are under `TOOLS_BASE_PATH/nonlinloc/` and `TOOLS_BASE_PATH/hypoinverse/`.
4. Relative relocation: hypoDD and GrowClust produce relative locations when the associated events and differential times provide adequate support; waveform cross-correlation differential times can be measured with ccdt. This is an additional result, not a substitute for absolute locations. Tool resources and documentation are under `TOOLS_BASE_PATH/hypodd/`, `TOOLS_BASE_PATH/growclust/` and `TOOLS_BASE_PATH/cross_correlation/`.
5. Template-matching detection: Match&Locate (MatchLocate2) correlates template waveforms of located events with the continuous data and locates each detection by a grid search around its template; with a zero-size grid it is a matched filter. Detections carry a relative magnitude from the amplitude ratio to the template. Tool resources and documentation are under `TOOLS_BASE_PATH/match_and_locate/`.

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
- `station_id` is `NET.STA` (for example `NZ.KHZ`). `channel_id` is the full SEED channel `NET.STA.LOC.CHA` with an empty location code written as an empty segment (for example `NZ.KHZ.10.HHE`, or `XX.ABC..HNE` when the location code is empty).
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

- Do not use existing Kaikōura 2016 earthquake catalogs, published phase picks, known event locations, or other reference earthquake products to construct or tune the result.
- Do not fabricate values; leave a field empty when it cannot be defensibly estimated.
- Do not modify the input directory, or the shared tools, weights, binaries or the evaluation environment.
- Files inside generic tool examples may be read only to understand documented usage; do not use them as case observations.
