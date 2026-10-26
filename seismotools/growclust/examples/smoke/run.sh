#!/usr/bin/env bash
# Synthetic 60-event cluster, catalog perturbed by 0.5 km, exact differential times;
# prints the recovered relative-location error (runs the validation's synthetic check).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PY="${PYTHON:-python}"
exec "$PY" - "$ROOT" <<'PYEOF'
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "seismotools/support/tools_usage_validation"))
import validate_growclust as v
with tempfile.TemporaryDirectory() as tmp:
    print(json.dumps(v.check_synthetic(Path(tmp)), indent=2))
PYEOF
