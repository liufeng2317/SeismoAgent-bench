
## 2019 Ridgecrest sequence monitoring (base, public ecosystem)

### Task objective

Construct a scientifically credible and reproducible **candidate earthquake catalog for the 2019 Ridgecrest sequence** using the waveform data and station metadata provided to this run.

You are responsible for determining an appropriate end-to-end seismological workflow from the available observations.

### Input

The run-local input is available under:
```text
input/waveforms/
```

Waveforms are under `input/waveforms/data/` and station metadata under `input/waveforms/stations/`. Auxiliary files at the input root (for example waveform-inventory summaries) are part of the supplied observations and may be used.

Treat the entire `input/` directory as read-only.

The supplied waveform and station metadata are the scientific observations available for this task. Do not use an existing Ridgecrest earthquake catalog, published phase picks, known event locations, or other reference earthquake products to construct or tune the catalog.

### Processing scope

The task covers the complete usable waveform collection in the declared input. Inspect and understand the supplied data before deciding how to process them.

Partial-coverage ruling: if the available compute or time budget does not allow the complete collection to be processed, work in strict chronological order starting from the earliest available data, keep the output artifacts current as processing advances, and report the achieved coverage honestly in the final report. Incomplete coverage is a reported outcome, not a contract violation; silently skipping data is.

### Tool policy (public ecosystem)

You are encouraged to build on the public scientific software ecosystem: install published seismological packages, pretrained picking/association models and open workflows from their official sources, and combine them with your own processing. The only restriction is provenance integrity: nothing you use may be trained on, derived from, or specific to the Ridgecrest sequence. Record for every installed dependency and model its identity, version, source URL and (for downloaded weights) a content hash, so the exact toolchain can be reconstructed. Verify that third-party model outputs (pick times, associations) actually correspond to the supplied waveforms before trusting them at scale.

### Workflow discipline

Before substantial processing, briefly document the planned workflow and the rationale for the major scientific decisions. You may revise the workflow when intermediate results indicate changes are needed; record significant revisions and their rationale.

The run budget is finite and may end earlier than expected. Refresh `picks.csv`, `catalog.csv` and `report.md` at defined checkpoints so that partial progress survives an interruption, rather than writing all outputs only at the end.

### Reproducibility

The workflow must be executed and reproducible from the supplied inputs.

Preserve sufficient code, configuration, and provenance under the assigned output directory so that the processing can be rerun and the origin of the final catalog can be understood. Third-party software installed during the run must be recorded precisely enough to reinstall the same versions.

Ensure the declared processing scope is fully covered, including when processing is performed in multiple batches or partitions.

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
- `station_id` is `NET.STA` (for example `CI.APL`). `channel_id` is the full SEED channel `NET.STA.LOC.CHA` with an empty location code written as an empty segment (for example `CI.APL..HNE`).
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
- the actual data coverage processed;
- the workflow you selected, its main scientific methods and assumptions, and the third-party components used with their provenance;
- the number of phase observations obtained and candidate events identified and located;
- major data or methodological limitations and important quality concerns;
- where the reproducible code, picks, catalog and diagnostic outputs are stored.

Do not present incomplete or failed processing as a completed catalog.
