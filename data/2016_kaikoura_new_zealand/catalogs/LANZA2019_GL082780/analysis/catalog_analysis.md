# LANZA2019_GL082780 catalog analysis

This QuakeML contains multiple origin solutions per event. The parser retains the `preferredOriginID` solution and does not merge SIMUL and HypoDD origins as independent events.

| Selection | Events | HypoDD | SIMUL |
|---|---:|---:|---:|
| `full` | 2655 | 2012 | 643 |
| `time_only` | 123 | 110 | 13 |
| `benchmark` | 122 | 110 | 12 |

Input: `raw/grl59060-sup-0003-ds01.xml`; SHA-256 `c87a16de4fb28be7cd873b03e93b3d410c6e2237d7ed443affbe798670fbd478`.
Depth is converted from QuakeML metres to kilometres. Schema: `docs/schemas/catalog_event.schema.yaml`.
