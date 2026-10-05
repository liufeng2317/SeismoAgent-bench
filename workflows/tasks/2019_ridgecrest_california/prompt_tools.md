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

Local seismological software, model files, documentation and executables are available under the project `seismotools` directory. You may inspect these resources and use any of them when scientifically appropriate. Their availability does not imply that every tool should be used, or that they define a required workflow.

Available resources include:
- **PhaseNet:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/phase_picking/`
- **GaMMA:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/gamma/`
- **NonLinLoc:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/nonlinloc/`
- **hypoDD:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/hypodd/`
- **General scientific Python:** the configured environment includes commonly used scientific and seismological Python packages.

You may inspect the source code, documentation, model metadata, example interfaces and executables provided with these tools in order to determine whether and how they should be used.

Tool resources are methodological references, not scientific observations for this case. The waveform data and station metadata under the declared `input/` directory are the case-specific observations available for constructing the catalog.

Do not use existing Ridgecrest catalogs, published phase picks, reference event locations, expert workflow outputs, or other case-specific observational products to construct or tune the result. General seismological knowledge and generic methodological assumptions or models may be used when needed, but any consequential choices must be independently justified from the task and available observations.

Do not modify shared tool sources, model weights, binaries, or the evaluation environment. Record sufficient information to identify and reproduce any tools actually used.

### Scientific task

Independently design and execute an appropriate workflow to construct the earthquake catalog from the supplied waveform observations and station metadata.

You are responsible for determining the scientific methods, software, models, parameters, and quality-control procedures needed to complete the task. Base these choices on the characteristics of the available data and established seismological practice. Before substantial processing, briefly document the planned workflow and the rationale for the major scientific decisions. You may revise the workflow when intermediate results indicate that changes are needed; record significant revisions and their rationale.

### Reproducibility

The workflow must be executed and reproducible from the supplied inputs. Preserve sufficient code, configuration, tool versions, commands and provenance under the assigned output directory so that the processing can be rerun and the origin of the final catalog can be understood. Ensure that the complete usable dataset is covered, including when processing is performed in multiple batches or partitions.

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
