#!/usr/bin/env python3
"""Apply the 2026-11-04 rule "inside_region judges the share of events outside the station coverage".

For every scored run: computes ``out_of_coverage_fraction`` from work/catalog.csv (located events farther
than the buffer outside the hull of the case's supplied stations, ``coverage.py``), adds it to the stored
headline and recomputes the trust verdict from the stored headline (nothing else is rescored). Prints the
runs whose failed criteria changed. Run after ``baseline`` has been rescored. Usage: inside_region_coverage.py [--dry-run].
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from SeismoAgentBench.scoring.catalog_metrics.case import final_headline, load_case  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.coverage import outside_coverage, station_coverage  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.trust import trust_verdict  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cache = {}
    for path in sorted((ROOT / "workflows/tasks").glob("*/runs/**/evaluation/metrics.json")):
        task_dir = ROOT / "workflows/tasks" / path.relative_to(ROOT / "workflows/tasks").parts[0]
        if task_dir not in cache:
            cache[task_dir] = (final_headline(load_case(task_dir)), station_coverage(task_dir))
        final, cov = cache[task_dir]
        m = json.loads(path.read_text())
        head = m.get("headline") or {}
        catalog = path.parent.parent / "work" / "catalog.csv"
        if not head or not catalog.is_file():
            continue
        c = pd.read_csv(catalog, usecols=["latitude", "longitude"]).apply(pd.to_numeric, errors="coerce").dropna()
        head["out_of_coverage_fraction"] = round(float(outside_coverage(c.latitude, c.longitude, cov).mean()), 4) if len(c) else None
        before = sorted((m.get("trust") or {}).get("failed") or [])
        m["trust"] = trust_verdict(head, final, bool((m.get("completion") or {}).get("completed")))
        after = sorted(m["trust"]["failed"])
        if before != after:
            print(f"{path.parent.parent.relative_to(ROOT / 'workflows/tasks')}: out_of_coverage "
                  f"{head['out_of_coverage_fraction']} (mask {head.get('out_of_mask_fraction')}); "
                  f"removed {sorted(set(before) - set(after))} added {sorted(set(after) - set(before))}")
        if not a.dry_run:
            m.setdefault("migrations", []).append("2026-11-04 inside_region judged on the station coverage")
            path.write_text(json.dumps(m, indent=2) + "\n")


if __name__ == "__main__":
    main()
