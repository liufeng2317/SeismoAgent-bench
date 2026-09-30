#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
expert_dir="$(cd -- "$script_dir/../.." && pwd)"
python_bin="${SEISMO_PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p "$script_dir/logs"
exec 9>"$script_dir/logs/42_pipeline.lock"
flock -n 9 || { echo 'Another stage42 pipeline is running.' >&2; exit 1; }
# Start only after extraction has completed. Never restart a live extraction here.
test -f "$expert_dir/export/42_vertical_p_observations/extraction_summary.json"
"$python_bin" -u "$script_dir/42_measure_vertical_cc.py" 2>&1 | tee "$script_dir/logs/42_cc.log"
"$python_bin" -u "$script_dir/42_run_vertical.py" --workers 4 2>&1 | tee "$script_dir/logs/42_location.log"
"$python_bin" -u "$script_dir/42_evaluate_vertical.py" 2>&1 | tee "$script_dir/logs/42_evaluation.log"
