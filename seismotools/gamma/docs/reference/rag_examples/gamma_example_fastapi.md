# Interactive Example of using Gamma to Phase association and location

```python
import requests
import json
import pandas as pd
import os
import warnings
import numpy as np
import matplotlib.pyplot as plt
%load_ext autoreload
%autoreload 2
```

```python
# GAMMA_API_URL = "http://127.0.0.1:8000"
GAMMA_API_URL = "https://ai4eps-gamma.hf.space"

```

## 2. Prepare test data

- Download test data: PhaseNet picks of the 2019 Ridgecrest earthquake sequence
1. picks file: picks.json
2. station information: stations.csv
3. events in SCSN catalog: events.csv
4. config file: config.pkl

```python
# prepare the input and output path
data_dir = lambda x: os.path.join("test_data", x)
station_csv = data_dir("stations.csv")
pick_json = data_dir("picks.json")
catalog_csv = data_dir("catalog_gamma.csv")
picks_csv = data_dir("picks_gamma.csv")
if not os.path.exists("figures"):
    os.makedirs("figures")
figure_dir = lambda x: os.path.join("figures", x)

# set the gamma config
config = {'xlim_degree': [-118.004, -117.004],
          'ylim_degree': [35.205, 36.205],
          'z(km)': [0, 41]}

# read stations
stations = pd.read_csv(station_csv, delimiter="\t")
stations = stations.rename(columns={"station":"station_id"})

# read picks
picks = pd.read_json(pick_json).sort_values("timestamp").iloc[:200]
picks["timestamp"] = pd.to_datetime(picks["timestamp"])


```

## Rename of the picks and stations dataframe

```python
picks.rename(columns={
    "id": "station_id",
    "timestamp": "phase_time",
    "prob": "phase_score",
    "amp": "phase_amplitude",
    "type": "phase_type"},
    inplace=True
    )
stations.rename(columns={
    "id": "station_id",
    "elevation(m)": "elevation_m"},
    inplace=True
    )
```

- picks require metadata: `id`, `timestamp`, `prob`, `amp`, `type`
- stations require metadata: `id`, `elevation(m)`

```python
# rename the columns as the gamma format (required by the gamma: station_id, phase_time, phase_score, phase_amplitude, phase_type)
picks.rename(columns={"id": "station_id", "timestamp": "phase_time", "prob": "phase_score", "amp": "phase_amplitude", "type": "phase_type"}, inplace=True)

# rename the columns as the gamma format (required by the gamma: station_id, elevation_m)
stations.rename(columns={"id": "station_id", "elevation(m)": "elevation_m"}, inplace=True)

# drop the columns that are not required by the gamma
stations.drop(columns=["unit", "component", "response"], inplace=True, errors="ignore")
```

```python
# upper the phase type (e.g. p -> P, s -> S)
picks["phase_type"] = picks["phase_type"].str.upper()

```

```python
# merge the picks and stations on the station_id
picks = picks.merge(stations[["station_id", "latitude", "longitude", "elevation_m"]], on="station_id", how="left")
```

```python
# filter some of the picks by phase time
picks = picks[(picks["phase_time"] > pd.to_datetime("2019-07-04T17:02:00.000")) & (picks["phase_time"] < pd.to_datetime("2019-07-04T17:04:00.000"))]
```

```python
# figure the picks (x-axis: time, y-axis: latitude)
plt.figure()
color = {"P": "red", "S": "blue"}
plt.scatter(picks["phase_time"], picks["latitude"], c=picks["phase_type"].apply(lambda x: color[x]), s=10)
plt.scatter([], [], c="red", label="P")
plt.scatter([], [], c="blue", label="S")
plt.legend()
plt.show()
```

## Define the runing function and configs for using gamma


```python
import pandas as pd
from fastapi import FastAPI
from gamma.utils import association
from pyproj import Proj

app = FastAPI()

@app.get("/")
def greet_json():
    return {"Hello": "GaMMA!"}

@app.post("/predict/")
def predict(picks: dict, stations: dict, config: dict):
    picks = picks["data"]
    stations = stations["data"]
    picks = pd.DataFrame(picks)
    picks["phase_time"] = pd.to_datetime(picks["phase_time"])
    stations = pd.DataFrame(stations)
    events_, picks_ = run_gamma(picks, stations, config)
    if events_ is None:
        return {"events": None, "picks": picks_}
    events_ = events_.to_dict(orient="records")
    picks_ = picks_.to_dict(orient="records")

    return {"events": events_, "picks": picks_}
```

