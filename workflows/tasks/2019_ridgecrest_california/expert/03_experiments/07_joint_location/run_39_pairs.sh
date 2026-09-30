#!/usr/bin/env bash
# Run or resume location and evaluation after verified CC measurements exist.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="${SEISMO_PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p "$script_dir/logs"
"$python_bin" -u "$script_dir/39_run_pairs.py" --workers 4 2>&1 | tee -a "$script_dir/logs/39_location.log"
"$python_bin" -u "$script_dir/39_evaluate_pairs.py" 2>&1 | tee -a "$script_dir/logs/39_evaluation.log"
