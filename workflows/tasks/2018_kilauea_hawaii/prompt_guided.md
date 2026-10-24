
## 2018 Kīlauea summit sequence monitoring (expert-guided)

### Task objective

Construct a scientifically credible and reproducible **candidate earthquake catalog for the 2018 Kīlauea summit earthquake sequence** using the waveform data and station metadata provided to this run.

You are responsible for determining an appropriate end-to-end seismological workflow from the available observations. The guidance below reflects established seismological practice; you may deviate from it when your data inspection justifies doing so, and must record the rationale.

### Input

The run-local input is available under:
```text
input/waveforms/
```

Waveforms are under `input/waveforms/data/` and station metadata under `input/waveforms/stations/`. Auxiliary files at the input root (for example waveform-inventory summaries) are part of the supplied observations and may be used.

Treat the entire `input/` directory as read-only.

The supplied waveform and station metadata are the scientific observations available for this task. Do not use an existing Kīlauea 2018 earthquake catalog, published phase picks, known event locations, or other reference earthquake products to construct or tune the catalog.

### Processing scope (fixed window)

Process the complete waveform collection inside the half-open window:
```text
[2018-05-01T00:00:00Z, 2018-05-09T00:00:00Z)
```

The daily waveform files are time-aligned to UTC days, so this window corresponds to the daily files dated 2018-05-01 through 2018-05-08. The supplied input may contain waveforms beyond the window; those files are out of scope. Process all stations and channels that have data in the window. Events outside the window must not be included in the reported catalog; you may read a small margin beyond the boundaries only where needed for correct filter startup or for events whose origin time lies inside the window.

The catalog reports events with origin time inside the window. Inspect and understand the supplied data before deciding how to process them; do not silently restrict to a subset of stations or channels.

### Tool policy

You may implement any method yourself and may install and use publicly available software and pretrained models from their official sources, provided they are not trained on, derived from, or specific to the 2018 Kīlauea summit sequence. Record the identity, version and source of every installed dependency or model in the provenance records.

### Suggested workflow structure

A complete catalog workflow normally chains the following stages. Implement each stage as a separately inspectable step with intermediate artifacts, so failures can be localized and reprocessing can start from the last completed stage.

1. **Data audit.** Build a station–channel–day inventory from the waveforms and station metadata: which channels exist, their sample rates, gaps, clips and instrumental response stages. Write the inventory as an intermediate artifact and use it, not ad-hoc file listing, to drive later stages.
2. **Preprocessing.** Demean, detrend, taper and filter consistently across stations; handle gaps explicitly rather than letting them silently corrupt filtering; decide and record how you treat different channel families and sample rates.
3. **Phase detection.** Produce per-channel candidate phase arrivals. Classical energy-ratio/STA-LTA detectors, matched-filtering approaches and learned pickers are all acceptable; whatever you choose, calibrate thresholds and record them. A deliberately sensitive initial setting with later network-level suppression of false triggers is a legitimate strategy.
4. **Association.** Group single-station or single-channel detections into candidate events using arrival-time consistency across stations. Coincidence-trigger and travel-time-consistency approaches are both acceptable; suppress duplicate origins from the same source aggressively.
5. **Location.** Locate associated events with a documented 1-D velocity model (a homogeneous half-space is acceptable as a first pass). Grid search or linearized inversion are both acceptable. Record residuals, root-mean-square travel-time residual, azimuthal gap and the number of stations used per event; these belong in the QC record, not only in internal logs.
6. **Magnitude.** Estimate magnitudes only when defensible: local magnitude via simulated Wood-Anderson displacement, duration magnitude, or relative-amplitude measures are all acceptable. Document the calibration assumptions; leave `magnitude` empty rather than publishing an unsupported value.
7. **Quality control and reporting.** Apply explicit acceptance criteria and encode them in the `status` column rather than dropping rows silently.

**Quality-control gates.** Before finalizing, check at minimum: pick residual distributions per station; per-station-day detection rates (a station dropping to zero detections usually means a processing fault, not seismology); P/S pick balance per event; duplicate-origin rate; and spatial clustering of solutions (unphysical lineations often indicate association or velocity-model artifacts).