### gamma_config settings
```yaml
  # --- Basic configuration ---
  min_picks: 8                  # int: Minimum number of picks required
  min_picks_ratio: 0.2          # float: Minimum ratio of picks
  max_residual_time: 1.0        # float: Maximum residual time in seconds
  max_residual_amplitude: 1.0   # float: Maximum residual amplitude
  min_score: 0.6                # float: Minimum score threshold
  min_s_picks: 2                # int: Minimum number of S-phase picks
  min_p_picks: 2                # int: Minimum number of P-phase picks
  use_amplitude: true           # bool: Whether to use amplitude information

  # --- Region settings ---
  region: "ridgecrest"          # str: region name
  minlongitude: -118.004        # float: Minimum longitude
  maxlongitude: -117.004        # float: Maximum longitude
  minlatitude: 35.205           # float: Minimum latitude
  maxlatitude: 36.205           # float: Maximum latitude
  mindepth_km: 0.0              # float: Minimum depth (km)
  maxdepth_km: 41.0             # float: Maximum depth (km)

  # --- Projection (computed) ---
  xlim_km: [xmin, xmax]         # list[float]: projected x range (km)
  ylim_km: [ymin, ymax]         # list[float]: projected y range (km)
  zlim_km: [0.0, 41.0]          # list[float]: depth range (km)
  z(km): [0.0, 41.0]            # list[float]: alias for depth range
  proj: null                     # object: pyproj.Proj instance (runtime only)

  # --- Event filtering ---
  min_picks_per_eq: 5           # int: Minimum picks per event
  min_p_picks_per_eq: 0         # int: Minimum P picks per event
  min_s_picks_per_eq: 0         # int: Minimum S picks per event
  max_sigma11: 3.0              # float: Max time uncertainty
  max_sigma22: 1.0              # float: Max amplitude uncertainty
  max_sigma12: 1.0              # float: Max covariance

  # --- Association parameters ---
  use_dbscan: false             # bool: Whether to use DBSCAN instead of BGMM
  oversample_factor: 8.0        # float: Oversampling factor for BGMM
  dims: ["x(km)", "y(km)", "z(km)"] # list[str]: Event location dimensions
  method: "BGMM"                # str: Association method ("BGMM" or "GMM")
  ncpu: 1                       # int: Number of CPUs

  # --- Velocity model ---
  vel:                          # dict: uniform velocity model
    p: 6.0                      # float: P-wave velocity (km/s)
    s: 3.428571                 # float: S-wave velocity (km/s)

  # --- Optimization bounds ---
  bfgs_bounds:                  # list[list[float|None]]: bounds for BFGS
    - [xmin-1, xmax+1]          # X range
    - [ymin-1, ymax+1]          # Y range
    - [0, zmax+1]               # Z range
    - [null, null]              # Time (unbounded)

  # --- Runtime ---
  event_index: 0                # int: Event index counter

```

```python
def set_config(region="ridgecrest"):
    """set config for gamma
    """
    # set the basic config of the gamma
    config = {
        "min_picks": 8,
        "min_picks_ratio": 0.2,
        "max_residual_time": 1.0,
        "max_residual_amplitude": 1.0,
        "min_score": 0.6,
        "min_s_picks": 2,
        "min_p_picks": 2,
        "use_amplitude": False,
    }
    ## Domain of the region
    if region.lower() == "ridgecrest":
        config.update(
            {
                "region": "ridgecrest",
                "minlongitude": -118.004,
                "maxlongitude": -117.004,
                "minlatitude": 35.205,
                "maxlatitude": 36.205,
                "mindepth_km": 0.0,
                "maxdepth_km": 41.0,
            }
        )
    # set the projection of the region
    lon0 = (config["minlongitude"] + config["maxlongitude"]) / 2
    lat0 = (config["minlatitude"] + config["maxlatitude"]) / 2
    proj = Proj(f"+proj=aeqd +lon_0={lon0} +lat_0={lat0}  +units=km")
    xmin, ymin = proj(config["minlongitude"], config["minlatitude"])
    xmax, ymax = proj(config["maxlongitude"], config["maxlatitude"])
    zmin, zmax = config["mindepth_km"], config["maxdepth_km"]
    xlim_km = (xmin, xmax)
    ylim_km = (ymin, ymax)
    zlim_km = (zmin, zmax)
    # update the config
    config.update(
        {
            "xlim_km": xlim_km,
            "ylim_km": ylim_km,
            "zlim_km": zlim_km,
            "z(km)": zlim_km,
            "proj": proj,
        }
    )
    config.update(
        {
            "min_picks_per_eq": 5,
            "min_p_picks_per_eq": 0,
            "min_s_picks_per_eq": 0,
            "max_sigma11": 3.0,
            "max_sigma22": 1.0,
            "max_sigma12": 1.0,
        }
    )
    # set the search method of the gamma
    config["use_dbscan"] = False
    config["use_amplitude"] = True
    config["oversample_factor"] = 8.0
    config["dims"] = ["x(km)", "y(km)", "z(km)"]
    config["method"] = "BGMM"
    config["ncpu"] = 32
    vel = {"p": 6.0, "s": 6.0 / 1.75}
    config["vel"] = vel

    config["bfgs_bounds"] = (
        (xlim_km[0] - 1, xlim_km[1] + 1),  # x
        (ylim_km[0] - 1, ylim_km[1] + 1),  # y
        (0, zlim_km[1] + 1),  # z
        (None, None),  # t
    )
    config["event_index"] = 0
    return config
config = set_config()
```

### runing gamma for phase association

- gamma.association usage
    ```python
    events, assignments = association(picks, stations, config, 0, config["method"])
    ```
