# GaMMA associator configuration (units: km for x,y,z; s for time; local projected coordinates)
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
