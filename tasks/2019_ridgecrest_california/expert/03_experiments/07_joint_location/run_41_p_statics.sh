#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="${SEISMO_PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p "$script_dir/logs"
"$python_bin" -u "$script_dir/41_calibrate_p.py" --workers 4 2>&1 | tee -a "$script_dir/logs/41_p_statics.log"
"$python_bin" -u "$script_dir/41_evaluate_p.py" 2>&1 | tee -a "$script_dir/logs/41_evaluation.log"
