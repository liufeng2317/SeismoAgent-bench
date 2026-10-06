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
