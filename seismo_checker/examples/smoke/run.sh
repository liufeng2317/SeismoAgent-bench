#!/usr/bin/env bash
# Synthetic check of every stage: clean inputs raise no flag, each injected error raises exactly its flag.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TOOL="$ROOT/seismo_checker"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
OUT="${1:-$(mktemp -d /tmp/checker-smoke.XXXXXX)}"
mkdir -p "$OUT"
"$PYTHON" -I "$TOOL/examples/smoke/make_synthetic.py" --output-dir "$OUT/inputs"
"$PYTHON" -I "$TOOL/examples/smoke/check_synthetic.py" --inputs-dir "$OUT/inputs" --output-dir "$OUT/runs" --python "$PYTHON"
