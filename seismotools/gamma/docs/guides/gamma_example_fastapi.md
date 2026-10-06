# GaMMA Fastapi guide

This guide combines the workflow, input/output, configuration and diagnostic notes for this example. It is a reference for adapting the project interface; it is not a case result.

## Workflow and usage

## 1) Import statements

```python
# Core imports for running GaMMA association
import pandas as pd
from pyproj import Proj
from gamma.utils import association  # core GaMMA association function
```

(Optional, only if you expose a service as in the example.)
```python
# Optional: building a simple API endpoint (not required for core usage)
from fastapi import FastAPI
import requests
```

## 2) Configuration

- Configure GaMMA with a Python dict. The example builds a region-aware configuration and adds a pyproj.Proj object for projecting lon/lat to x(km), y(km).
- You can override any parameter by updating the config dict (e.g., config.update({...})).
- Keys to pay attention to:
  - Region bounds: minlongitude, maxlongitude, minlatitude, maxlatitude, mindepth_km, maxdepth_km
  - Projection and derived ranges: xlim_km, ylim_km, zlim_km, z(km), proj
  - Association and filtering thresholds: min_picks, min_picks_ratio, max_residual_time, min_score, min_s_picks, min_p_picks, use_amplitude, etc.
  - Method and runtime: use_dbscan, method, oversample_factor, dims, ncpu
  - Velocity model: vel = {"p": ..., "s": ...}
  - Optimization bounds: bfgs_bounds
  - Runtime event counter: event_index

Example of the config layout used in the example:

```yaml
# --- Basic configuration ---
min_picks: 8
min_picks_ratio: 0.2
max_residual_time: 1.0
max_residual_amplitude: 1.0
min_score: 0.6
min_s_picks: 2
min_p_picks: 2
use_amplitude: true

# --- Region settings ---
region: "ridgecrest"
minlongitude: -118.004
maxlongitude: -117.004
minlatitude: 35.205
maxlatitude: 36.205
mindepth_km: 0.0
maxdepth_km: 41.0

# --- Projection (computed) ---
xlim_km: [xmin, xmax]
ylim_km: [ymin, ymax]
zlim_km: [0.0, 41.0]
z(km): [0.0, 41.0]
proj: null  # runtime-only pyproj.Proj instance

# --- Event filtering ---
min_picks_per_eq: 5
min_p_picks_per_eq: 0
min_s_picks_per_eq: 0
max_sigma11: 3.0
max_sigma22: 1.0
max_sigma12: 1.0

# --- Association parameters ---
use_dbscan: false
oversample_factor: 8.0
dims: ["x(km)", "y(km)", "z(km)"]
method: "BGMM"
ncpu: 1

# --- Velocity model ---
vel:
  p: 6.0
  s: 3.428571

# --- Optimization bounds ---
bfgs_bounds:
  - [xmin-1, xmax+1]  # X
  - [ymin-1, ymax+1]  # Y
  - [0, zmax+1]       # Z
  - [null, null]      # Time

# --- Runtime ---
event_index: 0
```

Example helper to build and override the config (with comments preserved):

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

# Build default config and override as needed
config = set_config()
config["region"] = "Ridgecrest"  # override example
config["event_index"] = 1        # override example
```

Notes on required DataFrame keys:
- Before calling association, GaMMA expects:
  - Picks columns: id, timestamp, prob, amp, type
  - Stations columns: id, x(km), y(km), z(km)
- For user-friendly preparation, the example uses:
  - Picks columns: station_id, phase_time, phase_score, phase_amplitude, phase_type
  - Stations columns: station_id, latitude, longitude, elevation_m
- You must rename between these two schemas before/after calling association.

## 3) Main function calls

Input preparation and function call:

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

    # run the gamma
    events, assignments = association(picks, stations, config, 0, config["method"])
    if events is None:
        return None, None

    # ... post-processing shown in the next section ...
    return events, picks
```

How to call the core function:

