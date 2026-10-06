# Package Contract Card: hypodd_runner

This card has higher priority than case examples. Use it as the compact contract for every retrieved `hypodd_runner` example.

## Public API

- Package name: `hypodd_runner`.
- Build task scripts around public Python functions and grouped parameter objects.
- Common groups: `HypoDDInputs`, `EventSelection`, `Ph2dtParams`, `HypoDDParams`, and `RuntimeOptions`.
- Add `FDTCCParams` when waveform cross-correlation is used.
- Add `CCOnlyWindowParams` when a CC-only catalog should be split into time windows automatically.
- In this environment, set `hypo_root="seismotools/hypodd/runtime"`. It must contain `ph2dt/ph2dt` and `hypoDD/hypoDD`.
- Native `ph2dt`, FDTCC, and `hypoDD` are executed inside the package; keep native logs and Python exceptions as run evidence.

Typical imports:

```python
from hypodd_runner import (
    HypoDDInputs, EventSelection, Ph2dtParams,
    HypoDDParams, FDTCCParams, RuntimeOptions,
    CCOnlyWindowParams,
)
```

## Mode Selection

- Catalog-only relocation: `run_catalog_only_relocation(...)` for one small/valid selection; `run_catalog_only_auto_time_windows(...)` for larger catalogs that may exceed native limits.
- Catalog plus waveform CC: `run_fdtcc_relocation(...)`. Runs `ph2dt`, FDTCC, then HypoDD. Claim waveform CC only when non-empty `dt_*.cc` files are produced and consumed.
- CC-only relocation: `run_cc_only_relocation(...)` for one small prepared window; `run_cc_only_auto_time_windows(...)` for larger catalogs.
- Larger catalogs should use package window helpers before native HypoDD execution whenever possible. Do not hand-write batch/window loops first when `run_catalog_only_auto_time_windows(...)` or `run_cc_only_auto_time_windows(...)` fits the task.

## Input Contract

- `phase_format="auto"` is the safest default unless the phase format is known exactly.
- Phase input is event-block based: one event header followed by station pick rows.
- Event header: `origin_time,lat,lon,depth,mag[,evid]`. Time must parse; lat/lon/depth must be numeric. Event id may be omitted and then assigned sequentially, but preserve integer-like source event ids when later merging outputs back to the source catalog. Magnitude should be numeric when available, but empty/bad magnitude is accepted and filled as `0.0`.
- Pick row: `station_id,p_pick_time,s_pick_time[,optional_numeric_columns...]`. Three or more columns are accepted; optional trailing numeric fields such as residual/weight are ignored by the phase splitter. Missing P/S values may be `-1`, `nan`, `None`, `null`, `NA`, or empty.
- If the provided `phase.dat` already has event headers followed by station pick rows, pass it directly as `HypoDDInputs.phase_file`. Do not hand-write a derived `phase_hypodd_runner.dat` or replace real pick times with `-1` for normal relocation.
- Station ids must be consistent across station, phase, and waveform metadata. For catalog-only HypoDD, `NET.STA` and bare `STA` are both accepted and matched by station code. For FDTCC/CC tasks, provide real network information through `NET.STA`, separate network/station columns, or `station_default_network` only when that network is known and matches waveform files.
- If raw tables are not already in package format, create valid `phase.dat` and `station.sta` first with `build_hypodd_inputs(...)` or a task-specific preparation helper.

## Raw Input Preparation Decision Tree

Use this before choosing a relocation entry point:

1. If the task provides a valid event-block `phase.dat` plus a matching station file, validate and use those files directly. Do not rebuild them from raw picks by default.
2. If the task provides simple tabular event, pick, and station CSV files, call `build_hypodd_inputs(events_csv=..., picks_csv=..., stations_csv=..., output_dir=...)` to create package-ready `phase.dat` and `station.sta`.
3. If the task provides more primitive or heterogeneous data, first normalize them into three explicit tables, then call `build_hypodd_inputs(...)` or a task-specific preparation helper:
   - events table: event id, origin time, latitude, longitude, depth, magnitude.
   - picks table: event id, station id, P pick time, S pick time. Preserve real pick times; only use missing tokens for truly missing P/S arrivals.
   - stations table: station id, latitude, longitude, optional elevation and network.
