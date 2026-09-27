# Advanced Topics

> **Relevant source files**
> * [docs/example_phasenet_ransac.ipynb](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb)
> * [tests/comparison/real/run.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/tests/comparison/real/run.py)

This document covers advanced usage patterns and specialized applications of GaMMA, including RANSAC integration for robust event location, custom velocity model implementation, and integration with other seismological software tools. This material assumes familiarity with basic GaMMA concepts and API usage.

For basic GaMMA usage and API reference, see [Core Association Functions](/AI4EPS/GaMMA/4.1-core-association-functions). For standard examples and tutorials, see [Examples and Tutorials](/AI4EPS/GaMMA/5-examples-and-tutorials).

## RANSAC Integration

GaMMA can be combined with RANSAC (Random Sample Consensus) algorithms to improve the robustness of earthquake event location, particularly when dealing with noisy pick data or complex velocity structures.

The integration leverages GaMMA's probabilistic association capabilities alongside RANSAC's outlier detection to iteratively refine event locations:

```mermaid
flowchart TD

A["PhaseNet Picks"]
B["gamma.utils.association()"]
C["Initial Event Association"]
D["RANSAC Location Refinement"]
E["Outlier Pick Detection"]
F["Consensus Reached?"]
G["Update Pick Weights"]
H["Final Event Catalog"]
I["gamma.seismic_ops.calc_loc()"]
J["Custom Velocity Model"]

subgraph subGraph0 ["RANSAC-Enhanced GaMMA Pipeline"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    J
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> B
    F --> H
    I --> D
    J --> I
end
```

**RANSAC Parameter Configuration:**

```mermaid
flowchart TD

A["config['ransac_params']"]
B["'min_picks_per_eq': 5"]
C["'max_sigma11': 15.0"]
D["'max_sigma22': 3.0"]
E["'max_sigma12': 3.0"]
F["'consensus_threshold': 0.8"]

subgraph subGraph0 ["RANSAC Configuration"]
    A
    B
    C
    D
    E
    F
    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
end
```

