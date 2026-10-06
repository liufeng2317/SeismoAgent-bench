# Gamma Usage Example with Seisbench

```python
import obspy
# only this way to import the gamma association function
from gamma.utils import association
```

# Creating a catalog - From waveforms to events

This model shows how to use [SeisBench](https://github.com/seisbench/seisbench) and the [GaMMA associator](https://github.com/wayneweiqiang/GaMMA) to create an earthquake catalog from raw waveforms. First, we will download raw waveforms and station metadata through FDSN. Second, we use an EQTransformer model in SeisBench to obtain phase arrival picks. Third, we use the GaMMA associator to associate the picks to events. We visualize the results.

```python
import obspy
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from pyproj import CRS, Transformer, Proj
import pandas as pd
import numpy as np
from collections import Counter
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import torch

# from gamma.utils import association
import seisbench.models as sbm

sns.set(font_scale=1.2)
sns.set_style("ticks")
```

## Configuration

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

## Obtaining the data

We download waveform data for 12 hours from the CX network in Northern Chile. We use the 1st May 2014, exactly one month after the Mw 8.1 Iquique mainshock on 1st April 2014. Therefore, we expect to still see an increased level of seismicity in the region.

```python
client = Client("GFZ")

t0 = UTCDateTime("2014/05/01 00:00:00")
t1 = t0 + 60 * 60
# t1 = t0 + 12 * 60 * 60   # Full day, requires more memory
stream = client.get_waveforms(network="CX", station="*", location="*", channel="HH?", starttime=t0, endtime=t1)

inv = client.get_stations(network="CX", station="*", location="*", channel="HH?", starttime=t0, endtime=t1)
```

## Picking

For this example, we use EQTransformer trained on the INSTANCE dataset from Italy. However, in principal any picker could be used for obtaining the picks with only minimal changes.

**Warning:** This will take some time and requires sufficient main memory. If you are short on memory, reduce the study in the cell before.

**Note:** We automatically check if CUDA is available and run the model on CUDA in this case. Alternatively, the model runs on CPU.

```python
picker = sbm.EQTransformer.from_pretrained("instance")

# if torch.cuda.is_available():
#     picker.cuda()

# We tuned the thresholds a bit - Feel free to play around with these values
picks, _ = picker.classify(stream, batch_size=256, P_threshold=0.075, S_threshold=0.1, parallelism=1)

Counter([p.phase for p in picks])  # Output number of P and S picks
```

We now convert the picks and station metadata into pandas dataframes in the format required for the GaMMA associator.

```python
pick_df = []
for p in picks:
    pick_df.append({
        "id": p.trace_id,
        "timestamp": p.peak_time.datetime,
        "prob": p.peak_value,
        "type": p.phase.lower()
    })
pick_df = pd.DataFrame(pick_df)

station_df = []
for station in inv[0]:
    station_df.append({
        "id": f"CX.{station.code}.",
        "longitude": station.longitude,
        "latitude": station.latitude,
        "elevation(m)": station.elevation
    })
station_df = pd.DataFrame(station_df)

station_df["x(km)"] = station_df.apply(lambda x: transformer.transform(x["latitude"], x["longitude"])[0] / 1e3, axis=1)
station_df["y(km)"] = station_df.apply(lambda x: transformer.transform(x["latitude"], x["longitude"])[1] / 1e3, axis=1)
station_df["z(km)"] = - station_df["elevation(m)"] / 1e3

northing = {station: y for station, y in zip(station_df["id"], station_df["y(km)"])}
station_dict = {station: (x, y) for station, x, y in zip(station_df["id"], station_df["x(km)"], station_df["y(km)"])}
```

Let's have a look at the picks generated by the model. Note that we retained the probability from the deep learning model. It will be used by the associator later on.

```python
pick_df.sort_values("timestamp")
```

## Association

We now run the phase association. This will take a moment. We convert the output into two dataframes, one for the catalog and one for the assignment of picks to the catalog.

- gamma.association usage
    ```python
    events, assignments = association(pick_df, station_df, config, method=config["method"])
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
# notice the keys of pick_df and station_df (!!! important)
# pick_df: id, timestamp, prob, type
# station_df: id, longitude, latitude, elevation(m), x(km), y(km), z(km) etc.

# run the gamma
events, assignments = association(pick_df, station_df, config, method=config["method"])

events = pd.DataFrame(events)
assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])


# create a catalog with the estimated location
events = pd.DataFrame(events)
events[["longitude","latitude"]] = events.apply(lambda x: pd.Series(proj(longitude=x["x(km)"], latitude=x["y(km)"], inverse=True)), axis=1)
events["depth_km"] = events["z(km)"]
events.to_csv("./text_data/seisbench_example/events.csv", index=False,
                float_format="%.3f",
                date_format='%Y-%m-%dT%H:%M:%S.%f')

# assign the event index to the picks (!!! important)
assignments = pd.DataFrame(assignments, columns=["pick_index", "event_index", "gamma_score"])
picks = picks.join(assignments.set_index("pick_index")).fillna(-1).astype({'event_index': int})
picks.rename(columns={"id": "station_id", "timestamp": "phase_time", "type": "phase_type", "prob": "phase_score", "amp": "phase_amplitude"}, inplace=True)
picks.to_csv("./text_data/seisbench_example/gamma_picks.csv", index=False,
                date_format='%Y-%m-%dT%H:%M:%S.%f')
```

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

## Visualizing the catalog

We can also plot the catalog. Conveniently, we are already in a local transverse mercator projection, so need for further thought in the plotting here.

We use the `scatter` function and encode the depth of the events using color. The plot nicely resolves the intense shallow seismicity in the Iquique area (offshore, Northing arong 7800 km, Easting around 300 km). It also shows the seismicity along the Slap (West-East dipping).

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

As a last check, we manually inspect some events. The code block below selects a random event and plots the waveforms, together with the P (solid black lines) and S (dashed black lines). The x axis denotes the time, the y axis the distance between station and estimated event location. Therefore, we should see roughly a hyperbolic moveout. Run the cell a few times to see a few example events.

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

## Closing remarks

In this tutorial, we saw how to quickly generate an event catalog from raw seismic waveforms and their metadata using SeisBench and the GaMMA associator.

- We used a local coordinate projection for Chile for this tutorial. Depending on the region, you will need to choose a different projection.
- Both the picker and the model have several tuning parameters. We tuned these parameters loosely, but we would like to make the reader aware that these parameters can have strong influence on the number of picks and events, the number of false positives, and the runtime performance of the associator.
- While GaMMA outputs locations, these are only preliminary. It is highly recommended to further improve these using a more advances tool for localization.
