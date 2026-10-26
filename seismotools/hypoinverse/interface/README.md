# HypoInverse location interface (version 1)

```bash
python seismotools/hypoinverse/interface/run.py \
  --arrivals arrivals.csv --stations stations.csv --velocity-model model.txt \
  --output-dir OUT [--config config.json] [--overwrite] [--quiet]
```

Requires the build (`python seismotools/support/build_native.py --tool hypoinverse`).
Same input contract as `seismotools/nonlinloc/interface/locate.py`, so the two
locators can be run on identical data.

## Inputs

| File | Columns | Notes |
|---|---|---|
| `--arrivals` | `event_id, pick_id, station_id, phase, time_utc[, uncertainty_s]` | one row per (event, station, phase); an event's arrivals must lie within 999 s of its first minute |
| `--stations` | `station_id, latitude, longitude, elevation_m` | elevation is written to the station file but CRH models ignore it (stations sit at the model surface) |
| `--velocity-model` | text `depth_km vp_km_s vs_km_s` | first row at 0; P and S become two CRH models paired with `SAL 1 2` (no fixed Vp/Vs) |

## Outputs

| File | Content |
|---|---|
| `events.csv` | `event_id, status (LOCATED / NOT_LOCATED), origin_time_utc, latitude, longitude, depth_km, rms_s, n_phases, n_s_phases, n_stations, gap_deg, erh_km, erz_km, min_distance_km, remark` (depth below the model surface; `remark` "-" = depth fixed by the program) |
| `arrivals.csv` | `event_id, pick_id, station_id, phase, residual_s, weight (used), distance_km` |
| `out.sum`, `out.arc`, `out.prt` | native summary, archive and print files |
| `stations.sta`, `p.crh`, `s.crh`, `phases.arc`, `locate.hyp`, `hyp.log` | generated inputs (stations aliased `S0001`…, net `XX`, component `HHZ`) and the run log |
| `config.json`, `run_result.json` | merged configuration; counts and any LVZ clipping |

## How the adapter writes HypoInverse inputs

Column positions follow the 1.40 manual and are checked against its sample
files: station format #2 (`H71 1 1 3`), Y2000 archive phase lines (P and S of
a station on one line; times in hundredths of a second, so arrivals are
rounded to 0.01 s), a header per event and a terminator carrying an integer
event id (cols 63-72). The command file sets `200 T 1900 0`, `LET 5 2 3 0 0`,
`ERR`, `RMS`, `MIN`, `ZTR … F`, `DI1`, `DIS`, `WET`, `JUN T` (force location
of poorly recorded events), `COP 3`, `CAR 1` and locates with `LOC`.

## Configuration

| Key | Default | Meaning |
|---|---|---|
| `velocity_layering` | `step` | `linear` profiles become constant sublayers of `linear_sublayer_km` (0.5) |
| `lvz_policy` | `error` | CRH models need velocities increasing with depth (manual); `clip` raises a slower (or equal) layer to 0.01 km/s above the one over it and reports each change in `run_result.json` |
| `trial_depth_km` | 5 | `ZTR` (depth not fixed) |
| `min_stations` | 4 | `MIN` |
| `timing_error_s` | 0.10 | `ERR` |
| `residual_weighting` | [4, 0.10, 2, 3] | `RMS` (NCSN defaults) |
| `distance_weighting` | [4, 15, 3.5, 7] | `DIS`: taper weights between 3.5× and 7× the distance of the 4th-nearest station (≥ 15 km) |
| `initial_distance_weighting` | [1, 50, 3, 6] | `DI1` |
| `weight_factors` | [1, 0.5, 0.2, 0.1] | `WET`: factors of weight codes 0-3 |
| `pick_weight_code` | P 0, S 1 | when arrivals carry no `uncertainty_s` |
| `uncertainty_codes_s` | [0.05, 0.10, 0.20, 0.40] | `uncertainty_s` ≤ these → codes 0-3, else 4 (unused) |

The weighting defaults are Northern California network values; set them for
the network geometry (distance weighting matters most). Station delays are
not supported in this version.
