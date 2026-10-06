# GaMMA Synthetic guide

This guide combines the workflow, input/output, configuration and diagnostic notes for this example. It is a reference for adapting the project interface; it is not a case result.

## Workflow and usage

This summary shows how to use gamma’s Gaussian mixture models to associate seismic P/S picks, based strictly on the provided example code.

## 1) Import statements

```python
import numpy as np
import time
from gamma import BayesianGaussianMixture, GaussianMixture
```

- numpy is used for array handling.
- time is used for timing the fit.
- gamma provides BayesianGaussianMixture and GaussianMixture.

## 2) Configuration

Key configuration parameters used in the example and how to override them:

- Data construction and feature toggle:
  - use_amplitude (bool): If True, associate using both time and amplitude (2D feature); if False, use time only (1D feature).
  - Override by setting use_amplitude = True/False before preparing the data matrix.

- Initialization and model shape:
  - num_event_init (int): Initial number of mixture components passed to the model’s n_components. In the example:
    - num_event_init = min(int(len(data)/min(num_station, 20) * 3), len(data))
  - centers_init (ndarray): Initial centers for components (init_params="centers"):
    - Without amplitude: columns are [loc, time]
    - With amplitude: columns are [loc, time, mag]
    - Override by building your own centers_init array and passing centers_init=... to the model.
  - covariance_prior (ndarray): Prior covariance matrix:
    - If not use_amplitude: covariance_prior = np.array([[1]])
    - If use_amplitude: covariance_prior = np.array([[1, 0], [0, 1]])
    - Override by passing covariance_prior=... when constructing the model.

- Phase metadata (must align with the picks array order):
  - station_locs: phase_loc array of shape (n_picks, 1)
  - phase_type: list/array of strings "p" or "s", length n_picks
  - These are required by the gamma models and must be passed to the constructor.

- Bayesian model hyperparameters:
  - weight_concentration_prior: Dirichlet concentration; in the example, weight_concentration_prior = 1/num_event_init
  - loss_type: Robust loss type; in the example, loss_type="l1"
  - Override by passing corresponding keyword arguments to the model constructor.

- Post-fit filtering threshold:
  - min_picks: minimum number of picks assigned to a component for it to be considered a valid event; in the example: min_picks = min(num_station, 6)
  - Override by changing the value before filtering.

Notes on input keys/names:
- The example uses arrays, not a DataFrame. If you maintain a DataFrame, ensure it has fields that correspond 1:1 (same order/length) to:
  - phase_time (float, seconds), phase_amp (float, log-amplitude), phase_type (str: "p"/"s"), phase_loc (float/location per pick).
- Keep a stable pick_index (e.g., 0..n_picks-1) to join predictions back to your original picks table.

## 3) Main function calls

Prepare inputs and call the core gamma API. The example constructs a feature matrix data depending on use_amplitude and fits the mixture model. Comments are preserved.

