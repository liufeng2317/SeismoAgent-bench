# Use GaMMA to associate PhaseNet picks

Applying GaMMA to associate PhaseNet picks

## 1) Import statements

```python
import os
import json
import numpy as np
import pandas as pd
from pyproj import Proj
from gamma.utils import association, estimate_eps
```

## 2) Configuration

- What GaMMA expects (DataFrame column keys):
  - picks DataFrame (required columns, after renaming):
    - id: station id (string)
    - timestamp: pick time (datetime64[ns])
    - type: phase type, e.g., "P" or "S" (string)
    - prob: pick probability/score (float)
    - amp: pick amplitude (float; filter out -1 if using amplitude)
  - stations DataFrame (required fields):
    - id: station id (string)
    - longitude, latitude (float)
    - elevation_m (float; used to derive depth)
    - x(km), y(km), z(km): projected coordinates in km (z is depth in km; negative elevation)
- How to override config parameters:
  - Use a Python dict config where keys match those shown below (types/values as in the example).
  - You can derive spatial bounds and projection from a region config file (e.g., config.json) and set/override any value programmatically (see code).

Human summary of key parameters:
- Method selection:
  - use_dbscan (bool): enable DBSCAN pre-clustering.
  - use_amplitude (bool): include amplitude in association.
  - method (str): "BGMM" or "GMM".
  - oversample_factor (int): 5 for BGMM, 1 for GMM.
- Earthquake location:
  - vel (dict): uniform velocity model, e.g., {"p": 6.0, "s": 3.428571}.
  - dims (list[str]): typically ["x(km)", "y(km)", "z(km)"].
  - x(km), y(km), z(km): search bounds in km (projected; z is depth range).
  - bfgs_bounds: optimization bounds for [x, y, z, t].
- DBSCAN:
  - dbscan_eps (float): eps in km (can be estimated with estimate_eps).
  - dbscan_min_samples (int).
- Eikonal (optional 1D velocity model for travel times):
  - eikonal = {"vel": {"z": [...], "p": [...], "s": [...]}, "h": 1.0, "xlim": [...], "ylim": [...], "zlim": [...]}
- Runtime:
  - ncpu (int): number of CPUs.
- Event filtering:
  - min_picks_per_eq, min_p_picks_per_eq, min_s_picks_per_eq
  - max_sigma11, max_sigma22, max_sigma12

Example config schema (from the example):

```yaml
# --- Method selection ---
use_dbscan: true
use_amplitude: true
method: "BGMM"
oversample_factor: 5

# --- Earthquake location ---
vel: {p: 6.0, s: 3.428571}
dims: ["x(km)", "y(km)", "z(km)"]
x(km): [xmin, xmax]
y(km): [ymin, ymax]
z(km): [zmin, zmax]

bfgs_bounds:
  - [x(km)_min-1, x(km)_max+1]
  - [y(km)_min-1, y(km)_max+1]
  - [0, z(km)_max+1]
  - [null, null]

# --- DBSCAN parameters ---
dbscan_eps: 10
dbscan_min_samples: 3

# --- Eikonal velocity model ---
eikonal:
  vel:
    z: [0.0, 5.5, 16.0, 32.0]
    p: [5.5, 5.5, 6.7, 7.8]
    s: [3.18, 3.18, 3.88, 4.51]
  h: 1.0
  xlim: [xmin, xmax]
  ylim: [ymin, ymax]
  zlim: [zmin, zmax]

# --- Initial points (optional) ---
initial_points: [1, 1, 1]

# --- Runtime & CPU ---
ncpu: 32

# --- Event filtering ---
min_picks_per_eq: 5
min_p_picks_per_eq: 0
min_s_picks_per_eq: 0
max_sigma11: 15.0
max_sigma22: 3.0
max_sigma12: 3.0
```

End-to-end preparation and overrides (including paths, reading/renaming, projection, and config):

