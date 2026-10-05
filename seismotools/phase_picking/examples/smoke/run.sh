#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OUT="${1:-/tmp/phase-picking-smoke}"
INPUT="$(mktemp --suffix=.npz)"
trap 'rm -f "$INPUT"' EXIT
python - "$INPUT" <<'PY'
import sys
import numpy as np
rng = np.random.default_rng(42)
np.savez(sys.argv[1], data=rng.normal(size=(3, 3001)).astype("float32"))
PY
exec python "$ROOT/seismotools/phase_picking/interface/run.py" \
  --input-npz "$INPUT" --output-dir "$OUT" --model phasenet --sample-rate 100
