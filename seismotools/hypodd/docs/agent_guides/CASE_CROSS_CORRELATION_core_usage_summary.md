# CASE_CROSS_CORRELATION Core Usage Summary

Use this case when waveform cross-correlation should contribute to HypoDD relocation. It describes the current `hypodd_runner` function API and should not be treated as a dataset-specific recipe.

## Workflow

1. Prepare valid `station.sta` and phase event-block input.
2. Call `run_fdtcc_relocation(...)` with grouped parameters.
3. The package runs `ph2dt` and writes `dt_*.ct`.
4. The package prepares FDTCC station/TTDB/waveform inputs and runs FDTCC, writing `dt_*.cc`.
5. The package runs HypoDD and merges native `.loc`, `.reloc`, `.pha`, and `.res` outputs.
6. Validate native outputs before interpreting plots or summaries.

Do not manually call native `ph2dt`, FDTCC, or `hypoDD` unless the task is explicitly low-level binary debugging.

## Minimal Call Pattern

```python
from hypodd_runner import (
    EventSelection, FDTCCParams, HypoDDInputs,
    HypoDDParams, Ph2dtParams, RuntimeOptions,
    run_fdtcc_relocation,
)

cfg = run_fdtcc_relocation(
    inputs=HypoDDInputs(hypo_root, phase_file, station_file, output_folder, catalog_code),
    selection=EventSelection(ot_range, lat_range, lon_range, dep_corr=dep_corr, phase_format="auto"),
    ph2dt=Ph2dtParams(maxdist=ph2dt_maxdist, maxoffset=ph2dt_maxoffset, minobs_pair=ph2dt_minobs_pair, maxobs_pair=ph2dt_maxobs_pair),
    hypodd=HypoDDParams(idata=2, iphase=hypodd_iphase, maxdist=hypodd_maxdist, iter_rows=iter_rows),
    fdtcc=FDTCCParams(
        waveform_dir_raw=waveform_dir_raw,
        wave_dir_mode=fdtcc_wave_dir_mode,
        velocity_layer=fdtcc_velocity_layer,
        velocity_vp=fdtcc_velocity_vp,
        velocity_vs=fdtcc_velocity_vs,
        flags=fdtcc_flags or {},
        prepare_inputs=True,
    ),
    runtime=RuntimeOptions(num_grids=num_grids, xy_pad=xy_pad, num_workers=num_workers, keep_grids=keep_grids),
)
```

## Input Requirements

- `hypo_root` must point to the compiled HYPODD root ending in `/src` in this environment.
- `phase_file` must parse to at least one event before bounds are applied.
- At least one parsed event must fall inside `ot_range`, `lat_range`, and `lon_range`.
- Station ids must be compatible across station file, phase file, and waveform metadata. Use real `NET.STA`, separate network/station columns, or `station_default_network` only when that network is known and matches waveform files.
- `waveform_dir_raw` must cover the event time span and station set.
- FDTCC travel-time table bounds must cover event depths and event-station distances.

## Cross-Correlation Rules

- `FDTCCParams.velocity_layer`, `velocity_vp`, and `velocity_vs` are for FDTCC travel-time tables.
- HypoDD relocation velocity is controlled separately by `HypoDDParams.mod_top`, `mod_vel`, and `mod_ratio`.
- If `dt_*.cc` is absent or empty, do not claim waveform CC was used. Inspect FDTCC stdout/stderr, station ids, waveform coverage, and FDTCC flags.
- Use `FDTCCParams(flags=fdtcc_flags or {})`; do not pass `flags=None`.
- For catalog+CC or CC-only runs, ensure `HypoDDParams.iter_rows` has positive CC weights and appropriate CC cutoffs.

## Full-Catalog Or Large-Scale Use

For large catalogs:

- compare event/station/observation counts with native limits before running;
- split by time, space, event count, or window only when needed, using the largest scientifically meaningful units that keep each native run below limits;
- keep per-window native outputs and logs;
- build a consolidated relocated catalog and failed/unrelocated-event table;
- label merged results as independent window/batch aggregates unless one global inversion was actually run.

## Failure Focus

- Empty `dt_*.ct`: check event bounds and phase parsing.
- Empty `dt_*.cc`: check waveform coverage, station ids, FDTCC flags, and FDTCC logs.
- Missing `.loc`: inspect `{i}-{j}.hypoDD` log before changing high-level workflow.
- `MAXEVE`/`MAXDATA` stops: use package-supported time/event windows or reduce link density/selection; do not invent config parameters.
