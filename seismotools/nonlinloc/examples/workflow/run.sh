#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-/tmp/nonlinloc-workflow}"
exec python "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/run_workflow.py" "$OUT"
