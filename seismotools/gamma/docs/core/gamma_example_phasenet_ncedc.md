# GaMMA Phasenet Ncedc guide

This guide combines the workflow, input/output, configuration and diagnostic notes for this example. It is a reference for adapting the project interface; it is not a case result.

## Workflow and usage

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

## Inputs and outputs

This example demonstrates how to use GaMMA (gamma) to associate PhaseNet picks into earthquake events for two demo regions (Ridgecrest and Chile), from data preparation through configuration, association, and output handling. It first sets paths for the chosen region/test case, loads picks and stations, renames pick columns to the GaMMA-required schema (id, timestamp, type, prob, amp), projects station coordinates to kilometers with an azimuthal equidistant projection, filters stations/picks to regional bounds, and optionally trims picks by time or amplitude. It then builds a configuration that controls clustering and location: toggling DBSCAN (eps, min_samples), selecting BGMM or GMM with oversampling, defining uniform or eikonal 1D velocity models (with region-specific depth ranges and grids), setting spatial search bounds and BFGS optimization limits, optional initial search points (Chile), CPU count, and event-quality filters (minimum picks and covariance thresholds). Running association(picks, stations, config, event_idx0, method) yields events and pick-to-event assignments; the workflow converts event x/y back to lon/lat, adds depth_km, and writes gamma_events.csv, while assignments (pick_index, event_index, gamma_score) are joined to the original picks to produce gamma_picks.csv, where event_index = -1 flags unused picks. It also shows how to group picks by event_index, visualize associations over time/space/amplitude, and optionally refine results by a nearest-station ratio filter using k-NN, rewriting a filtered gamma_events.csv and selecting corresponding picks. Example event outputs include timing, magnitude, uncertainties (sigma_time, sigma_amp, cov_time_amp), gamma_score, pick counts, event_index, and locations, enabling downstream plotting of rates, locations, magnitude distributions, and covariance diagnostics.

## Configuration

center: [lon0, lat0]            # float[2]: map center (deg), auto-set from region bounds
xlim_degree: [minlon, maxlon]   # float[2]: longitude bounds (deg)
ylim_degree: [minlat, maxlat]   # float[2]: latitude bounds (deg)

# --- Method selection ---
use_dbscan: true                # bool: use DBSCAN to pre-cluster picks
use_amplitude: true             # bool: use amplitude in association (False for Chile in example)
method: "BGMM"                  # str: "BGMM" (BayesianGaussianMixture) or "GMM"
oversample_factor: 5            # int: BGMM=5, GMM=1 in example

# --- Velocity (uniform) ---
vel:                            # dict: uniform velocity model used if no eikonal is provided
  p: 6.0                        # float: P-wave velocity (km/s)
  s: 3.428571                   # float: S-wave velocity (km/s), 6.0/1.75

# --- Location grid / search space ---
dims: ["x(km)", "y(km)", "z(km)"]  # list[str]: location parameter names
x(km): [xmin, xmax]             # float[2]: projected x-range (km) from xlim_degree
y(km): [ymin, ymax]             # float[2]: projected y-range (km) from ylim_degree
z(km): [zmin, zmax]             # float[2]: depth range (km); examples: Ridgecrest=[0,20], Chile=[0,250], else=[0,30]

# --- Optimization bounds (BFGS) ---
bfgs_bounds:                    # list[list]: [x_min,x_max],[y_min,y_max],[z_min,z_max],[t_min,t_max]
  - [x(km)_min-1, x(km)_max+1]  # x (km)
  - [y(km)_min-1, y(km)_max+1]  # y (km)
  - [0, z(km)_max+1]            # z (km)
  - [null, null]                # origin time (unbounded)

# --- DBSCAN parameters ---
dbscan_eps: 10                  # float: neighborhood radius (km); example uses 10
dbscan_min_samples: 3           # int: minimum samples per cluster

