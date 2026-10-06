#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
mkdir -p "$HERE/outputs"
for script in validate_phasenet.py validate_gamma.py validate_nonlinloc.py validate_hypodd.py; do
  echo "=== $script ==="
  "$PYTHON" "$HERE/$script" | tee "$HERE/outputs/${script%.py}.json"
done
echo "Validation outputs: $HERE/outputs"
