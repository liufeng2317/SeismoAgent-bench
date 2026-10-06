#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OUT="${1:-/tmp/hypodd-workflow}"
if [ -e "$OUT" ]; then
  echo "output exists: $OUT; choose a new output path" >&2
  exit 2
fi
mkdir -p "$OUT/input"
cat > "$OUT/input/event.dat" <<'EVENTS'
20190101 000001 35.0 -117.0 5.0 1.0 0.1 0.1 0.0 1001
20190101 000002 35.01 -117.01 5.0 1.0 0.1 0.1 0.0 1002
EVENTS
cat > "$OUT/input/station.dat" <<'STATIONS'
STA01 35.0 -117.0
STATIONS
cat > "$OUT/input/dt.ct" <<'DT'
# 1001 1002
STA01 0.0 1.0 1.0 P
DT
cat > "$OUT/input/hypoDD.inp" <<'CONTROL'
missing.cc
dt.ct
event.dat
station.dat
hypoDD.loc
hypoDD.reloc
hypoDD.res
hypoDD.stares
hypoDD.srcpar
2 3 1000
0 1
1 2 1
1 0.0 1.0 1.0 100.0 1.0 1.0 1.0 100.0 10.0
1 1.73
0.0
6.0
0
CONTROL
python "$ROOT/seismotools/hypodd/interface/run.py" \
  --input-dir "$OUT/input" --output-dir "$OUT/result" --mode ct \
  --bin-dir "$ROOT/seismotools/hypodd/runtime/bin"
python - "$OUT/result" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
result = json.loads((root / "run_result.json").read_text())
if result.get("status") != "success": raise SystemExit("hypoDD adapter did not succeed")
if not (root / "hypoDD.loc").is_file(): raise SystemExit("missing hypoDD.loc")
print(json.dumps({"status": "pass", "mode": result.get("mode"), "outputs": result.get("outputs", {})}, indent=2))
PY
