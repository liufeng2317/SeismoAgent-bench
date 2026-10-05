## 2019 Ridgecrest sequence monitoring

### Task objective

Construct a scientifically credible and reproducible **windowed candidate earthquake catalog for the 2019 Ridgecrest sequence** using the waveform data and station metadata provided to this run.

You are responsible for determining an appropriate end-to-end seismological workflow from the available observations.

This first tools-enabled run uses the fixed half-open UTC window `[2019-07-04T17:23:49Z, 2019-07-04T17:43:49Z)`, centered on the Mw 6.4 mainshock at `2019-07-04T17:33:49Z`. Process all usable waveform files, stations and available components that overlap this window. Do not reduce the window or silently select a subset of stations for convenience. This is a windowed tool-chain validation and must not be presented as a complete catalog for the full Ridgecrest sequence.

### Input

The run-local input is available under:
```text
input/waveforms/
```

Waveforms are under `input/waveforms/data/` and station metadata are under `input/waveforms/stations/`. Treat the entire `input/` directory as read-only.

The supplied waveform and station metadata are the scientific observations available for this task. Do not use an existing Ridgecrest earthquake catalog, published phase picks, known event locations, or other reference earthquake products to construct or tune the catalog.

### Available tools

This tools-enabled task evaluates whether the Agent can apply the supplied seismological software to the complete selected validation window. The main processing stages are fixed by the workflow below, while the Agent may choose preprocessing parameters, model settings and quality-control rules. The supplied tools are the preferred scientific implementations for their corresponding stages; a simpler custom implementation must not silently replace them.

#### Tool resources

The project provides source code, documentation, model files and executable interfaces at these locations:

- **PhaseNet:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/phase_picking/`
- **GaMMA:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/gamma/`
- **NonLinLoc:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/nonlinloc/`
- **hypoDD:** `/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/hypodd/`
- **General scientific Python:** the configured environment includes commonly used scientific and seismological Python packages.

Inspect the supplied documentation, model metadata, examples and executable interfaces to determine how to invoke the required stages. Do not modify the shared tool directories, model weights, binaries or evaluation environment.

#### Required and optional processing path

Attempt the first three stages in order and process the complete usable input within the fixed window, including batches or partitions:

1. Use **PhaseNet** (or its supplied command-line/API interface) for neural-network P and S phase picking on the waveform data in the selected window. Do not replace the full-window picking stage with a simple amplitude threshold, STA/LTA detector or custom peak finder unless PhaseNet has been tested and a documented execution failure prevents its use.
2. Use **GaMMA** to associate the resulting phase picks into candidate events. Preserve the association parameters and the input/output file locations.
3. Use **NonLinLoc** for absolute event location with an explicit velocity model.
4. After absolute locations are available, **hypoDD** may be used as an additional relative-relocation stage when sufficient differential-pick support exists. If it is used, generate or verify the catalog differential-time input with `ph2dt` before running hypoDD, and state whether the final catalog contains absolute locations, relative locations, or both. If it is not used, record the reason and retain the absolute-location catalog as the final location product.

The Agent may add transparent preprocessing and quality-control steps around this path. It must state the selected parameters and explain any change to the order or scope of the stages. Before substantial processing, document the planned workflow, tool interfaces and major scientific decisions. Record significant revisions and report any files or intervals that could not be processed. The first three stages are mandatory for this task; a custom detector, association method or locator cannot be substituted for them.

#### Repair loop and provenance

If a required stage fails, diagnose the error and repair the run-local code, control files or configuration, then rerun the failed stage. Allow at most 20 repair attempts for the complete required tool chain. For every attempt, record the attempt number, error, diagnosis, change made and rerun result. A help or no-argument invocation does not count as a completed tool stage; NonLinLoc must be run with generated control files, velocity/travel-time grids and event observations.

The Agent may stop before 20 attempts when all mandatory stages succeed. If the repair limit is reached, mark the run as failed or incomplete, preserve the partial outputs and diagnostics, and explain the unresolved error. Do not substitute a custom method, skip a mandatory stage or present an upstream partial catalog as the final result. The repair loop must not modify the shared tool directories, model weights, binaries, input observations or evaluation environment. Record the tools actually executed, their versions, commands, configurations, logs and output locations. Tool resources are methodological references; the waveform data and station metadata under `input/` are the only case-specific observations for constructing the catalog.

Do not use existing Ridgecrest catalogs, published phase picks, reference event locations, expert workflow outputs or other case-specific observational products to construct or tune the result. Ridgecrest files bundled inside tool examples are also reference examples only: they may be inspected to understand an interface, but must not be copied as case inputs, used to tune parameters, or merged into the output. General seismological knowledge and generic methodological assumptions or models may be used when needed, but consequential choices must be justified from the task and available observations.

### Reproducibility

The workflow must be executed and reproducible from the supplied inputs. Preserve sufficient code, configuration, tool versions, commands, tool logs and provenance under the assigned output directory so that the processing can be rerun and the origin of the final catalog can be understood. Record which supplied tools were actually executed, not only which tools were inspected. Ensure that the complete usable data within the fixed window is covered, including when processing is performed in multiple batches or partitions.

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

At completion, briefly summarize the actual data coverage processed within the fixed window; the workflow and tools selected; the main scientific methods and assumptions; the number of phase observations obtained; the number of candidate events identified and successfully located; major data or methodological limitations; important quality concerns; and where the reproducible code, picks, locations, catalog and diagnostic outputs are stored. State explicitly that the result is a windowed validation product rather than a full-sequence catalog.

Do not present incomplete or failed processing as a completed catalog.
