# Seismic Event Association

> **Relevant source files**
> * [docs/README.md](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/README.md)
> * [gamma/utils.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py)
> * [tests/comparison/stations_ridgecrest.csv](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/tests/comparison/stations_ridgecrest.csv)

This document explains the fundamental concept of seismic event association, the computational challenges it presents, and how GaMMA (Gaussian Mixture Model Associator) solves this problem using probabilistic clustering techniques. For information about the specific Gaussian Mixture Model algorithms used, see [Gaussian Mixture Models](/AI4EPS/GaMMA/3.2-gaussian-mixture-models). For details about travel time calculations and seismic physics, see [Travel Time Calculation](/AI4EPS/GaMMA/3.3-travel-time-calculation).

## What is Seismic Event Association?

Seismic event association is the process of grouping individual phase picks (P-wave and S-wave arrivals detected at seismic stations) that originate from the same earthquake event. When an earthquake occurs, it generates seismic waves that travel through the Earth and are recorded by multiple seismic stations across a network. Each station may detect both P-wave and S-wave arrivals, creating a collection of individual "picks" that must be correctly grouped to identify and locate the underlying earthquake events.

```mermaid
flowchart TD

E["Earthquake<br>Origin"]
P["P-waves<br>(faster)"]
S["S-waves<br>(slower)"]
S1["Station 1<br>P-pick: t1_p<br>S-pick: t1_s"]
S2["Station 2<br>P-pick: t2_p<br>S-pick: t2_s"]
S3["Station 3<br>P-pick: t3_p<br>S-pick: t3_s"]
SN["Station N<br>P-pick: tn_p<br>S-pick: tn_s"]
Mixed["Mixed Pick Stream:<br>t1_p, t2_p, t1_s, t3_p,<br>t2_s, t3_s, tn_p, tn_s"]
Question["Which picks belong<br>to the same event?"]

E --> P
E --> S
P --> S1
P --> S2
P --> S3
P --> SN
S --> S1
S --> S2
S --> S3
S --> SN
S1 --> Mixed
S2 --> Mixed
S3 --> Mixed
SN --> Mixed

subgraph subGraph3 ["Association Challenge"]
    Mixed
    Question
    Mixed --> Question
end

subgraph subGraph2 ["Station Network"]
    S1
    S2
    S3
    SN
end

subgraph subGraph1 ["Seismic Wave Propagation"]
    P
    S
end

subgraph subGraph0 ["Single Earthquake Event"]
    E
end
```

