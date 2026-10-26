#!/usr/bin/env bash
# Synthetic known-answer association: 40 events, 15 stations, noisy/false/dropped picks.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OUT="${1:-/tmp/pyocto-smoke}"
PY="${PYTHON:-python}"
"$PY" -I "$ROOT/seismotools/support/tools_usage_validation/synthetic_events.py" --out "$OUT/case" \
  --noise-s 0.05 --false-per-station 3 --drop-frac 0.1
cat > "$OUT/config.json" <<JSON
{"region": {"latitude": [35.3, 35.7], "longitude": [-97.25, -96.75], "depth_km": [0, 20]}, "time_before_s": 30}
JSON
exec "$PY" -I "$ROOT/seismotools/pyocto/interface/run.py" --picks "$OUT/case/picks.csv" \
  --stations "$OUT/case/stations.csv" --velocity-model "$OUT/case/velocity_model.txt" \
  --config "$OUT/config.json" --output-dir "$OUT/run" --overwrite
