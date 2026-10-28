#!/usr/bin/env bash
set -euo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$TASK_DIR/../../.." && pwd)"
VARIANT="${VARIANT:-min}"
AGENT="${AGENT:-claude}"  # formal runs: Claude Code x GLM (configs/agents/claude.yaml)
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
# Any packaged variant: task_<variant>.json in this directory.
TASK_FILE="$TASK_DIR/task_${VARIANT}.json"
if [ ! -f "$TASK_FILE" ]; then
  echo "VARIANT must be the stem of an existing task_<variant>.json (min, tools, guided)" >&2
  exit 2
fi
AGENT_NAME="${AGENT}-magna-${VARIANT}"
AGENT_CONFIG="$PROJECT_DIR/SeismoAgentBench/configs/agents/${AGENT}.yaml"
# Experiment factors map one-to-one onto path segments:
# runs/<variant>/<harness>/<model>/<timestamp>. The model segment defaults
# to the agent config's model line; CLAUDE_MODEL / CODEX_MODEL override it
# (and are passed to the CLI as --model). It must stay path-safe.
if [ "$AGENT" = "claude" ]; then
  MODEL="${CLAUDE_MODEL:-$(awk '$1=="model:"{print $2; exit}' "$AGENT_CONFIG")}"
else
  MODEL="${CODEX_MODEL:-$(awk '$1=="model:"{print $2; exit}' "$AGENT_CONFIG")}"
fi
if [ -z "$MODEL" ]; then
  echo "Could not resolve the model for $AGENT from $AGENT_CONFIG" >&2
  exit 2
fi
RUN_ROOT="$TASK_DIR/runs/$VARIANT/$AGENT/$MODEL"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
# The tools variant drives multi-hour science stages (picking, association,
# location) over an eight-day window (~2x the Ridgecrest data volume); it
# gets a 48 h budget by default while other variants keep 24 h.
case "$VARIANT" in
  tools) DEFAULT_TIMEOUT=172800 ;;
  *) DEFAULT_TIMEOUT=86400 ;;
esac
TIMEOUT="${TIMEOUT:-$DEFAULT_TIMEOUT}"
# DETACH=1 (default) runs the runner in its own session so a closed terminal
# cannot SIGHUP it mid-run; the run still streams to record/execution.log.
# DETACH=0 keeps the previous attached, streaming behavior.
DETACH="${DETACH:-1}"

if [ ! -x "$PYTHON" ]; then
  echo "Evaluation Python is not available: $PYTHON" >&2
  echo "Set PYTHON to a writable task environment such as seismoagent_eval." >&2
  exit 2
fi

RUNTIME_ENV_FILE="$(mktemp)"
trap 'rm -f "$RUNTIME_ENV_FILE"' EXIT

if [ "$AGENT" = "claude" ]; then
  # Claude Code authenticates from the env file below (ANTHROPIC_BASE_URL /
  # ANTHROPIC_AUTH_TOKEN, for example a GLM Anthropic-compatible endpoint).
  # CLAUDE_EXTRA_PATH optionally adds directories (for example a node
  # installation) to the sanitized run PATH.
  CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || true)}"
  if [ -z "$CLAUDE_BIN" ]; then
    # Fallback: the Cursor-bundled Claude Code binary, which is not on PATH.
    # sort -V picks the newest extension version, so extension updates keep
    # resolving without touching this script.
    CLAUDE_BIN="$(ls -d "$HOME"/.cursor-server/extensions/anthropic.claude-code-*-linux-*/resources/native-binary 2>/dev/null | sort -V | tail -n 1)"
  fi
  if [ -d "$CLAUDE_BIN" ]; then CLAUDE_BIN="$CLAUDE_BIN/claude"; fi
  if [ ! -x "$CLAUDE_BIN" ]; then
    echo "Claude executable is not available: $CLAUDE_BIN" >&2
    exit 2
  fi
  CLAUDE_ENV_FILE="${CLAUDE_ENV_FILE:-$PROJECT_DIR/SeismoAgentBench/configs/agents/claude.env}"
  if [ ! -f "$CLAUDE_ENV_FILE" ]; then
    echo "Claude env file is not available: $CLAUDE_ENV_FILE" >&2
    echo "Provide ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN (chmod 600, git-ignored)." >&2
    exit 2
  fi
  cat "$CLAUDE_ENV_FILE" > "$RUNTIME_ENV_FILE"
  AGENT_PATH="$(dirname "$CLAUDE_BIN"):$(dirname "$PYTHON")"
  if [ -n "${CLAUDE_EXTRA_PATH:-}" ]; then AGENT_PATH="$CLAUDE_EXTRA_PATH:$AGENT_PATH"; fi
  printf 'PATH=%s:/usr/bin:/bin\nPYTHON=%s\n' "$AGENT_PATH" "$PYTHON" >> "$RUNTIME_ENV_FILE"
