# CASE_CC_ONLY Config Summary

This case describes HypoDD relocation using waveform cross-correlation differential times only. It is separate from catalog-only and catalog+CC relocation.

## Purpose

- Mode: CC-only relocation.
- Small/already-windowed entry point: `run_cc_only_relocation(...)` with grouped parameter objects.
- Larger catalog entry point: `run_cc_only_auto_time_windows(...)` with the same grouped parameter objects plus `CCOnlyWindowParams`.
- Parameter style: grouped dataclasses that separate inputs, selection, ph2dt, HypoDD, FDTCC, runtime, and window controls.
- Use this case only when waveform data, station metadata, event phase/theoretical pick input, and FDTCC settings are available.

## Recommended Auto-Window Pattern

```python
from hypodd_runner import (
    CCOnlyWindowParams, EventSelection, FDTCCParams, HypoDDInputs,
    HypoDDParams, Ph2dtParams, RuntimeOptions,
    default_cc_only_hypodd_iter_rows, default_fdtcc_flags,
    run_cc_only_auto_time_windows,
)

inputs = HypoDDInputs(
    hypo_root=hypo_root,            # string path ending in /src
    phase_file=phase_file,          # string or Path; event-block phase/theoretical-pick file
    station_file=station_file,      # string or Path; station ids should match phase and waveform metadata
    output_folder=output_folder,    # string or Path; parent output directory for windows and merged products
    catalog_code=catalog_code,      # short string used for native output names
)
selection = EventSelection(
    phase_format="auto",           # usually safest; use "hypodd" or "pal" only when known
    dep_corr=dep_corr,              # float depth correction in km; use 0.0 when none is intended
    ot_range=ot_range,              # two dates/times, e.g. ("2025-11-01", "2025-11-12")
    lat_range=lat_range,            # two numbers: (min_lat, max_lat)
    lon_range=lon_range,            # two numbers: (min_lon, max_lon)
)
ph2dt = Ph2dtParams(
    maxdist=ph2dt_maxdist,          # number in km; event-station/link distance control
    maxoffset=ph2dt_maxoffset,      # number in km; event-pair separation control
    mnb=ph2dt_mnb,                  # integer neighbor limit
    limobs_pair=ph2dt_limobs_pair,  # integer observation limit per pair
    minobs_pair=ph2dt_minobs_pair,  # integer minimum observations per pair
    maxobs_pair=ph2dt_maxobs_pair,  # integer maximum observations per pair
)
hypodd = HypoDDParams(
    idata=1,                        # CC-only mode; do not set catalog+CC idata=2 for this case
    iphase=hypodd_iphase,           # integer phase mode; 3 for P+S when both are intended
    maxdist=hypodd_maxdist,         # number in km
    minobs_cc=hypodd_minobs_cc,     # integer minimum CC observations
    minobs_ct=0,                    # catalog observations are disabled in CC-only mode
    iter_rows=iter_rows or default_cc_only_hypodd_iter_rows(),  # rows of 10 numbers, CC weights positive
    mod_top=hypodd_mod_top,         # None or list of layer-top depths in km
    mod_vel=hypodd_mod_vel,         # None or list of Vp values in km/s; same length as mod_top
    mod_ratio=hypodd_mod_ratio,     # numeric Vp/Vs ratio
)
fdtcc = FDTCCParams(
    flags=fdtcc_flags or default_fdtcc_flags(max_depth_km=max_depth_km),  # dict of FDTCC bounds/windows/thresholds
    waveform_dir_raw=waveform_dir_raw,    # string or Path; raw MiniSEED root or existing FDTCC SAC tree
    waveform_temp_basename=sac_cache_dir, # string or Path; reusable SAC cache directory
    wave_dir_mode=fdtcc_wave_dir_mode,    # "miniseed" or "fdtcc_sac"
    velocity_layer=fdtcc_velocity_layer,  # list of layer depths in km
    velocity_vp=fdtcc_velocity_vp,        # list of Vp values in km/s; same length as velocity_layer
    velocity_vs=fdtcc_velocity_vs,        # list of Vs values in km/s; same length as velocity_layer
    station_default_network=station_default_network, # None or real network code for bare station ids
    keep_waveform_temp=True,              # Python bool; usually keep/reuse cache for windows
    prepare_inputs=True,                  # Python bool; let hypodd_runner prepare FDTCC station/TTDB/wave inputs
    rebuild_ttdb=False,                   # Python bool; true only when velocity/table settings changed
)
runtime = RuntimeOptions(
    num_grids=(1, 1),               # two integers: (nx, ny), not scalar 1
    xy_pad=xy_pad,                  # two numbers: (lat_pad, lon_pad)
    num_workers=num_workers,        # integer; start modestly for debugging
    keep_grids=False,               # Python bool
)
windows = CCOnlyWindowParams(
    base="month",                  # start coarse; shrink only if a planned month exceeds limits/evidence
    window_days=None,              # set only with base="days" for justified fixed-day windows
    min_events_per_window=min_events_per_window,  # integer, often 50-300
    max_events_per_window=max_events_per_window,  # optional cap chosen from native limits and CC scale
    window_prefix=window_prefix,    # short string used in generated window ids
    continue_on_error=False,        # Python bool; fail-fast for required full-coverage runs
    skip_existing=False,            # Python bool; False when validating a fresh run
)

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

Use `plan_cc_only_time_windows(...)` first for dry-run planning when choosing event-count limits.

## Direct Small-Window Pattern

Use the same `inputs`, `selection`, `ph2dt`, `hypodd`, `fdtcc`, and `runtime` groups, but call `run_cc_only_relocation(...)` for one already-small window:

```python
from hypodd_runner import run_cc_only_relocation