Sources: [docs/example_phasenet_ransac.ipynb L332-L338](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb#L332-L338)

## Custom Velocity Models

GaMMA supports sophisticated velocity models through its eikonal solver implementation, enabling accurate travel time calculations for complex geological structures.

### Velocity Model Configuration

The eikonal solver can handle both 1D layered velocity models and more complex 3D structures:

```mermaid
flowchart TD

A["Velocity Model Input"]
B["Model Type"]
C["config['eikonal']['vel']"]
D["Custom Implementation"]
E["'z': [0.0, 5.5, 16.0, 32.0]"]
F["'p': [5.5, 5.5, 6.7, 7.8]"]
G["'s': [3.2, 3.2, 3.9, 4.5]"]
H["gamma.seismic_ops EikonalSolver"]
I["Travel Time Calculation"]
J["gamma.seismic_ops.calc_loc()"]

subgraph subGraph0 ["Velocity Model Types"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    J
    A --> B
    B --> C
    B --> D
    C --> E
    C --> F
    C --> G
    D --> H
    H --> I
    I --> J
end
```

**Ridgecrest Velocity Model Example:**

```css
# 1D layered velocity model for Ridgecrest region
zz = [0.0, 5.5, 16.0, 32.0]  # Depth layers (km)
vp = [5.5, 5.5, 6.7, 7.8]    # P-wave velocities (km/s)
vs = [v / 1.73 for v in vp]   # S-wave velocities (km/s)
vel = {"z": zz, "p": vp, "s": vs}
config["eikonal"] = {
    "vel": vel, 
    "h": 1.0,  # Grid spacing
    "xlim": config["x(km)"], 
    "ylim": config["y(km)"], 
    "zlim": config["z(km)"]
}
```

**IASP91 Global Model Example:**

```css
# Global velocity model (e.g., for teleseismic events)
velocity_model = pd.read_csv("iasp91.csv", names=["zz", "rho", "vp", "vs"])
vel = {
    "z": velocity_model["zz"].values, 
    "p": velocity_model["vp"].values, 
    "s": velocity_model["vs"].values
}
```

Sources: [docs/example_phasenet_ransac.ipynb L308-L325](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb#L308-L325)

 [docs/example_phasenet_ransac.ipynb L317-L322](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb#L317-L322)

### Eikonal Solver Integration

The eikonal solver provides accurate travel times for complex velocity structures:

```mermaid
flowchart TD

A["config['eikonal']"]
B["gamma.seismic_ops"]
C["EikonalSolver.solve()"]
D["Travel Time Grid"]
E["calc_loc() Function"]
F["Event Location"]
G["Velocity Model"]
H["Station Coordinates"]
I["Source Grid"]

subgraph subGraph0 ["Eikonal Solver Workflow"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    G --> A
    H --> B
    I --> C
end
```

Sources: [docs/example_phasenet_ransac.ipynb L316-L322](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb#L316-L322)

## Advanced Configuration Parameters

GaMMA provides extensive configuration options for fine-tuning association performance and quality control.

### Association Method Selection

```mermaid
flowchart TD

A["config['method']"]
B["Algorithm Choice"]
C["BayesianGaussianMixture"]
D["GaussianMixture"]
E["config['oversample_factor'] = 5"]
F["config['oversample_factor'] = 1"]
G["gamma._bayesian_mixture"]
H["gamma._gaussian_mixture"]

subgraph subGraph0 ["Association Methods"]
    A
    B
    C
    D
    E
    F
    G
    H
    A --> B
    B --> C
    B --> D
    C --> E
    D --> F
    C --> G
    D --> H
end
```

### DBSCAN Pre-clustering

```mermaid
flowchart TD

A["config['use_dbscan'] = True"]
B["sklearn.cluster.DBSCAN"]
C["eps=config['dbscan_eps']"]
D["min_samples=config['dbscan_min_samples']"]
E["estimate_eps()"]
F["Station Density"]

subgraph subGraph0 ["DBSCAN Configuration"]
    A
    B
    C
    D
    E
    F
    A --> B
    B --> C
    B --> D
    E --> C
    F --> E
end
```

### Quality Control Parameters

```mermaid
flowchart TD

A["Event Filtering"]
B["config['min_picks_per_eq']: 5"]
C["config['min_p_picks_per_eq']: 0"]
D["config['min_s_picks_per_eq']: 0"]
E["Uncertainty Limits"]
F["config['max_sigma11']: 15.0"]
G["config['max_sigma22']: 3.0"]
H["config['max_sigma12']: 3.0"]
I["Amplitude Usage"]
J["config['use_amplitude']: True"]

subgraph subGraph0 ["Quality Control Settings"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    J
    A --> B
    A --> C
    A --> D
    E --> F
    E --> G
    E --> H
    I --> J
end
```

Sources: [docs/example_phasenet_ransac.ipynb L270-L338](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb#L270-L338)

## Integration with PhaseNet

GaMMA integrates seamlessly with PhaseNet deep learning picks, providing a complete workflow from raw seismic data to final event catalogs.

### PhaseNet Pick Processing

```mermaid
flowchart TD

A["PhaseNet Output"]
B["picks.csv"]
C["pd.read_csv()"]
D["Column Mapping"]
E["'station_id' → 'id'"]
F["'phase_time' → 'timestamp'"]
G["'phase_type' → 'type'"]
H["'phase_score' → 'prob'"]
I["'phase_amplitude' → 'amp'"]
J["stations.json"]
K["Station Coordinates"]
L["Coordinate Projection"]
M["proj(longitude, latitude)"]
N["x(km), y(km), z(km)"]
O["gamma.utils.association()"]

subgraph subGraph0 ["PhaseNet Integration Workflow"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    J
    K
    L
    M
    N
    O
    A --> B
    B --> C
    C --> D
    D --> E
    D --> F
    D --> G
    D --> H
    D --> I
    J --> K
    K --> L
    L --> M
    M --> N
    E --> O
    N --> O
end
```

### Data Format Requirements

| Column | Description | Example |
| --- | --- | --- |
| `id` | Station identifier | "BG.AL1..DP" |
| `timestamp` | Pick time | "2023-01-01 18:35:33.390" |
| `prob` | Detection probability | 0.349 |
| `type` | Phase type | "P" or "S" |
| `amp` | Phase amplitude | 0.000007 |

Sources: [docs/example_phasenet_ransac.ipynb L232-L242](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb#L232-L242)

## Performance Optimization

### Parallel Processing Configuration

```mermaid
flowchart TD

A["config['ncpu'] = 32"]
B["Multiprocessing Pool"]
C["Association Tasks"]
D["Location Calculations"]
E["CPU Core Count"]
F["Memory Constraints"]
G["Batch Size Adjustment"]

subgraph subGraph0 ["Parallel Processing Setup"]
    A
    B
    C
    D
    E
    F
    G
    A --> B
    B --> C
    B --> D
    E --> A
    F --> G
end
```

### Memory Management

```mermaid
flowchart TD

A["Large Dataset"]
B["Batch Processing"]
C["config['batch_size']"]
D["Pick Filtering"]
E["config['use_amplitude']"]
F["picks[picks['amp'] != -1]"]
G["Spatial Bounds"]
H["Station Selection"]
I["picks[picks['id'].isin(stations['id'])]"]

subgraph subGraph0 ["Memory Optimization"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    A --> B
    B --> C
    D --> E
    E --> F
    G --> H
    H --> I
end
```

Sources: [docs/example_phasenet_ransac.ipynb L329-L342](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb#L329-L342)

## Integration with Other Seismological Tools

### REAL Algorithm Comparison

GaMMA can be benchmarked against other association algorithms like REAL:

```mermaid
flowchart TD

A["Seismic Picks"]
B["GaMMA Association"]
C["REAL Algorithm"]
D["EikoGAMMA"]
E["Performance Comparison"]
F["tests.comparison notebooks"]
G["Statistical Analysis"]
H["Algorithm Selection"]

subgraph subGraph0 ["Multi-Algorithm Workflow"]
    A
    B
    C
    D
    E
    F
    G
    H
    A --> B
    A --> C
    A --> D
    B --> E
    C --> E
    D --> E
    E --> F
    F --> G
    G --> H
end
```

### External Tool Integration

```mermaid
flowchart TD

A["SeisbBench"]
B["Standardized Datasets"]
C["gamma.utils.association()"]
D["ObsPy"]
E["Waveform Processing"]
F["Pick Extraction"]
G["PyTorch Models"]
H["Deep Learning Picks"]
I["Catalog Output"]
J["ObsPy Catalog Format"]

subgraph subGraph0 ["Tool Integration Points"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    J
    A --> B
    B --> C
    D --> E
    E --> F
    F --> C
    G --> H
    H --> C
    C --> I
    I --> J
end
```

Sources: [docs/example_phasenet_ransac.ipynb L1-L67](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb#L1-L67)

## Advanced Error Analysis

### Uncertainty Quantification

The uncertainty parameters `max_sigma11`, `max_sigma22`, and `max_sigma12` control the covariance matrix bounds for event location:

* `max_sigma11`: Maximum time uncertainty (seconds)
* `max_sigma22`: Maximum amplitude uncertainty (log10(m/s))
* `max_sigma12`: Maximum covariance between time and amplitude

### Location Quality Assessment

```mermaid
flowchart TD

A["Event Location"]
B["RMS Residual"]
C["Azimuthal Gap"]
D["Station Distribution"]
E["Pick Quality"]
F["Phase Score Threshold"]
G["Signal-to-Noise Ratio"]
H["Association Quality"]
I["Number of Picks"]
J["P/S Phase Balance"]

subgraph subGraph0 ["Quality Assessment Metrics"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    J
    A --> B
    A --> C
    A --> D
    E --> F
    E --> G
    H --> I
    H --> J
end
```

This advanced configuration enables robust earthquake detection and location across diverse seismological applications, from local monitoring networks to regional catalog construction.

Sources: [docs/example_phasenet_ransac.ipynb L332-L338](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet_ransac.ipynb#L332-L338)