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