cfg = run_cc_only_relocation(
    inputs=inputs,
    selection=selection,
    ph2dt=ph2dt,
    hypodd=hypodd,
    fdtcc=fdtcc,
    runtime=runtime,
)
```

`run_cc_only_relocation(...)` enforces CC-only native mode internally (`hypodd_idata=1`) and requires non-empty CC differential-time files.

Use the grouped argument names shown above. Ranges are Python tuples/lists, `num_grids` is `(nx, ny)`, and paths/codes are provided through `HypoDDInputs`.

## Input File Format Reminder
`phase_file` is the API name for the event/pick-window input in CC-only mode; it defines events and P/S windows for FDTCC, not catalog differential-time constraints for the final inversion.
```text
origin_time,lat,lon,depth,mag,evid
station_id,p_pick_time,s_pick_time[,optional_numeric_columns...]
```
Notes:
- Do not pass a flat pick table as `phase_file`.
- `evid` may be omitted and then assigned sequentially, but preserve source event ids when outputs must be merged back to the input catalog.
- CC-only relocation success must come from non-empty CC differential times (`dt_*.cc`) and HypoDD relocation outputs, not from catalog-pick constraints.

- `station_file` is a station coordinate table,
```
station_id,latitude,longitude[,optional_columns...]
```
- For CC-only/FDTCC, station ids must provide real network information through `NET.STA`, separate network/station columns, or `station_default_network` when that network is known and matches waveform files.

## Required Task-Specific Values

Recompute these from the current task:

- `catalog_code`, `output_folder`, `phase_file`, `station_file`, `waveform_dir_raw`, and `sac_cache_dir`.
- `ot_range`, `lat_range`, `lon_range`, and `phase_format`.
- `min_events_per_window`, `max_events_per_window`, `base`, optional `window_days`, and `window_prefix` for auto-window runs.
- `vp_km_s`, `vp_vs_ratio`, or explicit `fdtcc_velocity_layer`, `fdtcc_velocity_vp`, `fdtcc_velocity_vs`.
- `fdtcc_flags`, especially travel-time table bounds and CC/SNR thresholds.
- `hypodd_minobs_cc`, `HypoDDParams.iter_rows`, and optional HypoDD velocity model.

## Initial Parameter Guidance

Use these as first-pass settings for CC-only smoke runs. Tune from CC link counts, `events_after_dtime_match`, cluster count, and native HypoDD logs.

Must set for every real CC-only task:

- `hypo_root`, `phase_file`, `station_file`, `output_folder`, `catalog_code`.
- `ot_range`, `lat_range`, `lon_range`, and `phase_format`.
- `waveform_dir_raw` and reusable `sac_cache_dir`.
- FDTCC velocity/travel-time settings or helper inputs such as `vp_km_s`, `vp_vs_ratio`, and `max_depth_km`.
- Window planning parameters: `base`, optional `window_days`, `min_events_per_window`, `max_events_per_window`, and `window_prefix`.
- CC-only HypoDD controls such as `hypodd_minobs_cc` and `HypoDDParams.iter_rows`.

Common starting ranges:

- `min_events_per_window`: often `50-300`; use lower values for sparse sequences and smoke tests.
- `max_events_per_window`: optional but recommended for CC-only full runs; choose from native limits, CC link density, waveform cost, and connectivity. It is often well below `MAXEVE=10800`, but should not force unnecessary tiny windows.
- `base`: start with the coarsest scientifically meaningful window, usually `"month"` or `base="days"` with a multi-day `window_days`. Shrink to `"day"` only when a coarser planned window exceeds event/data/native evidence limits or waveform coverage changes sharply by day. Do not split a multi-month catalog into daily CC windows just because the full selection is too large.
- `hypodd_minobs_cc`: often `2-6`; lower if too few events survive dtime matching, raise for quality after connectivity is adequate.
- `ph2dt.maxoffset`: often `5-30 km`; larger windows can create more candidate pairs but may degrade locality and scale.
- `fdtcc.flags.max_depth_km`: set above selected event depths, often `30-100 km`.
- `fdtcc.flags.max_distance_deg`: set above event-station distances for selected stations; too small causes out-of-table failures.
- `num_workers`: start modestly for debugging; increase after waveform export and SAC cache reuse are verified.

Scenario-dependent values:

- If `dt_cc_data_lines` is near zero, adjust station coverage, waveform availability, CC thresholds/windows, or event selection before changing HypoDD damping.
- If `events_after_dtime_match` or `clusters` is near zero, widen/merge windows or lower CC minimum-observation requirements.
- If one planned day still exceeds `max_events_per_window`, the planner fails fast rather than recursively splitting by event count. Use a larger justified limit, narrower scientific selection, or an explicit task-specific split.
- If many windows fail similarly, fix shared inputs/parameters rather than patching individual window outputs.
- Use `keep_waveform_temp=True` or a persistent `sac_cache_dir` for iterative debugging and repeated windows.
- Keep `skip_existing=False` for fresh validation. `skip_existing=True` only reuses a window when its existing `{catalog_code}.reloc` is non-empty; it does not verify that old inputs, FDTCC flags, velocity settings, or `iter_rows` match the current run.

## Parameter Cautions

- CC-only is not the same as catalog+CC. It requires usable `dt_*.cc`; catalog `dt_*.ct` alone is not enough.
- Keep inputs, selection, ph2dt, HypoDD, FDTCC, runtime, and window controls in separate grouped objects so the script remains readable and auditable.
- `default_cc_only_hypodd_iter_rows()` disables catalog weights with `-9.0` catalog fields and keeps positive CC weights. Do not replace it with catalog-only iteration rows unless you intentionally change the scientific mode.
- Keep `HypoDDParams.dt_cc_per_grid` at its default `True` for FDTCC/CC-only runs; `cc_engine=fdtcc` uses per-grid `dt_*.cc` files.
- If FDTCC creates too few CC links, HypoDD may report zero clusters or no `.loc/.reloc`. Treat this as insufficient CC connectivity, not as a successful relocation.
- `sac_cache_dir` should usually be reusable across windows so waveform conversion is not repeated unnecessarily.

## Success Checks

A valid CC-only run requires:

- non-empty `dt_*.cc` in successful windows;
- HypoDD logs showing CC observations were read;
- non-empty merged or per-window `{catalog_code}.loc`, `{catalog_code}.reloc`, and `{catalog_code}.res`;
- `cc_window_status.csv` and `cc_window_manifest.json` for auto-window runs;
- no blocking failed windows. With `continue_on_error=False`, the first failed non-empty window should stop the run after writing failure evidence.

Do not report success based only on waveform conversion, FDTCC execution without relocations, empty `dt.cc`, or plots alone.
