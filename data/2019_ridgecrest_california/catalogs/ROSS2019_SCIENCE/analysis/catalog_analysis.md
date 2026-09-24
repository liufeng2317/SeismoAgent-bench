# ROSS2019_SCIENCE catalog analysis

Each product is parsed with its native schema; benchmark selection uses the Ridgecrest fixed window (2019-07-04 to 2019-07-07, 35.45–36.05°N, −117.90–−117.20°E, depth 0–20 km).

| Product | Full | Time-only | Benchmark |
|---|---:|---:|---:|
| `qtm_event_catalog` | 111,918 | 12,806 | 12,768 |

QTM source rows preserve the original `nbranch` quality indicator; rows with nbranch > 1 are the multi-branch subset, not a separate catalog.
