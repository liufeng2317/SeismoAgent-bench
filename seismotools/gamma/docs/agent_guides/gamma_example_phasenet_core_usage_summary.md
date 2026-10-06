# Applying GaMMA to associate PhaseNet picks

Below is a concise, example-based workflow for using the gamma library to associate seismic phase picks to events, configure the run, call core functions, and handle outputs.

## 1) Import statements

```python
import pandas as pd
from gamma.utils import association, estimate_eps
import numpy as np
import os
from pyproj import Proj

import numpy as np
import random

np.random.seed(42)
random.seed(42)
```

## 2) Configuration

- Files and directories
  - Demo folders: test_data/ridgecrest or test_data/chile
  - Inputs: picks.csv, stations.csv, (optional) iasp91.csv for Chile
  - Outputs: results/{region}/gamma_events.csv, results/{region}/gamma_picks.csv

- Required DataFrame keys (column names)
  - picks DataFrame (rename to these keys before association):
    - id: station identifier (from station_id)
    - timestamp: pick time as pandas datetime (from phase_time)
    - type: phase type, e.g., P/S (from phase_type)
    - prob: pick probability/score (from phase_score)
    - amp: amplitude (from phase_amplitude)
  - stations DataFrame:
    - id: station identifier (from station_id)
    - longitude, latitude: station coordinates in degrees
    - elevation_m: elevation in meters (used to create z(km) = -elevation_m/1e3)
    - x(km), y(km), z(km): projected coordinates in kilometers (added via projection step)

- How to override config parameters
  - Build a Python dict config and set keys directly, e.g., config["use_dbscan"] = True.
  - Region-specific overrides (e.g., z(km), use_amplitude) are set via if region == "...".
  - Eikonal model and DBSCAN parameters are added to config as nested dicts/values.
  - Bounds, velocity, and filtering thresholds are directly assigned as shown below.

- Configuration parameters overview (from example)

```yaml
  # --- Method selection ---
  use_dbscan: true                      # bool: whether to use DBSCAN clustering
  use_amplitude: true                   # bool: whether to use amplitude information
  method: "BGMM"                        # str: Association method ("BGMM" or "GMM")
  oversample_factor: 5                  # int: oversampling factor for BGMM
  # covariance_prior: [5.0, 2.0]       # optional prior for (time, amplitude)

  # --- Earthquake location ---
  vel:                                  # dict: uniform velocity model
    p: 6.0
    s: 3.428571
  dims: ["x(km)", "y(km)", "z(km)"]    # list[str]: dimensions used for event location
  x(km): [xmin, xmax]                   # list[float]: projected x limits in km
  y(km): [ymin, ymax]                   # list[float]: projected y limits in km
  z(km): [zmin, zmax]                   # list[float]: projected depth limits in km

  bfgs_bounds:                           # list[list[float|None]]: optimization bounds for BFGS
    - [x(km)_min - 1, x(km)_max + 1]
    - [y(km)_min - 1, y(km)_max + 1]
    - [0, z(km)_max + 1]
    - [null, null]

  # --- DBSCAN parameters ---
  dbscan_eps: 15                         # float: DBSCAN eps parameter (km)
  dbscan_min_samples: 3                  # int: minimum samples for DBSCAN
  dbscan_min_cluster_size: 500           # int: min cluster size
  dbscan_max_time_space_ratio: 5         # float: max ratio of time to space

  # --- Eikonal velocity model ---
  eikonal:                               # dict: velocity model for travel-time computation
    vel:
      z: [0.0, 5.5, 16.0, 32.0]
      p: [5.5, 5.5, 6.7, 7.8]
      s: [3.18, 3.18, 3.88, 4.51]
    h: 1.0
    xlim: [xmin, xmax]
    ylim: [ymin, ymax]
    zlim: [zmin, zmax]

  # --- Runtime & CPU ---
  ncpu: 32                               # int: number of CPUs

  # --- Event filtering (post-association) ---
  min_picks_per_eq: 5                    # int: minimum picks per event
  min_p_picks_per_eq: 0                  # int: minimum P picks
  min_s_picks_per_eq: 0                  # int: minimum S picks
  max_sigma11: 3.0                       # float: maximum timing uncertainty (s)
  max_sigma22: 1.0                       # float: maximum amplitude uncertainty (log10 m/s)
  max_sigma12: 1.0                       # float: maximum covariance
```

- End-to-end setup (paths, reading/renaming, projection, and config)