```python
# set the running location
region = "ncedc"
test_name = "mtj"
data_path = lambda x: os.path.join(f"test_data/{region}", x)
result_dir = f"results/{region}"
os.makedirs(result_dir, exist_ok=True)
result_path = lambda x: os.path.join(result_dir, x)
station_json = data_path("stations.json")
if test_name == "geyser":
    picks_csv = data_path("picks_geyser.csv")
if test_name == "mtj":
    picks_csv = data_path("picks_mtj.csv")

## read picks
picks = pd.read_csv(picks_csv, parse_dates=["phase_time"])
picks = picks[['station_id', 'phase_time', 'phase_type', 'phase_score', 'phase_amplitude']]
if test_name == "geyser":
    picks = picks[(picks["phase_time"] >= "2023-03-02 21:15:00") & (picks["phase_time"] <= "2023-03-02 21:30:00")]

# REQUIRED picks columns for GaMMA: id, timestamp, type, prob, amp
picks.rename(columns={"station_id": "id", "phase_time": "timestamp",
                      "phase_type": "type", "phase_score": "prob",
                      "phase_amplitude": "amp"}, inplace=True)
print("Pick format:", picks.iloc[:3])

## read stations (must contain id, longitude, latitude, elevation_m)
stations = pd.read_json(station_json, orient="index")
stations["id"] = stations.index
print("Station format:", stations.iloc[:3])

## automatic region; you can also specify a region
with open(data_path("config.json"), "r") as f:
    config = json.load(f)
    config["center"] = ((config["minlongitude"] + config["maxlongitude"]) / 2,
                        (config["minlatitude"] + config["maxlatitude"]) / 2)
    config["xlim_degree"] = (config["minlongitude"], config["maxlongitude"])
    config["ylim_degree"] = (config["minlatitude"], config["maxlatitude"])

## projection to km (Azimuthal Equidistant)
proj = Proj(f"+proj=aeqd +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
stations[["x(km)", "y(km)"]] = stations.apply(
    lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1)
stations["z(km)"] = stations["elevation_m"].apply(lambda x: -x/1e3)

# region crop and station-pick consistency
stations = stations[
    (stations["longitude"] > config["minlongitude"]) & (stations["longitude"] < config["maxlongitude"]) &
    (stations["latitude"] > config["minlatitude"]) & (stations["latitude"] < config["maxlatitude"])
]
picks = picks[picks["id"].isin(stations["id"])]

### setting GaMMA configs (override/extend)
config["use_dbscan"] = True
config["use_amplitude"] = (region != "chile")
config["method"] = "BGMM"
config["oversample_factor"] = 5 if config["method"] == "BGMM" else 1

# earthquake location
config["vel"] = {"p": 6.0, "s": 6.0 / 1.75}
config["dims"] = ['x(km)', 'y(km)', 'z(km)']
config["x(km)"] = proj(longitude=config["xlim_degree"], latitude=[config["center"][1]] * 2)[0]
config["y(km)"] = proj(longitude=[config["center"][0]] * 2, latitude=config["ylim_degree"])[1]

# depth range by region
if region == "ridgecrest":
    config["z(km)"] = (0, 20)
elif region == "chile":
    config["z(km)"] = (0, 250)
else:
    config["z(km)"] = (0, 30)
    print("Please specify z(km) for your region")

# optimizer bounds: (x, y, z, t)
config["bfgs_bounds"] = (
    (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
    (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
    (0, config["z(km)"][1] + 1),                       # z
    (None, None),                                      # t
)

# DBSCAN parameters
# Optionally estimate eps: estimate_eps(stations, config["vel"]["p"])
config["dbscan_eps"] = 10
config["dbscan_min_samples"] = 3

## using Eikonal for 1D velocity model (optional)
if region == "ridgecrest":
    zz = [0.0, 5.5, 16.0, 32.0]
    vp = [5.5, 5.5,  6.7,  7.8]
    vp_vs_ratio = 1.73
    vs = [v / vp_vs_ratio for v in vp]
    h = 1.0
    vel = {"z": zz, "p": vp, "s": vs}
    config["eikonal"] = {"vel": vel, "h": h,
                         "xlim": config["x(km)"], "ylim": config["y(km)"], "zlim": config["z(km)"]}
elif region == "chile":
    velocity_model = pd.read_csv(data_path("iasp91.csv"), names=["zz", "rho", "vp", "vs"])
    velocity_model = velocity_model[velocity_model["zz"] <= config["z(km)"][1]]
    vel = {"z": velocity_model["zz"].values,
           "p": velocity_model["vp"].values,
           "s": velocity_model["vs"].values}
    h = 1.0
    config["eikonal"] = {"vel": vel, "h": h,
                         "xlim": config["x(km)"], "ylim": config["y(km)"], "zlim": config["z(km)"]}
else:
    print("Using uniform velocity model")

# initial search grid (optional, e.g., Chile)
if region == "chile":
    config["initial_points"] = [1, 1, 1]  # x, y, z

# resources and filtering
config["ncpu"] = 32
config["min_picks_per_eq"] = 5
config["min_p_picks_per_eq"] = 0
config["min_s_picks_per_eq"] = 0
config["max_sigma11"] = 3.0 * 5  # second
config["max_sigma22"] = 1.0 * 3  # log10(m/s)
config["max_sigma12"] = 1.0 * 3  # covariance

## filter picks without amplitude measurements (only if using amplitude)
if config["use_amplitude"]:
    picks = picks[picks["amp"] != -1]

for k, v in config.items():
    print(f"{k}: {v}")
```

