#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PYTHON=/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python
mkdir -p logs/52_full_catalog
if [[ ! -f ../export/52_full_catalog/design.json ]]; then
  "$PYTHON" -u 52_prepare_full_catalog.py 2>&1 | tee logs/52_full_catalog/prepare.log
fi
if [[ ! -f ../export/52_full_catalog/cc_measurements.csv ]]; then
  "$PYTHON" -u 52_measure_full_catalog.py 2>&1 | tee logs/52_full_catalog/measure.log
fi
"$PYTHON" -u 52_run_full_catalog.py 2>&1 | tee logs/52_full_catalog/run.log
"$PYTHON" -u ../04_comparison/52_compare_full_catalog.py 2>&1 | tee logs/52_full_catalog/compare.log

# Current ownership labels are applied by figure-only renderers after the frozen exporter.
"$PYTHON" -u ../04_comparison/52_plot_catalog_figures.py 2>&1 | tee logs/52_full_catalog/plot_catalog.log
"$PYTHON" -u ../04_comparison/52_plot_delivery_comparison.py 2>&1 | tee logs/52_full_catalog/plot_delivery.log
