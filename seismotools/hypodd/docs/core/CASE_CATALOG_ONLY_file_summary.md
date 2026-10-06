# CASE_CATALOG_ONLY File Summary

This case uses catalog picks only. No waveform files, FDTCC travel-time table, or CC differential-time file is required.

## Required Inputs

### Function Inputs

- `hypo_root`: HYPODD executable root containing `ph2dt/ph2dt` and `hypoDD/hypoDD`.
- `phase_file`: event-block phase file.
- `station_file`: station coordinate file.
- `output_folder`: writable run directory.
- `catalog_code`: output prefix.
- `ot_range`, `lat_range`, `lon_range`: event selection for the current data.

### Station File

```text
station_id,latitude,longitude[,optional_columns...]
NET.STA,lat,lon
```

`NET.STA` and bare `STA` are both accepted for catalog-only use; native HypoDD uses the station code. Keep phase and station station ids consistent.

### Phase File

```text
origin_time,lat,lon,depth,mag,evid
NET.STA,p_pick_time,s_pick_time
```

Event headers require parsable time and numeric lat/lon/depth. Magnitude should be numeric when available, but empty/bad magnitude is accepted by the package and filled as `0.0`. Use a preserved integer event id when later merging outputs back to the source catalog.

Missing picks may be represented as `-1`, `nan`, `None`, `null`, `NA`, or empty values.

## Files Not Required

Do not require these in catalog-only mode:

- waveform directory;
- MiniSEED/SAC cache;
- FDTCC velocity table;
- FDTCC stdout/stderr logs;
- `dt_*.cc`.

## Expected Generated Files

Under `output_folder` for one grid:

```text
hypoDD_station.dat
hypoDD_phase.dat
hypoDD_phase_0-0.dat
event_0-0.dat
dt_0-0.ct
0-0.ph2dt
0-0.hypoDD
hypoDD.log
{catalog_code}.loc
{catalog_code}.reloc
{catalog_code}.pha
{catalog_code}.res
```

For multiple grids, expect per-grid `dt_{i}-{j}.ct`, `event_{i}-{j}.dat`, and native logs.

Output hierarchy matters:

- In one native run directory, `{catalog_code}.loc`, `{catalog_code}.reloc`, `{catalog_code}.pha`, and `{catalog_code}.res` are the package-merged final outputs for that run/grid set.
- In a `run_catalog_only_auto_time_windows(...)` or batch run, each window/batch has its own native run directory. The top-level batch result may also expose concatenated `merged_loc_path`, `merged_reloc_path`, and `merged_residual_path`, usually `{catalog_code}.loc`, `{catalog_code}.reloc`, and `{catalog_code}.res`; an empty path means no top-level merged file was produced.
- `hypoDD_0-0.reloc`, `hypoDD_0-0.loc`, and `hypoDD_0-0.res` are native per-grid files for one run directory, not task-level full-catalog products.
- `hypoDD_0-0.reloc.001.NNN` files are iteration snapshots. Do not use them as final relocated catalogs, do not concatenate them into full-catalog results, and do not use them for final figures except as explicit native convergence/debug evidence.
- If `{catalog_code}.reloc` is empty but iteration snapshots are non-empty, treat this as a native/package output failure for that run. Inspect native logs and failure evidence; do not silently promote snapshots to success outputs.

## Preflight Checks

Before execution:

- verify `hypo_root/ph2dt/ph2dt` and `hypo_root/hypoDD/hypoDD` exist;
- verify `station_file` and `phase_file` exist;
- parse the phase file and confirm it has events;
- confirm selected events remain inside `ot_range`, `lat_range`, and `lon_range`;
- compare event count and expected differential-time count with native limits.

## Batched Or Windowed Outputs

For split full-catalog runs, keep each unit's native files and also write task-level summaries:

- manifest/status table;
- consolidated relocated catalog built from successful final package outputs only, with unit id/window id and verified original event id;
- failed/unrelocated-event table;
- global figures for coverage, shifts, and residuals.

Do not merge `.reloc` rows by assuming full-catalog row order. For windowed tasks, reconcile final relocated rows to the source catalog with preserved event ids when available, or with a verified per-window event-order mapping from that same run directory. Keep failed windows and attempted-but-unrelocated events separate; never count them as relocated.

## Success Evidence

Catalog-only success requires real execution and non-empty:

- `dt_*.ct`;
- `{catalog_code}.loc`;
- `{catalog_code}.reloc`;
- `{catalog_code}.res`.

For batch/windowed success, apply this requirement to each successful native unit and to package-reported top-level merged outputs when they are produced. A task-level consolidated CSV or figure can summarize successful units, but it is not a replacement for missing or empty final native relocation outputs in a required successful unit.

Config generation, validation-only runs, skipped execution, placeholders, and plots alone are not success.
