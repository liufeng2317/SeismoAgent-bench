# Gamma usage: Associating P/S picks with Gaussian mixtures (synthetic-data example)

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
