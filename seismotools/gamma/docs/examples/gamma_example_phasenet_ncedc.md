# Use Gamma to associate the picks from PhaseNet

Applying GaMMA to associate PhaseNet picks

```python
import pandas as pd
from gamma.utils import association, estimate_eps
import numpy as np
import os
from pyproj import Proj
import json
import matplotlib.pyplot as plt

```

## 1. Usage of Gamma for Phase Association

There are two examples in the demo data: Ridgecrest, CA and Chile.

**Phase Picks**:
- test_data/ridgecrest
    - picks.csv
    - stations.csv
    - standard_catalog.csv
- test_data/chile
    - picks.csv
    - stations.csv
    - iasp91.csv

**Results**:
- test_data/ridgecrest
    - gamma_events.csv
    - gamma_picks.csv
- test_data/chile
    - gamma_events.csv
    - gamma_picks.csv

### 1. Set the running location

```python
# set the running location
region = "ncedc"
test_name = "mtj"
data_path = lambda x: os.path.join(f"test_data/{region}", x)
result_path = f"results/{region}"
if not os.path.exists(result_path):
    os.makedirs(result_path)
result_path = lambda x: os.path.join(f"results/{region}", x)
station_csv = data_path("stations.csv")
station_json = data_path("stations.json")
if test_name == "geyser":
    picks_csv = data_path("picks_geyser.csv")
if test_name == "mtj":
    picks_csv = data_path("picks_mtj.csv")
if not os.path.exists("figures"):
    os.makedirs("figures")
figure_dir = lambda x: os.path.join("figures", x)
```

### 2. Read and Rename the picks & Set Gamma configs

```python
## read picks
picks = pd.read_csv(picks_csv, parse_dates=["phase_time"])
picks = picks[['station_id', 'phase_time', 'phase_type', 'phase_score', 'phase_amplitude']]
if test_name == "geyser":
    picks = picks[(picks["phase_time"] >= "2023-03-02 21:15:00") & (picks["phase_time"] <= "2023-03-02 21:30:00")]

picks.rename(columns={"station_id": "id", "phase_time": "timestamp", "phase_type": "type", "phase_score": "prob", "phase_amplitude": "amp"}, inplace=True)
print("Pick format:", picks.iloc[:3])

## read stations
stations = pd.read_json(station_json, orient="index")
stations["id"] = stations.index
print("Station format:", stations.iloc[:3])

## Automatic region; you can also specify a region
with open(data_path("config.json"), "r") as f:
    config = json.load(f)
    config["center"] = ((config["minlongitude"] + config["maxlongitude"]) / 2, (config["minlatitude"] + config["maxlatitude"]) / 2)
    config["xlim_degree"] = (config["minlongitude"], config["maxlongitude"])
    config["ylim_degree"] = (config["minlatitude"], config["maxlatitude"])

## projection to km
proj = Proj(f"+proj=aeqd +lon_0={config['center'][0]} +lat_0={config['center'][1]} +units=km")
stations[["x(km)", "y(km)"]] = stations.apply(lambda x: pd.Series(proj(longitude=x.longitude, latitude=x.latitude)), axis=1)
stations["z(km)"] = stations["elevation_m"].apply(lambda x: -x/1e3)
stations = stations[(stations["longitude"] > config["minlongitude"]) & (stations["longitude"] < config["maxlongitude"]) & (stations["latitude"] > config["minlatitude"]) & (stations["latitude"] < config["maxlatitude"])]
picks = picks[picks["id"].isin(stations["id"])]

```

