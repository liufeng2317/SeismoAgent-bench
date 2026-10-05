#!/usr/bin/env python3
"""Thin Gamma-to-NonLinLoc example.
"""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from nonlinlocpy.gamma_nonlinloc import (  # noqa: E402
    ExampleRunResult,
    config_from_json,
    run_example_workflow,
)


CONFIG_PATH = Path(__file__).with_name("nonlinloc_config.json")


def run_case(config_path: str | Path = CONFIG_PATH) -> ExampleRunResult:
    config = config_from_json(config_path)
    result = run_example_workflow(config)
    if config.prepare_only:
        print("[INFO] Preparation finished. Skipping NonLinLoc execution.")
        return result
    print(
        "[INFO] Workflow result: "
        f"input_events={result.n_input_events} "
        f"located_events={result.n_located_events} "
        f"chunk_count={result.chunk_count}"
    )
    return result


if __name__ == "__main__":
    run_case()
