#!/usr/bin/env bash
set -euo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$TASK_DIR/../../.." && pwd)"
VARIANT="${VARIANT:-base}"
AGENT="${AGENT:-codex}"
PYTHON="${PYTHON:-/liufeng1afs/software/miniconda3/envs/seismoagent_eval/bin/python}"
case "$VARIANT" in
  base) TASK_FILE="$TASK_DIR/task.json" ;;
  tools) TASK_FILE="$TASK_DIR/task_tools.json" ;;
  *)
    # Any additional packaged variant: task_<variant>.json in this directory.
    CANDIDATE="$TASK_DIR/task_${VARIANT}.json"
    if [ -f "$CANDIDATE" ]; then
      TASK_FILE="$CANDIDATE"
    else
      echo "VARIANT must be base, tools, or an existing task_<variant>.json stem" >&2
      exit 2
    fi
    ;;
esac
AGENT_NAME="${AGENT}-ridgecrest-${VARIANT}"
RUN_ROOT="$TASK_DIR/runs/$VARIANT"
RUN_ID="${RUN_ID:-$AGENT_NAME-$(date -u +%Y%m%dT%H%M%SZ)}"
TIMEOUT="${TIMEOUT:-86400}"

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
  CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude)}"
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
    --agent-config "$PROJECT_DIR/SeismoAgentBench/configs/agents/claude.yaml")
  if [ -n "${CLAUDE_MODEL:-}" ]; then CLAUDE_ARGS+=(--model "$CLAUDE_MODEL"); fi
  if [ -n "${CLAUDE_MAX_TURNS:-}" ]; then CLAUDE_ARGS+=(--max-turns "$CLAUDE_MAX_TURNS"); fi
  "$PYTHON" -m SeismoAgentBench run-claude \
    --task "$TASK_FILE" \
    --input "$TASK_DIR/input.json" \
    --agent-name "$AGENT_NAME" \
    --agent-version 1 \
    --run-root "$RUN_ROOT" \
    --run-id "$RUN_ID" \
    --environment-config "$PROJECT_DIR/SeismoAgentBench/configs/environments/seismoagent_eval.yaml" \
    "${CLAUDE_ARGS[@]}" \
    --prompt "Use the Python executable and Conda environment reported in the runtime context for scientific processing. Network access and package installation follow the configured runtime policy; do not modify the original shared seismoagent environment. Write all results below \$BENCH_OUTPUT." \
    --timeout "$TIMEOUT"
else
  "$PYTHON" -m SeismoAgentBench run-codex \
    --task "$TASK_FILE" \
    --input "$TASK_DIR/input.json" \
    --agent-name "$AGENT_NAME" \
    --agent-version 1 \
    --run-root "$RUN_ROOT" \
    --run-id "$RUN_ID" \
    --agent-config "$PROJECT_DIR/SeismoAgentBench/configs/agents/codex.yaml" \
    --environment-config "$PROJECT_DIR/SeismoAgentBench/configs/environments/seismoagent_eval.yaml" \
    --codex-bin "$CODEX_BIN" \
    --codex-home "$CODEX_HOME" \
    --env-file "$RUNTIME_ENV_FILE" \
    --prompt "Use the Python executable and Conda environment reported in the runtime context for scientific processing. Network access and package installation follow the configured runtime policy; do not modify the original shared seismoagent environment. Write all results below \$BENCH_OUTPUT." \
    --timeout "$TIMEOUT"
fi
