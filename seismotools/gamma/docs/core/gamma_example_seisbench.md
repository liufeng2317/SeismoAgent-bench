# GaMMA Seisbench guide

This guide combines the workflow, input/output, configuration and diagnostic notes for this example. It is a reference for adapting the project interface; it is not a case result.

## Workflow and usage

This summarizes the core workflow to run GaMMA association on phase picks and station metadata, focusing on imports, configuration, main function call, and output handling.

## 1) Import statements

```python
import obspy
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from pyproj import CRS, Transformer, Proj
import pandas as pd
import numpy as np
import torch
import seisbench.models as sbm

# only this way to import the gamma association function
from gamma.utils import association
```

## 2) Configuration

- Dimensions & method
  - dims: ["x(km)", "y(km)", "z(km)"] — event-location coordinates in km
  - use_dbscan: whether to pre-cluster picks with DBSCAN
  - use_amplitude: whether to include amplitude in association

- Projection bounds (km)
  - x(km), y(km), z(km): coordinate ranges in km; depth is positive downward

- Velocity model
  - vel.p, vel.s: P- and S-wave velocities (km/s)

- Association method
  - method: "BGMM" or "GMM"
  - oversample_factor: 4 if BGMM, 1 if GMM

- Optimization bounds (for BFGS refine)
  - bfgs_bounds: ((x_min, x_max), (y_min, y_max), (z_min, z_max), (None, None))

- DBSCAN parameters
  - dbscan_eps: seconds
  - dbscan_min_samples: minimum samples per cluster

- Post-association filtering
  - min_picks_per_eq
  - max_sigma11, max_sigma22, max_sigma12

Example YAML (reference):
```yaml
  # --- Dimensions & method ---
  dims: ["x(km)", "y(km)", "z(km)"]     # Dimensions used for event location
  use_dbscan: true                       # Whether to use DBSCAN for association
  use_amplitude: false                   # Whether to use amplitude information

  # --- Projection bounds (km) ---
  x(km): [250, 600]                      # X range in km
  y(km): [7200, 8000]                    # Y range in km
  z(km): [0, 150]                        # Depth range in km

  # --- Velocity model ---
  vel:
    p: 7.0                               # P-wave velocity in km/s
    s: 4.0                               # S-wave velocity in km/s (p / 1.75)

  # --- Association method ---
  method: "BGMM"                          # Bayesian Gaussian Mixture Model
  oversample_factor: 4                     # Oversampling factor for BGMM
  # oversample_factor: 1                   # Would be used if method is "GMM"

  # --- Optimization bounds ---
  bfgs_bounds:
    - [249, 601]                          # X bounds for BFGS
    - [7199, 8001]                        # Y bounds for BFGS
    - [0, 151]                             # Z bounds for BFGS
    - [null, null]                         # Time unbounded

  # --- DBSCAN parameters ---
  dbscan_eps: 25                           # eps parameter (seconds)
  dbscan_min_samples: 3                    # Minimum samples for DBSCAN

  # --- Post-association filtering ---
  min_picks_per_eq: 5                      # Minimum picks per event
  max_sigma11: 2.0                         # Maximum timing uncertainty (s)
  max_sigma22: 1.0                         # Maximum amplitude uncertainty (log10 m/s)
  max_sigma12: 1.0                         # Maximum covariance
```

Programmatic configuration and overrides:
```python
# Projections
wgs84 = CRS.from_epsg(4326)
local_crs = CRS.from_epsg(9155)  # SIRGAS-Chile 2016 / UTM zone 19S
transformer = Transformer.from_crs(wgs84, local_crs)

# Gamma configs (!!! important)
config = {}
config["dims"] = ['x(km)', 'y(km)', 'z(km)']
config["use_dbscan"] = True
config["use_amplitude"] = False
config["x(km)"] = (250, 600)
config["y(km)"] = (7200, 8000)
config["z(km)"] = (0, 150)
config["vel"] = {"p": 7.0, "s": 7.0 / 1.75}  # We assume rather high velocities as we expect deeper events
config["method"] = "BGMM"
if config["method"] == "BGMM":
    config["oversample_factor"] = 4
if config["method"] == "GMM":
    config["oversample_factor"] = 1

# Gamma conifigs for using DBSCAN for phase association
config["bfgs_bounds"] = (
    (config["x(km)"][0] - 1, config["x(km)"][1] + 1),  # x
    (config["y(km)"][0] - 1, config["y(km)"][1] + 1),  # y
    (0, config["z(km)"][1] + 1),  # x
    (None, None),  # t
)
config["dbscan_eps"] = 25  # seconds
config["dbscan_min_samples"] = 3

# Gamma configs for filtering the picks
config["min_picks_per_eq"] = 5
config["max_sigma11"] = 2.0
config["max_sigma22"] = 1.0
config["max_sigma12"] = 1.0
```

