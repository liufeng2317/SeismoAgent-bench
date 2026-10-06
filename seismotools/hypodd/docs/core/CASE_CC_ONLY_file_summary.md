# CASE_CC_ONLY File Summary

This case describes files for CC-only HypoDD relocation with FDTCC-generated differential times.

## Required Inputs

### Function Inputs

- `hypo_root`: HYPODD executable root containing `ph2dt/ph2dt` and `hypoDD/hypoDD`.
- `phase_file`: event-block phase/theoretical-pick file used to define events and FDTCC pick windows.
- `station_file`: station coordinate file.
- `output_folder`: top-level run directory.
- `catalog_code`: output prefix.
- `waveform_dir_raw`: waveform root or source tree.
- `sac_cache_dir` or `FDTCCParams.waveform_temp_basename`: optional reusable FDTCC SAC cache directory. Auto-window workflows default to `<output_folder>/sac_cache` when not supplied.
- `ot_range`, `lat_range`, `lon_range`: event selection bounds.

### Station File

```text
network.station,latitude,longitude[,optional_columns...]
NET.STA,lat,lon
```

For CC-only/FDTCC, station ids must provide real network information through `NET.STA`, separate network/station columns, or `station_default_network` when that network is known and matches waveform files.

### Phase File

```text
origin_time,lat,lon,depth,mag,evid
NET.STA,p_pick_time,s_pick_time
```

For CC-only workflows, phase rows may come from observed picks or theoretical picks, but they must define usable P/S windows for waveform cross-correlation.

## Expected Auto-Window Outputs

Top-level `output_folder` should contain:

```text
cc_window_status.csv
cc_window_manifest.json
{catalog_code}.loc
{catalog_code}.reloc
{catalog_code}.res
windows/
sac_cache/ or configured shared SAC cache
```

Each successful window under `windows/<window_id>/` should contain native evidence such as:

```text
dt_0-0.cc
0-0.hypoDD
fdtcc_work_0-0/
{catalog_code}.loc
{catalog_code}.reloc
{catalog_code}.res
```

Failed windows should contain `failure_traceback.txt` and native logs/FDTCC evidence when available.

## Manifest And Status Fields

`cc_window_status.csv` and `cc_window_manifest.json` should preserve:

- `window_id` and `ot_range`;
- `status`;
- `output_folder`;
- `input_events`;
- `dt_cc_pair_headers` and `dt_cc_data_lines`;
- `dtimes_total`, `events_after_dtime_match`, and `clusters` when parsed from HypoDD logs;
- `failure_kind` and `error_signature` for failed windows.

These status files are summaries. Long tracebacks and native logs should stay in separate evidence files.

## Files Not Sufficient For Success

These alone are not enough:

- generated SAC cache without non-empty `dt_*.cc`;
- FDTCC work directory with zero usable CC data lines;
- status/manifest files showing failed windows only;
- plots without native relocation outputs;
- per-window native files with no merged top-level outputs for a full-catalog task.
