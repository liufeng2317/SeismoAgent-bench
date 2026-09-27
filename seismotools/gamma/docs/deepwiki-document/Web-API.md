# Web API

> **Relevant source files**
> * [app.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/app.py)
> * [docs/app.py](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/app.py)
> * [docs/example_fastapi.ipynb](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_fastapi.ipynb)

This document describes GaMMA's FastAPI-based web service that provides HTTP endpoints for seismic event association. The web API allows remote clients to submit pick data and receive associated events through standard HTTP requests.

For information about the core association algorithms, see [Core Association Functions](/AI4EPS/GaMMA/4.1-core-association-functions). For direct Python usage without the web interface, see [Examples and Tutorials](/AI4EPS/GaMMA/5-examples-and-tutorials).

## API Overview

The FastAPI application provides a simple REST interface with two main endpoints. The service is designed to be lightweight and can be deployed as a standalone web service or integrated into larger seismological processing pipelines.

```mermaid
flowchart TD

Client["HTTP Client"]
API["FastAPI Application<br>(app.py)"]
Config["set_config()<br>Region Configuration"]
Runner["run_gamma()<br>Data Processing"]
Core["gamma.utils.association<br>Core Algorithm"]

Client --> API
Client --> API
API --> Config
API --> Runner
Runner --> Core
API --> Client
```

**API Endpoints**

| Endpoint | Method | Description |
| --- | --- | --- |
| `/` | GET | Health check endpoint returning `{"Hello": "GaMMA!"}` |
| `/predict/` | POST | Main prediction endpoint for seismic event association |

