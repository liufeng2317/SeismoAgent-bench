#!/usr/bin/env bash
set -euo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$TASK_DIR/../.." && pwd)"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
RUN_ID="${RUN_ID:-codex-phasepicking-$(date -u +%Y%m%dT%H%M%SZ)}"
CODEX_BIN="${CODEX_BIN:-$(command -v codex)}"
if [ -d "$CODEX_BIN" ]; then
  CODEX_BIN="$CODEX_BIN/codex"
fi
if [ ! -x "$CODEX_BIN" ]; then
  echo "Codex executable is not available: $CODEX_BIN" >&2
  exit 2
fi

cd "$PROJECT_DIR"
"$PYTHON" -m SeismoAgentBench run-codex \
  --task "$TASK_DIR/task.json" \
  --manifest "$TASK_DIR/input_manifest.json" \
  --agent-name codex-phase-picking \
  --agent-version 1 \
  --run-root "$TASK_DIR/runs" \
  --run-id "$RUN_ID" \
  --codex-bin "$CODEX_BIN" \
  --timeout 3600

"$PYTHON" -m SeismoAgentBench evaluate \
  --run-dir "$TASK_DIR/runs/$RUN_ID"