### 3. Set Gamma configs
```yaml

  # --- Method selection ---
  use_dbscan: true                # bool: Whether to use DBSCAN for clustering
  use_amplitude: true             # bool: Whether to use amplitude information
  method: "BGMM"                  # str: Association method (BGMM or GMM)
  oversample_factor: 5            # int: Oversampling factor for BGMM or GMM

  # --- Earthquake location ---
  vel:                            # dict: uniform velocity model
    p: 6.0                        # float: P-wave velocity (km/s)
    s: 3.428571                   # float: S-wave velocity (km/s)
  dims: ["x(km)", "y(km)", "z(km)"]  # list[str]: Dimensions used for location
  x(km): [xmin, xmax]             # list[float]: x coordinates in km (projected)
  y(km): [ymin, ymax]             # list[float]: y coordinates in km (projected)
  z(km): [zmin, zmax]             # list[float]: z coordinates (depth range in km)

  bfgs_bounds:                     # list[list[float|None]]: optimization bounds for BFGS
    - [x(km)_min-1, x(km)_max+1]  # X bounds
    - [y(km)_min-1, y(km)_max+1]  # Y bounds
    - [0, z(km)_max+1]            # Z bounds
    - [null, null]                # Time bounds (unbounded)

  # --- DBSCAN parameters ---
  dbscan_eps: 10                  # float: DBSCAN eps parameter (km)
  dbscan_min_samples: 3           # int: DBSCAN minimum samples

  # --- Eikonal velocity model ---
  eikonal:                        # dict: velocity model for travel-time computation
    vel:                           # dict: velocity profiles
      z: [0.0, 5.5, 16.0, 32.0]   # list[float]: depths in km
      p: [5.5, 5.5, 6.7, 7.8]     # list[float]: P-wave velocities (km/s)
      s: [3.18, 3.18, 3.88, 4.51] # list[float]: S-wave velocities (km/s)
    h: 1.0                         # float: grid spacing (km)
    xlim: [xmin, xmax]             # list[float]: x limits for travel-time grid
    ylim: [ymin, ymax]             # list[float]: y limits for travel-time grid
    zlim: [zmin, zmax]             # list[float]: z limits for travel-time grid

  # --- Initial points for specific regions ---
  initial_points: [1, 1, 1]       # list[int]: initial x,y,z for search (optional, e.g., Chile)

  # --- Runtime & CPU ---
  ncpu: 32                        # int: number of CPUs to use

  # --- Event filtering ---
  min_picks_per_eq: 5             # int: minimum picks per event
  min_p_picks_per_eq: 0           # int: minimum P picks per event
  min_s_picks_per_eq: 0           # int: minimum S picks per event
  max_sigma11: 15.0               # float: maximum timing uncertainty (seconds)
  max_sigma22: 3.0                # float: maximum amplitude uncertainty (log10 m/s)
  max_sigma12: 3.0                # float: maximum covariance
```


```python
### setting GMMA configs
config["use_dbscan"] = True
if region == "chile":
    config["use_amplitude"] = False
else:
    config["use_amplitude"] = True
config["method"] = "BGMM"
if config["method"] == "BGMM": ## BayesianGaussianMixture
    config["oversample_factor"] = 5
if config["method"] == "GMM": ## GaussianMixture
    config["oversample_factor"] = 1

# earthquake location
config["vel"] = {"p": 6.0, "s": 6.0 / 1.75}
config["dims"] = ['x(km)', 'y(km)', 'z(km)']
config["x(km)"] = proj(longitude=config["xlim_degree"], latitude=[config["center"][1]] * 2)[0]
config["y(km)"] = proj(longitude=[config["center"][0]] * 2, latitude=config["ylim_degree"])[1]

if region == "ridgecrest":
    config["z(km)"] = (0, 20)
elif region == "chile":
    config["z(km)"] = (0, 250)
else:
    config["z(km)"] = (0, 30)
    print("Please specify z(km) for your region")

config["bfgs_bounds"] = (
    (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
    (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
    (0, config["z(km)"][1] + 1),  # z
    (None, None),  # t
)

# DBSCAN
config["dbscan_eps"] = 10 #estimate_eps(stations, config["vel"]["p"])
config["dbscan_min_samples"] = 3

## using Eikonal for 1D velocity model
if region == "ridgecrest":
    zz = [0.0, 5.5, 16.0, 32.0]
    vp = [5.5, 5.5,  6.7,  7.8]
    vp_vs_ratio = 1.73
    vs = [v / vp_vs_ratio for v in vp]
    h = 1.0
    vel = {"z": zz, "p": vp, "s": vs}
    config["eikonal"] = {"vel": vel, "h": h, "xlim": config["x(km)"], "ylim": config["y(km)"], "zlim": config["z(km)"]}
elif region == "chile":
    velocity_model = pd.read_csv(data_path("iasp91.csv"), names=["zz", "rho", "vp", "vs"])
    velocity_model = velocity_model[velocity_model["zz"] <= config["z(km)"][1]]
    vel = {"z": velocity_model["zz"].values, "p": velocity_model["vp"].values, "s": velocity_model["vs"].values}
    h = 1.0
    config["eikonal"] = {"vel": vel, "h": h, "xlim": config["x(km)"], "ylim": config["y(km)"], "zlim": config["z(km)"]}
else:
    print("Using uniform velocity model")

if region == "chile":
    config["initial_points"] = [1, 1, 1] # x, y, z

# set number of cpus
config["ncpu"] = 32

# filtering
config["min_picks_per_eq"] = 5
config["min_p_picks_per_eq"] = 0
config["min_s_picks_per_eq"] = 0
config["max_sigma11"] = 3.0*5 # second
config["max_sigma22"] = 1.0*3 # log10(m/s)
config["max_sigma12"] = 1.0*3 # covariance

## filter picks without amplitude measurements
if config["use_amplitude"]:
    picks = picks[picks["amp"] != -1]

for k, v in config.items():
    print(f"{k}: {v}")
```