Notes:
- Override any parameter by setting config["key"] = value as shown.
- Units are kilometers for spatial coordinates and seconds for time-related parameters.

## 3) Main function calls

Prepare inputs (required DataFrame keys):

```python
# notice the keys of pick_df and station_df (!!! important)
# pick_df: id, timestamp, prob, type
# station_df: id, longitude, latitude, elevation(m), x(km), y(km), z(km) etc.

# Example: build pick_df from SeisBench outputs
picker = sbm.EQTransformer.from_pretrained("instance")
# if torch.cuda.is_available():
#     picker.cuda()
picks, _ = picker.classify(stream, batch_size=256, P_threshold=0.075, S_threshold=0.1, parallelism=1)

pick_df = []
for p in picks:
    pick_df.append({
        "id": p.trace_id,
        "timestamp": p.peak_time.datetime,
        "prob": p.peak_value,
        "type": p.phase.lower()
    })
pick_df = pd.DataFrame(pick_df)

# Example: build station_df from inventory, add projected coordinates (km)
station_df = []
for station in inv[0]:
    station_df.append({
        "id": f"CX.{station.code}.",
        "longitude": station.longitude,
        "latitude": station.latitude,
        "elevation(m)": station.elevation
    })
station_df = pd.DataFrame(station_df)

station_df["x(km)"] = station_df.apply(
    lambda x: transformer.transform(x["latitude"], x["longitude"])[0] / 1e3, axis=1
)
station_df["y(km)"] = station_df.apply(
    lambda x: transformer.transform(x["latitude"], x["longitude"])[1] / 1e3, axis=1
)
station_df["z(km)"] = - station_df["elevation(m)"] / 1e3
```

Run GaMMA association:

```python
# run the gamma
events, assignments = association(pick_df, station_df, config, method=config["method"])
```

Outputs:
- events: event catalog with fields like
  - time, magnitude, sigma_time, sigma_amp, cov_time_amp, gamma_score, num_picks, num_p_picks, num_s_picks, event_index, x(km), y(km), z(km)
- assignments: mapping of picks to events with columns
  - pick_index, event_index, gamma_score
  - pick_index matches pick_df.index values
  - event_index matches the event_index column in events

Example format of events:
```csv
time,magnitude,sigma_time,sigma_amp,cov_time_amp,gamma_score,num_picks,num_p_picks,num_s_picks,event_index,x(km),y(km),z(km)
2023-01-01T18:38:36.386,1.706,3.287,0.257,-0.1432,8.0,7,4,3,2,-249.3940,-25.8243,0.0
2023-01-01T18:51:28.791,0.117,0.485,0.635,0.0677,5.0,5,4,1,0,-370.6695,290.6818,0.0
2023-01-01T18:39:51.532,2.047,6.223,0.265,0.2399,12.8179,11,5,6,9,-254.3663,-8.2548,6.6394
2023-01-01T18:59:12.964,1.062,5.826,0.214,0.8124,5.0,5,2,3,1,-124.8804,-90.4987,0.0
```

Example format of assignments:
```csv
pick_index,event_index,gamma_score
987,2,0.01845
1102,2,0.01435
```

Notes:
- pick_index matches the pick_df.index.
- event_index matches the events.event_index column.

## 4) Output handling

Convert outputs to DataFrames, save catalog, and join assignments back to picks.

