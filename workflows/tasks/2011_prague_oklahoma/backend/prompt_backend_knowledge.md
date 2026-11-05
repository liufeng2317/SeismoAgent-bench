## 2011 Prague, Oklahoma sequence monitoring (back end, expert tools, catalog checker and knowledge)

### Objective

Phase picks and their association to events are given for the 2011 Prague, Oklahoma sequence. Using them, the supplied waveform data and station metadata, complete the earthquake catalog: locate every event, add relative relocations where the data support them, and compute magnitudes.

The run-local input is available under `input/`: `input/waveforms/` (`data/` for waveforms, `stations/` for station metadata) and `input/frontend/` (`picks.csv` with the association in `event_id`, `events.csv` listing the events, `README.md`).

Process the half-open window `[2011-11-11T00:00:00Z, 2011-11-19T00:00:00Z)`; the catalog reports events with origin time inside it.

The picks are fixed: do not add picks or change pick times. You may reject picks (status `rejected`, kept in the file) and reject events (status `rejected`); every submitted pick keeps its `pick_id`, and every event keeps its `event_id`.

### Tools

The tools base directory is TOOLS_BASE_PATH=`/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismotools/`. The supplied implementations may be used through their standard execution paths. Before calling a tool, read its README, the relevant guidance under its `docs/` directory and the validated executable examples under its `examples/` directory, and use those materials to determine the method, parameters, input preparation and output interpretation.

1. Absolute location: NonLinLoc and HypoInverse produce absolute locations using an explicit velocity model. NonLinLoc is a probabilistic grid search with selectable likelihood methods (`GAU_ANALYTIC`, `EDT`, `EDT_OT_WT`) and has a single-event and a catalog interface; HypoInverse is a linearised locator with distance and residual weighting. Tool resources and documentation are under `TOOLS_BASE_PATH/nonlinloc/` and `TOOLS_BASE_PATH/hypoinverse/`.
2. Relative relocation: hypoDD and GrowClust produce relative locations when the associated events and differential times provide adequate support; waveform cross-correlation differential times can be measured with ccdt. This is an additional result, not a substitute for absolute locations. Tool resources and documentation are under `TOOLS_BASE_PATH/hypodd/`, `TOOLS_BASE_PATH/growclust/` and `TOOLS_BASE_PATH/cross_correlation/`.
3. Magnitudes are computed from the waveforms and the station metadata (instrument responses in the StationXML); no dedicated magnitude tool is provided.

### Catalog checker and knowledge

A reference-free catalog checker is provided at CHECKER_PATH=`/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/SeismoAgentBench/seismo_checker/`. Two skills are under `input/agent_resource/skills/`; read each `SKILL.md` before you start and the files it points to when they apply:

- `catalog-checker/SKILL.md`: what the checker measures, when to run it, and what the output contract requires (the checker report on the submitted products and a disposition for every flag);
- `catalog-knowledge/SKILL.md`: how to test on a pilot batch before the full run, how to decide between two candidate products, what each checker symptom can mean and which experiment separates the causes, and which errors no check can see.

`input/agent_resource/magnitude/` holds the local-magnitude formulas with their units, a reference implementation and a library of regional calibrations.

### Required outputs

Write the following machine-readable files under the output directory (two of them are described in the catalog-checker skill).

`picks.csv` — one row per phase observation, header row exactly:
```text
pick_id,event_id,station_id,channel_id,phase,time_utc,probability,uncertainty_s,method,status
```

`catalog.csv` — one row per candidate earthquake, header row exactly:
```text
event_id,origin_time_utc,latitude,longitude,depth_km,magnitude,magnitude_type,n_picks,n_p_picks,n_s_picks,status
```

Field conventions:

- UTF-8, comma-separated, the header rows above in exactly this order (followed only by the optional columns below); the empty string for unavailable fields; no units inside cells.
- `station_id` is `NET.STA` (for example `GS.OK021`). `channel_id` is the full SEED channel `NET.STA.LOC.CHA` with an empty location code written as an empty segment (for example `GS.OK021.00.HHE`, or `XX.ABC..HNE` when the location code is empty).
- `phase` is `P` or `S`. `time_utc` and `origin_time_utc` are ISO 8601 UTC timestamps ending in `Z` or `+00:00`.
- `probability` is a detector-assigned quality score in [0, 1]; `uncertainty_s` is a pick-time uncertainty in seconds; both may be empty.
- `event_id` must match between the two files; an empty `event_id` marks an unassociated pick.
- `status` is `accepted`, `uncertain` or `rejected`; keep rejected rows in the files (they are not scored).
- `latitude` and `longitude` are decimal degrees (WGS84). `depth_km` is kilometres below sea level, positive down; it may be empty when depth is not resolvable.
- `magnitude` may be empty; `magnitude_type` is a short code such as `ML`, `Md`, `Mw` or `M`.
- `n_picks`, `n_p_picks` and `n_s_picks` count the non-rejected `picks.csv` rows of the event.
- `catalog.csv` may add, after the columns above, `horizontal_uncertainty_km`, `depth_uncertainty_km` and `origin_time_uncertainty_s` (1σ; may be empty).
- `picks.csv` may add, after the columns above, `residual_s`: the locator's arrival-time residual (observed minus predicted, seconds; may be empty). When the locator reports uncertainties and residuals, copy them into these optional columns.

`checker/final/checker_report.json` and `checker/dispositions.json` — as described in the catalog-checker skill.


### Validity conditions

- Do not use existing Prague 2011 earthquake catalogs, published phase picks, known event locations, or other reference earthquake products to construct or tune the result.
- Do not fabricate values; leave a field empty when it cannot be defensibly estimated.
- Do not modify the input directory, or the shared tools, weights, binaries or the evaluation environment.
- Files inside generic tool examples may be read only to understand documented usage; do not use them as case observations.