### 4. Phase Associaiton with GaMMA
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
# Association with GaMMA
event_idx0 = 0 ## current earthquake index
assignments = []
events, assignments = association(picks, stations, config, event_idx0, config["method"])

# create a catalog with the estimated location
events = pd.DataFrame(events)
events.to_csv("./temp_events.csv", index=False)
events[["longitude","latitude"]] = events.apply(lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1)
events["depth_km"] = events["z(km)"]
events.to_csv(result_path("gamma_events.csv"), index=False,
                float_format="%.3f",
                date_format='%Y-%m-%dT%H:%M:%S.%f')

# assign the event index to the picks (!!! important)
assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
assignments.to_csv("./temp_assignments.csv", index=False)
picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})
picks.rename(columns={"id": "station_id", "timestamp": "phase_time", "type": "phase_type", "prob": "phase_score", "amp": "phase_amplitude"}, inplace=True)
picks.to_csv(result_path("gamma_picks.csv"), index=False,
                date_format='%Y-%m-%dT%H:%M:%S.%f')
```

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

### 5. Reload the picks and events for visualize

```python
if test_name == "mtj":
    lat0, lon0 = 40.409, -123.971
if test_name == "geyser":
    lat0, lon0 = 38.821, -122.805
picks = pd.read_csv(result_path("gamma_picks.csv"), parse_dates=["phase_time"])
events = pd.read_csv(result_path("gamma_events.csv"), parse_dates=["time"])
picks["id"] = picks["station_id"]
picks = picks.merge(stations[["id", "latitude", "longitude"]], on="id")
picks["dist_km"] = np.sqrt((picks["latitude"] - lat0)**2 + (picks["longitude"] - lon0)**2) * 111.32
events["dist_km"] = np.sqrt((events["latitude"] - lat0)**2 + (events["longitude"] - lon0)**2) * 111.32

```

```python
plt.figure(figsize=(20, 5))
mapping_color = lambda x: f"C{x}" if x >= 0 else "k"
plt.scatter(picks["phase_time"], picks["latitude"], c=picks["event_index"].apply(mapping_color), s=1)
plt.scatter(events["time"], events["latitude"], c=events["event_index"].apply(mapping_color), s=50, marker="x")
plt.show()
```

```python
plt.figure(figsize=(20, 5))
mapping_color = lambda x: f"C{x}" if x >= 0 else "k"
plt.scatter(picks["phase_time"], np.log10(picks["phase_amplitude"]), c=picks["event_index"].apply(mapping_color), s=1)
plt.show()
```

```python
plt.figure(figsize=(20, 5))
mapping_color = lambda x: f"C{x}" if x >= 0 else "k"
plt.scatter(picks["phase_time"], picks["dist_km"], c=picks["event_index"].apply(mapping_color), s=1)
plt.scatter(events["time"], events["dist_km"], c=events["event_index"].apply(mapping_color), s=50, marker="x")
plt.show()
```

## 2. Optional Steps for Filtering results by the Nearest Station Ratio

```python
from sklearn.neighbors import NearestNeighbors
from tqdm import tqdm
import pandas as pd

# load the picks and events
events = pd.read_csv(result_path("gamma_events.csv"))
picks = pd.read_csv(result_path("gamma_picks.csv"))

# load the stations
stations = pd.read_json(station_json, orient="index")
stations["station_id"] = stations.index
MIN_NEAREST_STATION_RATIO = 0.1
stations["station_id"] = stations["station_id"].apply(lambda x: ".".join(x.split(".")[:3]))
stations = stations[stations["station_id"].isin(picks["station_id"].unique())]

