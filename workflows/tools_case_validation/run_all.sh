#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
mkdir -p "$HERE/outputs"
for tool in phasenet gamma pyocto real nonlinloc hypoinverse hypodd cross_correlation growclust; do
  echo "=== $tool ==="
  "$PYTHON" "$HERE/validate_cases.py" --tool "$tool" | tee "$HERE/outputs/$tool.json"
done
echo "Validation outputs: $HERE/outputs"