**Tuning discipline.** Tune thresholds and parameters on a small declared development subset, then apply the frozen configuration to the complete window; record the frozen values. Do not iterate parameters against the complete dataset.

### Workflow discipline

Before substantial processing, briefly document the planned workflow and the rationale for the major scientific decisions. You may revise the workflow when intermediate results indicate changes are needed; record significant revisions and their rationale.

The run budget is finite and may end earlier than expected. Refresh `picks.csv`, `catalog.csv` and `report.md` at defined checkpoints (for example after each processing day or stage) so that partial progress survives an interruption, rather than writing all outputs only at the end.

### Reproducibility

The workflow must be executed and reproducible from the supplied inputs.

Preserve sufficient code, configuration, and provenance under the assigned output directory so that the processing can be rerun and the origin of the final catalog can be understood.

Ensure the declared window is fully covered, including when processing is performed in multiple batches or partitions.

### Required scientific outputs

At minimum, provide machine-readable phase observations in `picks.csv`, a candidate-earthquake catalog in `catalog.csv`, and a final report in `report.md`.

`picks.csv` — one row per phase observation, header row exactly:
```text
pick_id,event_id,station_id,channel_id,phase,time_utc,probability,uncertainty_s,method,status
```

`catalog.csv` — one row per candidate event, header row exactly:
```text
event_id,origin_time_utc,latitude,longitude,depth_km,magnitude,magnitude_type,n_picks,n_p_picks,n_s_picks,status
```

Field conventions:

- CSV dialect: UTF-8, comma-separated, the header row above in exactly this order, one record per row, the empty string for unavailable fields, no units inside cells.
- `station_id` is `NET.STA` (for example `HV.RIMD`). `channel_id` is the full SEED channel `NET.STA.LOC.CHA` with an empty location code written as an empty segment (for example `HV.RIMD..HHE`, whose location code is empty; `XX.ABC.00.HNE` when it is not).
- `phase` is `P` or `S`. `time_utc` and `origin_time_utc` are ISO 8601 UTC timestamps ending in `Z` or `+00:00`.
- `probability` is a detector-assigned quality score in [0, 1]; document its semantics in the metadata file; it may be empty. `uncertainty_s` is a pick-time uncertainty in seconds; it may be empty.
- `status` is `accepted`, `uncertain` or `rejected` — the producer's verdict on that row. Keep rejected rows in the files for auditability. An empty `event_id` marks an unassociated pick.
- `latitude` and `longitude` are decimal degrees (WGS84). `depth_km` is positive downward; document the depth datum used in the metadata file; it may be empty when depth is not resolvable.
- `magnitude` may be empty when not defensible; `magnitude_type` is a short code such as `ML`, `Md`, `Mw` or `M`; document the derivation.
- `n_picks`, `n_p_picks` and `n_s_picks` count the non-rejected `picks.csv` rows for that event and must be consistent with them.
- Record the velocity model, location method, uncertainty estimates, depth datum, probability semantics and other diagnostic quantities in a metadata file of your choosing, referenced from `report.md`.

Fields that cannot be estimated defensibly may be empty and must not be fabricated. The final catalog must be traceable to the observational evidence used to construct it.

### Inspection and visualization

Provide a concise set of diagnostic figures or tables that allow a scientist to understand and inspect:
- the available waveform/station dataset;
- representative event or phase detections;
- the resulting earthquake catalog;
- important quality or uncertainty characteristics of the result.

Choose the diagnostics yourself based on what is scientifically useful for the workflow you adopt.

### Final report

Summarize in `report.md`:
- the window coverage actually processed;
- the workflow you selected and its main scientific methods and assumptions;
- the number of phase observations obtained and candidate events identified and located;
- the quality-control checks you ran and their outcomes;
- major data or methodological limitations and important quality concerns;
- where the reproducible code, picks, catalog and diagnostic outputs are stored.

Do not present incomplete or failed processing as a completed catalog.
