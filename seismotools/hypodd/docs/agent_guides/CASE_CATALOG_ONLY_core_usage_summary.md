# CASE_CATALOG_ONLY Core Usage Summary

Use this case for HypoDD relocation without waveform cross-correlation. It is the preferred baseline/debug mode when waveform coverage or FDTCC settings are not part of the task.

## Workflow

1. Prepare valid `station.sta` and phase event-block input.
2. Call `run_catalog_only_relocation(...)` with grouped parameters.
3. The package runs `ph2dt` and writes catalog differential times `dt_*.ct`.
4. The package runs HypoDD in catalog-only mode.
5. Validate non-empty native outputs before plotting or reporting success.

Do not manually call native `ph2dt` or `hypoDD` unless the task explicitly asks for low-level binary debugging.

## Minimal Call Pattern

```python
from hypodd_runner import (
    EventSelection, HypoDDInputs, HypoDDParams,
    Ph2dtParams, RuntimeOptions, run_catalog_only_relocation,
)

result = run_catalog_only_relocation(
    inputs=HypoDDInputs(hypo_root, phase_file, station_file, output_folder, catalog_code),
    selection=EventSelection(ot_range, lat_range, lon_range, dep_corr=dep_corr, phase_format="auto"),
    ph2dt=Ph2dtParams(maxdist=ph2dt_maxdist, maxoffset=ph2dt_maxoffset, minobs_pair=ph2dt_minobs_pair, maxobs_pair=ph2dt_maxobs_pair),
    hypodd=HypoDDParams(iphase=hypodd_iphase, maxdist=hypodd_maxdist, iter_rows=iter_rows),
    runtime=RuntimeOptions(num_grids=num_grids, xy_pad=xy_pad, num_workers=num_workers, keep_grids=keep_grids),
)
```

## Input Requirements

- `hypo_root` must point to the compiled HYPODD root ending in `/src` in this environment.
- `phase_file` must parse to at least one event.
- At least one parsed event must fall inside `ot_range`, `lat_range`, and `lon_range`.
- `station_file` and phase station ids must be consistent.
- Waveform paths, FDTCC velocity arrays, and `dt_*.cc` are not required.

When the source data are not already `phase.dat`/`station.sta`, prepare them first:

```python
from hypodd_runner import build_hypodd_inputs

prepared = build_hypodd_inputs(
    events_csv=events_csv,
    picks_csv=picks_csv,
    stations_csv=stations_csv,
    output_dir=prepared_input_dir,
)
phase_file = prepared.phase_path
station_file = prepared.station_path
```

Use this helper for simple event/pick/station tables. For rawer inputs, normalize into those three tables first and record a preparation manifest with source paths, column mappings, counts, missing station references, duplicate event ids, and generated file paths. Preserve real pick times; do not replace picks with `-1` except for genuinely missing arrivals.

## Scientific Controls

- `Ph2dtParams` controls the catalog differential-time link graph. Choose it from event-station geometry, event spacing, phase quality, and native data limits. Too strict can produce empty/sparse `dt_*.ct`; too loose can exceed `MAXDATA` or degrade quality.
- `HypoDDParams.iter_rows` controls cumulative iteration endpoints, catalog weights/cutoffs, and damping. Choose it for the current study from station geometry, event-window size, link density, phase quality, and residual behavior; do not use `iter_rows=None` or smoke-test rows for scientific output just because they are defaults.
- Treat damping and link-threshold comparisons as bounded diagnostics. If multiple `DAMP`, `iter_rows`, or ph2dt settings are being evaluated, run them on a documented subset such as a representative dense window, sparse window, or previously failed window. After selecting the parameter set, run one full-catalog production relocation. Do not run multiple full-catalog candidates unless the user explicitly approves the computational cost.
- `HypoDDParams.mod_top`, `mod_vel`, and `mod_ratio` optionally define the HypoDD 1D velocity model. HypoDD uses layer `Vp` and a global `Vp/Vs` ratio.
- `dep_corr` should be defined from the current catalog depth convention.

## Large-Catalog Use

