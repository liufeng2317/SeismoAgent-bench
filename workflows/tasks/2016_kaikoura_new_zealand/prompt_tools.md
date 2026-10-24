
## 2016 Kaikōura sequence monitoring (minimal instructions, expert tools)

### Objective

Using the supplied waveform data and station metadata, construct an earthquake catalog for the 2016 Kaikōura aftershock sequence. Local expert tools for the canonical processing stages are available and may be used (see Tools).

The run-local input is available under `input/waveforms/` (`data/` for waveforms, `stations/` for station metadata).

### Tools

The tools base directory is TOOLS_BASE_PATH=`/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/`. The supplied implementations may be used through their standard execution paths. Before calling a tool, read its README, the relevant guidance under its `docs/` directory and the validated executable examples under its `examples/` directory, and use those materials to determine the method, parameters, input preparation and output interpretation.

1. Phase picking: PhaseNet produces P/S probability output and extracted phase observations. Tool resources and documentation are under `TOOLS_BASE_PATH/phase_picking/`.
PhaseNet usage must follow the validated example at `TOOLS_BASE_PATH/phase_picking/examples/phasenet.py`: construct an ObsPy `Stream` with the PhaseNet component order `E,N,Z`, use `model.classify` as the preferred method for direct P/S picks and peak probabilities, or use `model.annotate` when probability sequences are required and then interpret channels as `N,P,S`. Resample waveform data to the validated 100 Hz model input before inference. The bundled `run.py` and `run_continuous.py` interfaces return model probabilities; they do not perform resampling, threshold selection or pick extraction, and `run_continuous.py` only applies overlapping windows to a long input. Do not use an unvalidated sampling rate or infer PhaseNet behavior from another picker.
2. Association: GaMMA produces candidate events and pick-to-event assignments. Tool resources and documentation are under `TOOLS_BASE_PATH/gamma/`.
3. Absolute location: NonLinLoc produces absolute locations using an explicit velocity model. Tool resources and documentation are under `TOOLS_BASE_PATH/nonlinloc/`.
4. Relative relocation: hypoDD produces relative locations when the associated events and differential times provide adequate support. This is an additional result, not a substitute for absolute locations.

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

Use ISO 8601 UTC timestamps. `event_id` must match between the two files and may be empty for an unassociated pick.

### Validity conditions

- Do not use existing Kaikōura 2016 earthquake catalogs, published phase picks, known event locations, or other reference earthquake products to construct or tune the result.
- Do not fabricate values; leave a field empty when it cannot be defensibly estimated.
- Do not modify the input directory, or the shared tools, weights, binaries or the evaluation environment.
- Files inside generic tool examples may be read only to understand documented usage; do not use them as case observations.
