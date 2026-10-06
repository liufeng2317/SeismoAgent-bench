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
