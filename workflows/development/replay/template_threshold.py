#!/usr/bin/env python3
"""How much does template matching add, and what does its detection threshold cost? From the human-in-loop runs.

For each case, from the expert Match&Locate run behind the final (hil_relocation/cases/<case>.yaml) and its null run
(channels shifted by >= 600 s, stage 60 ``full_null*``):

- false fraction at threshold T (N x MAD): null detections per day >= T over real detections per day >= T;
- the final catalog thinned to its picked events plus the Match&Locate events with ``ml_nmad >= T``, scored by the
  scorer (recall against every detection reference, normalised recall, share of the final's events kept): what a pipeline
  with the same templates keeps at T; T = infinity is the final without template matching;
- the lowest T on the grid whose false fraction is <= 2 % (the knowledge skill's rule).

Also lists how the formal tools runs used template matching (from their work folders), for comparison.
Usage: template_threshold.py [case ...]. Writes outputs/template_threshold/<case>.json and summary.md.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from SeismoAgentBench.scoring.catalog_metrics.case import _expert, headline, load_case  # noqa: E402
from SeismoAgentBench.scoring.catalog_metrics.metrics import ceilings, score_population  # noqa: E402

OUT = HERE / "outputs/template_threshold"
HIL = ROOT / "workflows/development/hil_relocation/cases"
GRID = [8.0, 8.5, 9.0, 9.5, 10.0, 11.0, 12.0, 14.0, 16.3, 20.0, math.inf]
MAX_FALSE = 0.02
# how the formal tools runs used template matching (read from their work folders and REPORT.md, 2026-11-05)
AGENT_USE = {"2011_prague_oklahoma": "not run", "2018_kilauea_hawaii": "not run", "2016_kaikoura_new_zealand": "not run",
             "2017_maple_creek_yellowstone": "one-day pilot at 10 x MAD; the full run was prepared but not run",
             "2019_ridgecrest_california": "full run at 10 x MAD and CC >= 0.3; used as a completeness cross-check, no events added",
             "2020_magna_utah": "full run, merged at 10 x MAD and CC >= 0.3, kept only detections with a PhaseNet pick within 0.3 s: lowest kept 16.3 x MAD"}


def per_day(det: pd.DataFrame, t: float) -> float:
    days = det.segment.nunique() if len(det) else 1
    return float((det.nmad >= t).sum()) / max(days, 1)


def run_case(case: str) -> dict:
    task = ROOT / "workflows/tasks" / case
    hil = yaml.safe_load((HIL / f"{case}.yaml").read_text())
    full = task / Path(hil["templates"]).parent.parent
    nulls = sorted(p for p in full.parent.glob(full.name + "_null*") if (p / "run/detections.csv").is_file())
    real = pd.read_csv(full / "run/detections.csv")
    null = pd.concat([pd.read_csv(p / "run/detections.csv") for p in nulls], ignore_index=True) if nulls else pd.DataFrame(columns=["nmad", "segment"])
    c = load_case(task)
    ceil = ceilings(c.refs)
    spec = c.config["expert"]["final"]
    final = pd.read_csv(task / spec["path"], dtype=str, keep_default_na=False)
    is_ml = final.location_source.str.startswith("ml")
    nmad = pd.to_numeric(final.get("ml_nmad"), errors="coerce")
    tmp = OUT / case
    tmp.mkdir(parents=True, exist_ok=True)
    n_final = len(c.expert["final"].events)  # in the scoring mask
    rows = []
    for t in GRID:
        keep = ~is_ml | (nmad >= t)
        path = tmp / f"final_T{t:g}.csv"
        final[keep].to_csv(path, index=False)
        pop = _expert("expert_final", dict(spec, path=str(path)),  # absolute: task_dir / path keeps it
                      c.config, task, c.mask)
        s = score_population(pop, c.refs, expert=c.expert.get("final"), center=c.center,
                             off_structure_km=c.config["off_structure_km"], primary=c.primary, mask=c.mask,
                             yardstick=c.expert.get("final"))
        h = headline(s, c, ceil)
        r_null, r_real = per_day(null, t), per_day(real, t)
        rows.append({"T": t, "events": int(keep.sum()), "ml_events": int((is_ml & keep).sum()),
                     "recall_norm": h.get("recall_norm"), "final_share": round(len(pop.events) / n_final, 4),
                     **{k: v for k, v in h.items() if k.startswith("recall_ref_")},
                     "false_fraction": None if math.isinf(t) or not nulls else (round(r_null / r_real, 4) if r_real else None)})
        print(case, rows[-1], flush=True)
    passing = [r["T"] for r in rows if r["false_fraction"] is not None and r["false_fraction"] <= MAX_FALSE]
    res = {"case": case, "ml_run": str(full.relative_to(task)), "null_runs": [str(p.relative_to(task)) for p in nulls],
           "null_days": int(null.segment.nunique()) if len(null) else 0, "real_days": int(real.segment.nunique()),
           "final_events": int(len(final)), "final_ml_events": int(is_ml.sum()),
           "final_ml_nmad_min": round(float(nmad[is_ml].min()), 2) if is_ml.any() else None,
           "lowest_passing_T": min(passing) if passing else None, "agent_use": AGENT_USE.get(case), "rows": rows}
    (OUT / f"{case}.json").write_text(json.dumps(res, indent=1, default=float))
    for p in tmp.glob("final_T*.csv"):
        p.unlink()
    return res


def summary(results: list[dict]) -> str:
    lines = ["# Template matching: threshold, false detections and recall (generated by template_threshold.py)", ""]
    for r in results:
        lines.append(f"## {r['case']}")
        lines.append(f"Final: {r['final_events']} events, {r['final_ml_events']} from Match&Locate (lowest kept {r['final_ml_nmad_min']} x MAD); "
                     f"null days {r['null_days']} of {r['real_days']}; lowest threshold with false fraction <= {MAX_FALSE:.0%}: {r['lowest_passing_T']}. "
                     f"Agent tools run: {r['agent_use']}.")
        lines.append("")
        refs = sorted({k for row in r["rows"] for k in row if k.startswith("recall_ref_")})
        lines.append("| T | events | M&L | false | recall_norm | share of final | " + " | ".join(k.replace("recall_ref_", "") for k in refs) + " |")
        lines.append("|" + "---|" * (6 + len(refs)))
        for row in r["rows"]:
            f = "–" if row["false_fraction"] is None else f"{row['false_fraction']:.3f}"
            lines.append(f"| {'none' if math.isinf(row['T']) else row['T']} | {row['events']} | {row['ml_events']} | {f} | "
                         f"{row['recall_norm']} | {row['final_share']} | " + " | ".join(str(row.get(k)) for k in refs) + " |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="*", default=sorted(p.stem for p in HIL.glob("*.yaml")))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    res = [run_case(c) for c in a.cases]
    (OUT / "summary.md").write_text(summary(res))


if __name__ == "__main__":
    main()
