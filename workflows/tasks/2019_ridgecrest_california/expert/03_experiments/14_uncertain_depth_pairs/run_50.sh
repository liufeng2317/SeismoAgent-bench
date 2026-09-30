#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p logs
"$PYTHON" -u 50_prepare.py 2>&1 | tee logs/50_prepare.log
"$PYTHON" -u 50_measure.py 2>&1 | tee logs/50_measure.log
"$PYTHON" -u 50_run.py --workers 8 2>&1 | tee logs/50_location.log
"$PYTHON" -u 50_evaluate.py 2>&1 | tee logs/50_evaluation.log
"$PYTHON" -u ../../02_diagnostics/50_plot_graph_update.py