4. After building inputs, audit event count, pick row count, station count, phase-station coverage, duplicate event ids, unparsable times, and selected event count before running native HypoDD.
5. For FDTCC or CC-only workflows, normalize station ids to `NET.STA` only when the network is known and matches waveform metadata. Do not invent a network prefix for waveform work unless it is applied consistently to stations, picks, and waveform lookup.

Treat input preparation as a separate evidence-producing step. Write a small manifest with source file paths, column mappings, row counts, dropped/filled rows, missing station references, and the generated `phase.dat`/`station.sta` paths. Input preparation alone is not relocation success.

## Core Parameters

- Dataset-specific parameters must be chosen from the current data: `ot_range`, `lat_range`, `lon_range`, `catalog_code`, output paths, velocity model, ph2dt thresholds, FDTCC flags, and iteration rows.
- Use documented Python shapes: ranges are 2-item tuples/lists, `num_grids` is `(nx, ny)`, velocity arrays have equal lengths, and `HypoDDParams.iter_rows` is `None` or a list of 10-value numeric rows.
- `HypoDDParams.iter_rows` row format: `NITER WTCCP WTCCS WRCC WDCC WTCTP WTCTS WRCT WDCT DAMP`.
- `NITER` values are cumulative iteration endpoints, not per-stage repeat counts. Correct: `(4, ...), (8, ...), (12, ...)`; wrong: `(8, ...), (8, ...), (8, ...)`. Use `iter_rows=None` only for smoke tests or when the package fallback has been validated for the current data; for scientific relocation, select iteration rows from the research region, observations, link density, residuals, and stability.
- Expensive tuning of `DAMP`, `iter_rows`, ph2dt link thresholds, or fallback-window parameters must not run multiple full-catalog candidates by default. First use a bounded diagnostic subset, such as one dense representative window plus one sparse/problem window, or another explicitly limited event/time selection. Run the full catalog only once with the selected production parameter set unless the user explicitly requests a full-scale parameter sweep.
- Catalog+CC and CC-only runs need CC weights (`WTCCP/WTCCS`) and CC cutoffs (`WRCC/WDCC`) that allow CC observations to affect relocation.
- `FDTCCParams.flags` must be a dict. Use `{}` for package defaults; do not pass `None`.
- HypoDD relocation velocity uses `hypodd.mod_top`, `hypodd.mod_vel`, and `hypodd.mod_ratio` (`Vs = Vp / VpVs`). FDTCC travel-time tables use `fdtcc.velocity_layer`, `fdtcc.velocity_vp`, `fdtcc.velocity_vs`, and `fdtcc.flags`.
- For FDTCC workflows, leave `HypoDDParams.dt_cc_per_grid` at its default `True`; the runner uses per-grid `dt_*.cc` files and does not support a shared `dt.cc` mode for `cc_engine=fdtcc`.
- `dep_corr` is a catalog depth-datum correction and should be justified from the current data.

## Native Scale Limits

Native limits come from compiled HYPODD include files, not Python parameters.

- `ph2dt.inc`: `MEV=16000`, `MSTA=2400`, `MOBS=500`.
- `hypoDD.inc`: `MAXEVE=10800`, `MAXDATA=3100000`, `MAXSTA=1300`, `MAXCL=100`.

If a limit is exceeded, split/reduce the run or explicitly rebuild native binaries as a separate maintenance task. Split with the largest windows that keep each native run below the active limit; avoid unnecessary daily windows when monthly or multi-week windows are valid. Preserve all selected scientific data in manifests/status outputs; do not silently truncate it.

For catalog-only tasks that exceed `MAXEVE`/`MAXDATA`, prefer `run_catalog_only_auto_time_windows(...)`. It keeps the original phase/station inputs, selects independent time/event windows internally, records per-window status/failure evidence, and produces consolidated outputs. Use the coarsest windows that remain below the active native limits: start with monthly/default windows, merge sparse windows, and shrink to daily/fixed-day windows only when a coarser planned window itself exceeds `MAXEVE`, `MAXDATA`, or other native evidence limits. Do not split a six-month catalog into daily windows just because the whole six-month selection is too large. Only implement a custom split if the package helper cannot express the required scientific windowing.

