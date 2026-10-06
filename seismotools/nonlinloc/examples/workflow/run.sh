#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OUT="${1:-/tmp/nonlinloc-workflow}"
if [ -e "$OUT" ]; then
  echo "output exists: $OUT; choose a new output path" >&2
  exit 2
fi
mkdir -p "$OUT/input"
cat > "$OUT/input/velocity_model_1d.txt" <<'MODEL'
0 5.0 2.9
5 6.0 3.5
20 7.0 4.0
MODEL
cat > "$OUT/input/stations_native.txt" <<'STATIONS'
S001 -117.0000 35.0000 0
S002 -116.9900 35.0000 0
S003 -117.0000 35.0100 0
S004 -116.9900 35.0100 0
STATIONS
cat > "$OUT/input/picks_simple.txt" <<'PICKS'
S001 P 10.0 ?
S001 S 12.0 ?
S002 P 10.8 ?
S002 S 13.4 ?
S003 P 10.7 ?
S003 S 13.2 ?
S004 P 11.4 ?
S004 S 14.0 ?
PICKS
python "$ROOT/seismotools/nonlinloc/interface/run.py" \
  --input-dir "$OUT/input" --output-dir "$OUT/result" \
  --bin-dir "$ROOT/seismotools/nonlinloc/runtime/bin" --date 201901010000
python - "$OUT/result" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
result = json.loads((root / "run_result.json").read_text())
if result.get("status") != "success": raise SystemExit("NonLinLoc adapter did not succeed")
if not (root / "located_events.csv").is_file(): raise SystemExit("missing located_events.csv")
print(json.dumps({"status": "pass", "located_events": result.get("located_events")}, indent=2))
PY
