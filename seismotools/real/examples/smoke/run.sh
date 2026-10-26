#!/usr/bin/env bash
# Synthetic known-answer association: 40 events, 15 stations, noisy/false/dropped picks.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OUT="${1:-/tmp/real-smoke}"
PY="${PYTHON:-python}"
"$PY" -I "$ROOT/seismotools/support/tools_usage_validation/synthetic_events.py" --out "$OUT/case" \
  --noise-s 0.05 --false-per-station 3 --drop-frac 0.1
cat > "$OUT/config.json" <<JSON
{"search": {"max_distance_deg": 0.5}, "table": {"max_distance_deg": 0.6, "max_depth_km": 25},
 "thresholds": {"nxd": 0.5}}
JSON
exec "$PY" -I "$ROOT/seismotools/real/interface/run.py" --picks "$OUT/case/picks.csv" \
  --stations "$OUT/case/stations.csv" --velocity-model "$OUT/case/velocity_model.txt" \
  --config "$OUT/config.json" --output-dir "$OUT/run" --overwrite
