## 2019 Ridgecrest sequence monitoring

### Task objective

Construct a reproducible candidate earthquake catalog for the one-day window `[2019-07-04T00:00:00Z, 2019-07-05T00:00:00Z)`. Process every usable waveform, station and component that overlaps this window.

### Input data

The read-only observations are under `input/waveforms/`:

- waveforms: `input/waveforms/data/`
- station metadata: `input/waveforms/stations/`

Discover the files and actual coverage before processing. Do not modify the input directory. Do not use existing Ridgecrest catalogs, published picks, reference locations, expert outputs or case-specific products to construct, tune or fill the result. Files inside generic tool examples may be read only to understand documented usage; do not use them as case observations.

### Tools and workflow

Use the supplied implementations through their standard execution paths. Before calling a tool, read its README and the documentation under its `docs/` directory, including curated Markdown/RAG guides and generic examples where present. Use those documents to determine the method, parameters, input preparation and output interpretation; use the listed execution path only to run the tool. The task-local code is responsible for MiniSEED conversion, preprocessing, batching, format conversion and pick extraction between stages. Do not modify shared tools, weights, binaries or the evaluation environment.

| Stage | Tool and execution path | Required result |
| --- | --- | --- |
| 1. Phase picking | PhaseNet: `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/phase_picking/interface/run_continuous.py` | P/S probability output and extracted phase observations for the complete window |
| 2. Association | GaMMA: `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/gamma/interface/run.py` | Candidate events and pick-to-event assignments |
| 3. Absolute location | NonLinLoc: `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/nonlinloc/interface/run.py` | Absolute locations using an explicit velocity model |
| 4. Relative relocation | hypoDD: `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/hypodd/interface/run.py` | Optional relative locations when the associated events and differential times provide adequate support |

The first three stages are mandatory and must be attempted in order. The mandatory processing scope is the complete fixed one-day window, not only a mainshock-centered subwindow. Do not replace PhaseNet, GaMMA or NonLinLoc with an amplitude threshold, STA/LTA detector, custom association or custom locator. hypoDD is an additional stage, not a substitute for absolute locations. If it is used, prepare or verify the required `dt.ct` and, when applicable, `dt.cc` inputs; state whether the final catalog contains absolute locations, relative locations or both. If it is not used, record the scientific reason.

For PhaseNet, each inference window is exactly 3001 samples with input components in E/N/Z order and output probability channels in Noise/P/S order. Use overlapping windows to cover the entire one-day interval, merge and de-duplicate picks, and report the window count and final pick time range. Processing only the first window is incomplete. Do not downsample or retain every Nth pick to make GaMMA finish; preserve the full validated pick set.

Before processing, write a concise `task_plan.md` below the assigned output directory. The plan must state discovered input coverage, preprocessing, tool calls, parameters, hand-off files and quality checks. Save complete reusable processing code below the output directory before running it. Record consequential assumptions, failed intervals, excluded stations, failed batches and unresolved data-quality issues.

### Execution resources

This host does not provide CUDA or NPU acceleration. Run the workflow on CPU and parallelize independent waveform files or batches. Use up to 32 CPU workers by default; increase to 64 only when those CPUs and sufficient memory are available. Do not create more workers than the available CPUs, and record the worker count and batching strategy in `task_plan.md` or the final report.

### Execution and repair rules

1. Keep all created files below the assigned output directory.
2. The input directory is read-only. Use the configured scientific Python environment and the supplied tool interfaces.
3. Record the actual tools executed, versions, commands, configurations, logs and output locations.

### Required outputs

Create the following machine-readable tables below the output directory.
1. `picks.csv`: phase picking results, contain columns at least:
```text
pick_id,station_id,phase,time_utc,probability
```
2. `catalog.csv` events infomation, with at least these columns:
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
