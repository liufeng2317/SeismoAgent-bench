#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
mkdir -p "$HERE/outputs"
"$PYTHON" "$HERE/validate_ridgecrest.py" | tee "$HERE/outputs/ridgecrest_validation.json"