Sources: [app.py L6-L27](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/app.py#L6-L27)

## Main Prediction Endpoint

The `/predict/` endpoint accepts seismic pick data, station metadata, and configuration parameters, then returns associated events and updated pick assignments.

### Request Format

The endpoint expects a JSON payload with three main components:

```mermaid
flowchart TD

Request["POST /predict/"]
Picks["picks: {data: [...]}"]
Stations["stations: {data: [...]}"]
Config["config: {...}"]
PickData["station_id<br>phase_time<br>phase_type<br>phase_score<br>phase_amplitude"]
StationData["station_id<br>longitude<br>latitude<br>elevation_m"]
ConfigData["region settings<br>algorithm parameters"]

Request --> Picks
Request --> Stations
Request --> Config
Picks --> PickData
Stations --> StationData
Config --> ConfigData
```

**Required Pick Data Fields:**

* `station_id`: Station identifier
* `phase_time`: Phase arrival time (ISO format string)
* `phase_type`: Phase type ("P" or "S")
* `phase_score`: Detection confidence score
* `phase_amplitude`: Phase amplitude value

**Required Station Data Fields:**

* `station_id`: Station identifier (must match picks)
* `longitude`: Station longitude in degrees
* `latitude`: Station latitude in degrees
* `elevation_m`: Station elevation in meters

Sources: [app.py L14-L27](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/app.py#L14-L27)

 [app.py L119-L132](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/app.py#L119-L132)

### Response Format

The endpoint returns a JSON object containing associated events and updated picks with event assignments:

```
{
  "events": [...],
  "picks": [...]
}
```

If no events are detected, the response returns `{"events": None, "picks": [...]}`.

Sources: [app.py L22-L27](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/app.py#L22-L27)

## Configuration System

The API includes a comprehensive configuration system with region-specific defaults. The `set_config()` function provides pre-configured settings optimized for different seismic regions.

```mermaid
flowchart TD

SetConfig["set_config(region)"]
BaseConfig["Base Configuration<br>min_picks, thresholds"]
RegionConfig["Region-Specific Settings<br>geographical bounds"]
Projection["Coordinate Projection<br>pyproj.Proj"]
AlgoConfig["Algorithm Parameters<br>BGMM, velocity models"]

SetConfig --> BaseConfig
SetConfig --> RegionConfig
RegionConfig --> Projection
SetConfig --> AlgoConfig
```

**Default Configuration Categories:**

| Category | Parameters | Purpose |
| --- | --- | --- |
| Pick Thresholds | `min_picks`, `min_score`, `min_p_picks`, `min_s_picks` | Quality control |
| Geographic Bounds | `minlongitude`, `maxlongitude`, `minlatitude`, `maxlatitude` | Study region |
| Algorithm Settings | `method="BGMM"`, `use_dbscan=False` | Association method |
| Velocity Model | `vel={"p": 6.0, "s": 3.43}` | Travel time calculation |

The system currently includes built-in support for the Ridgecrest region, with extensible architecture for additional regions.

Sources: [app.py L30-L106](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/app.py#L30-L106)

## Data Processing Pipeline

The `run_gamma()` function implements a multi-step data transformation pipeline that prepares input data for the core association algorithm.

```mermaid
flowchart TD

Input["Input Data<br>(picks, stations, config)"]
Transform["Data Transformation<br>Column Renaming"]
Project["Coordinate Projection<br>Geographic → Cartesian"]
Associate["Core Association<br>gamma.utils.association"]
PostProcess["Result Processing<br>Coordinate Conversion"]
Output["JSON Response"]
T1["station_id → id<br>phase_time → timestamp<br>phase_type → type"]
P1["longitude,latitude → x(km),y(km)<br>elevation_m → z(km)"]
PP1["x(km),y(km) → longitude,latitude<br>Add event_index to picks"]

Input --> Transform
Transform --> Project
Project --> Associate
Associate --> PostProcess
PostProcess --> Output
Transform --> T1
Project --> P1
PostProcess --> PP1
```

**Key Processing Steps:**

1. **Column Renaming**: Maps API field names to internal GaMMA conventions
2. **Coordinate Projection**: Converts geographic coordinates to Cartesian using azimuthal equidistant projection
3. **Core Association**: Calls the main `association()` function from `gamma.utils`
4. **Result Formatting**: Converts results back to API format with geographic coordinates

Sources: [app.py L112-L158](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/app.py#L112-L158)

## Deployment Architecture

The FastAPI application is designed for flexible deployment scenarios, from local development to cloud-based services.

```mermaid
flowchart TD

Notebook["Jupyter Notebooks"]
Script["Python Scripts"]
Web["Web Applications"]
FastAPI["FastAPI Server<br>app.py"]
Uvicorn["ASGI Server<br>(uvicorn)"]
Config["Configuration<br>set_config()"]
Runner["Data Pipeline<br>run_gamma()"]
Core["GaMMA Core<br>association()"]
Docker["Docker Container<br>Dockerfile"]
HF["Hugging Face Spaces<br>ai4eps-gamma.hf.space"]

Notebook --> FastAPI
Script --> FastAPI
Web --> FastAPI
FastAPI --> Config
FastAPI --> Runner
FastAPI --> Docker

subgraph Infrastructure ["Infrastructure"]
    Docker
    HF
    Docker --> HF
end

subgraph subGraph2 ["Processing Layer"]
    Config
    Runner
    Core
    Runner --> Core
end

subgraph subGraph1 ["API Layer"]
    FastAPI
    Uvicorn
    FastAPI --> Uvicorn
end

subgraph subGraph0 ["Client Layer"]
    Notebook
    Script
    Web
end
```

**Deployment Options:**

* **Local Development**: Direct FastAPI server using uvicorn
* **Containerized**: Docker-based deployment for consistency
* **Cloud Service**: Hugging Face Spaces for public access

The service is accessible both locally (`http://127.0.0.1:8000`) and through the public endpoint at `https://ai4eps-gamma.hf.space`.

Sources: [docs/example_fastapi.ipynb L34-L35](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_fastapi.ipynb#L34-L35)

## Usage Example

The following example demonstrates the complete workflow for using the GaMMA web API:

```javascript
import requests
import pandas as pd

# Prepare data
GAMMA_API_URL = "https://ai4eps-gamma.hf.space"
picks = pd.DataFrame(pick_data)
stations = pd.DataFrame(station_data)
config = {"region": "Ridgecrest"}

# Convert to API format
picks_dict = picks.to_dict(orient="records")
stations_dict = stations.to_dict(orient="records")

# Make API request
response = requests.post(
    f"{GAMMA_API_URL}/predict/",
    json={
        "picks": {"data": picks_dict},
        "stations": {"data": stations_dict},
        "config": config
    }
)

# Process results
if response.status_code == 200:
    result = response.json()
    events = result["events"]
    updated_picks = result["picks"]
```

The API handles all coordinate transformations, data validation, and association processing internally, returning results in a format suitable for further analysis or visualization.

Sources: [docs/example_fastapi.ipynb L1320-L1334](https://github.com/AI4EPS/GaMMA/blob/edcf2cec/docs/example_fastapi.ipynb#L1320-L1334)