# CASE_CC_ONLY Core Usage Summary

Use this case when the final HypoDD inversion should use waveform cross-correlation differential times only.

## Workflow

1. Prepare valid event/phase input and station file.
2. Ensure waveform data and station ids match the phase/station metadata.
3. Define grouped parameter objects: `HypoDDInputs`, `EventSelection`, `Ph2dtParams`, `HypoDDParams`, `FDTCCParams`, and `RuntimeOptions`.
4. For larger catalogs, define `CCOnlyWindowParams` and run independent time/event windows with `run_cc_only_auto_time_windows(...)`.
5. For one already-small window, call `run_cc_only_relocation(...)` with the same grouped parameter objects.
6. Validate CC link counts, HypoDD logs, native relocation outputs, and merged window outputs.

## Recommended Large-Catalog Flow

```python
result = run_cc_only_auto_time_windows(
    inputs=inputs,
    selection=selection,
    ph2dt=ph2dt,
    hypodd=hypodd,
    fdtcc=fdtcc,
    runtime=runtime,
    windows=windows,
)
```

The returned `CCOnlyWindowResult` records `status_csv`, `manifest_json`, merged `.loc/.reloc/.res` paths, and per-window status.

## Input Requirements

- `phase_file` must contain event blocks with event origin/location/depth/magnitude and station pick rows; an integer-like event id is recommended and otherwise assigned sequentially by the parser.
- `station_file` must contain station ids and coordinates.
- Station ids must be consistent across phase, station, and waveform metadata. Use real `NET.STA`, separate network/station columns, or `station_default_network` only when that network is known and matches waveform files.
- `waveform_dir_raw` must cover the selected event time span and station set.
- FDTCC travel-time table bounds must cover event depth and event-station distance.
- Event windows must be small enough for native HypoDD/FDTCC scale limits and large enough to produce connected CC event pairs. Use the largest scientifically meaningful windows that stay below limits; do not default to daily windows when multi-day or monthly windows are valid.

## CC-Only Failure Focus

- Empty or missing `dt_*.cc`: inspect waveform coverage, station ids, FDTCC flags, and SAC cache/export logs.
- Very few CC data lines: loosen FDTCC thresholds, expand waveform/station coverage, widen event window, or adjust event selection.
- `events after dtime match` is very small or `# clusters: 0`: CC graph is not connected enough for relocation.
- A planned window exceeding event/data limits: shrink from coarse windows to multi-day/day windows only as needed. If one day itself is over limit, the planner should fail fast; use a justified larger limit, narrower selection, or explicit task-specific split.
- Missing `.loc/.reloc`: inspect the native `{i}-{j}.hypoDD` log and window `failure_traceback.txt`.
- Repeated failed windows should be fixed at the shared input/parameter level rather than patched one window at a time.
- Use `skip_existing=True` only for deliberate reruns with verified unchanged inputs/parameters; the runner reuses a window based on a non-empty existing `{catalog_code}.reloc` file.

## Relation To Other Modes

- Use `CASE_CATALOG_ONLY` when waveform data are absent or not requested.
- Use `CASE_CROSS_CORRELATION` when catalog and CC constraints should both contribute.
- Use `CASE_CC_ONLY` when CC links are the intended final HypoDD data source.
