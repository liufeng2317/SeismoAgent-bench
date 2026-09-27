#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="${SEISMO_PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$script_dir/logs"
exec 9>"$script_dir/logs/43_pipeline.lock"
flock -n 9 || { echo 'Another stage43 pipeline is running.' >&2; exit 1; }
"$python_bin" -u "$script_dir/43_qualify_template.py" 2>&1 | tee -a "$script_dir/logs/43_qualification.log"
"$python_bin" -u "$script_dir/43_report_template.py" 2>&1 | tee -a "$script_dir/logs/43_report.log"
# This qualification runner never admits observations or starts catalog fitting.
