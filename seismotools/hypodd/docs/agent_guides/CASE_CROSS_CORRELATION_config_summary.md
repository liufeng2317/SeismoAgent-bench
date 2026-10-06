# CASE_CROSS_CORRELATION Config Summary

This case describes HypoDD relocation with waveform cross-correlation constraints using `hypodd_runner`. It is a generic package-use pattern, not a region-specific parameter template.

## Purpose

- Mode: catalog differential times plus waveform cross-correlation.
- Public entry point: `run_fdtcc_relocation(...)`.
- Parameter style: grouped dataclasses.
- Use this case only when waveform data and station metadata are available and cross-correlation should contribute to the relocation.

## Grouped Parameters

```python
from hypodd_runner import (
    HypoDDInputs, EventSelection, Ph2dtParams,
    HypoDDParams, FDTCCParams, RuntimeOptions,
    run_fdtcc_relocation,
)
```

Use these groups:

- `HypoDDInputs`: required files and output naming.
- `EventSelection`: time/space bounds, depth correction, and phase format.
- `Ph2dtParams`: catalog differential-time pairing thresholds.
- `HypoDDParams`: inversion mode, iteration schedule, damping, and HypoDD velocity model.
- `FDTCCParams`: waveform source, SAC conversion/cache behavior, FDTCC velocity model, and FDTCC flags.
- `RuntimeOptions`: grids, padding, workers, and intermediate retention.

## Generic Parameter Template

```python
inputs = HypoDDInputs(
    hypo_root="seismotools/hypodd/runtime",  # string path ending in /src
    phase_file=phase_file,          # string or Path; event-block phase file
    station_file=station_file,      # string or Path; station file matching phase/waveform station ids
    output_folder=output_folder,    # string or Path; task-specific output directory
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
    minwght=0.0,                    # numeric minimum pick weight
    maxdist=ph2dt_maxdist,          # number in km; event-station/link distance control
    maxoffset=ph2dt_maxoffset,      # number in km; event-pair separation control
    mnb=ph2dt_mnb,                  # integer neighbor limit
    limobs_pair=ph2dt_limobs_pair,  # integer observation limit per pair
    minobs_pair=ph2dt_minobs_pair,  # integer minimum observations per pair
    maxobs_pair=ph2dt_maxobs_pair,  # integer maximum observations per pair
)
hypodd = HypoDDParams(
    idata=2,                        # catalog + CC mode; runner synchronizes native mode after dt.cc exists
    iphase=hypodd_iphase,           # integer phase mode; 3 for P+S when both are intended
    maxdist=hypodd_maxdist,         # number in km
    iter_rows=iter_rows,     # choose rows of 10 numbers for real runs; use positive CC weights when CC should contribute
    mod_top=hypodd_mod_top,         # None or list of layer-top depths in km
    mod_vel=hypodd_mod_vel,         # None or list of Vp values in km/s; same length as mod_top
    mod_ratio=hypodd_mod_ratio,     # numeric Vp/Vs ratio
)
fdtcc = FDTCCParams(
    velocity_layer=fdtcc_velocity_layer,  # list of layer depths in km
    velocity_vp=fdtcc_velocity_vp,        # list of Vp values in km/s; same length as velocity_layer
    velocity_vs=fdtcc_velocity_vs,        # list of Vs values in km/s; same length as velocity_layer
    flags=fdtcc_flags or {},              # dict, e.g. {"max_distance_deg": 3.0, "max_depth_km": 90.0}; never None
    waveform_dir_raw=waveform_dir_raw,    # string or Path; raw MiniSEED root or existing FDTCC SAC tree
    waveform_temp_basename=fdtcc_waveform_temp_basename, # string; reusable SAC cache basename/path
    wave_dir_mode=fdtcc_wave_dir_mode,    # "miniseed" or "fdtcc_sac"
    station_default_network=station_default_network, # None or real network code for bare station ids
    keep_waveform_temp=keep_waveform_temp,# Python bool; keep/reuse expensive waveform conversion products
    prepare_inputs=True,                  # Python bool; let hypodd_runner prepare FDTCC station/TTDB/wave inputs
    rebuild_ttdb=False,                   # Python bool; true only when velocity/table settings changed
)
runtime = RuntimeOptions(
    num_grids=num_grids,            # two integers: (nx, ny), not scalar 1
    xy_pad=xy_pad,                  # two numbers: (lat_pad, lon_pad)
    num_workers=num_workers,        # integer; start modestly for debugging
    keep_grids=keep_grids,          # Python bool
)
```

Use the argument names shown above. Ranges are Python tuples/lists, `num_grids` is `(nx, ny)`, and paths/codes are provided through `HypoDDInputs`.

## Input File Format Reminder
`phase_file` should be an event-block file: one event header followed by that event's station pick rows.
```text
origin_time,lat,lon,depth,mag,evid
station_id,p_pick_time,s_pick_time[,optional_numeric_columns...]
```
Notes:
- Do not pass a flat pick table as `phase_file`.
- `evid` may be omitted and then assigned sequentially, but preserve source event ids when outputs must be merged back to the input catalog.