Sources: [gamma/utils.py L155-L276](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L155-L276)

 [docs/README.md L13-L16](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/README.md#L13-L16)

## The Association Problem

The association problem becomes complex when multiple earthquakes occur within overlapping time windows, creating ambiguity about which picks belong to which events. Real seismic networks may record hundreds or thousands of picks per day, and simple time-based grouping is insufficient because:

| Challenge | Description | Example |
| --- | --- | --- |
| **Overlapping Events** | Multiple earthquakes occur close in time | Two events 10 seconds apart may have overlapping S-wave arrivals |
| **Distance Variations** | Stations at different distances record the same event at different times | P-wave from distant event may arrive after S-wave from nearby event |
| **Network Geometry** | Irregular station spacing creates complex arrival patterns | Dense urban network vs. sparse regional network |
| **False Picks** | Noise and processing artifacts create spurious detections | Cultural noise, wind, processing errors |
| **Missing Picks** | Not all stations detect every event | Weak signals, station outages, directivity effects |

```mermaid
flowchart TD

Picks["Seismic Picks<br>station_id<br>phase_time<br>phase_type<br>phase_score"]
Issues["• Mixed event signatures<br>• Variable quality picks<br>• Incomplete detection<br>• Noise contamination"]
Constraints["• Physical consistency<br>• Travel time constraints<br>• Station geometry<br>• Phase relationships"]
Goals["• Accurate event detection<br>• Precise locations<br>• Quality assessment<br>• Computational efficiency"]
Events["Event Catalog<br>time, location<br>magnitude, quality"]
Assignments["Pick-Event Mapping<br>pick_id → event_id<br>association probability"]

Issues --> Constraints
Goals --> Events
Goals --> Assignments

subgraph subGraph2 ["Output Requirements"]
    Events
    Assignments
end

subgraph subGraph1 ["Association Requirements"]
    Constraints
    Goals
    Constraints --> Goals
end

subgraph subGraph0 ["Input Data Challenges"]
    Picks
    Issues
    Picks --> Issues
end
```

Sources: [gamma/utils.py L54-L86](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L54-L86)

 [docs/README.md L20-L38](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/README.md#L20-L38)

## GaMMA's Solution Approach

GaMMA solves the association problem using a probabilistic approach based on Gaussian Mixture Models (GMM), treating each earthquake as a cluster in a multidimensional space of time, location, and optionally amplitude. The key insight is that picks from the same event should cluster together when projected into a space that accounts for seismic wave travel times.

### Core Philosophy

GaMMA models each earthquake event as a Gaussian distribution in the joint space of:

* **Time dimension**: Event origin time
* **Spatial dimensions**: Event location (x, y, z coordinates)
* **Amplitude dimension**: Event magnitude (optional)

The association process finds the optimal clustering by maximizing the likelihood that observed picks originated from the hypothesized earthquake events, while incorporating seismic physics through travel time calculations.

```mermaid
flowchart TD

GMM["Gaussian Mixture Model<br>Each event = Gaussian cluster"]
Physics["Seismic Physics<br>Travel time constraints<br>Velocity models"]
Bayes["Bayesian Inference<br>Automatic model selection<br>Uncertainty quantification"]
EM["Expectation-Maximization<br>Iterative optimization<br>BayesianGaussianMixture<br>GaussianMixture"]
TravelTime["calc_time()<br>Eikonal solver<br>1D/3D velocity models"]
Filtering["Quality Filtering<br>min_picks_per_eq<br>max_sigma11/max_sigma22"]
BGMM["BayesianGaussianMixture<br>Automatic component selection"]
DBSCAN["Optional DBSCAN<br>Pre-clustering speedup<br>hierarchical_dbscan_clustering()"]
Parallel["Multiprocessing<br>Parallel cluster processing"]

GMM --> EM
Physics --> TravelTime
Bayes --> BGMM
EM --> BGMM

subgraph Implementation ["Implementation"]
    BGMM
    DBSCAN
    Parallel
    BGMM --> Parallel
    DBSCAN --> Parallel
end

subgraph subGraph1 ["GaMMA Core Algorithm"]
    EM
    TravelTime
    Filtering
    TravelTime --> EM
    Filtering --> EM
end

subgraph subGraph0 ["Probabilistic Framework"]
    GMM
    Physics
    Bayes
end
```

Sources: [gamma/_bayesian_mixture.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_bayesian_mixture.py)

 [gamma/_gaussian_mixture.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_gaussian_mixture.py)

 [gamma/utils.py L360-L401](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L360-L401)

## Core Workflow

The GaMMA association workflow processes seismic picks through several stages, from data preprocessing to final event output. The main entry point is the `association()` function in `gamma.utils`.

```mermaid
flowchart TD

PicksCSV["picks.csv<br>station_id, timestamp<br>phase_type, prob, amp"]
StationsCSV["stations.csv<br>station_id, longitude<br>latitude, elevation"]
Config["config dict<br>vel, bounds, dims<br>algorithm parameters"]
ConvertPicks["convert_picks_csv()<br>Timestamp normalization<br>Coordinate projection<br>Amplitude scaling"]
ValidateData["Data validation<br>Remove NaN locations<br>Check minimum picks"]
DBSCANCheck["use_dbscan?"]
HierarchicalDBSCAN["hierarchical_dbscan_clustering()<br>Time-space clustering<br>eps, min_samples"]
NoCluster["Single cluster<br>labels = [0, 0, ...]"]
ClusterLoop["For each cluster<br>Distribute across CPUs<br>associate() function"]
InitCenters["init_centers()<br>Smart initialization<br>P-picks preferred"]
ChooseMethod["method == 'BGMM'?"]
BGMM["BayesianGaussianMixture<br>Automatic model selection<br>Dirichlet process"]
GMM["GaussianMixture<br>Fixed components<br>Standard EM"]
FitModel["fit(data_)<br>EM algorithm convergence"]
Prediction["predict(data_)<br>Pick assignments<br>predict_proba()"]
TravelTimeCheck["calc_time()<br>Physical validation<br>max_sigma11 filter"]
QualityFilter["Quality filtering<br>min_picks_per_eq<br>Station uniqueness"]
EventOutput["Event dictionary<br>time, location, magnitude<br>sigma_time, sigma_amp"]

PicksCSV --> ConvertPicks
StationsCSV --> ConvertPicks
Config --> ConvertPicks
ValidateData --> DBSCANCheck
HierarchicalDBSCAN --> ClusterLoop
NoCluster --> ClusterLoop
InitCenters --> ChooseMethod
FitModel --> Prediction

subgraph subGraph5 ["Event Generation"]
    Prediction
    TravelTimeCheck
    QualityFilter
    EventOutput
    Prediction --> TravelTimeCheck
    TravelTimeCheck --> QualityFilter
    QualityFilter --> EventOutput
end

subgraph subGraph4 ["GMM Association"]
    ChooseMethod
    BGMM
    GMM
    FitModel
    ChooseMethod --> BGMM
    ChooseMethod --> GMM
    BGMM --> FitModel
    GMM --> FitModel
end

subgraph subGraph3 ["Parallel Processing"]
    ClusterLoop
    InitCenters
    ClusterLoop --> InitCenters
end

subgraph subGraph2 ["Optional Pre-clustering"]
    DBSCANCheck
    HierarchicalDBSCAN
    NoCluster
    DBSCANCheck --> HierarchicalDBSCAN
    DBSCANCheck --> NoCluster
end

subgraph Preprocessing ["Preprocessing"]
    ConvertPicks
    ValidateData
    ConvertPicks --> ValidateData
end

subgraph subGraph0 ["Data Input"]
    PicksCSV
    StationsCSV
    Config
end
```

Sources: [gamma/utils.py L155-L276](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L155-L276)

 [gamma/utils.py L279-L532](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L279-L532)

## Key Components and Functions

### Data Processing Pipeline

The association process begins with data conversion and validation through several key functions:

| Function | Purpose | Key Operations |
| --- | --- | --- |
| `convert_picks_csv()` | Convert input data to internal format | Timestamp normalization, coordinate projection, amplitude scaling |
| `estimate_eps()` | Calculate DBSCAN parameters | Station spacing analysis, velocity-based time windows |
| `hierarchical_dbscan_clustering()` | Pre-cluster picks by time-space proximity | Iterative DBSCAN with adaptive parameters |
| `init_centers()` | Initialize GMM cluster centers | P-pick preference, spatial weighting |

```mermaid
flowchart TD

Association["association()<br>Main orchestrator<br>gamma/utils.py:155"]
Associate["associate()<br>Single cluster processing<br>gamma/utils.py:279"]
ConvertPicks["convert_picks_csv()<br>Data preprocessing<br>gamma/utils.py:54"]
InitCenters["init_centers()<br>Smart initialization<br>gamma/utils.py:605"]
DBSCAN["hierarchical_dbscan_clustering()<br>Pre-clustering<br>gamma/utils.py:88"]
BGMM["BayesianGaussianMixture<br>Probabilistic clustering<br>gamma/_bayesian_mixture.py"]
GMM["GaussianMixture<br>Standard clustering<br>gamma/_gaussian_mixture.py"]
CalcTime["calc_time()<br>Travel time calculation<br>gamma/seismic_ops.py"]
CalcAmp["calc_amp()<br>Amplitude estimation<br>gamma/seismic_ops.py"]
Eikonal["initialize_eikonal()<br>Velocity model setup<br>gamma/seismic_ops.py"]

Associate --> BGMM
Associate --> GMM
DBSCAN --> Associate
BGMM --> CalcTime
GMM --> CalcTime
Associate --> CalcAmp

subgraph subGraph2 ["Seismic Operations"]
    CalcTime
    CalcAmp
    Eikonal
    CalcTime --> Eikonal
end

subgraph subGraph1 ["Clustering Components"]
    DBSCAN
    BGMM
    GMM
end

subgraph subGraph0 ["Core Functions"]
    Association
    Associate
    ConvertPicks
    InitCenters
    Association --> Associate
    Association --> ConvertPicks
    Associate --> InitCenters
end
```

Sources: [gamma/utils.py L54-L86](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L54-L86)

 [gamma/utils.py L88-L153](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L88-L153)

 [gamma/utils.py L605-L657](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L605-L657)

### Quality Control and Filtering

GaMMA implements multiple layers of quality control to ensure reliable event detection:

```mermaid
flowchart TD

MinPicks["min_picks_per_eq<br>Minimum pick count<br>Default: varies by config"]
DataQuality["Remove NaN coordinates<br>Validate timestamps<br>Check amplitude values"]
TravelTimeFilter["max_sigma11<br>Travel time residual<br>calc_time() validation"]
AmplitudeFilter["max_sigma22<br>Amplitude residual<br>calc_amp() validation"]
CovarFilter["max_sigma12<br>Cross-correlation limit<br>Covariance constraint"]
UniqueStations["Station uniqueness<br>Best pick per station<br>Minimum time residual"]
MinStations["min_stations<br>Minimum station count<br>Network geometry"]
PhaseBalance["min_p_picks_per_eq<br>min_s_picks_per_eq<br>Phase type requirements"]
ProbThreshold["Probability threshold<br>predict_proba() scores<br>gamma_score metric"]
CovarianceUpdate["Covariance refinement<br>Residual-based update<br>Iterative improvement"]

MinPicks --> TravelTimeFilter
DataQuality --> TravelTimeFilter
CovarFilter --> UniqueStations
PhaseBalance --> ProbThreshold

subgraph subGraph3 ["Statistical Filtering"]
    ProbThreshold
    CovarianceUpdate
    ProbThreshold --> CovarianceUpdate
end

subgraph subGraph2 ["Station-Based Filtering"]
    UniqueStations
    MinStations
    PhaseBalance
    UniqueStations --> MinStations
    MinStations --> PhaseBalance
end

subgraph subGraph1 ["Physics-Based Filtering"]
    TravelTimeFilter
    AmplitudeFilter
    CovarFilter
    TravelTimeFilter --> AmplitudeFilter
    AmplitudeFilter --> CovarFilter
end

subgraph subGraph0 ["Input Validation"]
    MinPicks
    DataQuality
end
```

Sources: [gamma/utils.py L422-L489](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L422-L489)

 [gamma/utils.py L427-L454](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L427-L454)

 [gamma/utils.py L456-L476](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L456-L476)

The association process outputs two main data structures: a list of events with their properties (time, location, magnitude, uncertainties) and a list of assignments mapping each pick to its most likely event. This probabilistic approach allows GaMMA to handle ambiguous cases while providing uncertainty estimates for downstream analysis.