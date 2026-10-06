# CASE_CROSS_CORRELATION File Summary

This case describes real inputs and outputs for FDTCC-enabled HypoDD relocation through the Python API. The files below are real inputs/outputs for FDTCC-enabled HypoDD relocation.

## Required Inputs

### Function Inputs

- `hypo_root`: HYPODD executable root containing `ph2dt/ph2dt` and `hypoDD/hypoDD`.
- `phase_file`: event-block phase file.
- `station_file`: station coordinate file.
- `output_folder`: writable run directory.
- `catalog_code`: output prefix.
- `waveform_dir_raw`: raw MiniSEED root or existing FDTCC SAC tree depending on `wave_dir_mode`.
- FDTCC velocity arrays and `fdtcc.flags`.

### Station File

```text
network.station,latitude,longitude[,optional_columns...]
NET.STA,lat,lon
```

No-header station files are also accepted as `NET.STA,lat,lon[,elevation_m]`. For FDTCC/CC, station ids must provide real network information through `NET.STA`, separate network/station columns, or `station_default_network` when that network is known and matches waveform files.

### Phase File

```text
origin_time,lat,lon,depth,mag,evid
NET.STA,p_pick_time,s_pick_time
```

Event headers must have parsable time, numeric latitude/longitude/depth, and preferably integer event id. Magnitude should be numeric when available, but empty/bad magnitude is accepted by the package and filled as `0.0`. Pick rows must keep station ids consistent with station and waveform metadata.

### Waveform Inputs

- `wave_dir_mode="miniseed"`: `waveform_dir_raw` points to raw MiniSEED; the package prepares/caches an FDTCC-compatible SAC tree.
- `wave_dir_mode="fdtcc_sac"`: `waveform_dir_raw` already points to an FDTCC SAC tree.
- Reuse an existing SAC cache when possible for expensive waveform conversion.

## Expected Native Outputs

Under `output_folder` for one grid:

```text
hypoDD_station.dat
hypoDD_phase.dat
hypoDD_phase_0-0.dat
event_0-0.dat
dt_0-0.ct
dt_0-0.cc
0-0.ph2dt
0-0.hypoDD
hypoDD.log
{catalog_code}.loc
{catalog_code}.reloc
{catalog_code}.pha
{catalog_code}.res
```

FDTCC work directories/logs may include `fdtcc_stdout.log`, `fdtcc_stderr.log`, and failure-evidence JSON.

## Success Evidence

A real cross-correlation result requires:

- non-empty `dt_*.ct`;
- non-empty `dt_*.cc`;
- non-empty `{catalog_code}.loc`, `{catalog_code}.reloc`, and `{catalog_code}.res`;
- logs showing real `ph2dt`, FDTCC, and `hypoDD` execution.

Do not report success from generated configs, copied templates, empty files, skipped execution, or plots alone.

## Batched Or Windowed Outputs

For full-catalog runs split into independent units, each unit should keep its own native files and logs. The task-level output should also include:

- manifest/status table with unit id, counts, status, output folder, and short failure signature;
- consolidated relocated catalog with unit id and verified original event id;
- failed/unrelocated-event table;
- global plots summarizing coverage, shifts, and residuals.

Failure tracebacks/native logs should be written to separate evidence files. The manifest should store concise status and paths, not long tracebacks.