# nearest neighbor search
neigh = NearestNeighbors(n_neighbors=min(len(stations), 10))
neigh.fit(stations[["longitude", "latitude"]].values)

# merge the picks and events
picks = picks.merge(events[["event_index", "longitude", "latitude"]], on="event_index", suffixes=("", "_event"))
picks = picks.merge(stations[["station_id", "longitude", "latitude"]], on="station_id", suffixes=("", "_station"))

# filter the events based on the nearest station ratio
filtered_events = []
for i, event in tqdm(events.iterrows(), total=len(events)):
    sid = neigh.kneighbors([[event["longitude"], event["latitude"]]])[1][0]
    picks_ = picks[picks["event_index"] == event["event_index"]]
    # longitude, latitude = picks_[["longitude", "latitude"]].mean().values
    # sid = neigh.kneighbors([[longitude, latitude]])[1][0]
    stations_neigh = stations.iloc[sid]["station_id"].values
    picks_neigh = picks_[picks_["station_id"].isin(stations_neigh)]
    stations_with_picks = picks_neigh["station_id"].unique()
    if len(stations_with_picks) / len(stations_neigh) > MIN_NEAREST_STATION_RATIO:
        filtered_events.append(event)

# rewrite the filtered events
print(f"Events before filtering: {len(events)}")
print(f"Events after filtering: {len(filtered_events)}")
filtered_events = pd.DataFrame(filtered_events)
os.system(f"mv {result_path('gamma_events.csv')} {result_path('gamma_events_raw.csv')}")
filtered_events.to_csv(result_path("gamma_events.csv"), index=False)

```

```python
if test_name == "mtj":
    lat0, lon0 = 40.409, -123.971
if test_name == "geyser":
    lat0, lon0 = 38.821, -122.805
picks = pd.read_csv(result_path("gamma_picks.csv"), parse_dates=["phase_time"])
picks["id"] = picks["station_id"]
picks = picks.merge(stations[["station_id", "latitude", "longitude"]], on="station_id")
filtered_events = pd.read_csv(result_path("gamma_events.csv"), parse_dates=["time"])
picks["dist_km"] = np.sqrt((picks["latitude"] - lat0)**2 + (picks["longitude"] - lon0)**2) * 111.32
events["dist_km"] = np.sqrt((events["latitude"] - lat0)**2 + (events["longitude"] - lon0)**2) * 111.32
filtered_events["dist_km"] = np.sqrt((filtered_events["latitude"] - lat0)**2 + (filtered_events["longitude"] - lon0)**2) * 111.32
# picks = picks[picks["event_index"].isin(filtered_events["event_index"])]
# picks["event_index"] = picks["event_index"].apply(lambda x: -1 if x not in filtered_events["event_index"].values else x)
filtered_picks = picks[picks["event_index"].isin(filtered_events["event_index"])]
```

```python
plt.figure(figsize=(20, 5))
mapping_color = lambda x: f"C{x}" if x >= 0 else "k"
plt.scatter(picks["phase_time"], picks["dist_km"], c=picks["event_index"].apply(mapping_color), s=1)
plt.scatter(filtered_events["time"], filtered_events["dist_km"], c=filtered_events["event_index"].apply(mapping_color), s=50, marker="x")
plt.show()
```

## 3. Optional Visualize results

Note that the location and magnitude are estimated during associaiton, which are not expected to have high accuracy.

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
result_label="GaMMA"
catalog_label="Standard"
```

### time-frequency

```python
# stations = pd.read_csv(data_path("stations.csv"))
stations = pd.read_json(station_json, orient="index")
stations["id"] = stations.index
gamma_events = pd.read_csv(result_path("gamma_events.csv"), parse_dates=["time"])

if os.path.exists(data_path("standard_catalog.csv")):
    standard_catalog = pd.read_csv(data_path("standard_catalog.csv"), parse_dates=["time"])
    starttime = standard_catalog["time"].min()
    endtime = standard_catalog["time"].max()
else:
    standard_catalog = None
    starttime = gamma_events["time"].min()
    endtime = gamma_events["time"].max()


plt.figure()
plt.hist(gamma_events["time"], range=(starttime, endtime), bins=24, edgecolor="k", alpha=1.0, linewidth=0.5, label=f"{result_label}: {len(gamma_events['time'])}")
if standard_catalog is not None:
    plt.hist(standard_catalog["time"], range=(starttime, endtime), bins=24, edgecolor="k", alpha=0.6, linewidth=0.5, label=f"{catalog_label}: {len(standard_catalog['time'])}")
plt.ylabel("Frequency")
plt.xlabel("Date")
plt.gca().autoscale(enable=True, axis='x', tight=True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d:%H'))
plt.gcf().autofmt_xdate()
plt.legend()
plt.savefig(figure_dir("earthquake_number.png"), bbox_inches="tight", dpi=300)
plt.show();
```

