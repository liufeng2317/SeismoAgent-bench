#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
expert_dir="$(cd -- "$script_dir/../.." && pwd)"
python_bin="${SEISMO_PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p "$script_dir/logs"
exec 9>"$script_dir/logs/44_pipeline.lock"
flock -n 9 || { echo 'Another stage44 pipeline is running.' >&2; exit 1; }
test -f "$expert_dir/export/44_missing_p_observations/extraction_summary.json"
"$python_bin" -u "$script_dir/44_measure_missing_cc.py" 2>&1 | tee "$script_dir/logs/44_cc.log"
"$python_bin" -u "$script_dir/44_run_missing.py" --workers 4 2>&1 | tee "$script_dir/logs/44_location.log"
"$python_bin" -u "$script_dir/44_evaluate_missing.py" 2>&1 | tee "$script_dir/logs/44_evaluation.log"
