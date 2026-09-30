
# Ridgecrest Earthquake Catalog: Expert Workflow Plan

## Objective and scope

Build a traceable, reproducible earthquake catalog from raw continuous waveforms and station metadata through phase picking, association, location, and quality control. The workflow will serve as an expert reference for subsequent agent evaluation, not as unique ground truth.

- **Window:** 2019-07-04 00:00:00 to 2019-07-07 00:00:00 UTC, end exclusive.
- **Inputs:** the currently prepared 41 stations, 117 channels, and corresponding StationXML; freeze the actual file and channel selection before execution.
- **Event region:** latitude 35.45–36.05°, longitude −117.90–−117.20°. Allow margins for association and location; do not restrict station selection to this region.
- **Reference catalogs:** use published catalogs for comparison. Any use of their templates, seed events, or picks belongs to a separate catalog-assisted experiment.

## Current phase

The initial full baseline is complete as provisional v1 in `export/01_baseline/10_validate_catalog/`. Stages 11–20 are comparison, local relocation and diagnostic branches, not successive full-catalog versions. The active objective is to improve and validate absolute location accuracy before publishing another full version. Broad parameter scanning is closed. The fixed station-phase correction experiment is complete (stage 17). It improves withheld timing and horizontal reference agreement but worsens compatible depth agreement, failing its adoption gate. Preserve it as an experimental result; resolve depth/model constraints before another adoption test. Stage 18 explains the shift through correction/depth coupling, but does not identify the physical source of the influential S residuals. The bounded stage-19 waveform review is complete and does not support systematic large late picking in its fixed sample. Retain observations and focus the next bounded intervention on velocity/path and depth constraints. Stage 20 now implements a controlled HK profile experiment under an explicit common +0.7-km ASL depth plane, holding observations and other settings fixed. Its four 147-event branches compare full-data locations and withheld-arrival prediction; model qualification is only an input note. Native SCSN datum reproduction is not claimed. Consult the experiment report for the outcome; no full v2 has been produced.

See [the evolution and organization plan](docs/EVOLUTION.md) for branch status, adoption gates and the current code layout. Scripts and configuration have moved into numbered responsibility groups; existing output paths remain unchanged.

## Existing implementation layout and baseline

Python entry points are grouped under `01_pipeline/`, `02_diagnostics/`, `03_experiments/` and `04_comparison/`; shared YAML lives in `00_config/`. Scripts resolve the expert root independently of their working directory. Outputs remain under the existing `export/<step>/` paths, and documents remain under `docs/`. Retain outputs until explicitly cleaned up.

The first baseline is **PhaseNet picking → GaMMA association and initial locations → NonLinLoc absolute locations**. Start with the local PhaseNet `original` v2 weights, subject to compatibility and inference validation. Use arrival times only for initial GaMMA association; magnitude processing is a separate stage. Preserve common pick/event interfaces so additional absolute-location methods can be compared later. See [README.md](README.md) for step names, implementation status and local dependency findings.

## Workflow

| Stage                       | Main work                                                                                                                                                                                                                                                                                             | Output                                                     |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 1. Fix inputs               | Reuse existing coverage and response checks; confirm channels, orientations, epochs, and gaps. Preserve raw waveforms.                                                                                                                                                                                | Input selection and file versions                          |
| 2. Define processing        | Trial pre-event, mainshock, and coda windows. Select detrending, filtering, normalization, chunking, and buffers according to picker requirements; correct instrument responses separately for physical-amplitude analysis.                                                                           | Processing configuration and short-window validation       |
| 3. Pick phases              | Extract P/S arrival times and confidence information throughout the three days. Handle overlapping chunks and preserve gaps; do not synthesize horizontal components for vertical-only stations.                                                                                                      | Standardized phase-pick table                              |
| 4. Associate and locate     | Select a baseline from the available 1-D velocity models; document the model, depth datum, and travel-time settings. Associate picks and estimate initial event locations.                                                                                                                            | Initial catalog and event–pick associations               |
| 5. Control location quality | Check travel-time residuals, station geometry, pick counts, depth boundaries, and duplicate events. Review outlier picks iteratively and record retention or rejection reasons.                                                                                                                       | Quality-controlled location catalog                        |
| 6. Estimate magnitudes      | Document the magnitude relation and applicability. Use valid response-corrected amplitudes, checking saturation and station consistency. Leave unreliable estimates missing with reasons.                                                                                                             | Magnitudes, contributing station counts, and quality flags |
| 7. Validate results         | Use an initial Shelly/Liu/official comparison during location-quality review; later validate the finalized product against applicable reference catalogs, including Ross. Examine pre/post-mainshock, dense-event, and coda periods; review representative apparent misses and additional detections. | Comparison results and explanations of major differences   |
| 8. Finalize                 | Fix configurations, code, and execution records; verify reproducibility and summarize limitations.                                                                                                                                                                                                    | First expert catalog and concise report                    |

## Execution principles

- Complete a short-window end-to-end trial before processing all three days. Do not expand general-purpose data screening.
- Response removal and filtering cannot repair saturation. Handle suspect intervals according to their intended use; do not discard an entire station because of a local anomaly.
- Set picking and association parameters on development windows before examining the remaining periods. Agreement with reference catalogs is not the sole tuning objective.
- Unmatched reference events are not automatically misses or false detections. Interpret depth datums and magnitude types separately.
- Differential travel times and relative relocation are optional second-stage enhancements, not requirements for the first catalog.

## Deliverables

1. **Event catalog:** event ID, UTC origin time, latitude, longitude, depth and datum, magnitude and type, station/pick counts, residuals, uncertainties where estimable, and quality flags.
2. **Phase table:** event ID, station/channel, P/S type, arrival time, confidence information, location residual, and usage status.
3. **Reproducibility materials:** input versions, processing configuration, execution code, and a concise results report. Keep expert-workflow materials in this directory, separate from agent-visible inputs.

The first version is complete when the three-day workflow runs successfully, events and picks are traceable, results are reproducible, and major differences and limitations are documented. Maximizing event counts or exactly reproducing a published catalog is not a completion criterion.

Stage-20 outcome: HK reduces withheld RMS by 11.1% and improves horizontal reference agreement, but increases the Shelly depth discrepancy by 29.9% and p90 posterior depth sigma by 11.3%. It fails promotion; retain v1 and close this fixed trial.