```python
# Convert to DataFrames
events = pd.DataFrame(events)
assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])

# create a catalog with the estimated location
# (convert local x/y in km back to lon/lat using a projection; example uses Proj inverse)
# NOTE: proj must be defined for your CRS; this shows the idea consistent with the example.
events[["longitude","latitude"]] = events.apply(
    lambda x: pd.Series(
        Proj(local_crs)(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)
    ), axis=1
)
events["depth_km"] = events["z(km)"]

events.to_csv("./text_data/seisbench_example/events.csv", index=False,
              float_format="%.3f",
              date_format='%Y-%m-%dT%H:%M:%S.%f')

# assign the event index to the picks (!!! important)
# Join by pick_index; unmatched picks get event_index = -1
pick_df = pick_df.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})

# Optional: rename columns to a standard schema used downstream
pick_df.rename(columns={"id": "station_id",
                        "timestamp": "phase_time",
                        "type": "phase_type",
                        "prob": "phase_score",
                        # include "amp" -> "phase_amplitude" if present in your picks
                        "amp": "phase_amplitude"}, inplace=True)

pick_df.to_csv("./text_data/seisbench_example/gamma_picks.csv", index=False,
               date_format='%Y-%m-%dT%H:%M:%S.%f')
```

Group picks by assigned event:

```python
# group the picks to events
grouped_picks = {event_idx: group for event_idx, group in pick_df.groupby("event_index")}
# exclude the event_index = -1
grouped_picks = {k: v for k, v in grouped_picks.items() if k != -1}

# print the events information and corresponding picks
event_id = 0
print(events[events["event_index"] == event_id])
print(grouped_picks[event_id])
```

Linking picks to events (example):
- Assign the event index to the picks correctly:
  - pick_df.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})
- Example of assigned picks:
```csv
    station_id	phase_time	            phase_type	phase_score	phase_amplitude	event_index	gamma_score
181	BK.AASB.00.HH	2023-01-01 18:35:49.170	P	        0.476	        6.782000e-06	72	        3.327747e-08
182	BK.ADAM.00.HH	2023-01-01 18:32:33.250	P	        0.488	        3.604000e-07	27	        4.517431e-03
183	BK.ADAM.00.HH	2023-01-01 18:52:58.650	P	        0.520	        2.249000e-07	-1	        -1.000000e+00
```
- The event_index = -1 means the pick was not used (not assigned to any event).

## Inputs and outputs

This example demonstrates how to build an earthquake catalog from raw waveforms using SeisBench for picking and the GaMMA associator for phase association and event location. After downloading CX network data and station metadata for May 1, 2014 via FDSN, an EQTransformer model produces P/S picks (with retained probabilities used later by the associator). Picks and station metadata are converted to pandas DataFrames in the format required by GaMMA, with station coordinates projected to a local CRS (SIRGAS-Chile 2016 / UTM 19S) and expressed in x/y/z kilometers. The GaMMA configuration highlights include specifying location dimensions and spatial bounds, a P/S velocity model, choosing the “BGMM” method with oversampling, BFGS optimization bounds (with unbounded origin time), optional DBSCAN-based pre-clustering (eps/min_samples), and post-association filters for minimum picks and timing/amplitude uncertainty limits. The association function (gamma.utils.association) returns events and assignments: events include origin time, magnitude, uncertainty metrics, gamma scores, pick counts, and x/y/z location; assignments map input pick indices to event indices with a per-pick gamma score. Output handling converts event x/y back to longitude/latitude, sets depth, and writes events to CSV; assignments are joined to the picks to attach event_index and gamma_score (with -1 marking unassociated picks), enabling grouping picks by event for inspection. The example concludes with visualizing the catalog in map view colored by depth and manually reviewing waveform moveouts for selected events.

## Configuration

# Station table must provide x(km), y(km), z(km) columns; picks provide P/S types and probabilities.

# --- Dimensions & method ---
dims: ["x(km)", "y(km)", "z(km)"]     # Location parameters to estimate
use_dbscan: true                      # Use DBSCAN to pre-cluster picks in time
use_amplitude: false                  # Do not use amplitude in association

# --- Projection bounds (km) ---
x(km): [250, 600]                     # Easting range
y(km): [7200, 8000]                   # Northing range
z(km): [0, 150]                       # Depth range

# --- Velocity model (km/s) ---
vel:
  p: 7.0                              # P-wave velocity
  s: 4.0                              # S-wave velocity (≈ p / 1.75)