```python
# gamma.association usage
events, assignments = association(picks, stations, config, 0, config["method"])
```

- Inputs:
  - picks: DataFrame with columns id, timestamp (datetime-like), prob, amp, type (P/S).
  - stations: DataFrame with columns id, x(km), y(km), z(km) (z is negative elevation in km).
  - config: dict as described above (must include projection-derived limits and proj).
  - 0: starting event index (int).
  - config["method"]: association method string, e.g., "BGMM".
- Outputs:
  - events: iterable/records of event solutions, including time, magnitude, sigma_time, sigma_amp, cov_time_amp, gamma_score, num_picks, num_p_picks, num_s_picks, event_index, x(km), y(km), z(km).
  - assignments: iterable of [pick_index, event_index, gamma_score] rows.

Example format of the output events:

```csv
time,magnitude,sigma_time,sigma_amp,cov_time_amp,gamma_score,num_picks,num_p_picks,num_s_picks,event_index,x(km),y(km),z(km)
2023-01-01T18:38:36.386,1.706,3.287,0.257,-0.1432,8.0,7,4,3,2,-249.3940,-25.8243,0.0
2023-01-01T18:51:28.791,0.117,0.485,0.635,0.0677,5.0,5,4,1,0,-370.6695,290.6818,0.0
2023-01-01T18:39:51.532,2.047,6.223,0.265,0.2399,12.8179,11,5,6,9,-254.3663,-8.2548,6.6394
2023-01-01T18:59:12.964,1.062,5.826,0.214,0.8124,5.0,5,2,3,1,-124.8804,-90.4987,0.0
```

Example format of the output assignments:

```csv
pick_index,event_index,gamma_score
987,2,0.01845
1102,2,0.01435
```

Notes:
- pick_index matches the picks.index values of the input picks DataFrame (after you rename to GaMMA schema).
- event_index matches the event_index column in the events DataFrame returned by association.

## 4) Output handling

Post-process events and link them back to the original picks using pick_index.

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

    # run the gamma
    events, assignments = association(picks, stations, config, 0, config["method"])
    if events is None:
        return None, None

    # format the output location results
    events = pd.DataFrame(events)
    events[["longitude", "latitude"]] = events.apply(
        lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1
    )
    events["depth_km"] = events["z(km)"]
    events.drop(columns=["x(km)", "y(km)", "z(km)"], inplace=True, errors="ignore")

    # rename picks back to user schema
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
    picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({"event_index": int})

    # group the picks to events
    grouped_picks = {event_idx: group for event_idx, group in picks.groupby("event_index")}
    # exclude the event_index = -1
    grouped_picks = {k: v for k, v in grouped_picks.items() if k != -1}

    return events, picks
```

- Joining assignments to the original picks:
  - Use the pick_index returned by association to join back to the user-schema picks.
  - Unassigned picks should be set to event_index = -1 (e.g., via fillna(-1)).

Example of assigned picks:

```csv
station_id,phase_time,phase_type,phase_score,phase_amplitude,event_index,gamma_score
BK.AASB.00.HH,2023-01-01 18:35:49.170,P,0.476,6.782000e-06,72,3.327747e-08
BK.ADAM.00.HH,2023-01-01 18:32:33.250,P,0.488,3.604000e-07,27,4.517431e-03
BK.ADAM.00.HH,2023-01-01 18:52:58.650,P,0.520,2.249000e-07,-1,-1.000000e+00
```

- Group picks by event:
```python
grouped_picks = {event_idx: group for event_idx, group in picks.groupby("event_index")}
grouped_picks = {k: v for k, v in grouped_picks.items() if k != -1}  # exclude unassigned
```

## 5) DataFrame key name requirements (recap)

- Input to GaMMA (before association):
  - Picks: id, timestamp, prob, amp, type
  - Stations: id, x(km), y(km), z(km)
- User-facing schema (before renaming):
  - Picks: station_id, phase_time, phase_score, phase_amplitude, phase_type
  - Stations: station_id, latitude, longitude, elevation_m
- Critical conversions:
  - stations["z(km)"] = -elevation_m / 1e3
  - stations[["x(km)", "y(km)"]] from Proj(longitude, latitude)
  - picks["phase_time"] must be datetime; convert to ISO strings only if sending over HTTP.

## 6) Optional: Run via FastAPI (as in the example)

```python
app = FastAPI()

