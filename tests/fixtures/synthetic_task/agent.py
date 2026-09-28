"""Deterministic agent used only by the framework smoke fixture."""

import json
import os
from pathlib import Path


output = Path(os.environ["BENCH_OUTPUT"])
output.mkdir(parents=True, exist_ok=True)
(output / "catalog.json").write_text(
    json.dumps({"events": [], "source": "synthetic-fixture"}, sort_keys=True) + "\n",
    encoding="utf-8",
)
