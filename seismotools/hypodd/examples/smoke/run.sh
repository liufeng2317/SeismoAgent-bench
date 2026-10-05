#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
WORK="$(mktemp -d /tmp/hypodd-smoke.XXXXXX)"
OUT="${1:-/tmp/hypodd-smoke-output}"
trap 'rm -rf "$WORK"' EXIT
cat > "$WORK/event.dat" <<'EOF'
20190101 000001 35.0 -117.0 5.0 1.0 0.1 0.1 0.0 1001
20190101 000002 35.01 -117.01 5.0 1.0 0.1 0.1 0.0 1002
EOF
cat > "$WORK/station.dat" <<'EOF'
STA01 35.0 -117.0
EOF
cat > "$WORK/dt.ct" <<'EOF'
# 1001 1002
STA01 0.0 1.0 1.0 P
EOF
cat > "$WORK/hypoDD.inp" <<'EOF'
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
EOF
exec python "$ROOT/seismotools/hypodd/interface/run.py" \
  --input-dir "$WORK" --output-dir "$OUT" --mode ct \
  --bin-dir "$ROOT/seismotools/hypodd/runtime/bin"