- `station_file` is a station coordinate table,
```
station_id,latitude,longitude[,optional_columns...]
```
- For FDTCC/CC, station ids must provide real network information through `NET.STA`, separate network/station columns, or `station_default_network` when that network is known and matches waveform files.

## Required Task-Specific Values

Recompute these from the current data and task:

- `catalog_code`, `output_folder`, `phase_file`, `station_file`, and `waveform_dir_raw`.
- `ot_range`, `lat_range`, `lon_range`, and `dep_corr`.
- `ph2dt_*` link parameters.
- `HypoDDParams.iter_rows`, `hypodd_*` inversion parameters, and HypoDD velocity model.
- `fdtcc_velocity_*`, `fdtcc_flags`, waveform mode, waveform cache behavior, and FDTCC thresholds.
- `num_grids`, `xy_pad`, `num_workers`, and any time/window split strategy.

## Initial Parameter Guidance

Use these as first-pass settings for a smoke run, then tune from waveform coverage, FDTCC logs, CC link counts, and relocation residuals.

Must set for every real cross-correlation task:

- All catalog-only required inputs: `hypo_root`, `phase_file`, `station_file`, `output_folder`, `catalog_code`, `ot_range`, `lat_range`, `lon_range`.
- `waveform_dir_raw` and `fdtcc.wave_dir_mode`.
- FDTCC velocity model: `fdtcc.velocity_layer`, `fdtcc.velocity_vp`, `fdtcc.velocity_vs`, or equivalent helper inputs.
- FDTCC flags for travel-time table bounds, windows, thresholds, and filtering.
- `HypoDDParams.iter_rows` with positive CC weights when CC should contribute.

Common starting ranges:

- `fdtcc.flags.max_distance_deg`: set above the maximum event-station distance; local runs often start around `1-3 deg`, regional runs may need more.
- `fdtcc.flags.max_depth_km`: set above maximum event depth plus margin; common starts are `30-100 km` depending on catalog depth range.
- `fdtcc.flags.distance_step_deg`: often `0.01-0.05 deg`; finer is slower/larger.
- `fdtcc.flags.depth_step_km`: often `0.5-2.0 km`; finer is slower/larger.
- `fdtcc` P/S windows: start from pick uncertainty and waveform sampling; widen if picks are rough, narrow if false correlations dominate.
- `cc_threshold` / `snr_threshold`: start permissive enough to generate links, then tighten after verifying CC quality.
- `ph2dt.maxdist` and `ph2dt.maxoffset`: choose from catalog geometry; loosen carefully because large link graphs can hit `MAXDATA`.
- `HypoDDParams.iter_rows`: include positive `WTCCP/WTCCS`; if these are zero or disabled, `dt.cc` will not meaningfully affect relocation.

Scenario-dependent values:

- Waveform cache behavior: keep/reuse SAC cache for expensive repeated runs; delete temp products only when storage matters and reruns are cheap.
- `station_default_network`: use only when source stations are bare names and the network prefix is known.
- `num_workers`: increase only after FDTCC waveform export and native runs are stable.
- Windowing: required when event count or CC link density exceeds native limits, or when FDTCC coverage is strongly time-dependent.

## Parameter Cautions

- `hypo_root` must contain `ph2dt/ph2dt` and `hypoDD/hypoDD`.
- `phase_format="auto"` is safest unless the current format is known exactly.
- `HypoDDParams.idata=2` is a safe starting value; after FDTCC creates non-empty `dt_*.cc`, the runner synchronizes native HypoDD input mode for catalog+CC use.
- `HypoDDParams.iter_rows` must be selected for the current study. For CC contribution, CC weights and cutoffs must not disable `dt.cc` observations.
- Keep `HypoDDParams.dt_cc_per_grid` at its default `True` for FDTCC runs; `cc_engine=fdtcc` uses per-grid `dt_*.cc` files.
- `FDTCCParams.flags` should be a dict. Use `{}` for package defaults; do not pass `None`.
- FDTCC travel-time bounds must cover event depths and event-station distances. If FDTCC reports out-of-table events, expand `max_distance_deg` or `max_depth_km` and rebuild/regenerate the TTDB.

## Success Checks

A valid cross-correlation run must produce:

- non-empty `dt_*.ct` from `ph2dt`;
- non-empty `dt_*.cc` from FDTCC;
- non-empty `{catalog_code}.loc`, `{catalog_code}.reloc`, and `{catalog_code}.res` from HypoDD;
- FDTCC and HypoDD logs showing real execution.

Input preparation, configs, plots, or empty native files are not success.

If `stop_after_cc=True` is intentionally used, non-empty `dt_*.cc` is evidence for waveform differential-time production only. It is not relocation success because HypoDD inversion outputs are intentionally not produced.