@app.get("/")
def greet_json():
    return {"Hello": "GaMMA!"}

@app.post("/predict/")
def predict(picks: dict, stations: dict, config: dict):
    picks = pd.DataFrame(picks["data"])
    picks["phase_time"] = pd.to_datetime(picks["phase_time"])
    stations = pd.DataFrame(stations["data"])
    events_, picks_ = run_gamma(picks, stations, config)
    if events_ is None:
        return {"events": None, "picks": picks_}
    return {"events": events_.to_dict(orient="records"),
            "picks": picks_.to_dict(orient="records")}
```

HTTP usage example:

```python
# run the gamma using the fastapi
picks_  = picks.copy()
picks_["phase_time"] = picks_["phase_time"].apply(lambda x: x.isoformat())
stations_ = stations.copy()

picks_ = picks_.to_dict(orient="records")
stations_ = stations.to_dict(orient="records")

response = requests.post(
    f"{GAMMA_API_URL}/predict/",
    json={"picks": {"data": picks_}, "stations": {"data": stations_}, "config": config}
)

if response.status_code == 200:
    result = response.json()
    # Process the result as needed
else:
    print(f"Request failed with status code: {response.status_code}")
    print(f"Error message: {response.text}")
```

This completes the core workflow: prepare/rename DataFrames, configure GaMMA with region and projection, call association, then post-process events and assign event_index back to the original picks using pick_index.

## Inputs and outputs

This example shows how to use the gamma library to associate PhaseNet seismic picks and locate events for the 2019 Ridgecrest sequence, both locally and through a FastAPI endpoint. It prepares inputs by loading picks and station metadata, renaming columns to gamma’s required schema, uppercasing phase types, dropping unused fields, merging station coordinates, filtering a target time window, and projecting station lat/lon/elevation to x(km)/y(km)/z(km) using an azimuthal equidistant projection. A region-specific configuration is built with geographic bounds, projection limits, association thresholds (e.g., min_picks, min_score, residual limits, P/S pick minimums), BGMM as the method (no DBSCAN) with an oversample factor, a uniform P/S velocity model, BFGS optimization bounds, CPU count, and an event index counter. The core workflow calls gamma.utils.association to produce an events table (time, magnitude, uncertainties, covariance, gamma_score, pick counts, event_index, and projected coordinates), which is then converted back to longitude/latitude and depth_km, and an assignments table mapping pick_index to event_index with gamma_score. Output handling joins assignments to the original picks (unmatched picks set to event_index = -1), enables grouping picks by event, and visualizing picks colored by event. The same process is exposed via a /predict API that accepts JSON-serialized picks, stations, and config (served locally or at ai4eps-gamma.hf.space), with responses parsed into events and picks DataFrames for downstream plotting and analysis.

## Configuration

gamma:
  api:  # Service wrapper used in the example (not part of core GaMMA config)
    base_url: "https://ai4eps-gamma.hf.space"  # Endpoint used by the FastAPI demo
    predict_endpoint: "/predict/"  # POST endpoint for association

  io:  # I/O schema expected by GaMMA
    picks_required_fields: ["id", "timestamp", "prob", "amp", "type"]  # Required pick fields
    stations_required_fields: ["id", "elevation(m)"]  # Required station fields
    rename_to_gamma:  # Column renaming performed before calling association()
      picks:
        station_id: "id"  # station identifier
        phase_time: "timestamp"  # pick time (ISO or pandas datetime)
        phase_type: "type"  # P/S (uppercased)
        phase_score: "prob"  # detection/phase probability
        phase_amplitude: "amp"  # observed amplitude
      stations:
        station_id: "id"
        elevation(m): "elevation_m"
    station_coordinates:  # Station coordinate preparation
      projection_spec: "+proj=aeqd +lon_0=<lon0> +lat_0=<lat0> +units=km"  # Azimuthal equidistant; lon0/lat0 are region midpoints
      x(km): "proj(longitude, latitude) -> x"  # Computed at runtime from lon/lat
      y(km): "proj(longitude, latitude) -> y"  # Computed at runtime from lon/lat
      z(km): "-elevation_m/1000"  # Depth positive down; elevation above sea level is negative depth

  config:
    basic:  # Core association thresholds
      min_picks: 8  # Minimum number of picks to consider an event
      min_picks_ratio: 0.2  # Minimum fraction of picks supporting an event
      max_residual_time: 1.0  # Max allowed time residual (s)
      max_residual_amplitude: 1.0  # Max allowed amplitude residual (linear units)
      min_score: 0.6  # Minimum pick probability to use
      min_s_picks: 2  # Minimum S picks per candidate event
      min_p_picks: 2  # Minimum P picks per candidate event
      use_amplitude: true  # Use amplitudes in association (set true in example)

    region:  # Spatial domain (Ridgecrest example)
      name: "ridgecrest"
      minlongitude: -118.004  # West bound
      maxlongitude: -117.004  # East bound
      minlatitude: 35.205  # South bound
      maxlatitude: 36.205  # North bound
      mindepth_km: 0.0  # Shallow bound
      maxdepth_km: 41.0  # Deep bound

    projection:  # Derived from region bounds (computed at runtime)
      lon0: "(minlongitude + maxlongitude)/2"  # Projection center longitude
      lat0: "(minlatitude + maxlatitude)/2"  # Projection center latitude
      proj: null  # pyproj.Proj instance (runtime only)
      xlim_km: ["xmin", "xmax"]  # Projected X bounds in km
      ylim_km: ["ymin", "ymax"]  # Projected Y bounds in km
      zlim_km: [0.0, 41.0]  # Depth bounds in km
      "z(km)": [0.0, 41.0]  # Alias for depth bounds

    event_filtering:  # Event-level quality control
      min_picks_per_eq: 5  # Min total picks per event to report
      min_p_picks_per_eq: 0  # Min P picks per event (post-fit)
      min_s_picks_per_eq: 0  # Min S picks per event (post-fit)
      max_sigma11: 3.0  # Max time uncertainty
      max_sigma22: 1.0  # Max amplitude uncertainty
      max_sigma12: 1.0  # Max covariance between time and amplitude

    association:  # Clustering/association settings
      method: "BGMM"  # Association method ("BGMM" or "GMM")
      use_dbscan: false  # Use DBSCAN instead of BGMM
      oversample_factor: 8.0  # Oversampling factor for BGMM
      dims: ["x(km)", "y(km)", "z(km)"]  # Location dimensions to solve
      ncpu: 32  # Parallel workers (set to 32 in example)

    velocity_model:  # Uniform velocities
      p: 6.0  # P-wave velocity (km/s)
      s: 3.428571  # S-wave velocity (km/s) = 6.0/1.75

    optimization:  # Local optimization bounds (BFGS)
      bfgs_bounds:
        - ["xmin-1", "xmax+1"]  # X in km (expanded by 1 km)
        - ["ymin-1", "ymax+1"]  # Y in km (expanded by 1 km)
        - [0, "zmax+1"]  # Z in km (from 0 to slightly deeper than maxdepth)
        - [null, null]  # Origin time (unbounded)

    runtime:  # State updated at run-time
      event_index: 1  # Event index counter (set to 1 before running in example)

## Diagnostics and plotting

Below are all plotting/visualization snippets found in the provided Gamma example, summarized individually.

Plot 1: Picks over time by latitude, colored by phase type (P vs S)
- What is plotted
  - X-axis: picks["phase_time"] (timestamp of each pick)
  - Y-axis: picks["latitude"] (station latitude for the pick)
  - Color: picks["phase_type"] mapped via {"P": "red", "S": "blue"}
  - Point size: s=10
  - Legend: created using two empty scatter calls for “P” (red) and “S” (blue)
- How it’s plotted
  - Matplotlib scatter plot, rendered inline in a Jupyter environment
- Inputs and outputs
  - Inputs:
    - DataFrame picks with columns:
      - phase_time (datetime-like)
      - latitude (float)
      - phase_type (string: “P” or “S”)
    - color mapping dict: {"P": "red", "S": "blue"}
  - Outputs:
    - A new matplotlib Figure (plt.figure())
    - A scatter PathCollection of the pick points
    - A legend with two entries (“P”, “S”)
    - Immediate rendering via plt.show()
- Code that produces the figure
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
- Purpose/interpretation
  - Visual check of the temporal-spatial distribution of picks and the separation of P vs S phases using color.

Plot 2: Associated picks over time by latitude, colored by event index (local run)
- What is plotted
  - X-axis: picks_["phase_time"]
  - Y-axis: picks_["latitude"]
  - Color: picks_["event_index"] mapped to “C{event_index}” for assigned picks; black for unassigned (-1)
  - Point size: s=10
- How it’s plotted
  - Matplotlib scatter plot; created with plt.figure() and plt.scatter()
- Inputs and outputs
  - Inputs:
    - DataFrame picks_ (result from run_gamma) with columns:
      - phase_time (datetime-like)
      - latitude (float)
      - event_index (int; -1 for unassigned)
    - Color mapping function: lambda x: f"C{x}" if x != -1 else "black"
  - Outputs:
    - A new matplotlib Figure
    - A scatter PathCollection of picks colored by event assignment
    - No legend and no explicit plt.show() in the snippet
- Code that produces the figure
  ```python
  plt.figure()
  mapping_color = lambda x: f"C{x}" if x!= -1 else "black"
  plt.scatter(picks_["phase_time"], picks_["latitude"], c=picks_["event_index"].apply(mapping_color), s=10)
  ```
- Purpose/interpretation
  - Visualize which picks are associated with which event after local Gamma association. Unassigned picks are black; each event gets a distinct default matplotlib cycle color (C0, C1, …).

Plot 3: Associated picks over time by latitude, colored by event index (FastAPI run)
- What is plotted
  - X-axis: picks_["phase_time"] (converted back to datetime)
  - Y-axis: picks_["latitude"]
  - Color: picks_["event_index"] mapped to “C{event_index}”; black for unassigned (-1)
  - Point size: s=10
- How it’s plotted
  - Matplotlib scatter plot, same style and mapping as Plot 2
- Inputs and outputs
  - Inputs:
    - DataFrame events = pd.DataFrame(result["events"]) (not plotted here)
    - DataFrame picks_ = pd.DataFrame(result["picks"]) with columns:
      - phase_time (converted to datetime via pd.to_datetime)
      - latitude (float)
      - event_index (int)
    - Color mapping function: lambda x: f"C{x}" if x != -1 else "black"
  - Outputs:
    - A new matplotlib Figure
    - A scatter PathCollection of picks colored by event assignment returned from the API
    - No legend and no explicit plt.show() in the snippet
- Code that produces the figure
  ```python
  # figure the associated events
  events = pd.DataFrame(result["events"])
  picks_ = pd.DataFrame(result["picks"])
  picks_["phase_time"] = pd.to_datetime(picks_["phase_time"])

  plt.figure()
  mapping_color = lambda x: f"C{x}" if x!= -1 else "black"
  plt.scatter(picks_["phase_time"], picks_["latitude"], c=picks_["event_index"].apply(mapping_color), s=10)
  ```
- Purpose/interpretation
  - Validate and visualize the event association produced by the remote FastAPI Gamma run. Colors differentiate events; black indicates unassigned picks.
