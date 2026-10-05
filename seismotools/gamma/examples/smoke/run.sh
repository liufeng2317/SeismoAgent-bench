#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
WORK="$(mktemp -d /tmp/gamma-smoke.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
python - "$WORK" <<'PY'
import sys
from pathlib import Path
import pandas as pd
root = Path(sys.argv[1])
origin = pd.Timestamp("2019-01-01T00:00:00Z")
stations = pd.DataFrame({"station_id": [f"S{i}" for i in range(8)], "x_km": [i*2.0 for i in range(8)], "y_km": [0.0]*8, "z_km": [0.0]*8})
picks=[]
for i in range(8):
    for phase, delay in (("P", 1.0 + i*0.01), ("S", 2.0 + i*0.01)):
        picks.append({"timestamp": (origin + pd.Timedelta(seconds=delay)).isoformat(), "station_id": f"S{i}", "phase": phase, "probability": 0.99})
stations.to_csv(root/"stations.csv", index=False)
pd.DataFrame(picks).to_csv(root/"picks.csv", index=False)
PY
exec python "$ROOT/seismotools/gamma/interface/run.py" \
  --picks "$WORK/picks.csv" --stations "$WORK/stations.csv" \
  --output-dir "${1:-/tmp/gamma-smoke-output}"
