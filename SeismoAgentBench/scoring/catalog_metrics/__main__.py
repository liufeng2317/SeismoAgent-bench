"""CLI: ``python -m SeismoAgentBench.scoring.catalog_metrics {baseline,run,summary} --task-dir T [--run-dir R]``."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .case import score_baseline, score_run
from .summary import summarize


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m SeismoAgentBench.scoring.catalog_metrics",
                                     description=__doc__)
    parser.add_argument("command", choices=("baseline", "run", "summary"))
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, help="runs/<variant>/<harness>/<model>/<run_id> (command run)")
    parser.add_argument("--rescore", action="store_true", help="summary: rescore every run first")
    args = parser.parse_args(argv)
    if args.command == "baseline":
        report = score_baseline(args.task_dir)
        summary = {k: v.get("headline") for k, v in report["rows"].items() if "headline" in v}
        summary["ceilings"] = {k: v["value"] for k, v in report["ceilings"].items()}
    elif args.command == "summary":
        report = summarize(args.task_dir, rescore=args.rescore)
        summary = [{**{k: c[k] for k in ("variant", "harness", "model", "launched", "completion_rate")},
                    **{k: (c["metrics"].get(k) or {}).get("mean")
                       for k in ("recall_norm", "union_support", "f1_M2", "f1_M3", "scatter_median_km")}}
                   for c in report["configurations"]]
    else:
        if args.run_dir is None:
            parser.error("run needs --run-dir")
        report = score_run(args.task_dir, args.run_dir)
        summary = {"completion": report["completion"], "headline": report["headline"]}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
