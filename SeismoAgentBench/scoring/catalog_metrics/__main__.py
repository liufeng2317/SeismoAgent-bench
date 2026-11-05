"""CLI: ``python -m SeismoAgentBench.scoring.catalog_metrics {baseline,run,summary,audit,ladder,swap} --task-dir T [--run-dir R]``.

``table`` writes the complete score table across all cases (docs/research/progress/scores/SCORE_TABLE.md).

audit prepares the blind review of a scored run (evaluation/audit/); rerun ``run`` after labelling.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import prepare_review
from .case import score_baseline, score_run
from .ladder import score_ladder
from .swap import run_swap
from .table import write_table
from .summary import summarize


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m SeismoAgentBench.scoring.catalog_metrics",
                                     description=__doc__)
    parser.add_argument("command", choices=("baseline", "run", "summary", "audit", "ladder", "swap", "table"))
    parser.add_argument("--task-dir", type=Path, help="workflows/tasks/<case> (every command except table)")
    parser.add_argument("--tasks-root", type=Path, default=Path("workflows/tasks"), help="table: all task packages")
    parser.add_argument("--output", type=Path, default=Path("docs/research/progress/scores/SCORE_TABLE.md"), help="table: output file")
    parser.add_argument("--run-dir", type=Path, help="runs/<variant>/<harness>/<model>/<run_id> (command run)")
    parser.add_argument("--rescore", action="store_true", help="summary: rescore every run first")
    args = parser.parse_args(argv)
    if args.command == "table":
        print(write_table(args.tasks_root, args.output))
        return 0
    if args.task_dir is None:
        parser.error(f"{args.command} needs --task-dir")
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
    elif args.command == "ladder":
        report = score_ladder(args.task_dir)
        summary = [{"round": s["round"], "step": s["step"], "events": s["events"],
                    **{k: s["headline"].get(k) for k in ("recall_norm", "f1_M3", "scatter_median_km",
                                                         "off_structure_fraction", "dmag_std")}}
                   for s in report["steps"]]
    elif args.command == "swap":
        if args.run_dir is None:
            parser.error("swap needs --run-dir")
        summary = run_swap(args.task_dir, args.run_dir)
    elif args.command == "audit":
        if args.run_dir is None:
            parser.error("audit needs --run-dir")
        summary = prepare_review(args.run_dir.resolve(), args.task_dir.resolve())
    else:
        if args.run_dir is None:
            parser.error("run needs --run-dir")
        report = score_run(args.task_dir, args.run_dir)
        summary = {"completion": report["completion"], "headline": report["headline"]}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