else
  CODEX_BIN="${CODEX_BIN:-$(command -v codex)}"
  CODEX_HOME="${CODEX_HOME:-$PROJECT_DIR/SeismoAgentBench/configs/agents/codex_home}"
  CODEX_ENV_FILE="${CODEX_ENV_FILE:-$CODEX_HOME/.env}"
  if [ -d "$CODEX_BIN" ]; then CODEX_BIN="$CODEX_BIN/codex"; fi
  if [ ! -x "$CODEX_BIN" ]; then
    echo "Codex executable is not available: $CODEX_BIN" >&2
    exit 2
  fi
  if [ -f "$CODEX_ENV_FILE" ]; then cat "$CODEX_ENV_FILE" > "$RUNTIME_ENV_FILE"; fi
  printf 'PATH=%s:/usr/bin:/bin\nPYTHON=%s\n' "$(dirname "$PYTHON")" "$PYTHON" >> "$RUNTIME_ENV_FILE"
fi

cd "$PROJECT_DIR"
if [ "$AGENT" = "claude" ]; then
  CLAUDE_ARGS=(--claude-bin "$CLAUDE_BIN" --env-file "$RUNTIME_ENV_FILE"
    --agent-config "$AGENT_CONFIG")
  if [ -n "${CLAUDE_MODEL:-}" ]; then CLAUDE_ARGS+=(--model "$CLAUDE_MODEL"); fi
  if [ -n "${CLAUDE_MAX_TURNS:-}" ]; then CLAUDE_ARGS+=(--max-turns "$CLAUDE_MAX_TURNS"); fi
  CMD=("$PYTHON" -m SeismoAgentBench run-claude \
    --task "$TASK_FILE" \
    --input "$TASK_DIR/input.json" \
    --agent-name "$AGENT_NAME" \
    --agent-version 1 \
    --run-root "$RUN_ROOT" \
    --run-id "$RUN_ID" \
    --environment-config "$PROJECT_DIR/SeismoAgentBench/configs/environments/seismoagent_eval.yaml" \
    "${CLAUDE_ARGS[@]}" \
    --prompt "Use the Python executable and Conda environment reported in the runtime context for scientific processing. Network access and package installation follow the configured runtime policy; do not modify the original shared seismoagent environment. Write all results below \$BENCH_OUTPUT." \
    --timeout "$TIMEOUT")
else
  CODEX_ARGS=(--codex-bin "$CODEX_BIN" --codex-home "$CODEX_HOME"
    --env-file "$RUNTIME_ENV_FILE")
  if [ -n "${CODEX_MODEL:-}" ]; then CODEX_ARGS+=(--model "$CODEX_MODEL"); fi
  CMD=("$PYTHON" -m SeismoAgentBench run-codex \
    --task "$TASK_FILE" \
    --input "$TASK_DIR/input.json" \
    --agent-name "$AGENT_NAME" \
    --agent-version 1 \
    --run-root "$RUN_ROOT" \
    --run-id "$RUN_ID" \
    --agent-config "$AGENT_CONFIG" \
    --environment-config "$PROJECT_DIR/SeismoAgentBench/configs/environments/seismoagent_eval.yaml" \
    "${CODEX_ARGS[@]}" \
    --prompt "Use the Python executable and Conda environment reported in the runtime context for scientific processing. Network access and package installation follow the configured runtime policy; do not modify the original shared seismoagent environment. Write all results below \$BENCH_OUTPUT." \
    --timeout "$TIMEOUT")
fi

if [ "$DETACH" != "1" ]; then
  "${CMD[@]}"
  exit $?
fi

mkdir -p "$RUN_ROOT"
RUNNER_LOG="$RUN_ROOT/runner-$RUN_ID.log"
setsid nohup "${CMD[@]}" >"$RUNNER_LOG" 2>&1 </dev/null &
# The runtime env file carries credentials and is deleted by the EXIT trap.
# Stay around until the runner has consumed it and started the agent
# (record/runner.pid appears) before letting that trap fire.
for _ in $(seq 1 180); do
  if [ -f "$RUN_ROOT/$RUN_ID/record/runner.pid" ]; then break; fi
  sleep 1
done
RUNNER_PID="$(sed -n 's/.*"pid": *\([0-9][0-9]*\).*/\1/p' "$RUN_ROOT/$RUN_ID/record/runner.pid" 2>/dev/null || true)"
echo "detached runner for run $RUN_ID"
echo "  runner pid : ${RUNNER_PID:-unknown (see $RUNNER_LOG)}"
echo "  runner log : $RUNNER_LOG"
echo "  live events: tail -f $RUN_ROOT/$RUN_ID/record/execution.log"
echo "  probe      : $PYTHON -m SeismoAgentBench status --run-dir $RUN_ROOT/$RUN_ID"
