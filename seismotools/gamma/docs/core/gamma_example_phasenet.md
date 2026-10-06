# GaMMA Phasenet guide

This guide combines the workflow, input/output, configuration and diagnostic notes for this example. It is a reference for adapting the project interface; it is not a case result.

## Workflow and usage

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

## Inputs and outputs

This example demonstrates how to use the gamma (GaMMA) library to associate PhaseNet picks into earthquake events for two demo regions (Ridgecrest, CA and Chile), configure the association pipeline, and manage outputs. It sets up region-specific paths, reads picks and stations, renames columns to the expected schema, and projects station coordinates to kilometers using an azimuthal equidistant projection while deriving depth from elevation. Core configuration includes enabling DBSCAN preprocessing, toggling amplitude usage by region, selecting BGMM or GMM with an oversample factor, defining location dimensions and bounds, specifying optimization limits (bfgs_bounds), choosing either a uniform or 1D eikonal travel-time model (with grid spacing and x/y/z limits), setting DBSCAN parameters (eps, min_samples, min_cluster_size, time-space ratio), defining CPU usage, and applying post-association quality filters on pick counts and covariance metrics. The association is run via gamma.utils.association to return event parameters and pick-to-event assignments; event coordinates are converted back to longitude/latitude, depth is recorded, and results are saved as gamma_events.csv and gamma_picks.csv, where assignments add event_index and gamma_score per pick (with -1 indicating unused picks), enabling grouping by event. An optional catalog refinement filters events by the fraction of nearest stations that contributed picks, using a NearestNeighbors-based nearest-station ratio threshold, and writes the filtered catalog. Finally, the example provides optional visualizations to inspect time-frequency of events, epicentral maps and cross-sections, magnitude distributions and time series, and covariance diagnostics, noting that magnitudes and locations estimated during association are approximate.

## Configuration

use_dbscan: true                    # whether to use DBSCAN preprocessing
use_amplitude: true                 # use amplitude in association (set false for 'chile' example); picks with amp == -1 are filtered out
method: "BGMM"                      # association method ("BGMM" or "GMM")
oversample_factor: 5                # BGMM: 5; if method == "GMM", use 2
# covariance_prior: [5.0, 2.0]      # optional prior for (time, amplitude); larger prevents splitting, too large may merge events

# --- Earthquake location (uniform velocity fallback) ---
vel:                                 # uniform velocity model used if no eikonal provided
  p: 6.0
  s: 3.428571                       # 6.0/1.75
dims: ["x(km)", "y(km)", "z(km)"]   # location parameterization in km (projected)
"x(km)": [xmin, xmax]               # projected X range in km (from AEQD projection around station median)
"y(km)": [ymin, ymax]               # projected Y range in km
"z(km)": [0, 20]                    # depth range in km; use [0, 250] for 'chile'

bfgs_bounds:                         # bounds for BFGS optimization: x, y, z, origin time
  - [x(km)_min - 1, x(km)_max + 1]
  - [y(km)_min - 1, y(km)_max + 1]
  - [0, z(km)_max + 1]
  - [null, null]                    # time is unbounded

# --- DBSCAN parameters (pre-clustering) ---
dbscan_eps: 15                      # neighborhood size in km; larger reduces splitting but increases preprocessing time
dbscan_min_samples: 3               # min samples to form a core point
dbscan_min_cluster_size: 500        # min cluster size to keep
dbscan_max_time_space_ratio: 5      # cap ratio of time to space scale

# --- Eikonal velocity model (1D, optional but used in examples) ---
eikonal:
  vel:                               # example 'ridgecrest' 1D model; for 'chile' load iasp91.csv into z/p/s arrays
    z: [0.0, 5.5, 16.0, 32.0]        # depths (km)
    p: [5.5, 5.5, 6.7, 7.8]          # P-wave velocities (km/s)
    s: [3.18, 3.18, 3.88, 4.51]      # S-wave velocities (km/s)
  h: 1.0                             # grid spacing (km)
  xlim: [xmin, xmax]                 # same spatial limits as x(km)
  ylim: [ymin, ymax]                 # same spatial limits as y(km)
  zlim: [zmin, zmax]                 # same depth limits as z(km)

# --- Runtime ---
ncpu: 32                             # number of CPUs

# --- Event filtering (post-association) ---
min_picks_per_eq: 5                  # minimum total picks per event
min_p_picks_per_eq: 0                # minimum P picks
min_s_picks_per_eq: 0                # minimum S picks
max_sigma11: 3.0                     # max timing uncertainty (s)
max_sigma22: 1.0                     # max amplitude uncertainty (log10 m/s)
max_sigma12: 1.0                     # max time–amplitude covariance

