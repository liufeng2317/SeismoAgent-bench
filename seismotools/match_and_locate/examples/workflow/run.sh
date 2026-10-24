#!/usr/bin/env bash
# Replay the upstream MatchLocate2 Hi-net example through the standard interface
# and compare it with the upstream outputs stored under source/upstream/example.
#
#   bash run.sh /path/to/MatchLocate2-master.zip [work-dir]
#
# The archive is extracted into <work-dir>/data (new or empty), the dataset is
# built in <work-dir>/dataset and the run written to <work-dir>/run.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
TOOL="$ROOT/seismotools/match_and_locate"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
ARCHIVE="${1:?usage: run.sh MatchLocate2-master.zip [work-dir]}"
WORK="${2:-$TOOL/runtime/example_data/upstream_hinet}"
"$PYTHON" -I "$TOOL/examples/workflow/prepare_upstream_example.py" \
  --archive "$ARCHIVE" --data-dir "$WORK/data" --dataset-dir "$WORK/dataset"
"$PYTHON" -I "$TOOL/interface/run.py" --input-dir "$WORK/dataset" --output-dir "$WORK/run" \
  --jobs "${JOBS:-14}" --threads "${THREADS:-4}" --quiet
"$PYTHON" -I "$TOOL/examples/workflow/compare_reference.py" --run-dir "$WORK/run"