# --- Association method ---
method: "BGMM"                        # Bayesian GMM for joint association-location
oversample_factor: 4                  # Oversampling for BGMM (set to 1 if using "GMM")

# --- Optimization bounds for BFGS (location and origin time) ---
bfgs_bounds:
  - [249, 601]                        # x bounds (expand search by 1 km)
  - [7199, 8001]                      # y bounds (expand search by 1 km)
  - [0, 151]                          # z bounds (down to max depth + 1 km)
  - [null, null]                      # origin time unbounded

# --- DBSCAN parameters (time-domain clustering) ---
dbscan_eps: 25                        # Max temporal separation within a cluster (s)
dbscan_min_samples: 3                 # Minimum picks per cluster

# --- Post-association filtering ---
min_picks_per_eq: 5                   # Discard events with fewer associated picks
max_sigma11: 2.0                      # Max timing uncertainty (s)
max_sigma22: 1.0                      # Max amplitude uncertainty (log10 m/s)
max_sigma12: 1.0                      # Max time–amplitude covariance magnitude

## Diagnostics and plotting

Below are all plotting/visualization snippets in the example, with what they show, how they are produced, their inputs/outputs, and their purpose. A brief global plotting style setup is also included since it affects the figures.

Global plotting style (applies to all figures)
- What it does: Sets the plotting style and font scaling for all subsequent plots.
- How to apply: Seaborn style configuration.
- Inputs: None (global).
- Outputs: No figure; changes default appearance (tick style and font scaling) for all plots in the session.

Code:
```python
import seaborn as sns
sns.set(font_scale=1.2)
sns.set_style("ticks")
```

Figure 1. Catalog map view: events colored by depth and station locations
0. Title of the plot
- Catalog events (x/y) colored by depth, with station locations overlaid.

1. What to plot
- Event epicenters: catalog['x(km)'] vs catalog['y(km)'].
- Event depth as color: catalog['z(km)'] encoded via colormap.
- Station locations: station_df['x(km)'] vs station_df['y(km)'] as red triangles.
- Interpretation: Visualizes spatial distribution of events and their depths. Depth colorbar is reversed so deeper events appear “lower” on the scale. Example text notes it resolves intense shallow seismicity near Iquique and shows slab-dipping seismicity.

2. How to plot
- Library: matplotlib (pyplot).
- Steps:
  - Create figure and axis, enforce equal aspect ratio.
  - Scatter events with colormap and small marker size.
  - Add colorbar, reverse its y-limits, and label it “Depth[km]”.
  - Overlay stations as red triangles with black edge.
  - Label axes (Easting/Northing in km) and show the plot inline.

3. Inputs and outputs
- Inputs:
  - catalog DataFrame with columns: "x(km)", "y(km)", "z(km)".
  - station_df DataFrame with columns: "x(km)", "y(km)".
  - Key plotting parameters:
    - figsize=(10, 10)
    - ax.set_aspect("equal")
    - s=8 (scatter size)
    - cmap="viridis"
    - colorbar label “Depth[km]” and reversed limits via cbar.ax.set_ylim(cbar.ax.get_ylim()[::-1])
    - station markers: "r^", ms=10, mew=1, mec="k"
- Outputs:
  - cb: matplotlib.collections.PathCollection for the event scatter.
  - cbar: matplotlib.colorbar.Colorbar object for depth.
  - A matplotlib Figure containing the map-view scatter of events and station markers (shown via plt.show()).

Code that produces this figure:
```python
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111)
ax.set_aspect("equal")
cb = ax.scatter(catalog["x(km)"], catalog["y(km)"], c=catalog["z(km)"], s=8, cmap="viridis")
cbar = fig.colorbar(cb)
cbar.ax.set_ylim(cbar.ax.get_ylim()[::-1])
cbar.set_label("Depth[km]")

ax.plot(station_df["x(km)"], station_df["y(km)"], "r^", ms=10, mew=1, mec="k")
ax.set_xlabel("Easting [km]")
ax.set_ylabel("Northing [km]")
plt.show()
```

Figure 2. Manual event check: waveforms vs hypocentral distance with P/S picks
0. Title of the plot
- Manual inspection of a random event: normalized waveforms plotted against hypocentral distance, with P and S picks marked.