## Diagnostics and plotting

Below is a summary of all plotting/visualization code in the provided gamma example, organized by figure. For each, you’ll find what is visualized, how it’s produced, inputs and outputs (including parameters), and the exact code that generates it.

1) Title: time-frequency
- What to plot:
  - Histogram of event occurrence times from GaMMA results (gamma_events["time"]).
  - Optionally overlay a standard catalog’s event times (standard_catalog["time"]) if available.
  - Purpose: Compare temporal frequency of detected events between GaMMA and a standard catalog over the same time range.
- How to plot:
  - Matplotlib pyplot, using plt.hist for time histograms.
  - Uses matplotlib.dates.DateFormatter for x-axis formatting.
- Inputs:
  - gamma_events: DataFrame with column "time" (parsed as datetime).
  - standard_catalog (optional): DataFrame with column "time" (parsed as datetime), loaded if test_data/<region>/standard_catalog.csv exists.
  - starttime, endtime: computed from standard_catalog if available, else from gamma_events.
  - Labels: result_label = "GaMMA", catalog_label = "Standard".
  - Parameters:
    - bins=24
    - range=(starttime, endtime)
    - edgecolor="k"
    - alpha=1.0 for GaMMA, 0.6 for standard catalog
    - linewidth=0.5
    - x-axis formatter: mdates.DateFormatter("%m-%d:%H")
    - plt.gca().autoscale(enable=True, axis="x", tight=True)
    - plt.gcf().autofmt_xdate()
- Outputs:
  - Displays the figure via plt.show().
  - Saves PNG to figures/earthquake_number.png with dpi=300 and bbox_inches="tight".
- Code:
```python
stations = pd.read_csv(data_path("stations.csv"))
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
plt.hist(
    gamma_events["time"],
    range=(starttime, endtime),
    bins=24,
    edgecolor="k",
    alpha=1.0,
    linewidth=0.5,
    label=f"{result_label}: {len(gamma_events['time'])}",
)
if standard_catalog is not None:
    plt.hist(
        standard_catalog["time"],
        range=(starttime, endtime),
        bins=24,
        edgecolor="k",
        alpha=0.6,
        linewidth=0.5,
        label=f"{catalog_label}: {len(standard_catalog['time'])}",
    )
plt.ylabel("Frequency")
plt.xlabel("Date")
plt.gca().autoscale(enable=True, axis="x", tight=True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m-%d:%H"))
plt.gcf().autofmt_xdate()
plt.legend()
plt.savefig(figure_dir("earthquake_number.png"), bbox_inches="tight", dpi=300)
plt.show();
```

2) Title: location results
- What to plot:
  - A composite figure (2x2 gridspec) with three subplots:
    (i) Map view: event longitude vs latitude (GaMMA and optionally standard catalog), plus station locations.
    (ii) Cross-section: longitude vs depth_km.
    (iii) Cross-section: latitude vs depth_km.
  - Purpose: Visualize spatial distribution of events and depth cross-sections, and compare GaMMA results to a standard catalog; show station coverage.
- How to plot:
  - Matplotlib pyplot with fig.add_gridspec for layout and multiple plt.plot scatter calls.
  - Axes formatting includes scaled aspect, bounding boxes from config, inverted depth axis, and legends.
- Inputs:
  - gamma_events: DataFrame with columns "longitude", "latitude", "depth_km".
  - standard_catalog (optional): DataFrame with columns "longitude", "latitude", "depth_km".
  - stations: DataFrame with "longitude", "latitude".
  - config:
    - config["xlim_degree"], config["ylim_degree"] for map extent.
    - config["z(km)"] for depth axis limits.
    - Small x-limits shifts in cross-sections: np.array([0.2, -0.27]) added to xlim degrees.
  - Parameters:
    - Figure size: plt.rcParams["figure.figsize"] * np.array([1.5, 1])
    - Gridspec: ncols=2, nrows=2, width_ratios=[1.5, 1], height_ratios=[1, 1]
    - Markers: "." (markersize=2, alpha=1.0 for GaMMA; alpha=0.6 for standard catalog)
    - Stations: "k^", markersize=5, alpha=0.7
    - Legends and labels: custom entries using empty plot([]) calls; legend loc="lower right"
    - Rasterization for some plotted elements: rasterized=True used on point plots/legend placeholders
    - Axis formatting: plt.axis("scaled") for map; inverted y-axis for depth sections
