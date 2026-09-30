#!/usr/bin/env bash
# Default to direct downloads; explicit trailing options can override these defaults.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$(mktemp "$LOG_DIR/download_$(date -u +%Y%m%dT%H%M%SZ)_XXXXXX.log")"
{
  printf 'Log file: %s\n' "$LOG_FILE"
  "${PYTHON_BIN:-python}" -u -B "$SCRIPT_DIR/download_observations.py" --action download --direct "$@"
} 2>&1 | tee "$LOG_FILE"
