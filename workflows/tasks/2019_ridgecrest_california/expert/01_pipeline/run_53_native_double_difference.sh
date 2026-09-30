#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PYTHON=${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}
mkdir -p logs/53_native_double_difference
stage=all
if [[ "${1:-}" == "--stage" ]]; then stage="${2:-all}"; fi
case "$stage" in all|prepare|locate|report) ;; *) echo "Invalid stage: $stage" >&2; exit 2;; esac
"$PYTHON" -u 53_native_double_difference.py "$@" 2>&1 | tee "logs/53_native_double_difference/${stage}.log"
