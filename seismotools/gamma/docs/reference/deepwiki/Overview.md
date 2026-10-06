# Overview

> **Relevant source files**
> * [docs/README.md](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/README.md)
> * [gamma/utils.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py)
> * [tests/comparison/stations_ridgecrest.csv](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/tests/comparison/stations_ridgecrest.csv)

This document provides a comprehensive introduction to GaMMA (Gaussian Mixture Model Associator), its architecture, and core components. GaMMA is a Python package that uses statistical machine learning to associate seismic phase picks into earthquake events.

For installation instructions, see [Installation and Setup](/AI4EPS/GaMMA/2-installation-and-setup). For detailed API documentation, see [API Reference](/AI4EPS/GaMMA/4-api-reference). For practical usage examples, see [Examples and Tutorials](/AI4EPS/GaMMA/5-examples-and-tutorials).

## Purpose and Scope

GaMMA solves the seismic event association problem by clustering phase picks (P-wave and S-wave arrivals) from multiple seismic stations into coherent earthquake events. The system uses Gaussian Mixture Models (GMM) and Bayesian Gaussian Mixture Models (BGMM) to perform probabilistic clustering in a joint space-time domain, incorporating seismic physics through travel time calculations.

The package is designed to work with various seismic data sources including PhaseNet picks, SeisbBench datasets, and custom CSV formats. It provides both programmatic Python APIs and web service interfaces for integration into larger seismological workflows.

## System Architecture

### High-Level Components

```mermaid
flowchart TD

A["FastAPI Service<br>(app.py)"]
B["Python API<br>(gamma.utils.association)"]
C["Jupyter Notebooks<br>(docs/examples)"]
D["Data Conversion<br>(convert_picks_csv)"]
E["Optional DBSCAN<br>(hierarchical_dbscan_clustering)"]
F["GMM Association<br>(GaussianMixture)"]
G["BGMM Association<br>(BayesianGaussianMixture)"]
H["Seismic Operations<br>(calc_time, calc_loc)"]
I["Picks CSV<br>(station_id, phase_time, type, score)"]
J["Stations CSV<br>(station_id, lon, lat, elevation)"]
K["Configuration Dict<br>(velocities, bounds, parameters)"]
L["Events List<br>(time, location, magnitude)"]
M["Pick Assignments<br>(pick-to-event mapping)"]
N["Quality Metrics<br>(sigma_time, sigma_amp)"]

A --> D
B --> D
C --> D
H --> L
H --> M
H --> N
I --> D
J --> D
K --> D

subgraph subGraph3 ["Output Layer"]
    L
    M
    N
end

subgraph subGraph2 ["Data Layer"]
    I
    J
    K
end

subgraph subGraph1 ["Core Processing Pipeline"]
    D
    E
    F
    G
    H
    D --> E
    E --> F
    E --> G
    F --> H
    G --> H
end

subgraph subGraph0 ["User Interfaces"]
    A
    B
    C
end
```

