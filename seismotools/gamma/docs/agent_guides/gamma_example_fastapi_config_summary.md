gamma:
  api:  # Service wrapper used in the example (not part of core GaMMA config)
    base_url: "https://ai4eps-gamma.hf.space"  # Endpoint used by the FastAPI demo
    predict_endpoint: "/predict/"  # POST endpoint for association

  io:  # I/O schema expected by GaMMA
    picks_required_fields: ["id", "timestamp", "prob", "amp", "type"]  # Required pick fields
    stations_required_fields: ["id", "elevation(m)"]  # Required station fields
    rename_to_gamma:  # Column renaming performed before calling association()
      picks:
        station_id: "id"  # station identifier
        phase_time: "timestamp"  # pick time (ISO or pandas datetime)
        phase_type: "type"  # P/S (uppercased)
        phase_score: "prob"  # detection/phase probability
        phase_amplitude: "amp"  # observed amplitude
      stations:
        station_id: "id"
        elevation(m): "elevation_m"
    station_coordinates:  # Station coordinate preparation
      projection_spec: "+proj=aeqd +lon_0=<lon0> +lat_0=<lat0> +units=km"  # Azimuthal equidistant; lon0/lat0 are region midpoints
      x(km): "proj(longitude, latitude) -> x"  # Computed at runtime from lon/lat
      y(km): "proj(longitude, latitude) -> y"  # Computed at runtime from lon/lat
      z(km): "-elevation_m/1000"  # Depth positive down; elevation above sea level is negative depth

  config:
    basic:  # Core association thresholds
      min_picks: 8  # Minimum number of picks to consider an event
      min_picks_ratio: 0.2  # Minimum fraction of picks supporting an event
      max_residual_time: 1.0  # Max allowed time residual (s)
      max_residual_amplitude: 1.0  # Max allowed amplitude residual (linear units)
      min_score: 0.6  # Minimum pick probability to use
      min_s_picks: 2  # Minimum S picks per candidate event
      min_p_picks: 2  # Minimum P picks per candidate event
      use_amplitude: true  # Use amplitudes in association (set true in example)

    region:  # Spatial domain (Ridgecrest example)
      name: "ridgecrest"
      minlongitude: -118.004  # West bound
      maxlongitude: -117.004  # East bound
      minlatitude: 35.205  # South bound
      maxlatitude: 36.205  # North bound
      mindepth_km: 0.0  # Shallow bound
      maxdepth_km: 41.0  # Deep bound

    projection:  # Derived from region bounds (computed at runtime)
      lon0: "(minlongitude + maxlongitude)/2"  # Projection center longitude
      lat0: "(minlatitude + maxlatitude)/2"  # Projection center latitude
      proj: null  # pyproj.Proj instance (runtime only)
      xlim_km: ["xmin", "xmax"]  # Projected X bounds in km
      ylim_km: ["ymin", "ymax"]  # Projected Y bounds in km
      zlim_km: [0.0, 41.0]  # Depth bounds in km
      "z(km)": [0.0, 41.0]  # Alias for depth bounds

    event_filtering:  # Event-level quality control
      min_picks_per_eq: 5  # Min total picks per event to report
      min_p_picks_per_eq: 0  # Min P picks per event (post-fit)
      min_s_picks_per_eq: 0  # Min S picks per event (post-fit)
      max_sigma11: 3.0  # Max time uncertainty
      max_sigma22: 1.0  # Max amplitude uncertainty
      max_sigma12: 1.0  # Max covariance between time and amplitude

    association:  # Clustering/association settings
      method: "BGMM"  # Association method ("BGMM" or "GMM")
      use_dbscan: false  # Use DBSCAN instead of BGMM
      oversample_factor: 8.0  # Oversampling factor for BGMM
      dims: ["x(km)", "y(km)", "z(km)"]  # Location dimensions to solve
      ncpu: 32  # Parallel workers (set to 32 in example)

    velocity_model:  # Uniform velocities
      p: 6.0  # P-wave velocity (km/s)
      s: 3.428571  # S-wave velocity (km/s) = 6.0/1.75

    optimization:  # Local optimization bounds (BFGS)
      bfgs_bounds:
        - ["xmin-1", "xmax+1"]  # X in km (expanded by 1 km)
        - ["ymin-1", "ymax+1"]  # Y in km (expanded by 1 km)
        - [0, "zmax+1"]  # Z in km (from 0 to slightly deeper than maxdepth)
        - [null, null]  # Origin time (unbounded)

    runtime:  # State updated at run-time
      event_index: 1  # Event index counter (set to 1 before running in example)
