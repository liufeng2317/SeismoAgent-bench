#!/usr/bin/env python3
"""Thin standard/native NonLinLoc example.

Reusable workflow logic lives in ``nonlinlocpy.standard_nonlinloc``. This file
loads a JSON config and calls the package API. No CLI is provided here.
"""

from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from nonlinlocpy.standard_nonlinloc import (  # noqa: E402
    StandardRunResult,
    config_from_json,
    run_standard_workflow,
)


CONFIG_PATH = Path(__file__).with_name("nonlinloc_config.json")


def run_case(config_path: str | Path = CONFIG_PATH) -> StandardRunResult:
    config = config_from_json(config_path)
    result = run_standard_workflow(config)
    if config.prepare_only:
        print("[INFO] Preparation finished. Skipping NonLinLoc execution.")
        return result
    print(
        "[INFO] Workflow result: "
        f"located_events={result.n_located_events} "
        f"located_csv={result.located_csv}"
    )
    return result


if __name__ == "__main__":
    run_case()
