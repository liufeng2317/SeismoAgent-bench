#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
exec python "$ROOT/seismotools/nonlinloc/interface/run.py" \
  --input-dir "$ROOT/seismotools/nonlinloc/examples/smoke/inputs" \
  --output-dir "${1:-/tmp/nonlinloc-smoke}" \
  --bin-dir "$ROOT/seismotools/nonlinloc/runtime/bin"