### location results

```python
fig = plt.figure(figsize=plt.rcParams["figure.figsize"]*np.array([1.5,1]))
box = dict(boxstyle='round', facecolor='white', alpha=1)
text_loc = [0.05, 0.92]
grd = fig.add_gridspec(ncols=2, nrows=2, width_ratios=[1.5, 1], height_ratios=[1,1])
fig.add_subplot(grd[:, 0])
plt.plot(gamma_events["longitude"], gamma_events["latitude"], '.',markersize=2, alpha=1.0)
if standard_catalog is not None:
    plt.plot(standard_catalog["longitude"], standard_catalog["latitude"], '.', markersize=5, alpha=0.6)
plt.axis("scaled")
plt.xlim(np.array(config["xlim_degree"]))
plt.ylim(np.array(config["ylim_degree"]))
plt.xlabel("Latitude")
plt.ylabel("Longitude")
plt.gca().set_prop_cycle(None)
plt.plot([], [], '.', markersize=10, label=f"{result_label}", rasterized=True)
plt.plot([], [], '.', markersize=10, label=f"{catalog_label}", rasterized=True)
plt.plot(stations["longitude"], stations["latitude"], 'k^', markersize=5, alpha=0.01, label="Stations")
plt.legend(loc="lower right")
plt.text(text_loc[0], text_loc[1], '(i)', horizontalalignment='left', verticalalignment="top",
         transform=plt.gca().transAxes, fontsize="large", fontweight="normal", bbox=box)

fig.add_subplot(grd[0, 1])
plt.plot(gamma_events["longitude"], gamma_events["depth_km"], '.', markersize=2, alpha=1.0, rasterized=True)
if standard_catalog is not None:
    plt.plot(standard_catalog["longitude"], standard_catalog["depth_km"], '.', markersize=2, alpha=0.6, rasterized=True)
plt.xlim(np.array(config["xlim_degree"])+np.array([0.2,-0.27]))
plt.ylim(config["z(km)"])
plt.gca().invert_yaxis()
plt.xlabel("Longitude")
plt.ylabel("Depth (km)")
plt.gca().set_prop_cycle(None)
plt.plot([], [], '.', markersize=10, label=f"{result_label}")
plt.plot([], [], '.', markersize=10, label=f"{catalog_label}")
plt.legend(loc="lower right")
plt.text(text_loc[0], text_loc[1], '(ii)', horizontalalignment='left', verticalalignment="top",
         transform=plt.gca().transAxes, fontsize="large", fontweight="normal", bbox=box)

fig.add_subplot(grd[1, 1])
plt.plot(gamma_events["latitude"], gamma_events["depth_km"], '.', markersize=2, alpha=1.0, rasterized=True)
if standard_catalog is not None:
    plt.plot(standard_catalog["latitude"], standard_catalog["depth_km"], '.', markersize=2, alpha=0.6, rasterized=True)
plt.xlim(np.array(config["ylim_degree"])+np.array([0.2,-0.27]))
plt.ylim(config["z(km)"])
plt.gca().invert_yaxis()
plt.xlabel("Latitude")
plt.ylabel("Depth (km)")
plt.gca().set_prop_cycle(None)
plt.plot([], [], '.', markersize=10, label=f"{result_label}")
plt.plot([], [], '.', markersize=10, label=f"{catalog_label}")
plt.legend(loc="lower right")
plt.tight_layout()
plt.text(text_loc[0], text_loc[1], '(iii)', horizontalalignment='left', verticalalignment="top",
         transform=plt.gca().transAxes, fontsize="large", fontweight="normal", bbox=box)
plt.savefig(figure_dir("earthquake_location.png"), bbox_inches="tight", dpi=300)
plt.show();
```