- Outputs:
  - Displays the figure via plt.show().
  - Saves PNG to figures/earthquake_location.png with dpi=300 and bbox_inches="tight".
- Code:
```python
fig = plt.figure(figsize=plt.rcParams["figure.figsize"] * np.array([1.5, 1]))
box = dict(boxstyle="round", facecolor="white", alpha=1)
text_loc = [0.05, 0.92]
grd = fig.add_gridspec(ncols=2, nrows=2, width_ratios=[1.5, 1], height_ratios=[1, 1])
fig.add_subplot(grd[:, 0])
plt.plot(gamma_events["longitude"], gamma_events["latitude"], ".", markersize=2, alpha=1.0)
if standard_catalog is not None:
    plt.plot(
        standard_catalog["longitude"],
        standard_catalog["latitude"],
        ".",
        markersize=2,
        alpha=0.6,
    )
plt.axis("scaled")
plt.xlim(np.array(config["xlim_degree"]))
plt.ylim(np.array(config["ylim_degree"]))
plt.xlabel("Latitude")
plt.ylabel("Longitude")
plt.gca().set_prop_cycle(None)
plt.plot([], [], ".", markersize=10, label=f"{result_label}", rasterized=True)
plt.plot([], [], ".", markersize=10, label=f"{catalog_label}", rasterized=True)
plt.plot(
    stations["longitude"],
    stations["latitude"],
    "k^",
    markersize=5,
    alpha=0.7,
    label="Stations",
)
plt.legend(loc="lower right")
plt.text(
    text_loc[0],
    text_loc[1],
    "(i)",
    horizontalalignment="left",
    verticalalignment="top",
    transform=plt.gca().transAxes,
    fontsize="large",
    fontweight="normal",
    bbox=box,
)

fig.add_subplot(grd[0, 1])
plt.plot(
    gamma_events["longitude"],
    gamma_events["depth_km"],
    ".",
    markersize=2,
    alpha=1.0,
    rasterized=True,
)
if standard_catalog is not None:
    plt.plot(
        standard_catalog["longitude"],
        standard_catalog["depth_km"],
        ".",
        markersize=2,
        alpha=0.6,
        rasterized=True,
    )
plt.xlim(np.array(config["xlim_degree"]) + np.array([0.2, -0.27]))
plt.ylim(config["z(km)"])
plt.gca().invert_yaxis()
plt.xlabel("Longitude")
plt.ylabel("Depth (km)")
plt.gca().set_prop_cycle(None)
plt.plot([], [], ".", markersize=10, label=f"{result_label}")
plt.plot([], [], ".", markersize=10, label=f"{catalog_label}")
plt.legend(loc="lower right")
plt.text(
    text_loc[0],
    text_loc[1],
    "(ii)",
    horizontalalignment="left",
    verticalalignment="top",
    transform=plt.gca().transAxes,
    fontsize="large",
    fontweight="normal",
    bbox=box,
)

fig.add_subplot(grd[1, 1])
plt.plot(
    gamma_events["latitude"],
    gamma_events["depth_km"],
    ".",
    markersize=2,
    alpha=1.0,
    rasterized=True,
)
if standard_catalog is not None:
    plt.plot(
        standard_catalog["latitude"],
        standard_catalog["depth_km"],
        ".",
        markersize=2,
        alpha=0.6,
        rasterized=True,
    )
plt.xlim(np.array(config["ylim_degree"]) + np.array([0.2, -0.27]))
plt.ylim(config["z(km)"])
plt.gca().invert_yaxis()
plt.xlabel("Latitude")
plt.ylabel("Depth (km)")
plt.gca().set_prop_cycle(None)
plt.plot([], [], ".", markersize=10, label=f"{result_label}")
plt.plot([], [], ".", markersize=10, label=f"{catalog_label}")
plt.legend(loc="lower right")
plt.tight_layout()
plt.text(
    text_loc[0],
    text_loc[1],
    "(iii)",
    horizontalalignment="left",
    verticalalignment="top",
    transform=plt.gca().transAxes,
    fontsize="large",
    fontweight="normal",
    bbox=box,
)
plt.savefig(figure_dir("earthquake_location.png"), bbox_inches="tight", dpi=300)
plt.show();
```

3) Title: magnitude frequency
- What to plot:
  - Histogram of event magnitudes for GaMMA results, optionally overlaid with standard catalog magnitudes.
  - Purpose: Compare magnitude distribution and event counts between GaMMA and standard catalog on a log-scaled frequency axis.
