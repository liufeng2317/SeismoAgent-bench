#!/usr/bin/env bash
set -euo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$TASK_DIR/../.." && pwd)"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python}"
SEISMOAGENT_BIN="${SEISMOAGENT_BIN:-$(dirname "$PYTHON")}"
RUN_ID="${RUN_ID:-codex-phasepicking-$(date -u +%Y%m%dT%H%M%SZ)}"
CODEX_BIN="${CODEX_BIN:-$(command -v codex)}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CODEX_ENV_FILE="${CODEX_ENV_FILE:-$CODEX_HOME/.env}"
if [ -d "$CODEX_BIN" ]; then
  CODEX_BIN="$CODEX_BIN/codex"
fi
if [ ! -x "$CODEX_BIN" ]; then
  echo "Codex executable is not available: $CODEX_BIN" >&2
  exit 2
fi

# The framework deliberately starts agents with a minimal PATH.  Add the
# preconfigured scientific runtime for this task without changing the host
# environment or the input data.
RUNTIME_ENV_FILE="$(mktemp)"
trap 'rm -f "$RUNTIME_ENV_FILE"' EXIT
if [ -f "$CODEX_ENV_FILE" ]; then
  cat "$CODEX_ENV_FILE" > "$RUNTIME_ENV_FILE"
fi
printf 'PATH=%s:/usr/bin:/bin\nPYTHON=%s\n' "$SEISMOAGENT_BIN" "$PYTHON" >> "$RUNTIME_ENV_FILE"

cd "$PROJECT_DIR"
CODEX_ARGS=(
  --task "$TASK_DIR/task.json"
  --manifest "$TASK_DIR/input.json"
  --agent-name codex-phase-picking
  --agent-version 1
  --run-root "$TASK_DIR/runs"
  --run-id "$RUN_ID"
  --codex-bin "$CODEX_BIN"
  --codex-home "$CODEX_HOME"
  --env-file "$RUNTIME_ENV_FILE"
  --prompt "Use the preconfigured seismoagent Python environment (python/\$PYTHON) for ObsPy, NumPy, SciPy and Matplotlib. Do not install packages or use network access; write the requested artifacts under \$BENCH_OUTPUT."
  --timeout 3600
)

"$PYTHON" -m SeismoAgentBench run-codex "${CODEX_ARGS[@]}"
