#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p logs
"$PYTHON" -u 49_calibrate.py 2>&1 | tee logs/49_calibrate.log
if "$PYTHON" -c 'import json,sys; from pathlib import Path; r=json.loads(Path("../../export/49_velocity_ratio/calibration.json").read_text()); sys.exit(0 if all(r["gates"].values()) else 1)'; then
  "$PYTHON" -u 49_run.py --workers 4 2>&1 | tee logs/49_location.log
  "$PYTHON" -u 49_report.py 2>&1 | tee logs/49_evaluation.log
  "$PYTHON" -u 49_plot.py
else
  echo "Calibration rejected; no location model changed."
fi