If the current catalog may exceed native limits, prefer the package large-catalog helper instead of hand-writing batch loops:

```python
from hypodd_runner import run_catalog_only_auto_time_windows

result = run_catalog_only_auto_time_windows(
    inputs=inputs,
    selection=selection,
    ph2dt=ph2dt,
    hypodd=hypodd,
    runtime=runtime,
    base="month",              # start coarse; shrink only if a month exceeds limits
    min_events_per_window=300,  # merge sparse neighboring windows
    max_events_per_window=None, # default: read active MAXEVE from hypoDD.inc
    window_prefix="catwin",
    continue_on_error=False,  # fail-fast: stop at the first failed non-empty window
    verbose=False,            # keep per-window details in manifest, not task log
)
```

This helper plans independent time/event windows from the original phase file and writes status/manifest evidence plus consolidated outputs. Use the largest scientifically meaningful windows that stay below native limits; do not split a six-month catalog into daily windows just because the full six-month selection is too large. Start with monthly/default windows, let sparse windows merge through `min_events_per_window`, and shrink to daily/fixed-day windows only when a coarser planned window itself exceeds `MAXEVE`, `MAXDATA`, or other native evidence limits. With `continue_on_error=False`, the first failed non-empty window writes traceback/status/manifest evidence and stops the run; inspect and fix that failure before rerunning. Keep `verbose=False` for agent/task runs so per-window details go to `time_window_manifest.json` rather than flooding the execution log. Use a custom per-window loop only when the package helper cannot express the required scientific split. A full-catalog product should include a manifest, consolidated relocated catalog, failed/unrelocated-event table, and global figures.

Window-level execution is currently sequential. If using lower-level time-window helpers, keep `num_window_workers=1`; use `RuntimeOptions.num_workers` only for work inside each native run.

Do not use the auto-window helper as a parameter-sweep engine by default. For damping or link-density screening, call it only on a limited diagnostic time/event range or a small set of windows. The production full-catalog auto-window run should use the chosen final parameters.

## Failure Focus

- Empty `dt_*.ct`: check event bounds, phase parsing, and ph2dt link parameters.
- Missing `.loc`: inspect `{i}-{j}.hypoDD` log first.
- Empty `.reloc` or `failure_kind=empty_native_output`: inspect the failed window's `failure_traceback.txt`, native `.hypoDD`/`ph2dt` logs, `dt_*.ct`, `.inp`, `.loc`, `.reloc`, `.src`, and `.sta` first. Do not reduce events or tune parameters from empty `.reloc` alone.
- `MAXEVE` stop: use `run_catalog_only_auto_time_windows(...)`, reduce the selection, or rebuild native HypoDD explicitly.
- `MAXDATA` stop: reduce link density or use package-supported time/event windows.
- Missing waveform data is not a catalog-only failure.

## Parameter Ranges Are Starting Points, Not Defaults

Common catalog-only first-pass ranges must be adapted to the research setting:

- `ph2dt.maxdist`: choose from useful event-station distances and station coverage, not from a fixed example; many local/regional first passes fall somewhere in the tens to hundreds of km.
- `ph2dt.maxoffset`: choose from event spacing and target cluster scale; smaller for dense local clusters, larger for broader regional windows.
- `ph2dt.minobs_pair`: raise for quality, lower only when the link graph is too sparse.
- `ph2dt.maxobs_pair`: reduce if `MAXDATA` or run time becomes excessive; increase only when enough high-quality common picks justify it.
- `hypodd.maxdist`: choose from the same event-station geometry used to justify `ph2dt.maxdist`, and verify station counts in the native log.
- `HypoDDParams.iter_rows`: total cumulative endpoints often end near `8-20` for first scientific runs, but tune `WTCTP/WTCTS`, `WRCT`, `WDCT`, and `DAMP` from native residuals, link distances, condition numbers, air-quake counts, and relocation shifts. Regional or weakly conditioned windows may need damping in the tens to hundreds; this is not a universal default. Compare candidate schedules on representative subsets first, then run the selected schedule on the full catalog.