# --- Eikonal 1D velocity model (optional; overrides uniform vel for travel times) ---
eikonal:                        # dict: enable to use 1D model and eikonal solver
  vel:                          # example (Ridgecrest); for Chile load iasp91.csv up to zmax
    z: [0.0, 5.5, 16.0, 32.0]   # float[]: depths (km)
    p: [5.5, 5.5, 6.7, 7.8]     # float[]: P velocities (km/s)
    s: [3.18, 3.18, 3.88, 4.51] # float[]: S velocities (km/s), vp/vs≈1.73
  h: 1.0                        # float: grid spacing (km)
  xlim: [xmin, xmax]            # float[2]: x-range (km)
  ylim: [ymin, ymax]            # float[2]: y-range (km)
  zlim: [zmin, zmax]            # float[2]: z-range (km)

# --- Initial search point (optional; used in Chile example) ---
initial_points: [1, 1, 1]       # int[3]: initial indices for x,y,z search

# --- Runtime ---
ncpu: 32                        # int: number of CPU cores

# --- Event filtering thresholds ---
min_picks_per_eq: 5             # int: minimum total picks per event
min_p_picks_per_eq: 0           # int: minimum P picks per event
min_s_picks_per_eq: 0           # int: minimum S picks per event
max_sigma11: 15.0               # float: max travel-time uncertainty (s)
max_sigma22: 3.0                # float: max amplitude uncertainty (log10 m/s)
max_sigma12: 3.0                # float: max time–amplitude covariance

# Notes:
# - x(km), y(km) are obtained by projecting lon/lat using an azimuthal equidistant projection centered at `center`.
# - dbscan_eps can be estimated from stations and P velocity (e.g., estimate_eps(stations, vel.p) in example).
# - When use_amplitude is true, picks without amplitude (amp == -1) are removed before association.

## Diagnostics and plotting

Below is a concise, per-figure summary of every plotting/visualization snippet in the provided Gamma example. For each, you’ll find: a descriptive title, what is plotted, how it’s produced (Matplotlib calls), the inputs/outputs (including parameters), and the intended purpose/interpretation. The original plotting code is included verbatim.

1) Time vs Latitude: picks and associated events (color-coded by event_index)
- What to plot:
  - Picks: phase_time (x) vs latitude (y), color-coded by event_index.
  - Events: time (x) vs latitude (y), color-coded by event_index, marked with “x”.
- How to plot: Matplotlib scatter plots (two layers), with a color mapping function mapping_color that assigns a categorical color C{index} for event_index >= 0, otherwise black (k).
- Inputs:
  - picks DataFrame with columns: phase_time (datetime), latitude (float), event_index (int).
  - events DataFrame with columns: time (datetime), latitude (float), event_index (int).
  - Parameters: figsize=(20, 5), s=1 for picks, s=50 and marker="x" for events; colors via mapping_color.
- Outputs:
  - On-screen figure (plt.show()). No file saved.
- Purpose/interpretation:
  - Visualize temporal and latitudinal distribution of picks and their association to events; confirm that clustered picks align in time and latitude with detected events.

```python
plt.figure(figsize=(20, 5))
mapping_color = lambda x: f"C{x}" if x >= 0 else "k"
plt.scatter(picks["phase_time"], picks["latitude"], c=picks["event_index"].apply(mapping_color), s=1)
plt.scatter(events["time"], events["latitude"], c=events["event_index"].apply(mapping_color), s=50, marker="x")
plt.show()
```

2) Time vs log10 Amplitude: picks (color-coded by event_index)
- What to plot:
  - Picks: phase_time (x) vs log10(phase_amplitude) (y), color-coded by event_index.
- How to plot: Matplotlib scatter plot with mapping_color for colors; log-transform applied via numpy log10 during plotting.
- Inputs:
  - picks DataFrame with columns: phase_time (datetime), phase_amplitude (float), event_index (int).
  - Parameters: figsize=(20, 5), s=1, colors via mapping_color.
- Outputs:
  - On-screen figure (plt.show()). No file saved.
- Purpose/interpretation:
  - Inspect amplitude evolution over time and how assigned events (color) distribute in amplitude domain.

```python
plt.figure(figsize=(20, 5))
mapping_color = lambda x: f"C{x}" if x >= 0 else "k"
plt.scatter(picks["phase_time"], np.log10(picks["phase_amplitude"]), c=picks["event_index"].apply(mapping_color), s=1)
plt.show()
```

