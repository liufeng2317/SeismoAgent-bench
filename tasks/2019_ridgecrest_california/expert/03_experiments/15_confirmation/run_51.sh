#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PYTHON=/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python
mkdir -p logs
for script in 51_prepare.py 51_observations.py 51_graph.py 51_measure.py 51_native_controls.py 51_run.py 51_evaluate.py; do
  if [[ "$script" == "51_observations.py" ]]; then
    "$PYTHON" -u 51_continue.py --observations 2>&1 | tee "logs/${script%.py}.log"
  else
    "$PYTHON" -u "$script" 2>&1 | tee "logs/${script%.py}.log"
  fi
done
"$PYTHON" -u ../../02_diagnostics/51_plot_confirmation.py 2>&1 | tee logs/51_plot_confirmation.log