1. What to plot
- For a randomly selected event:
  - Processed, normalized waveforms from stations that recorded picks for that event.
  - X-axis: time in seconds relative to the start of the plotted window.
  - Y-axis: hypocentral distance (km) between each station and the event location.
  - Pick markers:
    - P picks: solid black vertical lines.
    - S picks: dashed black vertical lines.
- Interpretation: Should display roughly hyperbolic moveout; used to verify temporal-spatial consistency of picks with the associated event.

2. How to plot
- Library: matplotlib (pyplot) and ObsPy for waveform handling.
- Steps:
  - Choose a random event index and collect its picks via assignments.
  - Extract and slice waveforms around the time window spanning the event’s picks.
  - Detrend and high-pass filter at 2 Hz.
  - Normalize each trace to its max absolute amplitude and vertically offset by its hypocentral distance y.
  - Plot each waveform: ax.plot(trace.times(), 10 * normed + y).
  - For each pick, compute its hypocentral distance y and time x relative to the trace start; draw a vertical line at x with linestyle depending on phase (P='-', S='--').
  - Set axis labels: “Hypocentral distance [km]” and “Time [s]”; set y-limits to start at 0; x-limits to [0, np.max(trace.times())].
  - Print the event information for context.

3. Inputs and outputs
- Inputs:
  - event_idx: a random integer in [0, len(catalog)).
  - assignments DataFrame to map event_idx to pick_index and collect event_picks.
  - picks: list-like of pick objects with attributes: trace_id, peak_time, phase.
  - catalog: DataFrame/Series entry for the selected event with "x(km)", "y(km)", "z(km)".
  - stream: ObsPy Stream of waveform data; filtered by station and channel.
  - station_dict: dict mapping station_id -> (x, y) in km for distance computation.
  - Processing parameters:
    - Time window: from 5 s before first pick to 5 s after last pick.
    - Filter: highpass at 2 Hz.
    - Normalization and scaling: trace is demeaned, normalized to max abs, then scaled by 10 and offset by y (hypocentral distance).
    - Line styles: P='-', S='--'; color 'k'.
    - Figure size: figsize=(15, 10).
- Outputs:
  - A matplotlib Figure showing time (s) vs hypocentral distance (km) with waveforms and pick lines.
  - Console output: printed “Event information” and the event row.

Code that produces this figure:
```python
event_idx = np.random.randint(len(catalog))
event_picks = [picks[i] for i in assignments[assignments["event_index"] == event_idx]["pick_index"]]
event = catalog.iloc[event_idx]

first, last = min(pick.peak_time for pick in event_picks), max(pick.peak_time for pick in event_picks)

sub = obspy.Stream()

for station in np.unique([pick.trace_id for pick in event_picks]):
    sub.append(stream.select(station=station[3:-1], channel="HHZ")[0])

sub = sub.slice(first - 5, last + 5)

sub = sub.copy()
sub.detrend()
sub.filter("highpass", freq=2)

fig = plt.figure(figsize=(15, 10))
ax = fig.add_subplot(111)

for i, trace in enumerate(sub):
    normed = trace.data - np.mean(trace.data)
    normed = normed / np.max(np.abs(normed))
    station_x, station_y = station_dict[trace.id[:-4]]
    y = np.sqrt((station_x - event["x(km)"]) ** 2 + (station_y - event["y(km)"]) ** 2 + event["z(km)"] ** 2)
    ax.plot(trace.times(), 10 * normed + y)

for pick in event_picks:
    station_x, station_y = station_dict[pick.trace_id]
    y = np.sqrt((station_x - event["x(km)"]) ** 2 + (station_y - event["y(km)"]) ** 2 + event["z(km)"] ** 2)
    x = pick.peak_time - trace.stats.starttime
    if pick.phase == "P":
        ls = '-'
    else:
        ls = '--'
    ax.plot([x, x], [y - 10, y + 10], 'k', ls=ls)

ax.set_ylim(0)
ax.set_xlim(0, np.max(trace.times()))
ax.set_ylabel("Hypocentral distance [km]")
ax.set_xlabel("Time [s]")

print("Event information")
print(event)
```
