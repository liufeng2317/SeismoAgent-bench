import multiprocessing as mp
import platform
import random
from collections import Counter
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from tqdm import tqdm

from ._bayesian_mixture import BayesianGaussianMixture
from ._gaussian_mixture import GaussianMixture
from .seismic_ops import calc_amp, calc_time, initialize_eikonal

to_seconds = lambda t: t.timestamp(tz="UTC")
from_seconds = lambda t: pd.Timestamp.utcfromtimestamp(t).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
# to_seconds = lambda t: datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%f").timestamp()
# from_seconds = lambda t: [datetime.utcfromtimestamp(x).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] for x in t]


def random_seed():
    np.random.seed(42)
    random.seed(42)


# def estimate_station_spacing(stations):
def estimate_eps(stations, vp, sigma=2.0):
    """ 
    Estimate eps based on station spacing and wave velocity.

    Parameters
    ----------
    stations : pandas.DataFrame
        Station coordinates with columns ["x(km)", "y(km)", "z(km)"].
    vp : float
        Seismic wave velocity (km/s).
    sigma : float, optional
        Adjustment factor for including variability in spacing. Default is 2.0.

    Returns
    -------
    eps : float
        Estimated eps (in seconds), reflecting typical travel time between stations.
    """
    X = stations[["x(km)", "y(km)", "z(km)"]].values
    D = np.sqrt(((X[:, np.newaxis, :] - X[np.newaxis, :, :]) ** 2).sum(axis=-1))

    D[D == 0] = np.inf
    dist = np.sort(D, axis=1)[:, 1]

    std = np.std(dist)
    dist = np.mean(dist) + sigma * std

    eps = dist / vp * 1.5

    return eps



def convert_picks_csv(picks, stations, config):
    """ 
    Convert seismic picks DataFrame into numerical arrays for further processing.

    Parameters
    ----------
    picks : pandas.DataFrame
        Pick information with columns:
        - "timestamp": pick time (string or datetime with/without timezone)
        - "amp": amplitude (if used)
        - "id": station ID
        - "type": phase type (e.g., P or S)
        - "prob": probability/confidence of the pick
    stations : pandas.DataFrame
        Station metadata with coordinates and station IDs.
    config : dict
        Configuration dictionary. Must include:
        - "use_amplitude": bool, whether to include amplitude
        - "dims": list of str, coordinate columns (e.g., ["x(km)", "y(km)", "z(km)"])

    Returns
    -------
    data : np.ndarray
        Time (and amplitude if enabled), shape (N, 1 or 2).
    locs : np.ndarray
        Station coordinates for picks, shape (N, len(dims)).
    phase_type : np.ndarray
        Phase types (lowercase strings).
    phase_weight : np.ndarray
        Pick probabilities, shape (N, 1).
    pick_index : np.ndarray
        Original row indices of picks.
    pick_station_id : np.ndarray
        Combined station-phase identifiers.
    timestamp0 : float
        Minimum timestamp (epoch seconds), used as reference.
    """
    # Ensure timestamps are datetime objects
    if isinstance(picks["timestamp"].iloc[0], str):
        picks.loc[:, "timestamp"] = picks["timestamp"].apply(lambda x: datetime.fromisoformat(x))

    # Convert timestamps to UTC epoch seconds
    t = (
        picks["timestamp"]
        .apply(
            lambda x: x.tz_convert("UTC").timestamp()
            if x.tzinfo is not None
            else x.tz_localize("UTC").timestamp()
        )
        .to_numpy()
    )

    # Normalize time to start from zero
    timestamp0 = np.min(t)
    t = t - timestamp0

    # Use amplitude if configured
    if config["use_amplitude"]:
        a = picks["amp"].apply(lambda x: np.log10(x * 1e2)).to_numpy()  # cm/s
        data = np.stack([t, a]).T
    else:
        data = t[:, np.newaxis]

    # Match picks with station metadata
    meta = stations.merge(picks["id"], how="right", on="id", validate="one_to_many")
    locs = meta[config["dims"]].to_numpy()

    # Extract phase info
    phase_type = picks["type"].apply(lambda x: x.lower()).to_numpy()
    phase_weight = picks["prob"].to_numpy()[:, np.newaxis]
    pick_station_id = picks.apply(lambda x: x.id + "_" + x.type, axis=1).to_numpy()

    # Remove entries with missing station metadata
    nan_idx = meta.isnull().any(axis=1)

    return (
        data[~nan_idx],
        locs[~nan_idx],
        phase_type[~nan_idx],
        phase_weight[~nan_idx],
        picks.index.to_numpy()[~nan_idx],
        pick_station_id[~nan_idx],
        timestamp0,
    )



