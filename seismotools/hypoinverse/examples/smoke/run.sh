#!/usr/bin/env bash
# Synthetic known-answer location: 40 events, 15 stations, exact arrivals (uniform half-space).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OUT="${1:-/tmp/hypoinverse-smoke}"
PY="${PYTHON:-python}"
"$PY" -I "$ROOT/seismotools/support/tools_usage_validation/synthetic_events.py" --out "$OUT/case"
"$PY" -c "import pandas as pd; p = pd.read_csv('$OUT/case/picks.csv', keep_default_na=False); \
p[p.event_id != ''].to_csv('$OUT/case/arrivals.csv', index=False)"
exec "$PY" -I "$ROOT/seismotools/hypoinverse/interface/run.py" --arrivals "$OUT/case/arrivals.csv" \
  --stations "$OUT/case/stations.csv" --velocity-model "$OUT/case/velocity_model.txt" \
  --output-dir "$OUT/run" --overwrite
