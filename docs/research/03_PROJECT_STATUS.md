# Assessing the Capabilities and Limitations of General-Purpose Agents in Seismological Workflows

## Current project status

| Stage | Current state | Boundary |
|---|---|---|
| Ridgecrest data preparation | Waveform data and StationXML metadata are prepared in the external data store. The case input currently exposes the read-only `waveforms/` root, including `data/` and `stations/`. | Fault traces and remote-sensing DEM are not yet formal task inputs. They must be added as separately documented resources before an Agent may use them. |
| Agent execution environment | A Codex CLI path is available through the framework. Authentication is resolved from an external profile, each run receives its own work root and input view, execution metadata is recorded, and evaluation is performed after execution. | The active host-direct backend is trusted development execution. Bubblewrap isolation is unavailable on the current host, so this is not yet a formally isolated evaluation backend. |
| Preliminary baseline tests | The framework has a deterministic catalog baseline and a separate Ridgecrest phase-picking workflow test. Task loading, input mapping, execution records, artifact handling and the regression suite are implemented. | The deterministic baseline is an infrastructure check, not a scientific catalog. A complete scientific score for detection, phase picking, association and location has not yet been frozen. |

## What is already established

1. **Data boundary** — source data remain outside Git and are linked read-only into
   a run-local `input/` directory. The Agent cannot modify the source tree.
2. **Execution boundary** — `run.sh` provides the task entry point; the framework
   controls the run directory, runtime environment, timeout and provenance.
3. **Task boundary** — `task.json` stores structured metadata, while
   `task_prompt.md` is the human-readable task specification and defines the
   expected scientific output.
4. **Baseline boundary** — `main.py` provides a deterministic output for testing
   the execution path. It is not used as evidence of scientific performance.
5. **Reference boundary** — published catalogs and the expert Ridgecrest workflow
   remain reference material; they are not silently treated as universal ground
   truth.

## Current limitations

- The current Ridgecrest task exposes waveforms and station metadata only. Fault
  geometry and DEM-derived information are prepared-data candidates, not active
  inputs.
- The current host-direct execution path records and controls runs but does not
  provide strong kernel-level isolation.
- The task prompt requires a candidate catalog and reproducibility evidence, but
  scientific scoring criteria for completeness, phase accuracy, association and
  location quality still need to be specified separately.
- The deterministic baseline does not perform PhaseNet picking, association,
  NonLinLoc location or double-difference relocation.

## Next bounded steps

1. Register fault traces and DEM as optional, versioned input resources only when
   their source, coverage and coordinate reference are documented.
2. Freeze the first external scientific scorer for catalog completeness and
   phase-pick quality without changing the execution contract.
3. Run the same task with the deterministic baseline and one real Agent, then
   compare artifact validity, provenance and scientific outputs separately.
4. Add stronger isolation only as an execution-backend change; do not mix it with
   task or catalog-method changes.