def hierarchical_dbscan_clustering(
    data,
    phase_loc,
    phase_type,
    phase_weight,
    vel,
    eps=15,
    min_samples=3,
    min_cluster_size=500,
    max_time_space_ratio=10,
):
    """ 
    Perform hierarchical DBSCAN clustering on seismic picks.

    This method first applies DBSCAN using time and spatial coordinates. 
    Large clusters with inconsistent time–space ratios are iteratively 
    split using progressively smaller eps values until clusters become 
    temporally compact relative to spatial extent.

    Parameters
    ----------
    data : np.ndarray
        Pick features (at least including time).
    phase_loc : np.ndarray
        Station coordinates of picks, shape (N, D).
    phase_type : np.ndarray
        Phase types (e.g., 'P', 'S').
    phase_weight : np.ndarray
        Sample weights for picks, shape (N, 1).
    vel : dict
        Dictionary of velocities, e.g., {"p": vp_value}.
    eps : float, optional
        Initial DBSCAN eps parameter (in seconds). Default is 15.
    min_samples : int, optional
        Minimum number of samples for DBSCAN. Default is 3.
    min_cluster_size : int, optional
        Minimum number of picks to allow splitting. Default is 500.
    max_time_space_ratio : float, optional
        Maximum allowed ratio of temporal span to spatial span/velocity. 
        Clusters exceeding this threshold are further split. Default is 10.

    Returns
    -------
    labels : np.ndarray
        Cluster labels for each pick. -1 denotes noise.
    """
    def dbscan2(t, xy, w, ph, vel, eps, min_samples, ratio=1.1):
        data = np.hstack([t, xy / vel["p"]])  # time, x, y
        db_ = DBSCAN(eps=eps * ratio, min_samples=min_samples, n_jobs=-1).fit(
            data, sample_weight=np.squeeze(w, axis=-1)
        )
        return db_.labels_

    db = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1).fit(
        np.hstack([data[:, 0:1], phase_loc[:, :2] / vel["p"]]),  # time, x, y
        sample_weight=np.squeeze(phase_weight, axis=-1),
    )

    labels = db.labels_
    unique_labels = np.unique(labels)
    current_label = labels.max() + 1
    ratio = 1

    for _ in range(50):
        ratio /= 1.2
        unique_labels = np.unique(labels)
        current_label = unique_labels.max() + 1
        keep_split = False

        for label in tqdm(unique_labels, desc=f"Clustering (eps={eps * ratio:.2f})"):
            if label == -1:
                continue

            idx = labels == label
            if np.sum(idx) < min_cluster_size:
                continue

            t = data[idx, 0:1]
            xy = phase_loc[idx, :2]
            w = phase_weight[idx]
            ph = phase_type[idx]

            dxy = np.linalg.norm(xy.max(axis=0) - xy.min(axis=0))
            dt = t.max() - t.min()
            if dt < dxy / vel["p"] * max_time_space_ratio:  # s
                continue

            labels_ = dbscan2(t, xy, w, ph, vel, eps=eps, min_samples=min_samples, ratio=ratio)
            labels_ = np.where(labels_ == -1, -1, labels_ + current_label)
            labels[idx] = labels_

            current_label = labels_.max() + 1
            keep_split = True

        if not keep_split:
            break

    return labels


