#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p logs
"$PYTHON" -u 45_pick_station.py --workers 8 2>&1 | tee logs/45_pick.log
"$PYTHON" -u 45_associate_station.py 2>&1 | tee logs/45_association.log
"$PYTHON" -u 45_measure_station_cc.py 2>&1 | tee logs/45_cc.log
"$PYTHON" -u 45_run_station.py --workers 4 2>&1 | tee logs/45_location.log
"$PYTHON" -u 45_evaluate_station.py 2>&1 | tee logs/45_evaluation.log