## 3) Main function calls

Core GaMMA association call and I/O format:

```python
# Association with GaMMA
event_idx0 = 0  # current earthquake index to start numbering
events, assignments = association(picks, stations, config, event_idx0, config["method"])
```

Inputs:
- picks: DataFrame with required keys [id, timestamp, type, prob, amp]
- stations: DataFrame with keys [id, longitude, latitude, elevation_m, x(km), y(km), z(km)]
- config: dict of parameters shown above
- event_idx0: int, starting index for event_index
- method: "BGMM" or "GMM"

Outputs:
- events: list/records convertible to DataFrame with columns like:
  - time, magnitude, sigma_time, sigma_amp, cov_time_amp, gamma_score,
    num_picks, num_p_picks, num_s_picks, event_index, x(km), y(km), z(km)
- assignments: list of triples [pick_index, event_index, gamma_score]
  - pick_index corresponds to the input picks.index values
  - event_index corresponds to events.event_index

Example events CSV format (from the example):
```
time,magnitude,sigma_time,sigma_amp,cov_time_amp,gamma_score,num_picks,num_p_picks,num_s_picks,event_index,x(km),y(km),z(km)
2023-01-01T18:38:36.386,1.706,3.287,0.257,-0.1432,8.0,7,4,3,2,-249.3940,-25.8243,0.0
2023-01-01T18:51:28.791,0.117,0.485,0.635,0.0677,5.0,5,4,1,0,-370.6695,290.6818,0.0
2023-01-01T18:39:51.532,2.047,6.223,0.265,0.2399,12.8179,11,5,6,9,-254.3663,-8.2548,6.6394
2023-01-01T18:59:12.964,1.062,5.826,0.214,0.8124,5.0,5,2,3,1,-124.8804,-90.4987,0.0
```

Example assignments CSV format:
```
pick_index,event_index,gamma_score
987,2,0.01845
1102,2,0.01435
```

## 4) Output handling

- Save events, convert projected coordinates back to lon/lat, and persist to CSV.
- Join assignments to picks by pick_index to add event_index (and gamma_score) back to the original picks.
- Group picks by event_index for downstream usage.

```python
# Convert and save events
events = pd.DataFrame(events)
events.to_csv("./temp_events.csv", index=False)

# add longitude/latitude and depth for output
events[["longitude","latitude"]] = events.apply(
    lambda x: pd.Series(Proj(f"+proj=aeqd +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
                        (longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1)
events["depth_km"] = events["z(km)"]

events.to_csv(
    result_path("gamma_events.csv"),
    index=False,
    float_format="%.3f",
    date_format='%Y-%m-%dT%H:%M:%S.%f'
)

# Assign the event index to the picks (!!! important)
assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
assignments.to_csv("./temp_assignments.csv", index=False)

# Join by pick_index; fill missing with -1 and cast event_index to int
picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})

# (Optional) rename back to original pick column names for exporting
picks.rename(columns={"id": "station_id", "timestamp": "phase_time",
                      "type": "phase_type", "prob": "phase_score",
                      "amp": "phase_amplitude"}, inplace=True)

picks.to_csv(
    result_path("gamma_picks.csv"),
    index=False,
    date_format='%Y-%m-%dT%H:%M:%S.%f'
)

# Group the picks to events; event_index = -1 means not used
grouped_picks = {event_idx: group for event_idx, group in picks.groupby("event_index")}
grouped_picks = {k: v for k, v in grouped_picks.items() if k != -1}

# Example: print one event and its assigned picks
event_id = 0
print(events[events["event_index"] == event_id])
print(grouped_picks[event_id])
```

Notes:
- Join assignment info to the original picks using pick_index. The pick_index aligns with the original picks DataFrame index (picks.index.values) before the join.
- An event_index of -1 indicates the pick was not used/assigned.
