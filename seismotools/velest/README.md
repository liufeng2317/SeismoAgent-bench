# VELEST

VELEST (Kissling et al. 1994) inverts arrival times jointly for hypocentres, a layered 1-D P and S velocity model and station corrections: the "minimum 1-D model" used as the starting model of local tomography and as the routine location model of many networks. This package wraps VELEST 3.x in simultaneous mode.

## Use

```bash
python seismotools/velest/interface/run.py \
  --arrivals arrivals.csv --events events.csv --stations stations.csv \
  --model start_model.txt [--vpvs 1.73] --use-s --output-dir velest_run/
```

| Input | Columns |
|---|---|
| `--arrivals` | `event_id, station_id, phase (P/S), time_utc` (optional `weight` 0–4, 0 best) |
| `--events` | starting hypocentres: `event_id, origin_time_utc, latitude, longitude, depth_km` (km below sea level) |
| `--stations` | `station_id, latitude, longitude, elevation_m` |
| `--model` | one row per layer: `top_km vp_km_s [vs_km_s]`, tops in km below sea level (negative above it); `--vpvs` gives Vs when there is no Vs column |

Outputs: `model_final.txt` (`top_km vp_km_s vs_km_s`), `station_corrections.csv` (`station_id, p_correction_s, s_correction_s`; positive = arrivals later than predicted; the reference station keeps a P correction of zero), `events_final.csv`, `summary.json` (events used, reference station, RMS per iteration, starting and final model) and the native files in `velest/`.

The events are selected by data quality, best first (`--min-p 8`, `--min-s 2`, `--max-gap 180`, up to `--max-events 500`; VELEST holds at most 658). The model top is raised above the highest station when needed (every station must lie inside the first layer). Station codes are mapped to four-character aliases internally. Other controls: `--iterations` (9), `--damping OTHET XYTHET ZTHET VTHET STATHET` (0.01 0.01 0.01 1.0 0.1), `--no-station-corrections`, `--veladj`, `--zadj`, `--dmax`, `--low-velocity`, `--reference-station`.

## What a minimum 1-D model needs

One run is not a minimum 1-D model. The standard procedure (Kissling 1988; Kissling et al. 1994):

- **Use well-constrained events only** (many P and S picks, azimuthal gap below 180°, a station within about one focal depth).
- **Start from several models** (a regional model, a generic one, the regional one faster and slower by 5–10 %) and keep the result only where the final models converge; layers whose velocity depends on the start are not resolved by the data.
- **Perturb the hypocentres** (shift them by a few km) and check that they return; if they do not, the model does not constrain them.
- **Check the station corrections against the geology**: slow ground (sediment, basin fill) gives positive corrections, hard rock near zero; corrections that are all of one sign or grow with distance from the reference station point to a model error absorbed by the stations.
- **Velocity and depth trade off**: a model that lowers the misfit can still move all depths and origin times together. Compare the result with independent information before adopting it, and report the spread over the converging models as an uncertainty.

## Build and test

```bash
python seismotools/support/build_native.py --tool velest   # fetches the pinned source, compiles runtime/bin/velest
bash seismotools/velest/examples/smoke/run.sh             # the program's own example must reproduce its reference output
```

The source is VELEST 3.x as revised to compile with gfortran (https://github.com/sean0921/velest_revised, pinned commit in `support/build_native.py`). That repository states no license, so the source is fetched at build time and not copied into this project.

Reference: Kissling, E., W. L. Ellsworth, D. Eberhart-Phillips and U. Kradolfer (1994). Initial reference models in local earthquake tomography. J. Geophys. Res. 99, 19635–19646.