```python
# Build the feature matrix from picks
# - If use_amplitude: 2D features [time, amplitude]
# - If not use_amplitude: 1D features [time]
data = np.hstack([phase_time, phase_amp])
if not use_amplitude:
    covariance_prior = np.array([[1]])
    data = data[:, 0:1]  # time only
else:
    covariance_prior = np.array([[1, 0], [0, 1]])  # time + amplitude

# Choose number of initial components from data size and station count
num_event_loc_init = 3
num_event_init = min(int(len(data)/min(num_station, 20) * 3), len(data))

# Build initial centers over location and time (and amplitude if used)
centers_init = np.vstack([
    np.vstack([
        np.ones(num_event_init//num_event_loc_init) * x,
        np.linspace(data[:, 0].min(), data[:, 0].max(), num_event_init//num_event_loc_init)
    ]).T
    for x in np.linspace(np.min(station_loc), np.max(station_loc), num_event_loc_init+2)[1:-1]
])
if use_amplitude:
    centers_init = np.hstack([centers_init, 1.0 * np.ones((len(centers_init), 1))])  # add magnitude column

# Fit a Gaussian mixture with EM
t_start = time.time()
gmm = BayesianGaussianMixture(
    n_components=num_event_init,
    station_locs=phase_loc,
    phase_type=phase_type,
    weight_concentration_prior=1/num_event_init,
    covariance_prior=covariance_prior,
    init_params="centers",
    centers_init=centers_init.copy(),
    loss_type="l1",
    # max_covar=10**2,
).fit(data)

# gmm = GaussianMixture(
#     n_components=num_event_init,
#     station_locs=phase_loc,
#     phase_type=phase_type,
#     init_params="centers",
#     centers_init=centers_init.copy(),
#     loss_type="l1",
#     max_covar=10,
#     # dummy_comp=True,
#     # dummy_prob=0.01,
# ).fit(data)

t_end = time.time()
print(f"GMMA time = {t_end - t_start}")

# Inference: per-pick assignments, probabilities, and scores
pred = gmm.predict(data)               # shape (n_picks,), integer component id per pick
prob = gmm.predict_proba(data)         # shape (n_picks, n_components)
score = gmm.score_samples(data)        # shape (n_picks,), log-likelihood per sample

# Per-component diagnostics
prob_eq = prob.mean(axis=0)            # average responsibility per component
std_eq = gmm.covariances_              # shape (n_components, D, D)
centers = gmm.centers_                 # shape (n_components, D or 3 if amplitude included)

# Filter valid events by pick count threshold
min_picks = min(num_station, 6)
filtered_idx = np.array([
    True if len(data[pred == i, 0]) >= min_picks else False
    for i in range(len(prob_eq))
])
filtered_idx = np.arange(len(prob_eq))[filtered_idx]

# Print a concise summary of associated events
print("Associated events:")
for i in np.argsort(gmm.centers_[:, 1]):  # sort by time center
    if i in filtered_idx:
        if not use_amplitude:
            # columns: [loc, time]
            print(f"loc={gmm.centers_[i, 0]:.1f}\tt0={gmm.centers_[i, 1]:.1f}\tsigma11={std_eq[i,0,0]:.3f}")
        else:
            # columns: [loc, time, mag]
            print(f"loc={gmm.centers_[i, 0]:.1f}\tt0={gmm.centers_[i, 1]:.1f}\tmag={gmm.centers_[i, 2]:.1f}\tsigma11={std_eq[i,0,0]:.3f}")
```

Input and output formats (especially field names/shapes):
- Inputs required by the model:
  - data: ndarray of shape (n_picks, D), where D=1 (time) if not use_amplitude, or D=2 (time, amplitude) if use_amplitude.
  - station_locs: phase_loc, ndarray shape (n_picks, 1), per-pick station location.
  - phase_type: list/array of length n_picks with values "p" or "s".
  - centers_init: ndarray of shape (n_components, 2) if not use_amplitude ([loc, time]) or shape (n_components, 3) if use_amplitude ([loc, time, mag]).
  - covariance_prior: 1x1 or 2x2 as above.
- Outputs:
  - pred: component index for each pick (length n_picks), to be joined back to the original picks via index alignment.
  - prob: per-pick responsibilities over components (n_picks x n_components).
  - centers_: per-component centers with same feature layout as data plus location (and mag if used).
  - covariances_: per-component covariance matrices.

## 4) Output handling

Attach assignments back to the original picks and optionally save to disk. The example arrays are already aligned by index; use that index as pick_index.

```python
# Create a pick_index to preserve original order for joins back to any external table
pick_index = np.arange(len(data))  # 0..n_picks-1

# Join assignment info back to your picks structure by index alignment:
# - pred gives the assigned event id per pick
# - prob gives the full probability vector per pick
assigned_event_id = pred  # same length/order as the original picks

# Example: save assignments and component summaries with numpy
np.savez(
    "gamma_results.npz",
    pick_index=pick_index,
    assigned_event_id=assigned_event_id,
    prob=prob,
    centers=centers,
    covariances=std_eq,
    filtered_components=filtered_idx
)

# If you maintain a DataFrame for picks, ensure it has a 'pick_index' column matching this order.
# Then you can merge on 'pick_index' to add 'assigned_event_id' (and any other fields) back into the picks table.
# (Pseudocode — assuming picks_df has pick_index 0..n_picks-1 in the same order)
# picks_df['assigned_event_id'] = assigned_event_id
# picks_df = picks_df.merge(component_info_df, how='left', on='assigned_event_id')

print("Saved: gamma_results.npz (assignments, probabilities, centers, covariances, filtered component ids)")
```

