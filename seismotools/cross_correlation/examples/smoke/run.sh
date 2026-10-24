#!/usr/bin/env bash
# Synthetic known-answer run: build the dataset, measure, check.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
OUT="${1:-$(mktemp -d)}"
"$PYTHON" -I "$HERE/make_synthetic.py" --out "$OUT/data"
"$PYTHON" -I "$HERE/../../interface/run.py" --events "$OUT/data/events.csv" --arrivals "$OUT/data/arrivals.csv" \
  --waveforms "$OUT/data/waveforms" --output-dir "$OUT/run" --workers 4 --quiet
"$PYTHON" -I "$HERE/check_synthetic.py" --data "$OUT/data" --run "$OUT/run"
