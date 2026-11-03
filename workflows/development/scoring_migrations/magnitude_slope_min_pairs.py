#!/usr/bin/env python3
"""Apply the 2026-11-04 rule "a magnitude-scale slope needs >= 30 matched pairs" to scored runs.

Rewrites evaluation/metrics.json in place: the slope is cleared when the strength pairs are fewer than
SLOPE_MIN_PAIRS, the headline gains dmag_pairs, and the trust verdict is recomputed from the stored headline
(nothing else is rescored, so the checker audit keeps the checker version the run used). Prints the runs
whose failed criteria changed. Usage: magnitude_slope_min_pairs.py [--dry-run].
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from SeismoAgentBench.scoring.catalog_metrics.case import final_headline, load_case  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.dimensions import SLOPE_MIN_PAIRS  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.trust import trust_verdict  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    finals = {}
    for path in sorted((ROOT / "workflows/tasks").glob("*/runs/**/evaluation/metrics.json")):
        task = path.relative_to(ROOT / "workflows/tasks").parts[0]
        if task not in finals:
            finals[task] = final_headline(load_case(ROOT / "workflows/tasks" / task))
        m = json.loads(path.read_text())
        strength = (m.get("scores") or {}).get("strength") or {}
        pairs = strength.get("pairs")
        head = m.get("headline") or {}
        if pairs is None or not head:
            continue
        head["dmag_pairs"] = pairs
        if pairs < SLOPE_MIN_PAIRS:
            strength["dmag_slope_per_unit"] = None
            head["dmag_slope_per_unit"] = None
        before = sorted((m.get("trust") or {}).get("failed") or [])
        m["trust"] = trust_verdict(head, finals[task], bool((m.get("completion") or {}).get("completed")))
        after = sorted(m["trust"]["failed"])
        if before != after:
            print(f"{path.parent.parent.relative_to(ROOT)}: pairs {pairs}; {before} -> {after}")
        if not a.dry_run:
            m.setdefault("migrations", []).append("2026-11-04 magnitude slope needs >= %d pairs" % SLOPE_MIN_PAIRS)
            path.write_text(json.dumps(m, indent=2) + "\n")


if __name__ == "__main__":
    main()