Catalog-only time-window execution is currently deterministic/sequential at the window level: leave `num_window_workers=1` if using the lower-level time-window helper. `RuntimeOptions.num_workers` is for work inside each native run, not for parallelizing independent time windows.

Parameter screening is separate from production relocation. If comparing multiple damping schedules or link-density settings, compare them on a small, documented diagnostic subset or selected failed windows first. Do not execute every candidate across every full-catalog auto-window run unless full-sweep cost is explicitly approved.

For CC-only auto-window tasks, use the same largest-valid-window rule. CC connectivity often gets worse when windows are too small, so a daily split is not automatically safer. Start with monthly or justified multi-day windows, inspect planned event counts and CC scale, and shrink only when a coarser planned window exceeds event/data/native evidence limits or waveform coverage changes sharply.

The grouped-object auto-window call is the intended public API. Use `inputs=...`, `selection=...`, `ph2dt=...`, `hypodd=...`, and `runtime=...`; do not switch to a hand-written batch loop or phase-file converter just because the catalog is large.

For CC-only windows, keep `skip_existing=False` for fresh validation runs. `skip_existing=True` only checks whether the existing per-window `{catalog_code}.reloc` file is non-empty; it does not prove that old inputs, velocity settings, FDTCC flags, or iteration rows match the current task.

Keep `verbose=False` for agent/task runs. Per-window details are preserved in `time_window_manifest.json` or `cc_window_manifest.json`; they should not be printed line-by-line into the task log unless explicitly debugging the window planner.

For required scientific runs, set `continue_on_error=False`. This is fail-fast: the first failed non-empty window writes traceback/status/manifest evidence and stops the run so the current error can be fixed before later windows are attempted. Use `continue_on_error=True` only for diagnostic sweeps where partial failures are expected.

## Output Contract

- Catalog-only success requires non-empty `dt_*.ct`, `{catalog_code}.loc`, `{catalog_code}.reloc`, and `{catalog_code}.res`.
- FDTCC success additionally requires non-empty `dt_*.cc` and FDTCC execution evidence.
- `stop_after_cc=True` is only a waveform differential-time production task. Do not report relocation success from it because HypoDD inversion outputs are intentionally absent.
- `.reloc` may contain only events selected/relocated by HypoDD. Match by preserved event ids or verified event order within the same run/window, not by full-catalog row order.
- In `.res`, `RES [ms]` is already milliseconds. Do not parse `DT` as residual and do not multiply `RES [ms]` by 1000 again.
- Windowed/batched results need a manifest/status table, consolidated relocated catalog, failed/unrelocated-event table, and global figures. Per-window native files are intermediate evidence.

## Failure Rules

- `No such file or directory: .../ph2dt/ph2dt`: fix `hypo_root`.
- `events total = 0`, `events selected = 0`, or empty `dt_*.ct`: fix event bounds, phase format, or event-block parsing.
- `STOP >>> Increase MAXEVE in hypoDD.inc.`: too many events in one native run; use package-supported windowing such as `run_catalog_only_auto_time_windows(...)`, reduce the selection, or rebuild native HypoDD explicitly.
- `STOP >>> Increase MAXDATA in hypoDD.inc.`: too many differential-time observations; reduce link density or use package-supported windowing.
- `HypoDD did not create expected loc file`: inspect the native `{i}-{j}.hypoDD` log before changing high-level workflow.
- `failure_kind=empty_native_output` or empty `{catalog_code}.reloc`: HypoDD produced the expected catalog path but no valid relocated rows. This message alone does not identify the scientific/native cause. Inspect the failed window's `failure_traceback.txt`, native `{i}-{j}.hypoDD`/`ph2dt` logs, `dt_*.ct`, `hypoDD_*.inp`, `hypoDD_phase_*.dat`, `.loc`, `.reloc`, `.src`, and `.sta` before changing parameters. Do not infer `MAXEVE`/`MAXDATA`, reduce events, alter phase parsing, or tune ph2dt/HypoDD parameters from empty `.reloc` alone.
- `FDTCC failed with return code 255`: inspect `fdtcc_stdout.log`, `fdtcc_stderr.log`, and package failure evidence; common causes are station/waveform mismatch, missing SAC files, or travel-time table bounds that are too small.
- Config generation, validation-only runs, empty outputs, skipped execution, mock/fallback catalogs, and plotting-only artifacts are not relocation success.
