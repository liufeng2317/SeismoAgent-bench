# Examples and Tutorials

> **Relevant source files**
> * [docs/example_phasenet.ipynb](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb)

This page provides practical examples and tutorials demonstrating how to use GaMMA for seismic event association with real-world data. The examples cover different data sources, configuration patterns, and integration scenarios commonly encountered in seismological applications.

For detailed API documentation of the functions used in these examples, see [API Reference](/AI4EPS/GaMMA/4-api-reference). For conceptual background on the algorithms, see [Core Concepts](/AI4EPS/GaMMA/3-core-concepts).

## Overview

GaMMA includes several comprehensive tutorials that demonstrate different aspects of the system:

* **PhaseNet Integration**: Complete workflow using machine learning-generated picks from PhaseNet
* **Synthetic Data Processing**: Examples with controlled synthetic datasets for testing and validation
* **Multi-format Data Support**: Integration with SeisbBench and other seismic data formats
* **Web Service Usage**: Accessing GaMMA functionality through the FastAPI interface

The examples are designed to be self-contained and can be run directly, with demo data provided for immediate experimentation.

## Tutorial Data Flow

The following diagram shows the typical data processing workflow used across all GaMMA tutorials:

```mermaid
flowchart TD

A["CSV_Files"]
B["convert_picks_csv()"]
C["Station_Metadata"]
D["Config_Dict"]
E["proj()"]
F["DBSCAN_clustering"]
G["association()"]
H["Events_DataFrame"]
I["Assignments_DataFrame"]
J["to_csv()"]
K["to_csv()"]
L["Velocity_Models"]
M["eikonal_solver"]

A --> B
C --> B
D --> B
B --> E
E --> F
F --> G
G --> H
G --> I
H --> J
I --> K
L --> M
M --> G
```

**Sources:** [docs/example_phasenet.ipynb L195-L325](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L195-L325)

## Configuration Patterns

All tutorials follow a consistent configuration pattern using Python dictionaries with region-specific parameters:

```mermaid
flowchart TD

A["region"]
B["Region_Type"]
C["Ridgecrest_Config"]
D["Chile_Config"]
E["config['use_dbscan'] = True"]
F["config['use_amplitude'] = True"]
G["config['z(km)'] = (0, 20)"]
H["config['use_amplitude'] = False"]
I["config['z(km)'] = (0, 250)"]
J["iasp91_velocity_model"]
K["association()"]

A --> B
B --> C
B --> D
C --> E
C --> F
C --> G
D --> H
D --> I
D --> J
E --> K
F --> K
G --> K
H --> K
I --> K
J --> K
```

**Sources:** [docs/example_phasenet.ipynb L234-L305](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L234-L305)

## Key Tutorial Components

### Data Input Processing

The tutorials demonstrate standardized data input handling through specific function calls and data transformations:

| Component | Function/Method | Purpose |
| --- | --- | --- |
| Pick Loading | `pd.read_csv(picks_csv, parse_dates=["phase_time"])` | Load timestamped seismic picks |
| Station Loading | `pd.read_csv(station_csv)` | Load station metadata with coordinates |
| Column Mapping | `picks.rename(columns={...})` | Standardize column names |
| Coordinate Projection | `Proj(f"+proj=aeqd +lon_0={x0} +lat_0={y0} +units=km")` | Convert to Cartesian coordinates |

**Sources:** [docs/example_phasenet.ipynb L195-L231](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L195-L231)

### Algorithm Configuration

The tutorials show systematic configuration of key algorithm parameters:

```mermaid
flowchart TD

A["Algorithm_Config"]
B["config['method'] = 'BGMM'"]
C["config['use_dbscan'] = True"]
D["config['use_amplitude'] = True"]
E["BayesianGaussianMixture"]
F["dbscan_eps = 15"]
G["dbscan_min_samples = 3"]
H["Amplitude_Features"]
I["association()"]
J["Events_Output"]
K["Assignments_Output"]

A --> B
A --> C
A --> D
B --> E
C --> F
C --> G
D --> H
E --> I
F --> I
G --> I
H --> I
I --> J
I --> K
```

**Sources:** [docs/example_phasenet.ipynb L234-L243](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L234-L243)

 [docs/example_phasenet.ipynb L266-L271](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L266-L271)

### Velocity Model Integration

Tutorials demonstrate two approaches for incorporating velocity models:

```mermaid
flowchart TD

A["Velocity_Models"]
B["Model_Type"]
C["config['vel'] = {'p': 6.0, 's': 3.43}"]
D["config['eikonal']"]
E["association()"]
F["Velocity_Arrays"]
G["eikonal_solver"]
H["vel = {'z': zz, 'p': vp, 's': vs}"]
I["h = 1.0"]
J["Grid_Bounds"]

A --> B
B --> C
B --> D
C --> E
D --> F
F --> G
G --> E
F --> H
F --> I
F --> J
```

**Sources:** [docs/example_phasenet.ipynb L274-L303](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L274-L303)

## Result Processing and Validation

The tutorials include comprehensive result processing workflows:

### Output Generation

The examples show systematic output file generation with specific naming conventions and formats:

| Output Type | Filename | Content | Format Function |
| --- | --- | --- | --- |
| Events | `gamma_events.csv` | Event locations, times, magnitudes | `to_csv(float_format="%.3f")` |
| Assignments | `gamma_picks.csv` | Pick-to-event associations | `to_csv(date_format="%Y-%m-%dT%H:%M:%S.%f")` |
| Visualizations | `figures/*.png` | Quality assessment plots | `plt.savefig(dpi=300)` |

**Sources:** [docs/example_phasenet.ipynb L420-L441](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L420-L441)

### Quality Control Filtering

Advanced tutorials demonstrate optional quality control through nearest station analysis:

```mermaid
flowchart TD

A["Raw_Events"]
B["NearestNeighbors()"]
C["Station_Locations"]
D["kneighbors()"]
E["Nearest_Stations_Per_Event"]
F["station_coverage_ratio"]
G["Ratio > MIN_THRESHOLD"]
H["Filtered_Events"]
I["Rejected_Events"]
J["gamma_events.csv"]

A --> B
C --> B
B --> D
D --> E
E --> F
F --> G
G --> H
G --> I
H --> J
```

**Sources:** [docs/example_phasenet.ipynb L465-L503](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L465-L503)

## Visualization Framework

All tutorials include standardized visualization components using matplotlib with specific styling patterns:

### Plot Types Generated

The tutorial framework automatically generates several analysis plots:

1. **Temporal Distribution**: `earthquake_number.png` - Event frequency over time
2. **Spatial Distribution**: `earthquake_location.png` - Geographic and depth distribution
3. **Magnitude Analysis**: `earthquake_magnitude_frequency.png` - Magnitude-frequency relationship
4. **Quality Metrics**: `covariance.png` - Association uncertainty measures

**Sources:** [docs/example_phasenet.ipynb L566-L941](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L566-L941)

### Comparison Framework

The tutorials support automatic comparison with reference catalogs when available:

```mermaid
flowchart TD

A["GaMMA_Results"]
C["Visualization"]
B["Standard_Catalog"]
D["Combined_Histograms"]
E["Location_Comparisons"]
F["Magnitude_Comparisons"]
G["plt.hist() for both datasets"]
H["plt.plot() with alpha transparency"]
I["statistical comparison metrics"]

A --> C
B --> C
C --> D
C --> E
C --> F
D --> G
E --> H
F --> I
```

**Sources:** [docs/example_phasenet.ipynb L553-L585](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_phasenet.ipynb#L553-L585)