**Sources:** [gamma/utils.py L155-L276](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L155-L276)

 [docs/README.md L1-L54](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/README.md#L1-L54)

 [app.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/app.py)

### Core Processing Workflow

The association workflow implements a multi-stage pipeline that transforms raw seismic picks into earthquake catalogs:

```mermaid
flowchart TD

A["convert_picks_csv()<br>Normalize timestamps<br>Apply coordinate projection"]
B["Data Validation<br>Filter invalid picks<br>Check minimum requirements"]
C["hierarchical_dbscan_clustering()<br>Group picks by space-time proximity<br>Adaptive epsilon scaling"]
D["BayesianGaussianMixture<br>Probabilistic clustering<br>Automatic component selection"]
E["GaussianMixture<br>Fixed component clustering<br>Manual component count"]
F["calc_time()<br>Travel time calculation<br>Eikonal solver integration"]
G["initialize_eikonal()<br>3D velocity model<br>Fast marching method"]
H["calc_loc()<br>Event location estimation<br>Magnitude calculation"]
I["Filter by time residuals<br>(max_sigma11 parameter)"]
J["Filter by amplitude residuals<br>(max_sigma22 parameter)"]
K["Station uniqueness check<br>Remove duplicate picks per station"]
L["Minimum pick requirements<br>(min_picks_per_eq, min_p_picks_per_eq)"]

B --> C
C --> D
C --> E
D --> F
E --> F
H --> I

subgraph subGraph4 ["Quality Control"]
    I
    J
    K
    L
    I --> J
    J --> K
    K --> L
end

subgraph subGraph3 ["Seismic Physics"]
    F
    G
    H
    F --> G
    G --> H
end

subgraph subGraph2 ["Association Methods"]
    D
    E
end

subgraph subGraph1 ["Pre-clustering (Optional)"]
    C
end

subgraph subGraph0 ["Input Processing"]
    A
    B
    A --> B
end
```

**Sources:** [gamma/utils.py L54-L86](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L54-L86)

 [gamma/utils.py L88-L152](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L88-L152)

 [gamma/utils.py L279-L532](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L279-L532)

 [gamma/seismic_ops.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py)

## Key Code Components

### Main Association Function

The primary entry point is the `association()` function in `gamma.utils`, which orchestrates the entire workflow:

| Component | Function | Purpose |
| --- | --- | --- |
| Data preprocessing | `convert_picks_csv()` | Convert input CSV data to internal format with coordinate transformations |
| Pre-clustering | `hierarchical_dbscan_clustering()` | Optional spatial-temporal clustering to improve performance |
| Association core | `associate()` | Core GMM/BGMM clustering with seismic physics constraints |
| Initialization | `init_centers()` | Smart initialization of cluster centers based on pick distribution |

**Sources:** [gamma/utils.py L155-L162](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L155-L162)

 [gamma/utils.py L279-L294](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L279-L294)

 [gamma/utils.py L605-L657](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L605-L657)

### Statistical Models

GaMMA implements two clustering approaches, both extending scikit-learn's mixture models with seismic-specific features:

```mermaid
flowchart TD

A["BaseMixture<br>(gamma._base.py)<br>EM algorithm foundation"]
B["GaussianMixture<br>(gamma._gaussian_mixture.py)<br>Fixed component count<br>Standard EM algorithm"]
C["BayesianGaussianMixture<br>(gamma._bayesian_mixture.py)<br>Automatic model selection<br>Variational inference"]
D["station_locs parameter<br>Spatial constraints"]
E["phase_type parameter<br>P/S wave differentiation"]
F["vel parameter<br>Velocity model integration"]
G["eikonal parameter<br>3D travel time calculation"]

A --> B
A --> C
B --> D
B --> E
B --> F
B --> G
C --> D
C --> E
C --> F
C --> G

subgraph subGraph2 ["Seismic Extensions"]
    D
    E
    F
    G
end

subgraph subGraph1 ["Mixture Model Implementations"]
    B
    C
end

subgraph subGraph0 ["Base Architecture"]
    A
end
```

**Sources:** [gamma/_base.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_base.py)

 [gamma/_gaussian_mixture.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_gaussian_mixture.py)

 [gamma/_bayesian_mixture.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/_bayesian_mixture.py)

### Seismic Operations Module

The `seismic_ops` module provides specialized functions for seismological calculations:

| Function | Purpose | Key Features |
| --- | --- | --- |
| `calc_time()` | Travel time calculation | Supports both 1D velocity models and 3D eikonal solver |
| `calc_loc()` | Event location estimation | Iterative least-squares with phase weighting |
| `calc_amp()` | Amplitude prediction | Distance-based magnitude estimation |
| `initialize_eikonal()` | 3D velocity model setup | Fast marching method for complex velocity structures |

**Sources:** [gamma/seismic_ops.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/seismic_ops.py)

## Configuration and Parameters

GaMMA uses a configuration dictionary to control association behavior. Key parameter categories include:

### Core Algorithm Parameters

* `method`: Choice between "GMM" and "BGMM"
* `vel`: P and S wave velocities (default: `{"p": 6.0, "s": 6.0/1.73}`)
* `dims`: Spatial dimensions to use (`["x(km)", "y(km)", "z(km)"]`)
* `use_amplitude`: Whether to include amplitude information in clustering

### Quality Control Filters

* `min_picks_per_eq`: Minimum picks required per event
* `max_sigma11`: Maximum time residual threshold
* `max_sigma22`: Maximum amplitude residual threshold
* `min_stations`: Minimum number of unique stations per event

### Performance Optimization

* `use_dbscan`: Enable hierarchical DBSCAN pre-clustering
* `dbscan_eps`: DBSCAN time epsilon parameter
* `ncpu`: Number of CPU cores for parallel processing
* `oversample_factor`: Controls initial number of mixture components

**Sources:** [gamma/utils.py L163-L198](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L163-L198)

 [docs/README.md L20-L37](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/README.md#L20-L37)

## Data Flow and Integration Points

### Input Data Formats

GaMMA accepts standardized CSV formats for both picks and station metadata:

**Picks CSV Format:**

* `station_id`: Station identifier
* `timestamp`: Pick time (ISO format)
* `type`: Phase type ("P" or "S")
* `prob`: Pick confidence score
* `amp`: Amplitude measurement (optional)

**Stations CSV Format:**

* `station_id`: Station identifier
* `longitude`, `latitude`: Station coordinates
* `elevation`: Station elevation in meters

**Sources:** [gamma/utils.py L54-L86](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L54-L86)

 [tests/comparison/stations_ridgecrest.csv L1-L60](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/tests/comparison/stations_ridgecrest.csv#L1-L60)

### Output Data Structure

The system returns structured results containing:

1. **Events List**: Array of event dictionaries with time, location, magnitude, and quality metrics
2. **Assignment List**: Tuples linking pick indices to event indices with association probabilities
3. **Quality Metrics**: Covariance matrices, sigma values, and confidence scores

**Sources:** [gamma/utils.py L507-L532](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/gamma/utils.py#L507-L532)

This architecture enables GaMMA to process large volumes of seismic data efficiently while maintaining high association accuracy through physics-informed clustering and robust quality control mechanisms.