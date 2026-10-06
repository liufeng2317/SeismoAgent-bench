# GaMMA

GaMMA is the local arrival-association implementation used to group P and S
picks into candidate events. The source snapshot reports distribution name
`GMMA`, version `1.2.17`, and imports as `gamma`. It consumes picks and station
coordinates; event location is a downstream operation.

## Directory layout

```text
gamma/
├── source/                 # GaMMA implementation, dependencies and original tests
├── interface/              # Stable association entry point and contracts
├── examples/smoke/         # Small synthetic association example
├── docs/                   # Source and expanded reference documentation
├── metadata.json           # Tool and interface identity
└── README.md
```

GaMMA has no bundled executable or model weights, so it does not need a
`runtime/` directory. Python dependencies are installed in the selected
benchmark environment; `source/requirements.txt` records the package needs.

## Standard interface

Use `interface/run.py` for a predictable association call:

```bash
python seismotools/gamma/interface/run.py \
  --picks /path/to/picks.csv \
  --stations /path/to/stations.csv \
  --output-dir /path/to/writable-run
```

The pick table requires `timestamp`, `station_id` and `phase` columns. Optional
columns are `probability` and `amplitude`. The station table requires
`station_id`, `x_km`, `y_km` and `z_km` local Cartesian coordinates. Contracts
are documented in [interface/input_schema.json](interface/input_schema.json)
and [interface/output_schema.json](interface/output_schema.json).

The adapter writes `events.csv`, `assignments.csv` and `run_result.json`. It
uses single-process BGMM defaults, fixes the local random seed, preserves
unassociated picks by reporting assignments separately, and does not read
reference catalogs.

Run the smoke example with:

```bash
conda run -n seismoagent bash seismotools/gamma/examples/smoke/run.sh /tmp/gamma-smoke
```

A case may pass a JSON configuration with `--config` when it needs different
association thresholds, velocity settings or spatial bounds. Those choices
belong to the case workflow and should be recorded with its outputs.

## Direct Python use

For custom workflows, add the source directory to `PYTHONPATH` and call the
local association function:

```python
import sys
sys.path.insert(0, "seismotools/gamma/source")
from gamma.utils import association

events, assignments = association(picks, stations, config, method="BGMM")
```

The caller must normalize timestamps, station identifiers, coordinate units,
phase labels and probability values before calling the API. Keep the original
pick table and the association configuration alongside the run output.

## Documentation and validation

The detailed source and expanded reference material is in [docs/README.md](docs/README.md),
including API notes, travel-time assumptions and example notebooks. The
notebooks are references rather than guaranteed offline benchmark launchers.

Run the project validation from the repository root:

```bash
conda run -n seismoagent python seismotools/support/tools_usage_validation/validate_gamma.py
```

It checks a deterministic synthetic association and one bounded Ridgecrest
event. Passing confirms local execution and file plumbing, not scientific
accuracy of a full catalog.
