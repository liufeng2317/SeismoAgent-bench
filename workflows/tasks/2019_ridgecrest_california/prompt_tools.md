## 2019 Ridgecrest sequence monitoring

### Task objective

Construct a reproducible candidate earthquake catalog for the fixed two-hour window `[2019-07-04T16:30:00Z, 2019-07-04T18:30:00Z)`, centered on the Mw 6.4 Ridgecrest mainshock origin time. Process every available waveform interval and every usable station/component that overlaps this window; report incomplete station components and gaps instead of silently dropping them.

Before processing, write a concise `task_plan.md` below the assigned output directory. The plan must state discovered input coverage, preprocessing, tool calls, parameters, hand-off files and quality checks. Save complete reusable processing code below the output directory before running it. Record consequential assumptions, failed intervals, excluded stations, failed batches and unresolved data-quality issues.

### Input data

The read-only observations are under `input/waveforms/`:

- waveforms: `input/waveforms/data/`
- station metadata: `input/waveforms/stations/`

Discover the files and actual coverage before processing. Do not modify the input directory. Do not use existing Ridgecrest catalogs, published picks, reference locations, expert outputs or case-specific products to construct, tune or fill the result. Files inside generic tool examples may be read only to understand documented usage; do not use them as case observations.

### Tools and workflow

The tools base directory is TOOLS_BASE_PATH=`/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/`. Use the supplied implementations through their standard execution paths. Before calling a tool, read its README and the documentation under its `docs/` directory, including curated Markdown/RAG guides and the validated Python examples. Use those documents to determine the method, parameters, input preparation and output interpretation; use the listed tool directory only to locate the appropriate interface. Do not modify shared tools, weights, binaries or the evaluation environment.

1. Phase picking: Use PhaseNet to produce P/S probability output and extracted phase observations for the complete window. Tool resources and documentation are under `TOOLS_BASE_PATH/phase_picking/`.
PhaseNet usage must follow all validated Python examples under `TOOLS_BASE_PATH/phase_picking/docs/examples/`, especially `phasenet.py`: construct an ObsPy `Stream` with the PhaseNet component order `E,N,Z`, use `model.classify` as the preferred method for direct P/S picks and peak probabilities, or use `model.annotate` when probability sequences are required and then interpret channels as `N,P,S`. Resample waveform data to the validated 100 Hz model input before inference. The bundled `run.py` and `run_continuous.py` interfaces return model probabilities; they do not perform resampling, threshold selection or pick extraction, and `run_continuous.py` only applies overlapping windows to a long input. Do not use an unvalidated sampling rate or infer PhaseNet behavior from another picker.
2. Association: Use GaMMA to produce candidate events and pick-to-event assignments. Tool resources and documentation are under `TOOLS_BASE_PATH/gamma/`.
3. Absolute location: Use NonLinLoc to produce absolute locations using an explicit velocity model. Tool resources and documentation are under `TOOLS_BASE_PATH/nonlinloc/`.
4. Relative relocation: Use hypoDD to produce relative locations when the associated events and differential times provide adequate support. Tool resources and documentation are under `TOOLS_BASE_PATH/hypodd/`. This is an additional result, not a substitute for absolute locations.

### Execution and repair rules

1. Keep all created files below the assigned output directory.
2. The input directory is read-only. Use the configured scientific Python environment and the supplied tool interfaces.
3. Record the actual tools executed, versions, commands, configurations, logs and output locations.
4. This host does not provide CUDA or NPU acceleration. Run the workflow on CPU and parallelize independent waveform files or batches (e.g. 32/64 CPU workers)

### Required outputs

Create the following machine-readable tables below the output directory.
1. `picks.csv`: phase picking results, contain columns at least:
```text
pick_id,station_id,phase,time_utc,probability
```
2. `catalog.csv` event information, with at least these columns:
```text
event_id,origin_time_utc,latitude,longitude,depth_km,magnitude,magnitude_type,n_picks,n_p_picks,n_s_picks,status
```

Use ISO 8601 UTC timestamps, `P` or `S` phase labels. Leave values empty when they cannot be estimated defensibly; do not fabricate magnitudes, locations or uncertainties. Keep velocity models, detailed uncertainties and other diagnostics in additional files chosen by the process.

Also provide:
- PNG diagnostic figures:
  - station/data coverage
  - representative raw and/or preprocessed waveforms with picks
  - associated or located catalog in space, time and depth.
- a concise final report describing actual coverage, tools and parameters, phase and event counts, located-event counts, limitations and output locations;
- enough code, configuration, provenance and logs to reproduce the result from the declared inputs.