3) Time vs Distance to a reference point: picks and events (color-coded by event_index)
- What to plot:
  - Picks: phase_time (x) vs dist_km (y).
  - Events: time (x) vs dist_km (y), marked with “x”.
  - Both color-coded by event_index.
- How to plot: Matplotlib scatter plots (two layers). dist_km is precomputed from reference (lat0, lon0).
- Inputs:
  - picks DataFrame: phase_time, dist_km, event_index.
  - events DataFrame: time, dist_km, event_index.
  - Parameters: figsize=(20, 5), s=1 for picks, s=50 and marker="x" for events; colors via mapping_color.
- Outputs:
  - On-screen figure (plt.show()). No file saved.
- Purpose/interpretation:
  - Show spatiotemporal relation relative to a fixed reference location; validate that associated events track pick clusters in distance through time.

```python
plt.figure(figsize=(20, 5))
mapping_color = lambda x: f"C{x}" if x >= 0 else "k"
plt.scatter(picks["phase_time"], picks["dist_km"], c=picks["event_index"].apply(mapping_color), s=1)
plt.scatter(events["time"], events["dist_km"], c=events["event_index"].apply(mapping_color), s=50, marker="x")
plt.show()
```

4) Time vs Distance after nearest-station-ratio filtering
- What to plot:
  - Picks: phase_time (x) vs dist_km (y), color-coded by event_index.
  - Filtered Events: time (x) vs dist_km (y), marked with “x”, color-coded by event_index.
- How to plot: Matplotlib scatter plots (two layers); same color mapping as above.
- Inputs:
  - picks DataFrame: phase_time, dist_km, event_index.
  - filtered_events DataFrame: time, dist_km, event_index.
  - Parameters: figsize=(20, 5), s=1 for picks, s=50 and marker="x" for filtered_events; colors via mapping_color.
- Outputs:
  - On-screen figure (plt.show()). No file saved.
- Purpose/interpretation:
  - Visual confirmation of which events remain after filtering based on nearest station ratio.

```python
plt.figure(figsize=(20, 5))
mapping_color = lambda x: f"C{x}" if x >= 0 else "k"
plt.scatter(picks["phase_time"], picks["dist_km"], c=picks["event_index"].apply(mapping_color), s=1)
plt.scatter(filtered_events["time"], filtered_events["dist_km"], c=filtered_events["event_index"].apply(mapping_color), s=50, marker="x")
plt.show()
```

5) Time-frequency (event counts) histogram
- What to plot:
  - Histogram of event times for gamma_events, optionally overlaid with a standard_catalog.
- How to plot: Matplotlib histograms with consistent time range and 24 bins; date formatting on x-axis; legend; saving to file.
- Inputs:
  - gamma_events DataFrame: time.
  - Optional standard_catalog DataFrame: time; determines starttime/endtime (min/max).
  - Parameters: bins=24, range=(starttime, endtime), edgecolor="k", alpha (1.0 for Gamma, 0.6 for catalog), linewidth=0.5; autoscale tight on x; x-axis formatter mdates.DateFormatter('%m-%d:%H'); legend; labeling.
- Outputs:
  - Saved image: figures/earthquake_number.png (bbox_inches="tight", dpi=300).
  - On-screen via plt.show().
- Purpose/interpretation:
  - Compare event rate over time between GaMMA-associated catalog and a standard catalog, if available.