- How to plot:
  - Matplotlib pyplot using plt.hist for magnitudes, with y-axis set to log scale.
- Inputs:
  - gamma_events["magnitude"], with a filter to proceed only if any value != 999.
  - standard_catalog["magnitude"] (optional).
  - range:
    - If standard catalog exists: (0, standard_catalog["magnitude"].max())
    - Else: (-1, gamma_events["magnitude"].max())
  - Parameters:
    - bins=25
    - alpha=1.0 for GaMMA, 0.6 for standard catalog
    - edgecolor="k", linewidth=0.5
    - plt.xlim([-1, standard_catalog["magnitude"].max()]) if standard catalog exists
    - plt.gca().set_yscale("log")
- Outputs:
  - Displays the figure via plt.show().
  - Saves PNG to figures/earthquake_magnitude_frequency.png with dpi=300 and bbox_inches="tight".
- Code:
```python
if standard_catalog is not None:
    range = (0, standard_catalog["magnitude"].max())
else:
    range = (-1, gamma_events["magnitude"].max())
if (gamma_events["magnitude"] != 999).any():
    plt.figure()
    plt.hist(
        gamma_events["magnitude"],
        range=range,
        bins=25,
        alpha=1.0,
        edgecolor="k",
        linewidth=0.5,
        label=f"{result_label}: {len(gamma_events['magnitude'])}",
    )
    if standard_catalog is not None:
        plt.hist(
            standard_catalog["magnitude"],
            range=range,
            bins=25,
            alpha=0.6,
            edgecolor="k",
            linewidth=0.5,
            label=f"{catalog_label}: {len(standard_catalog['magnitude'])}",
        )
    plt.legend()
    plt.xlim([-1, standard_catalog["magnitude"].max()])
    plt.xlabel("Magnitude")
    plt.ylabel("Frequency")
    plt.gca().set_yscale("log")
    plt.savefig(figure_dir("earthquake_magnitude_frequency.png"), bbox_inches="tight", dpi=300)
    plt.show()
```

4) Title: magnitude-time
- What to plot:
  - Scatter plot of magnitude vs. time for GaMMA results, optionally overlaying standard catalog.
  - Purpose: Visualize temporal evolution of magnitudes and compare coverage between GaMMA and standard catalog.
- How to plot:
  - Matplotlib pyplot using plt.plot with "." markers; date formatting via mdates.DateFormatter.
  - Adds legend entries with counts by plotting invisible points (plot([], []) with labels).
- Inputs:
  - gamma_events["time"], gamma_events["magnitude"], filtered to ensure magnitudes != 999 exist.
  - standard_catalog["time"], standard_catalog["magnitude"] (optional).
  - starttime, endtime from earlier block (time-frequency).
  - Parameters:
    - markersize=5
    - alpha=1.0 (GaMMA) and 0.8 (standard catalog)
    - rasterized=True
    - x limits: [starttime, endtime]
    - x-axis format: mdates.DateFormatter("%m-%d:%H")
    - plt.gcf().autofmt_xdate()
    - Legend created with placeholder points and labels including counts
    - plt.grid()
- Outputs:
  - Displays the figure via plt.show().
  - Saves PNG to figures/earthquake_magnitude_time.png with dpi=300 and bbox_inches="tight".
- Code:
```python
if (gamma_events["magnitude"] != 999).any():
    plt.figure()
    plt.plot(
        gamma_events["time"],
        gamma_events["magnitude"],
        ".",
        markersize=5,
        alpha=1.0,
        rasterized=True,
    )
    if standard_catalog is not None:
        plt.plot(
            standard_catalog["time"],
            standard_catalog["magnitude"],
            ".",
            markersize=5,
            alpha=0.8,
            rasterized=True,
        )
    plt.xlim([starttime, endtime])
    ylim = plt.ylim()
    plt.ylabel("Magnitude")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m-%d:%H"))
    plt.gcf().autofmt_xdate()
    plt.gca().set_prop_cycle(None)
    plt.plot(
        [],
        [],
        ".",
        markersize=15,
        alpha=1.0,
        label=f"{result_label}: {len(gamma_events['magnitude'])}",
    )
    plt.plot(
        [],
        [],
        ".",
        markersize=15,
        alpha=1.0,
        label=f"{catalog_label}: {len(standard_catalog['magnitude'])}",
    )
    plt.legend()
    plt.ylim(ylim)
    plt.grid()
    plt.savefig(figure_dir("earthquake_magnitude_time.png"), bbox_inches="tight", dpi=300)
    plt.show()
```

