## 2019 Ridgecrest sequence monitoring

### Task objective

Construct a reproducible candidate earthquake catalog for the one-day window `[2019-07-04T00:00:00Z, 2019-07-05T00:00:00Z)`. The Mw 6.4 mainshock occurred at approximately `2019-07-04T17:33:49Z`. Process every usable waveform, station and component that overlaps this window, using batches when necessary. This is a one-day validation product, not a complete catalog for the Ridgecrest sequence.

### Input data

The read-only observations are under `input/waveforms/`:

- waveforms: `input/waveforms/data/`
- station metadata: `input/waveforms/stations/`

Discover the files and actual coverage before processing. Do not modify the input directory. Do not use existing Ridgecrest catalogs, published picks, reference locations, expert outputs or case-specific products to construct, tune or fill the result. Ridgecrest files inside tool examples may be read only to understand an interface; do not use them as observations.

### Tools and workflow

Use the supplied implementations through their standard interfaces. Read the relevant tool README and interface schemas before calling a tool. The task-local code is responsible for MiniSEED conversion, preprocessing, batching, format conversion and pick extraction between stages. Do not modify shared tools, weights, binaries or the evaluation environment.

| Stage | Tool and interface | Required result |
| --- | --- | --- |
| 1. Phase picking | PhaseNet: `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/phase_picking/interface/run.py` | P/S probability output and extracted phase observations for the complete window |
| 2. Association | GaMMA: `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/gamma/interface/run.py` | Candidate events and pick-to-event assignments |
| 3. Absolute location | NonLinLoc: `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/nonlinloc/interface/run.py` | Absolute locations using an explicit velocity model |
| 4. Relative relocation | hypoDD: `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/hypodd/interface/run.py` | Optional relative locations when the associated events and differential times provide adequate support |

The first three stages are mandatory and must be attempted in order. Do not replace PhaseNet, GaMMA or NonLinLoc with an amplitude threshold, STA/LTA detector, custom association or custom locator. hypoDD is an additional stage, not a substitute for absolute locations. If it is used, prepare or verify the required `dt.ct` and, when applicable, `dt.cc` inputs; state whether the final catalog contains absolute locations, relative locations or both. If it is not used, record the scientific reason.

Before processing, write a concise `task_plan.md` below the assigned output directory. The plan must state discovered input coverage, preprocessing, tool calls, parameters, hand-off files and quality checks. Save complete reusable processing code below the output directory before running it. Record consequential assumptions, failed intervals, excluded stations, failed batches and unresolved data-quality issues.

### Execution resources

This host does not provide CUDA or NPU acceleration. Run the workflow on CPU and parallelize independent waveform files or batches. Use up to 32 CPU workers by default; increase to 64 only when those CPUs and sufficient memory are available. Do not create more workers than the available CPUs, and record the worker count and batching strategy in `task_plan.md` or the final report.

### Execution and repair rules

Keep all created files below the assigned output directory. The input directory is read-only. Use the configured scientific Python environment and the supplied tool interfaces. If a mandatory stage fails, diagnose and repair only run-local code or configuration, then rerun the failed stage. Allow at most 20 repair attempts for the complete required chain. For every attempt, record the error, diagnosis, change, command and result. Do not skip a mandatory stage or present a partial upstream product as the completed catalog. If the limit is reached, mark the run incomplete and preserve the diagnostics.

Record the actual tools executed, versions, commands, configurations, logs and output locations. A zero exit code alone does not establish success; verify the expected output files and contents after every stage. For NonLinLoc, this verification must include generated control files, velocity and travel-time grids, and event observations, not only a help or no-argument invocation.

### Required outputs

Create the following machine-readable tables below the output directory.

`picks.csv` contains one row per phase observation before association, with these columns:

```text
pick_id,station_id,channel_id,phase,time_utc,probability,uncertainty_s,method,status
```

`catalog.csv` contains one row per candidate event, with these columns:

```text
event_id,origin_time_utc,latitude,longitude,depth_km,magnitude,magnitude_type,n_picks,n_p_picks,n_s_picks,status
```

`picks.csv` does not require `event_id`; keep any association table separately and link it using `pick_id`. Use ISO 8601 UTC timestamps, `P` or `S` phase labels, and `accepted`, `uncertain` or `rejected` status values. Leave values empty when they cannot be estimated defensibly; do not fabricate magnitudes, locations or uncertainties. Derive event pick counts from the association used for location. Keep velocity models, detailed uncertainties and other diagnostics in additional files chosen by the Agent.

Also provide:

- diagnostic figures or tables showing data/station coverage, representative waveforms or picks, catalog results and important quality concerns;
- a concise final report describing actual coverage, tools and parameters, phase and event counts, located-event counts, limitations and output locations;
- enough code, configuration, provenance and logs to reproduce the result from the declared inputs.

State explicitly that the result covers only the fixed one-day window.