Special attention to join/assignment:
- Use the array index (pick_index) as the stable key to join predicted labels back to your picks store.
- The predicted labels (pred) and probabilities (prob) are in the same order as the input arrays, so you can directly align by position or merge on a pick_index column you maintain.

## Inputs and outputs

This example demonstrates how to use the gamma library’s BayesianGaussianMixture (with an alternative GaussianMixture commented) to associate synthetic P/S phase picks from multiple stations into earthquake events, optionally leveraging amplitudes. It first builds a controlled synthetic scenario by setting velocities (vp/vs), domain size and counts (events/stations), and noise controls (time/amp errors, false positives), then generates station/event locations, origin times, magnitudes, and picks by computing P/S travel times and log-amplitudes as a function of magnitude and distance, with optional fake picks to test robustness; initial visualizations compare raw picks and ground truth. For association, the data matrix includes time and amplitude (or time only if amplitudes are disabled), and cluster initialization places centers across space and time; key configurations include init_params="centers", loss_type="l1", a Dirichlet weight_concentration_prior scaled by the number of components, and a covariance_prior matching the data dimensionality. After fitting, the model returns per-pick labels (predict), soft cluster probabilities (predict_proba), sample scores, event-wise probabilities, and covariances; clusters are filtered by a minimum number of supporting picks, sorted by origin time, and then visualized by overlaying associated picks and inferred event centers (with marker sizes reflecting amplitudes when used). Output handling includes timing the fit, plotting before/after association, and printing each detected event’s location, origin time, (in amplitude mode) magnitude, and a covariance element (sigma11) for uncertainty.

## Configuration

gamma:
  inputs:
    features: ["phase_time", "phase_amp"]  # data columns used as features; amplitude included when use_amplitude is true
    station_locs: phase_loc  # 2D array of station positions aligned with picks
    phase_type: phase_type  # list/array of "p"/"s" phase labels aligned with picks
    assemble_data:
      use_amplitude: true  # if false, only time is used as a 1D feature
      data_matrix:
        when_true: "np.hstack([phase_time, phase_amp])"  # shape (n_samples, 2)
        when_false: "data = data[:, 0:1]"  # keep only time; shape (n_samples, 1)
  initialization:
    num_event_loc_init: 3  # number of spatial bands used to seed centers across station locations
    num_event_init: "min(int(len(data)/min(num_station, 20) * 3), len(data))"  # initial number of mixture components
    centers_init:
      layout: "grid over station_locs (num_event_loc_init interior bands) × uniform time bins"  # spatial × temporal seeding
      spatial_grid: "np.linspace(min(station_loc), max(station_loc), num_event_loc_init+2)[1:-1]"  # interior bands only
      time_grid: "np.linspace(data[:,0].min(), data[:,0].max(), num_event_init//num_event_loc_init)"  # per spatial band
      amplitude_seed: 1.0  # only appended as a 3rd column when use_amplitude is true
    covariance_prior:
      value: [[1, 0], [0, 1]]  # identity prior for 2D (time, amp)
      note: "use [[1]] if use_amplitude is false (1D time-only feature)"
  model:
    class: BayesianGaussianMixture  # variational Bayesian GMM
    params:
      n_components: "${num_event_init}"  # initial number of components
      station_locs: "${inputs.station_locs}"  # required by gamma to incorporate geometry
      phase_type: "${inputs.phase_type}"  # "p"/"s" labels for each pick
      weight_concentration_prior: "1/num_event_init"  # symmetric Dirichlet prior over component weights
      covariance_prior: "${initialization.covariance_prior.value}"  # prior on component covariances
      init_params: "centers"  # use user-provided centers
      centers_init: "${initialization.centers_init}"  # seeded centers
      loss_type: "l1"  # robust loss
      # max_covar: 1e2  # optional cap on covariance (commented out in example)
    fit: "gmm = BayesianGaussianMixture(...).fit(data)"  # train on assembled data
  alternative_model:  # optional EM GMM path (commented in example)
    class: GaussianMixture
    params:
      n_components: "${num_event_init}"
      station_locs: "${inputs.station_locs}"
      phase_type: "${inputs.phase_type}"
      init_params: "centers"
      centers_init: "${initialization.centers_init}"
      loss_type: "l1"
      max_covar: 10  # capped covariance in EM path
      # dummy_comp: true  # optional extra component for unassigned picks (commented)
      # dummy_prob: 0.01  # prior probability for dummy component (commented)
    fit: "gmm = GaussianMixture(...).fit(data)"
  inference:
    predict_labels: "pred = gmm.predict(data)"  # component assignment per pick
    predict_proba: "prob = gmm.predict_proba(data)"  # assignment probabilities
    score_samples: "score = gmm.score_samples(data)"  # per-sample score
    component_stats:
      prob_eq: "prob.mean(axis=0)"  # mean responsibility per component
      covariances: "std_eq = gmm.covariances_"  # per-component covariance matrices
  postprocessing:
    min_picks: "min(num_station, 6)"  # minimum picks to consider a component as an event
    filter_rule: "keep component i if count(pred==i) >= min_picks"  # simple quality control
    filtered_idx: "np.where([len(data[pred==i, 0]) >= min_picks for i in range(len(prob_eq))])[0]"
  notes:
    - "dummy_prob was computed but not used in the final Bayesian path."
    - "When use_amplitude is false, set covariance_prior to [[1]] and use only the time column."

