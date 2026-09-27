#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p logs
export SEISBENCH_CACHE_ROOT="$(pwd)/../../export/47_missing_s_observations/cache"
"$PYTHON" -c "import seisbench"
"$PYTHON" -u 47_extract_s.py --workers 16 2>&1 | tee logs/47_extraction.log
"$PYTHON" -u 47_measure_s_cc.py 2>&1 | tee logs/47_cc.log
"$PYTHON" -u 47_run_s.py --workers 4 2>&1 | tee logs/47_location.log
"$PYTHON" -u 47_evaluate_s.py 2>&1 | tee logs/47_evaluation.log