- example format of the output `events`
    ```csv
    time,magnitude,sigma_time,sigma_amp,cov_time_amp,gamma_score,num_picks,num_p_picks,num_s_picks,event_index,x(km),y(km),z(km)
    2023-01-01T18:38:36.386,1.706,3.287,0.257,-0.1432,8.0,7,4,3,2,-249.3940,-25.8243,0.0
    2023-01-01T18:51:28.791,0.117,0.485,0.635,0.0677,5.0,5,4,1,0,-370.6695,290.6818,0.0
    2023-01-01T18:39:51.532,2.047,6.223,0.265,0.2399,12.8179,11,5,6,9,-254.3663,-8.2548,6.6394
    2023-01-01T18:59:12.964,1.062,5.826,0.214,0.8124,5.0,5,2,3,1,-124.8804,-90.4987,0.0
    ```
- example format of the output `assignments`
    ```csv
    pick_index,event_index,gamma_score
    987,2,0.01845
    1102,2,0.01435
    ```
    - Note:
       - `pick_index` matches the `picks.index.values` index of the input picks.
       - `event_index` matches the `event_index` column in the `events` DataFrame.
- link the events with corresponding picks
    - assign the event index to the picks correctly
      - `picks.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})`
      - example of assigned picks
        ```csv
            station_id	phase_time	phase_type	phase_score	phase_amplitude	event_index	gamma_score
        181	BK.AASB.00.HH	2023-01-01 18:35:49.170	P	0.476	6.782000e-06	72	3.327747e-08
        182	BK.ADAM.00.HH	2023-01-01 18:32:33.250	P	0.488	3.604000e-07	27	4.517431e-03
        183	BK.ADAM.00.HH	2023-01-01 18:52:58.650	P	0.520	2.249000e-07	-1	-1.000000e+00
        ```
      - the event_index = -1 means not used
    - group the picks to events
      - `grouped_picks = {event_idx: group for event_idx, group in picks.groupby("event_index")}`

```python
def run_gamma(picks, stations, config_):
    # update the config
    config.update(config_)
    # set the projection of the region
    proj = config["proj"]
    # rename the columns as the gamma format (!!! important)
    picks = picks.rename(
        columns={
            "station_id": "id",
            "phase_time": "timestamp",
            "phase_type": "type",
            "phase_score": "prob",
            "phase_amplitude": "amp",
        }
    )
    # rename the columns as the gamma format (!!! important)
    stations = stations.rename(columns={"station_id": "id"})
    stations[["x(km)", "y(km)"]] = stations.apply(
        lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1
    )
    stations["z(km)"] = stations["elevation_m"].apply(lambda x: -x / 1e3)

    print(picks.head())
    print(stations.head())
    # run the gamma
    events, assignments = association(picks, stations, config, 0, config["method"])
    if events is None:
        return None, None

    # format the output location results
    events = pd.DataFrame(events)
    print(events.head())
    events[["longitude", "latitude"]] = events.apply(
        lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1
    )
    events["depth_km"] = events["z(km)"]
    events.drop(columns=["x(km)", "y(km)", "z(km)"], inplace=True, errors="ignore")
    picks = picks.rename(
        columns={
            "id": "station_id",
            "timestamp": "phase_time",
            "type": "phase_type",
            "prob": "phase_score",
            "amp": "phase_amplitude",
        }
    )

    # assign the event index to the picks (!!! important)
    assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
    print(assignments.head())
    picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({"event_index": int})

    # group the picks to events
    grouped_picks = {event_idx: group for event_idx, group in picks.groupby("event_index")}
    # exclude the event_index = -1
    grouped_picks = {k: v for k, v in grouped_picks.items() if k != -1}

    return events, picks
```

```python
# run the gamma
config["region"] = "Ridgecrest"
config["event_index"] = 1

picks_ = picks.copy()
evengts_, picks_ = run_gamma(picks, stations, config)

```

```python
plt.figure()
mapping_color = lambda x: f"C{x}" if x!= -1 else "black"
plt.scatter(picks_["phase_time"], picks_["latitude"], c=picks_["event_index"].apply(mapping_color), s=10)
```

### run the gamma using the fastapi

```python
# run the gamma using the fastapi
picks_  = picks.copy()
picks_["phase_time"] = picks_["phase_time"].apply(lambda x: x.isoformat())
stations_ = stations.copy()

picks_ = picks_.to_dict(orient="records")
stations_ = stations.to_dict(orient="records")

response = requests.post(f"{GAMMA_API_URL}/predict/", json={"picks": {"data":picks_}, "stations": {"data": stations_}, "config": config})

if response.status_code == 200:
    result = response.json()
    # Process the result as needed
else:
    print(f"Request failed with status code: {response.status_code}")
    print(f"Error message: {response.text}")
```

```python
# figure the associated events
events = pd.DataFrame(result["events"])
picks_ = pd.DataFrame(result["picks"])
picks_["phase_time"] = pd.to_datetime(picks_["phase_time"])

plt.figure()
mapping_color = lambda x: f"C{x}" if x!= -1 else "black"
plt.scatter(picks_["phase_time"], picks_["latitude"], c=picks_["event_index"].apply(mapping_color), s=10)
```

```python

```
