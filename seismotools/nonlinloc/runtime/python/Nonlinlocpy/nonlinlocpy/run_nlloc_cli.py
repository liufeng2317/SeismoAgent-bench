#!/usr/bin/env python3
"""Minimal CLI around ``nonlinlocpy`` (native NLLOC_OBS + run)."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List

_DIR = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_ROOT = os.path.dirname(_DIR)
while _PACKAGE_ROOT in sys.path:
    sys.path.remove(_PACKAGE_ROOT)
sys.path.insert(0, _PACKAGE_ROOT)

try:  # pragma: no cover - import path depends on script/module execution style
    from .workflows import NLLocConfig, run_nlloc  # type: ignore
except ImportError:  # pragma: no cover
    from nonlinlocpy.workflows import NLLocConfig, run_nlloc  # type: ignore  # noqa: E402


DirectNLLocConfig = NLLocConfig


def run_direct_nlloc(config: DirectNLLocConfig) -> List[Dict[str, Any]]:
    """Backward-compatible wrapper around ``run_nlloc``.
    
    Args:
        config (DirectNLLocConfig): config.
    
    Returns:
        List[Dict[str, Any]]: Result returned by the function.
    """

    return run_nlloc(config)

def main() -> None:
    """CLI entry point for direct native/simple-pick NLLoc execution."""

    p = argparse.ArgumentParser(description="Run NLLoc with native NLLOC_OBS.")
    p.add_argument("--nlloc-bin", required=True, help="Directory with NLLoc executable")
    p.add_argument("--control-dir", required=True, help="Run directory (nlloc.in, obs/, loc/, …)")
    p.add_argument("--date", required=True, help="Reference time YYYYMMDDHHMM (12 digits)")
    p.add_argument(
        "--picks",
        help="Pick file: station_id phase time_sec per line (# comments ok)",
    )
    p.add_argument("--skip-obs", action="store_true", help="Do not write obs; use existing")
    p.add_argument("--skip-clear-loc", action="store_true", help="Do not clear loc/ before run")
    args = p.parse_args()

    try:
        solutions = run_direct_nlloc(DirectNLLocConfig(**vars(args)))
    except ValueError as exc:
        p.error(str(exc))
        return

    for sol in solutions:
        if "lat" in sol and "lon" in sol:
            print(sol)


if __name__ == "__main__":
    main()