```python
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

6) Location results: map and cross-sections (composite figure with three panels)
- What to plot:
  - Panel (i) Map: longitude (x) vs latitude (y) for gamma_events and optionally standard_catalog; station locations as faint triangles.
  - Panel (ii) Cross-section: longitude (x) vs depth_km (y).
  - Panel (iii) Cross-section: latitude (x) vs depth_km (y).
- How to plot: Matplotlib figure with GridSpec (2 rows × 2 cols; left column is map spanning both rows; right column two cross-sections). Scaled axes, bounds from config, inverted y-axis for depth. Legends and annotated panel labels (i), (ii), (iii). Saves to file.
- Inputs:
  - gamma_events: longitude, latitude, depth_km.
  - Optional standard_catalog: longitude, latitude, depth_km.
  - stations: longitude, latitude (plotted with 'k^', markersize=5, alpha=0.01).
  - Config: xlim_degree, ylim_degree, z(km).
  - Parameters: figure size scaled by plt.rcParams["figure.figsize"]*np.array([1.5,1]); width_ratios=[1.5, 1], height_ratios=[1,1]; markersizes; alpha; axis("scaled"); xlim/ylim from config; invert_yaxis on depth plots; set_prop_cycle(None) for legend proxy points; rasterized=True on some point plots; legend loc="lower right"; text annotations with rounded white box.
- Outputs:
  - Saved image: figures/earthquake_location.png (bbox_inches="tight", dpi=300).
  - On-screen via plt.show().
- Purpose/interpretation:
  - Visualize spatial distribution of epicenters and depth structure; compare GaMMA results with a standard catalog and show station coverage context.

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

7) Magnitude-frequency (Gutenberg-Richter style) histogram
- What to plot:
  - Histogram of event magnitudes for gamma_events; optional overlay of standard_catalog.
- How to plot: Matplotlib histogram with 25 bins; range chosen based on available catalog; log-scale y-axis; legend; saving to file. Plot only if gamma_events["magnitude"] contains any values != 999.
- Inputs:
  - gamma_events: magnitude (float), includes special value 999 to indicate unavailable; filtered by (gamma_events["magnitude"] != 999).any().
  - Optional standard_catalog: magnitude.
  - Parameters: bins=25, alpha (1.0 for Gamma, 0.6 for catalog), edgecolor="k", linewidth=0.5; xlim depends on catalog presence; y-axis set to log scale.
- Outputs:
  - Saved image: figures/earthquake_magnitude_frequency.png (bbox_inches="tight", dpi=300).
  - On-screen via plt.show().
- Purpose/interpretation:
  - Compare magnitude distributions (completeness and frequency) of GaMMA-inferred events vs a standard catalog.

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

8) Magnitude vs Time
- What to plot:
  - Scatter of magnitudes through time for gamma_events; optional overlay of standard_catalog.
- How to plot: Matplotlib scatter plots; x-axis formatted with mdates.DateFormatter('%m-%d:%H'); legend assembled with empty proxy plots for counts; grid; saving to file. Rendered only if (gamma_events["magnitude"] != 999).any().
- Inputs:
  - gamma_events: time, magnitude.
  - Optional standard_catalog: time, magnitude.
  - Parameters: markersize=5, alpha (1.0 for Gamma, 0.8 for catalog); xlim=[starttime, endtime]; legend entries via plt.plot([],[]...) with labels showing counts; grid on.
- Outputs:
  - Saved image: figures/earthquake_magnitude_time.png (bbox_inches="tight", dpi=300).
  - On-screen via plt.show().
- Purpose/interpretation:
  - Examine temporal evolution of magnitudes, and compare with a standard catalog if available.

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

9) Covariance diagnostics: uncertainties over time
- What to plot:
  - Three subplots (stacked):
    - (i) sigma_time (σ11, travel-time uncertainty) vs time.
    - (ii) sigma_amp (σ22, amplitude uncertainty in log10 m/s) vs time.
    - (iii) cov_time_amp (Σ12, covariance) vs time.
- How to plot: Matplotlib figure with three subplots; each uses plt.plot with small markers; legends; panel labels (i–iii) with boxed annotations; x-axis formatted with mdates.DateFormatter; layout tightened and labels aligned; saved to file.
- Inputs:
  - gamma_events: time, sigma_time, sigma_amp, cov_time_amp.
  - Parameters: figure size scaled by plt.rcParams["figure.figsize"]*np.array([0.8,1.1]); markersize=3.0; legends in upper right; optional y-limits commented out for covariance; DateFormatter('%m-%d:%H'); tight_layout; align_labels.
- Outputs:
  - Saved image: figures/covariance.png (bbox_inches="tight", dpi=300).
  - On-screen via plt.show().
- Purpose/interpretation:
  - Assess estimated timing and amplitude uncertainties and their covariance through time as diagnostics of association quality.

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
