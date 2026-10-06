center: [lon0, lat0]            # float[2]: map center (deg), auto-set from region bounds
xlim_degree: [minlon, maxlon]   # float[2]: longitude bounds (deg)
ylim_degree: [minlat, maxlat]   # float[2]: latitude bounds (deg)

# --- Method selection ---
use_dbscan: true                # bool: use DBSCAN to pre-cluster picks
use_amplitude: true             # bool: use amplitude in association (False for Chile in example)
method: "BGMM"                  # str: "BGMM" (BayesianGaussianMixture) or "GMM"
oversample_factor: 5            # int: BGMM=5, GMM=1 in example

# --- Velocity (uniform) ---
vel:                            # dict: uniform velocity model used if no eikonal is provided
  p: 6.0                        # float: P-wave velocity (km/s)
  s: 3.428571                   # float: S-wave velocity (km/s), 6.0/1.75

# --- Location grid / search space ---
dims: ["x(km)", "y(km)", "z(km)"]  # list[str]: location parameter names
x(km): [xmin, xmax]             # float[2]: projected x-range (km) from xlim_degree
y(km): [ymin, ymax]             # float[2]: projected y-range (km) from ylim_degree
z(km): [zmin, zmax]             # float[2]: depth range (km); examples: Ridgecrest=[0,20], Chile=[0,250], else=[0,30]

# --- Optimization bounds (BFGS) ---
bfgs_bounds:                    # list[list]: [x_min,x_max],[y_min,y_max],[z_min,z_max],[t_min,t_max]
  - [x(km)_min-1, x(km)_max+1]  # x (km)
  - [y(km)_min-1, y(km)_max+1]  # y (km)
  - [0, z(km)_max+1]            # z (km)
  - [null, null]                # origin time (unbounded)

# --- DBSCAN parameters ---
dbscan_eps: 10                  # float: neighborhood radius (km); example uses 10
dbscan_min_samples: 3           # int: minimum samples per cluster

# --- Eikonal 1D velocity model (optional; overrides uniform vel for travel times) ---
eikonal:                        # dict: enable to use 1D model and eikonal solver
  vel:                          # example (Ridgecrest); for Chile load iasp91.csv up to zmax
    z: [0.0, 5.5, 16.0, 32.0]   # float[]: depths (km)
    p: [5.5, 5.5, 6.7, 7.8]     # float[]: P velocities (km/s)
    s: [3.18, 3.18, 3.88, 4.51] # float[]: S velocities (km/s), vp/vs≈1.73
  h: 1.0                        # float: grid spacing (km)
  xlim: [xmin, xmax]            # float[2]: x-range (km)
  ylim: [ymin, ymax]            # float[2]: y-range (km)
  zlim: [zmin, zmax]            # float[2]: z-range (km)

# --- Initial search point (optional; used in Chile example) ---
initial_points: [1, 1, 1]       # int[3]: initial indices for x,y,z search

# --- Runtime ---
ncpu: 32                        # int: number of CPU cores

# --- Event filtering thresholds ---
min_picks_per_eq: 5             # int: minimum total picks per event
min_p_picks_per_eq: 0           # int: minimum P picks per event
min_s_picks_per_eq: 0           # int: minimum S picks per event
max_sigma11: 15.0               # float: max travel-time uncertainty (s)
max_sigma22: 3.0                # float: max amplitude uncertainty (log10 m/s)
max_sigma12: 3.0                # float: max time–amplitude covariance

# Notes:
# - x(km), y(km) are obtained by projecting lon/lat using an azimuthal equidistant projection centered at `center`.
# - dbscan_eps can be estimated from stations and P velocity (e.g., estimate_eps(stations, vel.p) in example).
# - When use_amplitude is true, picks without amplitude (amp == -1) are removed before association.
