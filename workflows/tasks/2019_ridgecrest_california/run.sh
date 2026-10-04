#!/usr/bin/env bash
set -euo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$TASK_DIR/../../.." && pwd)"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
CODEX_BIN="${CODEX_BIN:-$(command -v codex)}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CODEX_ENV_FILE="${CODEX_ENV_FILE:-$CODEX_HOME/.env}"
RUN_ID="${RUN_ID:-codex-ridgecrest-catalog-$(date -u +%Y%m%dT%H%M%SZ)}"

if [ ! -x "$PYTHON" ]; then
  echo "Evaluation Python is not available: $PYTHON" >&2
  echo "Set PYTHON to a writable task environment such as seismoagent_eval." >&2
  exit 2
fi

if [ -d "$CODEX_BIN" ]; then CODEX_BIN="$CODEX_BIN/codex"; fi
if [ ! -x "$CODEX_BIN" ]; then
  echo "Codex executable is not available: $CODEX_BIN" >&2
  exit 2
fi

RUNTIME_ENV_FILE="$(mktemp)"
trap 'rm -f "$RUNTIME_ENV_FILE"' EXIT
if [ -f "$CODEX_ENV_FILE" ]; then cat "$CODEX_ENV_FILE" > "$RUNTIME_ENV_FILE"; fi
printf 'PATH=%s:/usr/bin:/bin\nPYTHON=%s\n' "$(dirname "$PYTHON")" "$PYTHON" >> "$RUNTIME_ENV_FILE"

cd "$PROJECT_DIR"
"$PYTHON" -m SeismoAgentBench run-codex \
  --task "$TASK_DIR/task.json" \
  --input "$TASK_DIR/input.json" \
  --agent-name codex-ridgecrest-catalog \
  --agent-version 1 \
  --run-root "$TASK_DIR/runs" \
  --run-id "$RUN_ID" \
  --agent-config "$PROJECT_DIR/SeismoAgentBench/configs/agents/codex.yaml" \
  --codex-bin "$CODEX_BIN" \
  --codex-home "$CODEX_HOME" \
  --env-file "$RUNTIME_ENV_FILE" \
  --prompt "Use the configured scientific Python environment. Network access and additional Python package installation are allowed in the designated evaluation environment; do not modify the original shared seismoagent environment. Write all results below \$BENCH_OUTPUT." \
  --timeout 3600
