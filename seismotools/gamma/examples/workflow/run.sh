#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OUT="${1:-/tmp/gamma-workflow}"
if [ -e "$OUT" ]; then
  echo "output exists: $OUT; choose a new output path" >&2
  exit 2
fi
mkdir -p "$OUT/input" "$OUT/result"
python - "$OUT/input" <<'PY'
import sys
from pathlib import Path
import pandas as pd
root = Path(sys.argv[1])
origin = pd.Timestamp("2019-01-01T00:00:00Z")
stations = pd.DataFrame({
    "station_id": [f"S{i:02d}" for i in range(8)],
    "x_km": [i * 2.0 for i in range(8)],
    "y_km": [0.0] * 8,
    "z_km": [0.0] * 8,
})
picks = []
for i in range(8):
    for phase, delay in (("P", 1.0 + i * 0.01), ("S", 2.0 + i * 0.01)):
        picks.append({
            "timestamp": (origin + pd.Timedelta(seconds=delay)).isoformat(),
            "station_id": f"S{i:02d}", "phase": phase, "probability": 0.99,
        })
stations.to_csv(root / "stations.csv", index=False)
pd.DataFrame(picks).to_csv(root / "picks.csv", index=False)
PY
python "$ROOT/seismotools/gamma/interface/run.py" \
  --picks "$OUT/input/picks.csv" \
  --stations "$OUT/input/stations.csv" \
  --output-dir "$OUT/result"
python - "$OUT/result" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
result = json.loads((root / "run_result.json").read_text())
if result.get("status") != "success": raise SystemExit("GaMMA adapter did not succeed")
for name in ("events.csv", "assignments.csv"):
    if not (root / name).is_file(): raise SystemExit(f"missing {name}")
print(json.dumps({"status": "pass", "events": result.get("events"), "assignments": result.get("assignments")}, indent=2))
PY