## Diagnostics and plotting

Below is a concise, plot-by-plot summary of all visualizations in the example, including what is shown, how it is produced (matplotlib calls), the inputs and outputs (with parameters as used), and the intended interpretation. Each figure has two subplots; each subplot is summarized separately and paired with the exact code used to produce it.

Figure 1 — Synthetic data visualization (two subplots)

Left subplot: “P/S phase picks”
- What to plot:
  - All generated phase picks (P and S) as a function of time (x-axis) and station distance (y-axis).
  - If use_amplitude is True, bubble size encodes phase amplitude via s=(4**phase_amp)*1e3; otherwise a fixed size (s=12).
- How to plot:
  - Matplotlib scatter plot via plt.scatter.
  - Plot configuration: grey markers, circle marker "o", alpha=0.8, legend entry added via a dummy off-plot point at (-1, -1).
  - Axes configuration: xlim left bound at 0, ylim set to xlim variable (distance range), labels, legend, and an in-axes text annotation “(i)”.
- Inputs:
  - phase_time (x), phase_loc (y), phase_amp (for marker size when use_amplitude=True)
  - Global config and styling variables: use_amplitude, xlim, text_loc = [0.05, 0.95], box = dict(boxstyle='round', facecolor='white', alpha=1)
- Outputs:
  - A scatter plot titled “P/S phase picks” displayed in the left panel of Figure 1.

Code that produces this subplot:
```python
plt.figure()
text_loc = [0.05, 0.95]
box = dict(boxstyle='round', facecolor='white', alpha=1)
plt.subplot(121)
if use_amplitude:
    plt.scatter(phase_time, phase_loc, s=(4**np.array(phase_amp))*1e3, color="grey",  marker="o", alpha=0.8)
else:
    plt.scatter(phase_time, phase_loc, s=12, color="grey",  marker="o", alpha=0.8)
plt.scatter(-1, -1, s=24, color="grey",  marker="o", alpha=0.8, label="Picks")
plt.xlim(left=0)
plt.ylim(xlim)
ylim_ = plt.ylim()
xlim_ = plt.xlim()
plt.ylabel("Distance (km)")
plt.xlabel("Time (s)")
plt.legend()
plt.text(text_loc[0], text_loc[1], '(i)', horizontalalignment='left', verticalalignment='top',
         transform=plt.gca().transAxes, fontsize="medium", fontweight="normal", bbox=box)
plt.title("P/S phase picks")
```
Interpretation:
- Visual check of the simulated P/S arrival times across stations; marker size reflects amplitude if used.

Right subplot: “Ground truth”
- What to plot:
  - Picks associated with true events colored by their event index; unassociated (fake) picks in grey.
  - True event origins plotted as “Earthquakes” using a pointed “P” marker at (event_t0, event_loc), with size proportional to 5**event_mag*3.
- How to plot:
  - Matplotlib scatter; two scatter calls for associated vs fake picks; event markers plotted in a loop.
  - Y-axis tick labels removed; same x/y limits as left plot; legend and “(ii)” annotation.
