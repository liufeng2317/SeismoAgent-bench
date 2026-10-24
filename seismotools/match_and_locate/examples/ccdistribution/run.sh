#!/usr/bin/env bash
# Replay the upstream MatchLocate2 CC-distribution example (location-resolution
# output, -O3) through the standard interface and compare with upstream.
#
#   bash run.sh /path/to/MatchLocate2-master.zip [work-dir]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
TOOL="$ROOT/seismotools/match_and_locate"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
ARCHIVE="${1:?usage: run.sh MatchLocate2-master.zip [work-dir]}"
WORK="${2:-$TOOL/runtime/example_data/upstream_ccdistribution}"
"$PYTHON" -I "$TOOL/examples/ccdistribution/prepare_ccdistribution_example.py" \
  --archive "$ARCHIVE" --data-dir "$WORK/data" --dataset-dir "$WORK/dataset"
"$PYTHON" -I "$TOOL/interface/run.py" --input-dir "$WORK/dataset" --output-dir "$WORK/run" \
  --threads "${THREADS:-16}" --quiet
"$PYTHON" -I "$TOOL/examples/ccdistribution/compare_ccdistribution.py" --run-dir "$WORK/run" \
  --upstream-ccdistribution "$WORK/data/archive/MatchLocate2-master/example_CCdistribution/CCdistribution.out"