def association(picks, stations, config, event_idx0=0, method="BGMM", **kwargs):
    """ 
    Associate seismic picks into events using DBSCAN clustering and pick-to-event assignment.

    This function performs the following steps:
    1. Convert the input picks DataFrame into numerical arrays.
    2. Apply hierarchical DBSCAN clustering if enabled to group nearby picks.
    3. Split processing into CPU cores for parallel association if multiple CPUs are specified.
    4. For each cluster, associate picks to seismic events using the specified method.

    Parameters
    ----------
    picks : pandas.DataFrame
        Pick information ("timestamp", "amp", "type", "id", "prob", etc.).
            - "timestamp": pick time (string or datetime with/without timezone)
            - "amp": amplitude (if used)
            - "type": phase type (e.g., 'P', 'S')
            - "id": station ID
            - "prob": probability/confidence of the pick
    stations : pandas.DataFrame
        Station metadata ("id", "x(km)", "y(km)", "z(km)", etc.).
            - "id": station ID
            - "x(km)": station longitude in kilometers
            - "y(km)": station latitude in kilometers
            - "z(km)": station elevation in kilometers
    config : dict
        Configuration dictionary, may include:
        - "use_dbscan": bool, whether to apply hierarchical DBSCAN.
        - "dbscan_eps": float, DBSCAN eps parameter.
        - "dbscan_min_samples": int, minimum samples for DBSCAN.
        - "dbscan_min_cluster_size": int, minimum cluster size for splitting.
        - "dbscan_max_time_space_ratio": float, max time/space ratio for splitting clusters.
        - "vel": dict, velocities {"p": value, "s": value}.
        - "ncpu": int, number of CPUs for parallel processing.
        - "min_picks_per_eq": int, minimum picks to form an event.
        - other parameters used by `associate` function.
    event_idx0 : int, optional
        Starting event index. Default is 0.
    method : str, optional
        Method for pick association (default: "BGMM").
    **kwargs : additional arguments
        Passed to underlying `associate` function.

    Returns
    -------
    events : list
        List of associated events.
    assignment : list
        List of pick-to-event assignments (indices or IDs).

    Notes
    -----
    - If DBSCAN is enabled, picks are first clustered in time-space space.
    - Large clusters with high time-to-space ratios are iteratively split.
    - Supports single-threaded or multi-threaded execution.
    """
    data, locs, phase_type, phase_weight, pick_idx, pick_station_id, timestamp0 = convert_picks_csv(
        picks, stations, config
    )

    if len(data) < config["min_picks_per_eq"]:
        return [], []

    vel = config["vel"] if "vel" in config else {"p": 6.0, "s": 6.0 / 1.73}
    if ("eikonal" not in config) or (config["eikonal"] is None):
        config["eikonal"] = None
    else:
        config["eikonal"] = initialize_eikonal(config["eikonal"])

    if ("use_dbscan" in config) and config["use_dbscan"]:
        labels = hierarchical_dbscan_clustering(
            data,
            locs,
            phase_type,
            phase_weight,
            vel,
            eps=config["dbscan_eps"],
            min_samples=config["dbscan_min_samples"],
            min_cluster_size=config["dbscan_min_cluster_size"] if "dbscan_min_cluster_size" in config else 500,
            max_time_space_ratio=(
                config["dbscan_max_time_space_ratio"] if "dbscan_max_time_space_ratio" in config else 10
            ),
        )
        unique_labels = set(labels)
        unique_labels = unique_labels.difference([-1])
    else:
        labels = np.zeros(len(data))
        unique_labels = [0]

    if "ncpu" not in config:
        config["ncpu"] = max(1, min(len(unique_labels) // 4, min(32, mp.cpu_count() - 1)))
    else:
        config["ncpu"] = min(mp.cpu_count(), config["ncpu"])

    if config["ncpu"] == 1:
        print(f"Associating {len(data)} picks with {config['ncpu']} CPUs")
        event_idx = 0
        events, assignment = [], []
        for unique_label in list(unique_labels):
            events_, assignment_ = associate(
                unique_label,
                labels,
                data,
                locs,
                phase_type,
                phase_weight,
                pick_idx,
                pick_station_id,
                config,
                timestamp0,
                vel,
                method,
                event_idx,
            )
            event_idx += len(events_)
            events.extend(events_)
            assignment.extend(assignment_)
    else:
        manager = mp.Manager()
        lock = manager.Lock()
        # event_idx0 - 1 as event_idx is increased before use
        event_idx = manager.Value("i", event_idx0 - 1)
        print(f"Associating {len(unique_labels)} clusters with {config['ncpu']} CPUs")
        # the following sort and shuffle is to make sure jobs are distributed evenly
        counter = Counter(labels)
        unique_labels = sorted(unique_labels, key=lambda x: counter[x], reverse=True)
        np.random.shuffle(unique_labels)
        # the default chunk_size is len(unique_labels)//(config["ncpu"]*4), which makes some jobs very heavy
        chunk_size = max(len(unique_labels) // (config["ncpu"] * 20), 1)
        # Check for OS to start a child process in multiprocessing
        # https://superfastpython.com/multiprocessing-context-in-python/
        if platform.system().lower() in ["darwin", "windows"]:
            context = "spawn"
        else:
            context = "fork"
        with mp.get_context(context).Pool(config["ncpu"], initializer=random_seed) as p:
            results = p.starmap(
                associate,
                [
                    [
                        k,
                        labels,
                        data,
                        locs,
                        phase_type,
                        phase_weight,
                        pick_idx,
                        pick_station_id,
                        config,
                        timestamp0,
                        vel,
                        method,
                        event_idx,
                        lock,
                    ]
                    for k in unique_labels
                ],
                chunksize=chunk_size,
            )
            # resuts is a list of tuples, each tuple contains two lists events and assignment
            # here we flatten the list of tuples into two lists
            events, assignment = [], []
            for each_events, each_assignment in results:
                events.extend(each_events)
                assignment.extend(each_assignment)

    return events, assignment  # , event_idx.value


def associate(
    k,
    labels,
    data,
    locs,
    phase_type,
    phase_weight,
    pick_idx,
    pick_station_id,
    config,
    timestamp0,
    vel,
    method,
    event_idx,
    lock=None,
):
    """
    Associate picks in a single cluster into seismic events using GMM or Bayesian GMM.

    Steps:
    1. Select picks corresponding to cluster `k`.
    2. Estimate maximum number of events based on station redundancy.
    3. Initialize event centers using weighted location and time.
    4. Set covariance priors adaptively based on spatial spread and amplitude usage.
    5. Fit GMM/BGMM to the cluster picks (time ± amplitude).
    6. Predict cluster membership and probability for each pick.
    7. Filter predicted events:
       - Minimum number of picks per event
       - Picks consistent in time relative to predicted center
       - Only one pick per station (closest in time)
       - Optional amplitude consistency
       - Minimum number of P/S picks or stations
    8. Assign an event index safely (supporting multiprocessing via `lock`).
    9. Construct event dictionary with location, time, magnitude, covariance, and score.
    10. Return list of events and pick-to-event assignments.

    Parameters
    ----------
    k : int
        Cluster label to process.
    labels : np.ndarray
        Cluster labels for all picks.
    data : np.ndarray
        Pick data (time ± amplitude).
    locs : np.ndarray
        Pick station locations.
    phase_type : np.ndarray
        Pick phase types ('P', 'S', etc.).
    phase_weight : np.ndarray
        Pick weights (probabilities).
    pick_idx : np.ndarray
        Original indices of picks.
    pick_station_id : np.ndarray
        Station-phase identifiers.
    config : dict
        Configuration dictionary, including GMM/BGMM parameters and thresholds.
    timestamp0 : float
        Reference timestamp (epoch seconds) for normalization.
    vel : dict
        Velocities, e.g., {"p": vp, "s": vs}.
    method : str
        Association method: "GMM" or "BGMM".
    event_idx : int or multiprocessing.Value
        Counter for event indices (supports shared memory in multiprocessing).
    lock : multiprocessing.Lock, optional
        Lock for safely incrementing shared `event_idx` in parallel.

    Returns
    -------
    events : list of dict
        List of associated events, including time, magnitude, covariance, and location.
    assignment : list of tuples
        List of pick-to-event assignments (pick index, event index, probability).
    """
    print(".", end="")

    data_ = data[labels == k]
    locs_ = locs[labels == k]
    phase_type_ = phase_type[labels == k]
    phase_weight_ = phase_weight[labels == k]
    pick_idx_ = pick_idx[labels == k]
    pick_station_id_ = pick_station_id[labels == k]

    max_num_event = max(Counter(pick_station_id_).values()) * config["oversample_factor"]
    max_num_event = min(max_num_event, len(data_) // 3)

    if len(pick_idx_) < max(3, config["min_picks_per_eq"]):
        return [], []

    # ## initialization with [1,1,1] horizontal points and N time points
    centers_init = init_centers(config, data_, locs_, phase_type_, phase_weight_, max_num_event)

    ## run clustering
    if "covariance_prior" in config:
        covariance_prior_pre = config["covariance_prior"]
    else:
        # covariance_prior_pre = [5.0, 2.0]
        ## TODO: design a smark way to set covariance_prior
        weight = np.squeeze(phase_weight_)
        x_mean = np.average(locs_[:, 0], weights=weight)
        y_mean = np.average(locs_[:, 1], weights=weight)
        x_std = np.sqrt(np.average((locs_[:, 0] - x_mean) ** 2, weights=weight))
        y_std = np.sqrt(np.average((locs_[:, 1] - y_mean) ** 2, weights=weight))
        # x_std = np.std(locs_[:, 0])
        # y_std = np.std(locs_[:, 1])
        # t_std = np.std(data_[:, 0])
        ## option 1
        # scaler = max(np.sqrt(x_std**2 + y_std**2) / 6.0 , 0.1)
        ## option 2
        # scaler = max(np.sqrt(x_std**2 + y_std**2) / 6.0 / t_std, 0.1) * 10
        ## option 3
        # d, v = 50, 6.0
        # scaler = max((np.exp(np.sqrt(x_std**2 + y_std**2)/d) - 1)/(np.exp(1) - 1) * d / v / t_std, 0.2) * 10
        ## option 4
        rstd = np.sqrt(x_std**2 + y_std**2)
        # scaler = max(10.0, (rstd / 6.0) * (rstd / 60.0))  # 6.0 km/s, 60 km
        # scaler = max(1.0, (rstd / 6.0) * (rstd / 30.0))  # 6.0 km/s, 30 km
        a, b = 0.5, 15
        scaler = a + (b ** (rstd / 30) - 1) / (b - 1) * 4.0  # (0, a), (30, 4 + a)
        # print(f"rstd: {rstd}, scaler: {scaler}, max_num_event: {max_num_event}")
        if config["use_amplitude"]:
            # covariance_prior_pre = [time_range * 10.0, amp_range * 10.0]
            covariance_prior_pre = [scaler, scaler]
        else:
            # covariance_prior_pre = [time_range * 10.0]
            covariance_prior_pre = [scaler]
    # print(f"covariance_prior_pre: {covariance_prior_pre}")
    if config["use_amplitude"]:
        covariance_prior = np.array([[covariance_prior_pre[0], 0.0], [0.0, covariance_prior_pre[1]]])
    else:
        covariance_prior = np.array([[covariance_prior_pre[0]]])
        data_ = data_[:, 0:1]

    random_state = 42
    if method == "BGMM":
        gmm = BayesianGaussianMixture(
            n_components=max_num_event,
            # weight_concentration_prior_type="dirichlet_process",
            weight_concentration_prior=1.0 / max_num_event,
            # mean_precision_prior=mean_precision_prior,
            covariance_prior=covariance_prior,
            # init_params="random",
            # init_params="k-means++",
            # init_params="kmeans",
            init_params="centers",
            centers_init=centers_init.copy(),
            station_locs=locs_,
            phase_type=phase_type_,
            phase_weight=phase_weight_,
            vel=vel,
            eikonal=config["eikonal"],
            bounds=config["bfgs_bounds"],
            random_state=random_state,
        ).fit(data_)
    elif method == "GMM":
        gmm = GaussianMixture(
            n_components=max_num_event,
            # init_params="random",
            # init_params="k-means++",
            # init_params="kmeans",
            init_params="centers",
            centers_init=centers_init.copy(),
            station_locs=locs_,
            phase_type=phase_type_,
            phase_weight=phase_weight_,
            vel=vel,
            eikonal=config["eikonal"],
            bounds=config["bfgs_bounds"],
            # dummy_comp=True,
            # dummy_prob=1 / (1 * np.sqrt(2 * np.pi)) * np.exp(-1 / 2),
            # dummy_quantile=0.1,
            random_state=random_state,
        ).fit(data_)
    else:
        raise (f"Unknown method {method}; Should be 'BGMM' or 'GMM'")

    ## run prediction
    pred = gmm.predict(data_)
    prob = np.exp(gmm.score_samples(data_))
    prob_matrix = gmm.predict_proba(data_)
    prob_eq = prob_matrix.sum(axis=0)

    ## filtering
    events = []
    assignment = []

    # for i in range(len(centers_init)):
    for i in range(max_num_event):
        tmp_data = data_[pred == i]
        tmp_locs = locs_[pred == i]
        tmp_pick_station_id = pick_station_id_[pred == i]
        tmp_phase_type = phase_type_[pred == i]
        # tmp_phase_weight = phase_weight_[pred == i]
        if (len(tmp_data) == 0) or (len(tmp_data) < config["min_picks_per_eq"]):
            # if (len(tmp_data) == 0) or (np.sum(tmp_phase_weight) < config["min_picks_per_eq"]):
            continue
        # idx_filter = np.ones(len(tmp_data)).astype(bool)

        ## filter by time
        t_ = calc_time(
            gmm.centers_[i : i + 1, : len(config["dims"]) + 1],
            tmp_locs,
            tmp_phase_type,
            vel=vel,
            eikonal=config["eikonal"],
        )
        diff_t = np.abs(t_ - tmp_data[:, 0:1])
        idx_t = (diff_t < config["max_sigma11"]).squeeze(axis=1)
        idx_filter = idx_t
        if len(tmp_data[idx_filter]) < config["min_picks_per_eq"]:
            # if np.sum(tmp_phase_weight[idx_filter]) < config["min_picks_per_eq"]:
            continue

        ## filter multiple picks at the same station
        unique_sta_id = {}
        for j, k in enumerate(tmp_pick_station_id):
            if (k not in unique_sta_id) or (diff_t[j] < unique_sta_id[k][1]):
                unique_sta_id[k] = (j, diff_t[j])
        idx_s = np.zeros(len(idx_t)).astype(bool)  ## based on station
        for k in unique_sta_id:
            idx_s[unique_sta_id[k][0]] = True
        idx_filter = idx_filter & idx_s
        if len(tmp_data[idx_filter]) < config["min_picks_per_eq"]:
            # if np.sum(tmp_phase_weight[idx_filter]) < config["min_picks_per_eq"]:
            continue
        gmm.covariances_[i, 0, 0] = np.mean((diff_t[idx_t]) ** 2)

        ## filter by amplitude
        if config["use_amplitude"]:
            a_ = calc_amp(
                gmm.centers_[i : i + 1, len(config["dims"]) + 1 : len(config["dims"]) + 2],
                gmm.centers_[i : i + 1, : len(config["dims"]) + 1],
                tmp_locs,
            )
            diff_a = np.abs(a_ - tmp_data[:, 1:2])
            idx_a = (diff_a < config["max_sigma22"]).squeeze()
            idx_filter = idx_filter & idx_a
            if len(tmp_data[idx_filter]) < config["min_picks_per_eq"]:
                # if np.sum(tmp_phase_weight[idx_filter]) < config["min_picks_per_eq"]:
                continue

            if "max_sigma12" in config:
                idx_cov = np.abs(gmm.covariances_[i, 0, 1]) < config["max_sigma12"]
                idx_filter = idx_filter & idx_cov
                if len(tmp_data[idx_filter]) < config["min_picks_per_eq"]:
                    # if np.sum(tmp_phase_weight[idx_filter]) < config["min_picks_per_eq"]:
                    continue

            gmm.covariances_[i, 1, 1] = np.mean((diff_a[idx_a]) ** 2)

        if "min_p_picks_per_eq" in config:
            if len(tmp_data[idx_filter & (tmp_phase_type == "p")]) < config["min_p_picks_per_eq"]:
                # if np.sum(tmp_phase_weight[idx_filter & (tmp_phase_type == "p")]) < config["min_p_picks_per_eq"]:
                continue
        if "min_s_picks_per_eq" in config:
            if len(tmp_data[idx_filter & (tmp_phase_type == "s")]) < config["min_s_picks_per_eq"]:
                # if np.sum(tmp_phase_weight[idx_filter & (tmp_phase_type == "s")]) < config["min_s_picks_per_eq"]:
                continue
        if "min_stations" in config:
            if len(np.unique(tmp_locs[idx_filter], axis=0)) < config["min_stations"]:
                continue

        if lock is not None:
            with lock:
                if not isinstance(event_idx, int):
                    event_idx.value += 1
                    event_idx_value = event_idx.value
                else:
                    event_idx += 1
                    event_idx_value = event_idx
        else:
            if not isinstance(event_idx, int):
                event_idx.value += 1
                event_idx_value = event_idx.value
            else:
                event_idx += 1
                event_idx_value = event_idx

        event = {
            # "time": from_seconds(gmm.centers_[i, len(config["dims"])]),
            "time": datetime.utcfromtimestamp(gmm.centers_[i, len(config["dims"])] + timestamp0).isoformat(
                timespec="milliseconds"
            ),
            # "time(s)": gmm.centers_[i, len(config["dims"])],
            "magnitude": gmm.centers_[i, len(config["dims"]) + 1] if config["use_amplitude"] else 999,
            "sigma_time": np.sqrt(gmm.covariances_[i, 0, 0]),
            "sigma_amp": np.sqrt(gmm.covariances_[i, 1, 1]) if config["use_amplitude"] else 0,
            "cov_time_amp": gmm.covariances_[i, 0, 1] if config["use_amplitude"] else 0,
            "gamma_score": prob_eq[i],
            "num_picks": len(tmp_data[idx_filter]),
            "num_p_picks": len(tmp_data[idx_filter & (tmp_phase_type == "p")]),
            "num_s_picks": len(tmp_data[idx_filter & (tmp_phase_type == "s")]),
            "event_index": event_idx_value,
        }
        for j, k in enumerate(config["dims"]):  ## add location
            event[k] = gmm.centers_[i, j]
        events.append(event)

        for pi, pr in zip(pick_idx_[pred == i][idx_filter], prob):
            assignment.append((pi, event_idx_value, pr))

        if (event_idx_value + 1) % 100 == 0:
            print(f"\nAssociated {event_idx_value + 1} events")
    return events, assignment


def init_centers(config, data_, locs_, type_, weight_, max_num_event=1):
    """
    Initialize event centers for clustering based on pick times and station locations.

    This function selects initial guesses for event centers for GMM/BGMM fitting, 
    using the earliest picks (prioritizing P-phases) and adding small random perturbations 
    in spatial coordinates. Optionally initializes magnitudes if amplitude is used.

    Steps:
    1. Sort picks by time; separate P and S phases.
    2. Select up to `max_num_event` picks as initial centers, using P-phase first.
       If insufficient P-phases, fill with S-phases.
    3. Compute weighted mean and standard deviation of station coordinates (x, y).
    4. Add small random offsets to x, y to create diversity in initial centers.
    5. Initialize z (depth) as the midpoint of configured depth range.
    6. Combine x, y, z (optional) and time into centers array.
    7. If amplitude is used, add a column for initial magnitude (default 1.0).

    Parameters
    ----------
    config : dict
        Configuration dictionary; must include "dims" (list of coordinate names), "z(km)" range, and "use_amplitude".
    data_ : np.ndarray
        Pick times (and amplitudes if used) for the cluster.
    locs_ : np.ndarray
        Station coordinates for the picks.
    type_ : np.ndarray
        Pick phase types ('p' or 's').
    weight_ : np.ndarray
        Pick weights/probabilities.
    max_num_event : int, optional
        Maximum number of events to initialize at a station (default: 1).

    Returns
    -------
    centers_init : np.ndarray
        Initial event centers array, shape (num_events, num_dims + 1 [+1 if amplitude]).
    """
    # index = np.argsort(data_[:, 0])[:: max(len(data_) // max_num_event, 1)][:max_num_event]
    # use p first, then s
    index = np.argsort(data_[:, 0])
    p_index = index[type_ == "p"]
    s_index = index[type_ == "s"]
    if len(p_index) >= max_num_event:
        index = p_index[:: max(len(p_index) // max_num_event, 1)][:max_num_event]
    else:
        num = max_num_event - len(p_index)
        index = np.concatenate([p_index, s_index[:: max(len(s_index) // num, 1)][:num]])

    weight_ = weight_.squeeze()
    mu_x = np.average(locs_[:, 0], weights=weight_)
    sigma_x = np.sqrt(np.average((locs_[:, 0] - mu_x) ** 2, weights=weight_))
    mu_y = np.average(locs_[:, 1], weights=weight_)
    sigma_y = np.sqrt(np.average((locs_[:, 1] - mu_y) ** 2, weights=weight_))
    t_init = (
        data_[index, 0]
        # + np.random.uniform(low=-1, high=0, size=max_num_event)
        # * (np.std(locs_[:, 0]) + np.std(locs_[:, 1]))
        # / 2.0
        # / 6.0
    )
    x_init = locs_[index, 0] + np.random.uniform(low=-1, high=1, size=max_num_event) * sigma_x
    y_init = locs_[index, 1] + np.random.uniform(low=-1, high=1, size=max_num_event) * sigma_y
    z_init = (
        np.ones(max_num_event) * (config["z(km)"][0] + config["z(km)"][1]) / 2.0
        # + np.random.uniform(low=-1, high=1, size=max_num_event) * (config["z(km)"][1] - config["z(km)"][0]) / 6.0
    )

    if config["dims"] == ["x(km)", "y(km)", "z(km)"]:
        centers_init = np.vstack([x_init, y_init, z_init, t_init]).T
    elif config["dims"] == ["x(km)", "y(km)"]:
        centers_init = np.vstack([x_init, y_init, t_init]).T
    elif config["dims"] == ["x(km)"]:
        centers_init = np.vstack([x_init, t_init]).T
    else:
        raise (ValueError("Unsupported dims"))

    if config["use_amplitude"]:
        centers_init = np.hstack([centers_init, 1.0 * np.ones((len(centers_init), 1))])  # init magnitude to 1.0

    return centers_init