- Inputs:
  - phase_time, phase_loc, phase_amp, phase_event_idx, event_t0, event_loc, event_mag, num_event, use_amplitude
  - Reuse xlim_ and ylim_ captured from the left subplot so the panels align.
- Outputs:
  - A scatter plot titled “Ground truth” displayed in the right panel of Figure 1.

Code that produces this subplot:
```python
plt.subplot(122)
if use_amplitude:
    plt.scatter(phase_time[phase_event_idx!=num_event], phase_loc[phase_event_idx!=num_event], \
                s=(4**np.array(phase_amp[phase_event_idx!=num_event]))*1e3, \
                color=[f"C{x}"for x in phase_event_idx[phase_event_idx!=num_event]],  marker="o", facecolors='none')
    plt.scatter(phase_time[phase_event_idx==num_event], phase_loc[phase_event_idx==num_event], \
                s=(4**np.array(phase_amp[phase_event_idx==num_event]))*1e3, \
                color="grey",  marker="o", alpha=0.8)
else:
    plt.scatter(phase_time[phase_event_idx!=num_event], phase_loc[phase_event_idx!=num_event], \
                s=12, \
                color=[f"C{x}"for x in phase_event_idx[phase_event_idx!=num_event]],  marker="o", facecolors='none')
    plt.scatter(phase_time[phase_event_idx==num_event], phase_loc[phase_event_idx==num_event], \
                s=12, \
                color="grey",  marker="o", alpha=0.8)
plt.scatter(-1, -1, s=24, color="C0",  marker="o", facecolors='none', label="Associated picks")
for i in range(len(event_mag)):
    plt.scatter(event_t0[i], event_loc[i], s=5**np.array(event_mag[i])*3, color=f"C{i}", marker="P")
plt.scatter(-1, -1, s=48, color="C0", marker="P", label="Earthquakes")
plt.xlim(xlim_)
plt.ylim(ylim_)
plt.xlabel("Time (s)")
# plt.ylabel("Distance (km)")
plt.gca().yaxis.set_ticklabels([])
plt.legend()
plt.text(text_loc[0], text_loc[1], '(ii)', horizontalalignment='left', verticalalignment='top',
         transform=plt.gca().transAxes, fontsize="medium", fontweight="normal", bbox=box)
plt.title("Ground truth")
plt.show();
```
Interpretation:
- Shows the true association of picks to events and the true event origin points; serves as a baseline for later model predictions.

Figure 2 — GaMMA results (two subplots)

Left subplot: “P/S phase picks” (repeated data view)
- What to plot:
  - Same as Figure 1, left panel; re-establishes the pick field for side-by-side comparison with model predictions.
- How to plot:
  - Identical matplotlib scatter sequence as the first panel in Figure 1.
- Inputs:
  - phase_time, phase_loc, phase_amp, use_amplitude, xlim, text_loc, box.
- Outputs:
  - A scatter plot titled “P/S phase picks” in the left panel of Figure 2.

Code that produces this subplot:
```python
plt.figure()
plt.subplot(121)
if use_amplitude:
    plt.scatter(phase_time, phase_loc, s=(4**np.array(phase_amp))*1e3, color="grey",  marker="o", alpha=0.8)
else:
    plt.scatter(phase_time, phase_loc, s=12, color="grey",  marker="o", alpha=0.8)
plt.scatter(-1, -1, s=24, color="grey",  marker="o", alpha=0.8, label="Picks")
plt.xlim(left=0)
plt.ylim(xlim)
ylim_ = plt.ylim()
xlim_ = plt.xlim()
plt.ylabel("Distance (km)")
plt.xlabel("Time (s)")
plt.legend()
plt.text(text_loc[0], text_loc[1], '(i)', horizontalalignment='left', verticalalignment='top',
         transform=plt.gca().transAxes, fontsize="medium", fontweight="normal", bbox=box)
plt.title("P/S phase picks")
```
Interpretation:
- Repeats the data scatter for visual consistency before overlaying model outputs.

Right subplot: “GMMA prediction”
- What to plot:
  - Model-associated picks per predicted event/component after running BayesianGaussianMixture (GaMMA), filtered to components with at least min_picks observations.
  - Event centers inferred by GaMMA (gmm.centers_) plotted as “Earthquakes” (marker "P"), sized by 4**gmm.centers_[i,2]*3 when use_amplitude=True; otherwise fixed markersize=8 via plt.plot for the center.