```python
# 1) Set the running location
region = "ridgecrest"
# region = "chile"
data_path = lambda x: os.path.join(f"test_data/{region}", x)
result_path = f"results/{region}"
if not os.path.exists(result_path):
    os.makedirs(result_path)
result_path = lambda x: os.path.join(f"results/{region}", x)
station_csv = data_path("stations.csv")
picks_csv = data_path("picks.csv")
if not os.path.exists("figures"):
    os.makedirs("figures")
figure_dir = lambda x: os.path.join("figures", x)

# 2) Read and Rename the picks and stations
## read picks
picks = pd.read_csv(picks_csv, parse_dates=["phase_time"])
picks.rename(
    columns={
        "station_id": "id",
        "phase_time": "timestamp",
        "phase_type": "type",
        "phase_score": "prob",
        "phase_amplitude": "amp",
    },
    inplace=True,
)
print("Pick format:", picks.iloc[:10])

## read stations
stations = pd.read_csv(station_csv)
stations.rename(columns={"station_id": "id"}, inplace=True)
print("Station format:", stations.iloc[:10])

# 3) Configure Gamma
## Automatic region; you can also specify a region
x0   = stations["longitude"].median()
y0   = stations["latitude"].median()
xmin = stations["longitude"].min()
xmax = stations["longitude"].max()
ymin = stations["latitude"].min()
ymax = stations["latitude"].max()
config = {}
config["center"] = (x0, y0)
config["xlim_degree"] = (2 * xmin - x0, 2 * xmax - x0)
config["ylim_degree"] = (2 * ymin - y0, 2 * ymax - y0)

## projection to km
proj = Proj(f"+proj=aeqd +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
stations[["x(km)", "y(km)"]] = stations.apply(
    lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1
)
stations["z(km)"] = stations["elevation_m"].apply(lambda x: -x / 1e3)

### setting GMMA configs
config["use_dbscan"] = True
if region == "chile":
    config["use_amplitude"] = False
else:
    config["use_amplitude"] = True
config["method"] = "BGMM"
if config["method"] == "BGMM":  ## BayesianGaussianMixture
    config["oversample_factor"] = 5
if config["method"] == "GMM":  ## GaussianMixture
    config["oversample_factor"] = 2
#!!Prior for (time and amplitude): set a larger value to prevent splitting events. A too large value will cause merging events.
# config["covariance_prior"] = [5.0, 2.0]

# earthquake location
config["vel"] = {"p": 6.0, "s": 6.0 / 1.75}
config["dims"] = ["x(km)", "y(km)", "z(km)"]
config["x(km)"] = proj(longitude=config["xlim_degree"], latitude=[config["center"][1]] * 2)[0]
config["y(km)"] = proj(longitude=[config["center"][0]] * 2, latitude=config["ylim_degree"])[1]
if region == "ridgecrest":
    config["z(km)"] = (0, 20)
elif region == "chile":
    config["z(km)"] = (0, 250)
else:
    print("Please specify z(km) for your region")
    raise NotImplementedError
config["bfgs_bounds"] = (
    (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
    (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
    (0, config["z(km)"][1] + 1),  # z
    (None, None),  # t
)

# DBSCAN:
##!!Truncate the picks into segments: change the dbscan_eps to balance speed and event splitting. A larger eps prevent spliting events but can take longer time in the preprocessing step.
config["dbscan_eps"] = 15  # estimate_eps(stations, config["vel"]["p"])
config["dbscan_min_samples"] = 3
config["dbscan_min_cluster_size"] = 500
config["dbscan_max_time_space_ratio"] = 5

## using Eikonal for 1D velocity model
if region == "ridgecrest":
    zz = [0.0, 5.5, 16.0, 32.0]
    vp = [5.5, 5.5, 6.7, 7.8]
    vp_vs_ratio = 1.73
    vs = [v / vp_vs_ratio for v in vp]
    h = 1.0
    vel = {"z": zz, "p": vp, "s": vs}
    config["eikonal"] = {
        "vel": vel,
        "h": h,
        "xlim": config["x(km)"],
        "ylim": config["y(km)"],
        "zlim": config["z(km)"],
    }
elif region == "chile":
    velocity_model = pd.read_csv(data_path("iasp91.csv"), names=["zz", "rho", "vp", "vs"])
    velocity_model = velocity_model[velocity_model["zz"] <= config["z(km)"][1]]
    vel = {
        "z": velocity_model["zz"].values,
        "p": velocity_model["vp"].values,
        "s": velocity_model["vs"].values,
    }
    h = 1.0
    config["eikonal"] = {
        "vel": vel,
        "h": h,
        "xlim": config["x(km)"],
        "ylim": config["y(km)"],
        "zlim": config["z(km)"],
    }
else:
    print("Using uniform velocity model")

# set number of cpus
config["ncpu"] = 32

##!!Post filtering (indepent of gmm): change these parameters to filter out associted picks with large errors
config["min_picks_per_eq"] = 5
config["min_p_picks_per_eq"] = 0
config["min_s_picks_per_eq"] = 0
config["max_sigma11"] = 3.0  # second
config["max_sigma22"] = 1.0  # log10(m/s)
config["max_sigma12"] = 1.0  # covariance

## filter picks without amplitude measurements
if config["use_amplitude"]:
    picks = picks[picks["amp"] != -1]

for k, v in config.items():
    print(f"{k}: {v}")
```

