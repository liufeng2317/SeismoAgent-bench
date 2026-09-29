#!/usr/bin/env bash
set -euo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$TASK_DIR/../.." && pwd)"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
RUN_ID="${RUN_ID:-codex-phasepicking-20190705}"

cd "$PROJECT_DIR"
"$PYTHON" -m SeismoAgentBench run-codex \
  --task "$TASK_DIR/task.json" \
  --manifest "$TASK_DIR/input_manifest.json" \
  --agent-name codex-phase-picking \
  --agent-version 1 \
  --run-root "$TASK_DIR/runs" \
  --run-id "$RUN_ID" \
  --codex-bin "${CODEX_BIN:-$(command -v codex)}" \
  --timeout 3600

"$PYTHON" -m SeismoAgentBench evaluate \
  --run-dir "$TASK_DIR/runs/$RUN_ID"