- How to plot:
  - Matplotlib scatter; color cycles per detected event (C0, C1, …) following a sorted order by event time gmm.centers_[:, 1].
  - Picks: plotted with hollow circles (facecolors='none'); sizes scale with amplitude if applicable.
  - Centers: plotted at (t0, loc) from gmm.centers_ with pointed “P” marker; size depends on whether amplitude is modeled.
  - Legend entries created via off-plot dummy scatters; y-tick labels hidden; “(iii)” annotation added; axes share limits with the left panel.
- Inputs:
  - data[:, 0] (time), phase_loc[:, 0] (distance), pred (cluster assignments), gmm.centers_, std_eq (covariances), filtered_idx (component filter), use_amplitude, xlim_, ylim_, text_loc, box.
  - The code uses np.argsort(gmm.centers_[:, 1]) to order components by time.
- Outputs:
  - A scatter overlay of GaMMA-associated picks and inferred event centers; printed console lines with estimated parameters per event; a titled figure “GMMA prediction”.

Code that produces this subplot:
```python
plt.subplot(122)
colors = defaultdict(int)
idx = np.argsort(gmm.centers_[:, 1])
dum = 0
print("Associated events:")
for i in idx:
    if i in filtered_idx:
        if not use_amplitude:
            plt.scatter(data[(pred==i), 0], phase_loc[(pred==i), 0], color=f"C{dum}", s=12, marker='o', facecolors='none')
            plt.plot(gmm.centers_[i, 1], gmm.centers_[i, 0], "P", c=f"C{dum}", markersize=8)
            print(f"loc={gmm.centers_[i, 0]:.1f}\tt0={gmm.centers_[i, 1]:.1f}\tsigma11={std_eq[i,0,0]:.3f}")
        else:
            plt.scatter(data[(pred==i), 0], phase_loc[(pred==i), 0], color=f"C{dum}", s=4**(data[(pred==i), 1])*1e3, marker='o', facecolors='none')
            plt.scatter(gmm.centers_[i, 1], gmm.centers_[i, 0], color=f"C{dum}", s=4**gmm.centers_[i, 2]*3, marker="P")
            print(f"loc={gmm.centers_[i, 0]:.1f}\tt0={gmm.centers_[i, 1]:.1f}\tmag={gmm.centers_[i, 2]:.1f}\tsigma11={std_eq[i,0,0]:.3f}")
        dum += 1
plt.scatter(-1, -1, s=24, color="C0",  marker="o", facecolors='none', label="Associated picks")
plt.scatter(-1, -1, s=48, color="C0", marker="P", label="Earthquakes")
plt.xlim(xlim_)
plt.ylim(ylim_)
plt.xlabel("Time (s)")
plt.gca().yaxis.set_ticklabels([])
plt.legend()
plt.text(text_loc[0], text_loc[1], '(iii)', horizontalalignment='left', verticalalignment='top',
         transform=plt.gca().transAxes, fontsize="medium", fontweight="normal", bbox=box)
plt.title("GMMA prediction")
plt.show()
```
Interpretation:
- Visualizes GaMMA’s association of picks to events and its estimated event centers; serves to compare model predictions to the earlier “Ground truth” view. Picks’ sizes and event marker sizes reflect modeled amplitudes when enabled.

General plotting details across figures
- Library:
  - matplotlib.pyplot as plt
- Display:
  - Figures are rendered with plt.show() at the end of each figure block.
- Legends:
  - Created using dummy scatter points at (-1, -1) to control labels and marker styles.
- Annotations:
  - Subplots are annotated with “(i)”, “(ii)”, and “(iii)” via plt.text using:
    - text_loc = [0.05, 0.95]
    - box = dict(boxstyle='round', facecolor='white', alpha=1)
- Axes:
  - Left subplots set xlim(left=0) and ylim(xlim). Right subplots reuse xlim_/ylim_ captured from the left subplot to ensure matched limits.
- Conditional sizing by amplitude:
  - When use_amplitude is True:
    - Pick size s=(4**phase_amp)*1e3
    - True event marker size s=5**event_mag*3
    - Predicted event center size s=4**gmm.centers_[i, 2]*3
  - When use_amplitude is False:
    - Pick size s=12; predicted center plotted with markersize=8.
