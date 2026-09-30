#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p logs
"$PYTHON" -u 48_prepare.py 2>&1 | tee logs/48_prepare.log
"$PYTHON" -u 48_run.py --branch fixed --workers 4 2>&1 | tee logs/48_fixed_location.log
"$PYTHON" -u 48_evaluate.py --branch fixed 2>&1 | tee logs/48_fixed_evaluation.log
"$PYTHON" -u 48_measure.py 2>&1 | tee logs/48_measure.log
"$PYTHON" -u 48_run.py --branch refreshed --workers 4 2>&1 | tee logs/48_refreshed_location.log
"$PYTHON" -u 48_evaluate.py --branch refreshed 2>&1 | tee logs/48_refreshed_evaluation.log