5) Title: covariance
- What to plot:
  - Three time series subplots:
    (i) sigma_time (γ-events timing uncertainty) vs time.
    (ii) sigma_amp (amplitude uncertainty) vs time.
    (iii) cov_time_amp (time-amplitude covariance) vs time.
  - Purpose: Assess event-level uncertainty and covariance behavior through time for GaMMA results.
- How to plot:
  - Matplotlib pyplot with a single figure and three plt.subplot panels (311, 312, 313).
  - Date formatting via mdates.DateFormatter for the x-axis; annotations "(i)", "(ii)", "(iii)" added using plt.text with a boxed style.
- Inputs:
  - gamma_events: DataFrame columns "time", "sigma_time", "sigma_amp", "cov_time_amp".
  - Parameters:
    - Figure size: plt.rcParams["figure.figsize"] * np.array([0.8, 1.1])
    - Markers: ".", markersize=3.0
    - Legends: loc="upper right"
    - y-limit for covariance subplot: [-0.5, 0.5]
    - Labels with LaTeX-like strings for symbols: r"$\sigma_{11}$ (s)", r"$\sigma_{22}$ ($\log10$ m/s)", r"$\Sigma_{12}$"
    - Box style for annotations: box = dict(boxstyle="round", facecolor="white", alpha=1), text location text_loc = [0.05, 0.90]
    - plt.tight_layout(), plt.gcf().align_labels()
- Outputs:
  - Displays the figure via plt.show().
  - Saves PNG to figures/covariance.png with dpi=300 and bbox_inches="tight".
- Code:
```python
fig = plt.figure(figsize=plt.rcParams["figure.figsize"] * np.array([0.8, 1.1]))
box = dict(boxstyle="round", facecolor="white", alpha=1)
text_loc = [0.05, 0.90]
plt.subplot(311)
plt.plot(
    gamma_events["time"],
    gamma_events["sigma_time"],
    ".",
    markersize=3.0,
    label="Travel-time",
)
plt.ylabel(r"$\sigma_{11}$ (s)")
plt.legend(loc="upper right")
plt.text(
    text_loc[0],
    text_loc[1],
    "(i)",
    horizontalalignment="left",
    verticalalignment="top",
    transform=plt.gca().transAxes,
    fontsize="large",
    fontweight="normal",
    bbox=box,
)
plt.subplot(312)
plt.plot(
    gamma_events["time"],
    gamma_events["sigma_amp"],
    ".",
    markersize=3.0,
    label="Amplitude",
)
plt.ylabel(r"$\sigma_{22}$ ($\log10$ m/s)")
plt.legend(loc="upper right")
plt.text(
    text_loc[0],
    text_loc[1],
    "(ii)",
    horizontalalignment="left",
    verticalalignment="top",
    transform=plt.gca().transAxes,
    fontsize="large",
    fontweight="normal",
    bbox=box,
)
plt.subplot(313)
plt.plot(
    gamma_events["time"],
    gamma_events["cov_time_amp"],
    ".",
    markersize=3.0,
    label="Travel-time vs. Amplitude",
)
plt.ylabel(r"$\Sigma_{12}$")
plt.ylim([-0.5, 0.5])
plt.legend(loc="upper right")
plt.text(
    text_loc[0],
    text_loc[1],
    "(iii)",
    horizontalalignment="left",
    verticalalignment="top",
    transform=plt.gca().transAxes,
    fontsize="large",
    fontweight="normal",
    bbox=box,
)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m-%d:%H"))
plt.gcf().autofmt_xdate()
plt.tight_layout()
plt.gcf().align_labels()
plt.savefig(figure_dir("covariance.png"), bbox_inches="tight", dpi=300)
plt.show();
```

General notes for all plots in this example:
- All figures are produced using Matplotlib (matplotlib.pyplot as plt) and date formatting via matplotlib.dates as mdates.
- Plots conditionally include a standard catalog overlay if test_data/<region>/standard_catalog.csv exists.
- Figures are saved under the "figures" directory using figure_dir("<filename>.png") with dpi=300 and bbox_inches="tight", then displayed with plt.show().
- Labels result_label = "GaMMA" and catalog_label = "Standard" are used consistently in legends.
- Some plots reset the color cycle via plt.gca().set_prop_cycle(None) to align legend colors with plotted points.
