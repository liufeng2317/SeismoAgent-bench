#!/usr/bin/env bash
# Synthetic end-to-end check of the two-step interface: raw MiniSEED + tables
# -> prepare.py -> run.py -> score against known answers.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
TOOL="$ROOT/seismotools/match_and_locate"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
OUT="${1:-$(mktemp -d /tmp/matchlocate-smoke.XXXXXX)}"
mkdir -p "$OUT"
"$PYTHON" -I "$TOOL/examples/smoke/make_synthetic.py" --output-dir "$OUT/inputs"
"$PYTHON" -I "$TOOL/interface/prepare.py" --waveforms "$OUT/inputs/waveforms" \
  --stations "$OUT/inputs/stations.csv" --templates "$OUT/inputs/templates.csv" \
  --picks "$OUT/inputs/picks.csv" --velocity-model "$OUT/inputs/velocity_model.csv" \
  --config "$OUT/inputs/prepare_config.json" --output-dir "$OUT/dataset" --workers 4 --quiet
"$PYTHON" -I "$TOOL/interface/run.py" --input-dir "$OUT/dataset" --output-dir "$OUT/run" \
  --jobs 1 --threads "${THREADS:-4}" --quiet
"$PYTHON" -I "$TOOL/examples/smoke/check_synthetic.py" --inputs-dir "$OUT/inputs" --run-dir "$OUT/run"