### magnitude frequency

```python
if standard_catalog is not None:
    range = (0, standard_catalog["magnitude"].max())
else:
    range = (-1, gamma_events["magnitude"].max())
if (gamma_events["magnitude"] != 999).any():
    plt.figure()
    plt.hist(gamma_events["magnitude"], range=range, bins=25, alpha=1.0,  edgecolor="k", linewidth=0.5, label=f"{result_label}: {len(gamma_events['magnitude'])}")
    if standard_catalog is not None:
        plt.hist(standard_catalog["magnitude"], range=range, bins=25, alpha=0.6,  edgecolor="k", linewidth=0.5, label=f"{catalog_label}: {len(standard_catalog['magnitude'])}")
    plt.legend()
    if standard_catalog is not None:
        plt.xlim([0, standard_catalog["magnitude"].max()])
    else:
        plt.xlim([-1,gamma_events["magnitude"].max()])
    plt.xlabel("Magnitude")
    plt.ylabel("Frequency")
    plt.gca().set_yscale('log')
    plt.savefig(figure_dir("earthquake_magnitude_frequency.png"), bbox_inches="tight", dpi=300)
    plt.show();
```

### magnitude-time

```python
if (gamma_events["magnitude"] != 999).any():
    plt.figure()
    plt.plot(gamma_events["time"], gamma_events["magnitude"], '.', markersize=5, alpha=1.0, rasterized=True)
    if standard_catalog is not None:
        plt.plot(standard_catalog["time"], standard_catalog["magnitude"], '.', markersize=5, alpha=0.8, rasterized=True)
    plt.xlim([starttime, endtime])
    ylim = plt.ylim()
    plt.ylabel("Magnitude")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d:%H'))
    plt.gcf().autofmt_xdate()
    plt.gca().set_prop_cycle(None)
    plt.plot([],[], '.', markersize=15, alpha=1.0, label=f"{result_label}: {len(gamma_events['magnitude'])}")
    if standard_catalog is not None:
        plt.plot([],[], '.', markersize=15, alpha=1.0, label=f"{catalog_label}: {len(standard_catalog['magnitude'])}")
    plt.legend()
    plt.ylim(ylim)
    plt.grid()
    plt.savefig(figure_dir("earthquake_magnitude_time.png"), bbox_inches="tight", dpi=300)
    plt.show();
```

### covariance

```python
fig = plt.figure(figsize=plt.rcParams["figure.figsize"]*np.array([0.8,1.1]))
box = dict(boxstyle='round', facecolor='white', alpha=1)
text_loc = [0.05, 0.90]
plt.subplot(311)
plt.plot(gamma_events["time"], gamma_events["sigma_time"], '.', markersize=3.0, label="Travel-time")
plt.ylabel(r"$\sigma_{11}$ (s)")
plt.legend(loc="upper right")
plt.text(text_loc[0], text_loc[1], '(i)', horizontalalignment='left', verticalalignment="top",
         transform=plt.gca().transAxes, fontsize="large", fontweight="normal", bbox=box)
plt.subplot(312)
plt.plot(gamma_events["time"], gamma_events["sigma_amp"], '.', markersize=3.0, label="Amplitude")
plt.ylabel(r"$\sigma_{22}$ ($\log10$ m/s)")
plt.legend(loc="upper right")
plt.text(text_loc[0], text_loc[1], '(ii)', horizontalalignment='left', verticalalignment="top",
         transform=plt.gca().transAxes, fontsize="large", fontweight="normal", bbox=box)
plt.subplot(313)
plt.plot(gamma_events["time"], gamma_events["cov_time_amp"], '.', markersize=3.0, label="Travel-time vs. Amplitude")
plt.ylabel(r"$\Sigma_{12}$")
# plt.ylim([-0.5, 0.5])
plt.legend(loc="upper right")
plt.text(text_loc[0], text_loc[1], '(iii)', horizontalalignment='left', verticalalignment="top",
         transform=plt.gca().transAxes, fontsize="large", fontweight="normal", bbox=box)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d:%H'))
plt.gcf().autofmt_xdate()
plt.tight_layout()
plt.gcf().align_labels()
plt.savefig(figure_dir("covariance.png"), bbox_inches="tight", dpi=300)
plt.show();
```

```python

```
