#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OUT="${1:-/tmp/phase-picking-workflow}"
if [ -e "$OUT" ]; then
  echo "output exists: $OUT; choose a new output path" >&2
  exit 2
fi
mkdir -p "$OUT/input" "$OUT/result"
python - "$OUT/input/waveform.npz" <<'PY'
import sys
import numpy as np
rng = np.random.default_rng(42)
data = (0.02 * rng.normal(size=(3, 3001))).astype("float32")
data[:, 1500:1510] += np.array([[2.0], [1.0], [0.5]], dtype="float32")
np.savez(sys.argv[1], data=data)
PY
python "$ROOT/seismotools/phase_picking/interface/run.py" \
  --input-npz "$OUT/input/waveform.npz" \
  --output-dir "$OUT/result" --model phasenet --sample-rate 100
python - "$OUT/result" <<'PY'
import json, sys
from pathlib import Path
import numpy as np
root = Path(sys.argv[1])
summary = json.loads((root / "run_result.json").read_text())
prob = np.load(root / "probabilities.npz")
if summary.get("status") != "success": raise SystemExit("PhaseNet adapter did not succeed")
if prob["probabilities"].shape[0] != 1: raise SystemExit("unexpected probability batch shape")
print(json.dumps({"status": "pass", "model": summary.get("model"), "output_shape": list(prob["probabilities"].shape)}, indent=2))
PY
