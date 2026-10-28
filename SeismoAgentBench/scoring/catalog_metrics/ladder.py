"""Expert ladder: every adopted expert round scored with metrics v1 (analysis, not a benchmark score).

``evaluation/expert/expert_ladder.yaml`` lists one catalog per adopted round in order,
with the step it added and its kind (start, location, detection, qc,
magnitude, dedupe). Each catalog is masked and scored exactly like the expert
rows of the baseline, so consecutive rows show what each expert step added -
the steps an Agent would have to reproduce to close a given gap.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .case import EXPERT_DIR, _expert, _scorer_record, _strip, headline, load_case
from .metrics import ceilings, score_population

LADDER_FILE = "expert_ladder.yaml"
OUTPUT_FILE = "expert_ladder.json"


def score_ladder(task_dir: Path, *, write: bool = True) -> dict:
    case = load_case(task_dir)
    steps = yaml.safe_load((case.task_dir / EXPERT_DIR / LADDER_FILE).read_text(encoding="utf-8"))["steps"]
    ceiling = ceilings(case.refs)
    rows = []
    for step in steps:
        pop = _expert(f"ladder_{step['round']}", step, case.config, case.task_dir, case.mask)
        score = _strip(score_population(pop, case.refs, expert=None, center=case.center,
                                        off_structure_km=case.config["off_structure_km"],
                                        primary=case.primary, mask=case.mask))
        rows.append({"round": step["round"], "step": step["step"], "kind": step["kind"], "path": step["path"],
                     "events": score["events"], "local_thickness_km": score["local_thickness_km"],
                     "headline": headline(score, case, ceiling)})
    report = {**_scorer_record(), "task": case.task_dir.name, "steps": rows}
    if write:
        (case.task_dir / EXPERT_DIR / OUTPUT_FILE).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return report
