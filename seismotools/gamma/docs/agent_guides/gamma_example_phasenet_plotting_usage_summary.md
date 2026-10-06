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
