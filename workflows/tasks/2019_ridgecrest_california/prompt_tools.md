## 2019 Ridgecrest sequence monitoring

### Task objective

Construct a scientifically credible and reproducible **candidate earthquake catalog for the 2019 Ridgecrest sequence** using the waveform data and station metadata provided to this run.

You are responsible for determining an appropriate end-to-end seismological workflow from the available observations.

The task covers the complete usable waveform collection in the declared input. Inspect and understand the supplied data before deciding how to process them. Do not silently select a small example subset or short time interval for convenience.

### Input

The run-local input is available under:
```text
input/waveforms/
```

Waveforms are under `input/waveforms/data/` and station metadata are under `input/waveforms/stations/`. Treat the entire `input/` directory as read-only.

The supplied waveform and station metadata are the scientific observations available for this task. Do not use an existing Ridgecrest earthquake catalog, published phase picks, known event locations, or other reference earthquake products to construct or tune the catalog.

### Available tools

Local seismological software, model files, documentation and executables are available under the project `seismotools` directory. This tools-enabled task is intended to test whether an Agent can use the supplied seismological software, rather than replace it with an unrelated ad-hoc detector.

Available resources include:
- **PhaseNet:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/phase_picking/`
- **GaMMA:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/gamma/`
- **NonLinLoc:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/nonlinloc/`
- **hypoDD:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/hypodd/`
- **General scientific Python:** the configured environment includes commonly used scientific and seismological Python packages.

You may inspect the source code, documentation, model metadata, example interfaces and executables provided with these tools in order to determine whether and how they should be used.

Use the following tool chain as the default workflow:

1. Use **PhaseNet** (or its supplied command-line/API interface) for neural-network P and S phase picking on the waveform data. Do not replace the full-data picking stage with a simple amplitude threshold, STA/LTA detector or custom peak finder unless PhaseNet has been tested and a documented execution failure prevents its use.
2. Use **GaMMA** to associate the resulting phase picks into candidate events. Preserve the association parameters and the input/output file locations.
3. Use **NonLinLoc** for absolute event location with an explicit velocity model. If appropriate, use **hypoDD** for relative relocation after absolute locations and differential picks are available; describe whether the final catalog contains absolute locations, relative locations, or both.

The Agent may add transparent preprocessing or quality-control steps around this chain. It must not silently substitute a custom detector or locator merely because that is simpler. If a required tool cannot be executed, first record the command or interface tested, the exact error, and the affected data scope; then use the least-complex documented fallback and mark the affected results as limited.

Tool resources are methodological references, not scientific observations for this case. The waveform data and station metadata under the declared `input/` directory are the case-specific observations available for constructing the catalog.

Do not use existing Ridgecrest catalogs, published phase picks, reference event locations, expert workflow outputs, or other case-specific observational products to construct or tune the result. General seismological knowledge and generic methodological assumptions or models may be used when needed, but any consequential choices must be independently justified from the task and available observations.

Do not modify shared tool sources, model weights, binaries, or the evaluation environment. Record sufficient information to identify and reproduce any tools actually used.

### Scientific task

Independently design and execute an appropriate workflow to construct the earthquake catalog from the supplied waveform observations and station metadata.

You are responsible for selecting the preprocessing parameters, model configuration, quality-control rules and, where applicable, the relative-relocation strategy. The default PhaseNet–GaMMA–NonLinLoc chain above must be attempted before any fallback is chosen. Before substantial processing, briefly document the planned workflow, the tool interfaces to be used, and the rationale for the major scientific decisions. You may revise the workflow when intermediate results indicate that changes are needed; record each significant revision and its rationale. Process the complete usable input, including batches or partitions, and report any files or intervals that could not be processed.

### Reproducibility

The workflow must be executed and reproducible from the supplied inputs. Preserve sufficient code, configuration, tool versions, commands, tool logs and provenance under the assigned output directory so that the processing can be rerun and the origin of the final catalog can be understood. Record which supplied tools were actually executed, not only which tools were inspected. Ensure that the complete usable dataset is covered, including when processing is performed in multiple batches or partitions.

### Required scientific outputs

At minimum, provide machine-readable phase observations in `picks.csv` and a versioned candidate-earthquake catalog in `catalog.csv`.

Use these columns for `picks.csv`, with one row per phase observation:
```text
pick_id,event_id,station_id,channel_id,phase,time_utc,probability,uncertainty_s,method,status
```

Use these columns for `catalog.csv`, with one row per candidate event:
```text
event_id,origin_time_utc,latitude,longitude,depth_km,magnitude,magnitude_type,n_picks,n_p_picks,n_s_picks,status
```

The catalog records the event identifier, origin time in UTC, location, depth, magnitude when defensible, phase counts and event status. Use ISO 8601 UTC for `time_utc` and `origin_time_utc`; `event_id` must match between the two files and may be empty for an unassociated pick. Use `P` or `S` for `phase`, and `accepted`, `uncertain` or `rejected` for `status`. Fields that cannot be estimated defensibly may be empty and must not be fabricated. Record the velocity model, location method, uncertainty estimates and other diagnostic quantities in workflow documentation or a separate metadata file chosen by the Agent. The final catalog must be traceable to the observational evidence used to construct it.

### Inspection and visualization

Provide a concise set of diagnostic figures or tables that allow a scientist to understand and inspect the available waveform/station dataset, representative event or phase detections, the resulting earthquake catalog, and important quality or uncertainty characteristics. Choose the diagnostics yourself based on the workflow you adopt.

### Final report

At completion, briefly summarize the actual data coverage processed; the workflow and tools selected; the main scientific methods and assumptions; the number of phase observations obtained; the number of candidate events identified and successfully located; major data or methodological limitations; important quality concerns; and where the reproducible code, picks, locations, catalog and diagnostic outputs are stored.

Do not present incomplete or failed processing as a completed catalog.
