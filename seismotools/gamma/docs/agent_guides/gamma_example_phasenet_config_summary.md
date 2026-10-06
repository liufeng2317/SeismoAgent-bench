use_dbscan: true                    # whether to use DBSCAN preprocessing
use_amplitude: true                 # use amplitude in association (set false for 'chile' example); picks with amp == -1 are filtered out
method: "BGMM"                      # association method ("BGMM" or "GMM")
oversample_factor: 5                # BGMM: 5; if method == "GMM", use 2
# covariance_prior: [5.0, 2.0]      # optional prior for (time, amplitude); larger prevents splitting, too large may merge events

# --- Earthquake location (uniform velocity fallback) ---
vel:                                 # uniform velocity model used if no eikonal provided
  p: 6.0
  s: 3.428571                       # 6.0/1.75
dims: ["x(km)", "y(km)", "z(km)"]   # location parameterization in km (projected)
"x(km)": [xmin, xmax]               # projected X range in km (from AEQD projection around station median)
"y(km)": [ymin, ymax]               # projected Y range in km
"z(km)": [0, 20]                    # depth range in km; use [0, 250] for 'chile'

bfgs_bounds:                         # bounds for BFGS optimization: x, y, z, origin time
  - [x(km)_min - 1, x(km)_max + 1]
  - [y(km)_min - 1, y(km)_max + 1]
  - [0, z(km)_max + 1]
  - [null, null]                    # time is unbounded

# --- DBSCAN parameters (pre-clustering) ---
dbscan_eps: 15                      # neighborhood size in km; larger reduces splitting but increases preprocessing time
dbscan_min_samples: 3               # min samples to form a core point
dbscan_min_cluster_size: 500        # min cluster size to keep
dbscan_max_time_space_ratio: 5      # cap ratio of time to space scale

# --- Eikonal velocity model (1D, optional but used in examples) ---
eikonal:
  vel:                               # example 'ridgecrest' 1D model; for 'chile' load iasp91.csv into z/p/s arrays
    z: [0.0, 5.5, 16.0, 32.0]        # depths (km)
    p: [5.5, 5.5, 6.7, 7.8]          # P-wave velocities (km/s)
    s: [3.18, 3.18, 3.88, 4.51]      # S-wave velocities (km/s)
  h: 1.0                             # grid spacing (km)
  xlim: [xmin, xmax]                 # same spatial limits as x(km)
  ylim: [ymin, ymax]                 # same spatial limits as y(km)
  zlim: [zmin, zmax]                 # same depth limits as z(km)

# --- Runtime ---
ncpu: 32                             # number of CPUs

# --- Event filtering (post-association) ---
min_picks_per_eq: 5                  # minimum total picks per event
min_p_picks_per_eq: 0                # minimum P picks
min_s_picks_per_eq: 0                # minimum S picks
max_sigma11: 3.0                     # max timing uncertainty (s)
max_sigma22: 1.0                     # max amplitude uncertainty (log10 m/s)
max_sigma12: 1.0                     # max time–amplitude covariance
