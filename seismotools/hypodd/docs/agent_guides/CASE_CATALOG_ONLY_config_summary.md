# CASE_CATALOG_ONLY Config Summary

This case describes HypoDD relocation using catalog differential times only. It does not require waveform data or FDTCC inputs.

## Purpose

- Mode: catalog-only relocation.
- Public entry points: `run_catalog_only_relocation(...)` for one small/valid selection, and `run_catalog_only_auto_time_windows(...)` for larger catalogs that may exceed native limits.
- Parameter style: grouped dataclasses.
- Use this case as the baseline/debug mode when waveform cross-correlation is absent or not requested.

## Grouped Parameters

```python
from hypodd_runner import (
    HypoDDInputs, EventSelection, Ph2dtParams,
    HypoDDParams, RuntimeOptions,
    run_catalog_only_relocation,
)
```

Use these groups:

- `HypoDDInputs`: required files and output naming.
- `EventSelection`: time/space bounds, depth correction, and phase format.
- `Ph2dtParams`: catalog differential-time pairing thresholds.
- `HypoDDParams`: catalog-only inversion controls and optional HypoDD velocity model.
- `RuntimeOptions`: grids, padding, workers, and intermediate retention.

## Generic Parameter Template

```python
inputs = HypoDDInputs(
    hypo_root="seismotools/hypodd/runtime",  # string path ending in /src
    phase_file=phase_file,          # string or Path; event-block phase file
    station_file=station_file,      # string or Path; station file matching phase station ids
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
    iphase=hypodd_iphase,           # integer phase mode; 3 for P+S when both are intended
    maxdist=hypodd_maxdist,         # number in km
    iter_rows=iter_rows,     # choose rows of 10 numbers for real runs; None is only a fallback/smoke default
    mod_top=hypodd_mod_top,         # None or list of layer-top depths in km
    mod_vel=hypodd_mod_vel,         # None or list of Vp values in km/s; same length as mod_top
    mod_ratio=hypodd_mod_ratio,     # numeric Vp/Vs ratio
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
- Station ids may be `NET.STA` or bare `STA`; catalog-only matching uses the station code.

## Required Task-Specific Values

Recompute these from the current data and task:

- `catalog_code`, `output_folder`, `phase_file`, and `station_file`.
- `ot_range`, `lat_range`, `lon_range`, and `dep_corr`.
- `ph2dt_*` link parameters.
- `HypoDDParams.iter_rows`, `hypodd_*` inversion parameters, and optional HypoDD velocity model.
- `num_grids`, `xy_pad`, `num_workers`, and any time/window split strategy.

## Initial Parameter Guidance

Use these as first-pass smoke/full-run ranges, then tune from current data, native logs, and output quality. Expensive parameter tuning is a diagnostic step, not a default full-catalog sweep: test multiple candidate damping schedules, `iter_rows`, or ph2dt link settings on a bounded representative subset before selecting one production configuration for the full catalog.

Must set for every real task:

- `hypo_root`, `phase_file`, `station_file`, `output_folder`, `catalog_code`.
- `ot_range`, `lat_range`, `lon_range`, and `phase_format`.
- `ph2dt` pair selection parameters.
- `HypoDDParams.iter_rows` and core HypoDD inversion settings.

Common first-pass diagnostics:

- `phase_format`: start with `"auto"`; use `"hypodd"` only for verified compact HypoDD headers.
- `ph2dt.maxdist`: choose from event-station geometry and station coverage; many local/regional first passes fall somewhere in the tens to hundreds of km, but this is not a fixed range.
- `ph2dt.maxoffset`: choose from event spacing and target cluster scale; smaller for dense local clusters, larger for broader regional windows.
- `ph2dt.minobs_pair`: raise for quality, lower only if links become too sparse.
- `ph2dt.maxobs_pair`: reduce if `MAXDATA` is approached; increase only when high-quality common-pick coverage justifies it.
- `hypodd.maxdist`: choose from useful event-station geometry and verify station counts in the native log.
- `hypodd.iphase`: `3` when both P and S are intended; choose a narrower phase mode only when justified.
- `HypoDDParams.iter_rows`: use multi-stage positive cumulative `NITER` endpoints, often ending near `8-20` for first scientific runs; tune weights/cutoffs/damping from the current study's station geometry, event-window size, link density, phase quality, residual behavior, and numerical stability. Do not use `iter_rows=None` for full scientific relocation unless a short validation run shows the package fallback is appropriate.
- `DAMP`: LSQR damping is data dependent. Small local tests may tolerate small values, while larger or weakly conditioned regional windows may require damping in the tens to hundreds. Values such as `80-120` are examples from some regional catalog-only runs, not a universal recommendation; validate from convergence, residuals, condition numbers, air-quake counts, and shifts. When trying multiple `DAMP` values, use a small diagnostic selection or a few representative/problem windows first; do not run several full-catalog candidates unless the task explicitly asks for a full parameter sweep.
- `num_grids`: start `(1, 1)` for one coherent local run; use more grids only when it genuinely reduces per-grid scale or supports independent spatial windows.
- `num_workers`: start modestly (`1-8`) for debugging; increase only after IO/native execution is stable.

Scenario-dependent values:

- `dep_corr`: set from catalog depth datum; use `0.0` only when no correction is intended.
- `hypodd.mod_top`, `hypodd.mod_vel`, `hypodd.mod_ratio`: set from the regional 1D velocity model or a documented assumption.
- Time/spatial/event-count windows: required when event count, station count, cluster count, or differential-time count approaches native limits.

## Parameter Cautions

- `run_catalog_only_relocation(...)` sets catalog-only mode internally. Do not add waveform paths, FDTCC velocity arrays, `dt.cc`, or `cc_engine` fields for this case.
- `hypo_root` must contain `ph2dt/ph2dt` and `hypoDD/hypoDD`.
- `phase_format="auto"` avoids many format mistakes. Use `"hypodd"` only for known compact HypoDD-style headers.
- `HypoDDParams.iter_rows` still matters in catalog-only mode because catalog weights, cutoffs, damping, and iteration endpoints control the inversion.

## Success Checks

A valid catalog-only run must produce non-empty:

- `dt_*.ct`;
- `{catalog_code}.loc`;
- `{catalog_code}.reloc`;
- `{catalog_code}.res`.

`dt_*.cc`, waveform directories, FDTCC logs, and FDTCC velocity tables are not required.