Notes:
- dbscan_eps can be estimated via estimate_eps(stations, config["vel"]["p"]) as shown in the inline comment.
- If use_amplitude is True, remove picks with amp == -1.
- Be sure picks are a pandas DataFrame with the required renamed keys before association.
- stations must include projected x(km), y(km), z(km) as shown.

## 3) Main function calls (inputs/outputs)

- Core call
  - Function: association(picks, stations, config, event_idx0, method)
  - Inputs:
    - picks: DataFrame with columns [id, timestamp, type, prob, amp]
    - stations: DataFrame with [id, longitude, latitude, elevation_m] plus projected [x(km), y(km), z(km)]
    - config: dict with keys described above (DBSCAN, velocity, bounds, eikonal, filters, etc.)
    - event_idx0: integer starting index for event_index
    - method: "BGMM" or "GMM" (e.g., config["method"])
  - Outputs:
    - events: list/dict convertible to DataFrame with event metadata and location in km
    - assignments: list of [pick_index, event_index, gamma_score]

```python
# Association with GaMMA
event_idx0 = 0  ## current earthquake index
assignments = []
events, assignments = association(picks, stations, config, event_idx0, config["method"])
event_idx0 += len(events)
```

- Output formats (examples)
  - events DataFrame columns:
    - time,magnitude,sigma_time,sigma_amp,cov_time_amp,gamma_score,
      num_picks,num_p_picks,num_s_picks,event_index,x(km),y(km),z(km)
  - assignments DataFrame columns:
    - pick_index,event_index,gamma_score
  - Index and linkage:
    - pick_index matches picks.index values of the input picks.
    - event_index matches the event_index column in events.

Example rows (from the example content):
```csv
# events
time,magnitude,sigma_time,sigma_amp,cov_time_amp,gamma_score,num_picks,num_p_picks,num_s_picks,event_index,x(km),y(km),z(km)
2023-01-01T18:38:36.386,1.706,3.287,0.257,-0.1432,8.0,7,4,3,2,-249.3940,-25.8243,0.0
2023-01-01T18:51:28.791,0.117,0.485,0.635,0.0677,5.0,5,4,1,0,-370.6695,290.6818,0.0
```

```csv
# assignments
pick_index,event_index,gamma_score
987,2,0.01845
1102,2,0.01435
```

## 4) Output handling (processing, saving, and joining assignments)

- Convert events to DataFrame, add lon/lat, and save
- Convert assignments to DataFrame, join back to picks using pick_index, and save
- After joining, event_index = -1 indicates not associated

```python
# create a catalog with the estimated location
events = pd.DataFrame(events)
events[["longitude", "latitude"]] = events.apply(
    lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)),
    axis=1,
)
events["depth_km"] = events["z(km)"]
events.to_csv(
    result_path("gamma_events.csv"),
    index=False,
    float_format="%.3f",
    date_format="%Y-%m-%dT%H:%M:%S.%f",
)

## add assignment to picks (!!! important)
assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({"event_index": int})
picks.rename(
    columns={
        "id": "station_id",
        "timestamp": "phase_time",
        "type": "phase_type",
        "prob": "phase_score",
        "amp": "phase_amplitude",
    },
    inplace=True,
)
picks.to_csv(result_path("gamma_picks.csv"), index=False, date_format="%Y-%m-%dT%H:%M:%S.%f")
```

- Assign event index to picks correctly (standalone snippet)
```python
# assign the event index to the picks correctly
# picks.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})
```

- Example of assigned picks (event_index = -1 means not used)
```csv
station_id,phase_time,phase_type,phase_score,phase_amplitude,event_index,gamma_score
BK.AASB.00.HH,2023-01-01 18:35:49.170,P,0.476,6.782000e-06,72,3.327747e-08
BK.ADAM.00.HH,2023-01-01 18:32:33.250,P,0.488,3.604000e-07,27,4.517431e-03
BK.ADAM.00.HH,2023-01-01 18:52:58.650,P,0.520,2.249000e-07,-1,-1.000000e+00
```

- Optional: Group picks by event (convenience)
```python
# group the picks to events
grouped_picks = {event_idx: group for event_idx, group in picks.groupby("event_index")}
# exclude the event_index = -1
grouped_picks = {k: v for k, v in grouped_picks.items() if k != -1}

# print the events information and corresponding picks
event_id = 0
print(events[events["event_index"] == event_id])
print(grouped_picks[event_id])
```

This completes the core usage: import, configure, call association, and handle outputs (including joining assignments back to the original picks via pick_index).
