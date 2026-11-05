#!/usr/bin/env python3
"""Compare the checker reports of a current product and a candidate that would replace it.

Usage:
    compare.py --before checker/current/checker_report.json --after checker/candidate/checker_report.json \
        --change velocity_model [--output compare.json]

Run the checker with the same stage and the same inputs on both products first; only the product
that differs should change between the two runs. ``--change`` names what differs (velocity_model,
location_method, picks, association, event_selection, relocation, magnitude, other): checks known not
to rank that kind of change are listed but not counted.

Prints the verdict (better, worse, mixed, uncertain, no_difference) with the checks that improved and
worsened, and writes the full comparison as JSON. The verdict follows a rule fixed in advance (see
the ``rule`` field of the output); it says which product the checks prefer, not that either is right.
Exit code 0; 2 on unreadable reports.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))

from catalog_checker.compare import CHANGES, compare_reports  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--before", type=Path, required=True, help="checker_report.json of the current product")
    parser.add_argument("--after", type=Path, required=True, help="checker_report.json of the candidate")
    parser.add_argument("--change", choices=CHANGES, default="other", help="what differs between the two products")
    parser.add_argument("--output", type=Path, help="write the comparison here (JSON)")
    parser.add_argument("--config", type=Path, help="JSON overriding removed_share_max")
    args = parser.parse_args(argv)
    try:
        before, after = json.loads(args.before.read_text()), json.loads(args.after.read_text())
    except (OSError, ValueError) as exc:
        print(f"compare: cannot read reports: {exc}", file=sys.stderr)
        return 2
    config = json.loads(args.config.read_text()) if args.config else {}
    result = compare_reports(before, after, args.change, config)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"verdict: {result['verdict']} (change: {args.change}; events {result['events']['before']} -> {result['events']['after']})")
    for key in ("improved", "worsened", "not_counted"):
        for cid in result[key]:
            r = next(x for x in result["checks"] if x["id"] == cid)
            print(f"  {key:11s} {cid}: {r['before']} -> {r['after']} {r['unit']}" + (f"  ({r['not_counted']})" if key == "not_counted" else ""))
    for n in result["notes"]:
        print(f"  note: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
