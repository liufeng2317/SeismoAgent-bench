#!/usr/bin/env bash
# Sequential round execution. The round identity (r1, r2, ...) comes from
# 00_config/config.yaml (round + export_root); each round exports into its own
# export root and log directory and never mutates previous rounds.
#
# Usage: run_round.sh [stage ...]
#   stages: 01_pilot 02_pilot 03_pilot 04_pilot 01_full 02_full 03_full
#           04_full 05 09 10   (default: the full DAG 01_full..10)
#
# Pilot stages are diagnostic subsets (quiet + mainshock windows) meant to be
# run and inspected manually before committing to the full eight-day pass.
set -euo pipefail
cd "$(dirname "$0")/.."
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PYTHON=/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python
ROUND=$($PYTHON -I -c "import yaml;print(yaml.safe_load(open('00_config/config.yaml'))['round'])")
LOGS=logs/$ROUND
mkdir -p "$LOGS"

run() {  # run <label> <command...>
    local label=$1; shift
    echo "[$(date -u +%FT%TZ)] $label"
    "$@" 2>&1 | tee "$LOGS/$label.log"
}

STAGES=${*:-"01_full 02_full 03_full 04_full 05 09 10"}
for stage in $STAGES; do
    case $stage in
        01_pilot) run 01_pilot "$PYTHON" -I 01_pipeline/01_prepare_inputs.py --scope pilot ;;
        02_pilot) run 02_pilot "$PYTHON" -I 01_pipeline/02_pick_phasenet.py --scope pilot --workers 4 ;;
        03_pilot) run 03_pilot "$PYTHON" -I 01_pipeline/03_associate_gamma.py --scope pilot ;;
        04_pilot) run 04_pilot "$PYTHON" -I 01_pipeline/04_locate_nonlinloc.py --scope pilot ;;
        01_full)  run 01_full  "$PYTHON" -I 01_pipeline/01_prepare_inputs.py --scope full ;;
        02_full)  run 02_full  "$PYTHON" -I 01_pipeline/02_pick_phasenet.py --scope full --workers 16 ;;
        03_full)  run 03_full  "$PYTHON" -I 01_pipeline/03_associate_gamma.py --scope full ;;
        04_full)  run 04_full  "$PYTHON" -I 01_pipeline/04_locate_nonlinloc.py --scope full ;;
        05)       run 05       "$PYTHON" -I 04_comparison/05_match_references.py ;;
        09)       run 09       "$PYTHON" -I 01_pipeline/09_estimate_magnitude.py --workers 16 ;;
        10)       run 10       "$PYTHON" -I 01_pipeline/10_validate_catalog.py ;;
        *) echo "unknown stage: $stage" >&2; exit 2 ;;
    esac
done
echo "round $ROUND complete: stages $STAGES"
