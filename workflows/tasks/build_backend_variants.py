#!/usr/bin/env python3
"""Build the back-end task variants (iteration tier B) for every case.

The Agent gets the picks and the pick-to-event association of a formal `tools` run (its own front
end) and does the back end only: absolute location, optional relative relocation, magnitudes. Three
arms differ by one factor each:

- ``backend``: tools only (back-end S1);
- ``backend_checker``: + the catalog-checker skill and the checker contract (back-end S2c);
- ``backend_knowledge``: + the catalog-checker and catalog-knowledge skills and the magnitude resource (back-end S3).

Writes per case: ``backend/frontend/{picks.csv,events.csv,README.md}`` (the CSVs are not tracked;
rerun this script to rebuild them from the run), ``input_<arm>.json``, ``prompt_<arm>.md``,
``task_<arm>.json``. Usage: ``python workflows/tasks/build_backend_variants.py``.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "workflows/tasks"
TOOLS = ROOT / "seismotools"
# the backend arm sees the tools without the checker (one factor per arm): a view with every tool but the checker
TOOLS_WITHOUT_CHECKER = ROOT / "workflows/tasks/_tool_views/without_checker"
RESOURCE = ROOT / "data/agent_resource"
FRONT_END_RUNS = {  # the formal tools run whose front end is reused
    "2011_prague_oklahoma": "tools/claude/glm-5.3/20261028T043719Z",
    "2016_kaikoura_new_zealand": "tools/claude/glm-5.3/20261029T183933Z",
    "2017_maple_creek_yellowstone": "tools/claude/glm-5.3/20261028T220746Z",
    "2018_kilauea_hawaii": "tools/claude/glm-5.3/20261029T084718Z",
    "2019_ridgecrest_california": "tools/claude/glm-5.3/20261029T203757Z",
    "2020_magna_utah": "tools/claude/glm-5.3/20261028T135931Z",
}
ARMS = ("backend", "backend_checker", "backend_knowledge")

TOOLS_SECTION = """### Tools

The tools base directory is TOOLS_BASE_PATH=`{tools}/`. The supplied implementations may be used through their standard execution paths. Before calling a tool, read its README, the relevant guidance under its `docs/` directory and the validated executable examples under its `examples/` directory, and use those materials to determine the method, parameters, input preparation and output interpretation.

1. Absolute location: NonLinLoc and HypoInverse produce absolute locations using an explicit velocity model. NonLinLoc is a probabilistic grid search with selectable likelihood methods (`GAU_ANALYTIC`, `EDT`, `EDT_OT_WT`) and has a single-event and a catalog interface; HypoInverse is a linearised locator with distance and residual weighting. Tool resources and documentation are under `TOOLS_BASE_PATH/nonlinloc/` and `TOOLS_BASE_PATH/hypoinverse/`.
2. Relative relocation: hypoDD and GrowClust produce relative locations when the associated events and differential times provide adequate support; waveform cross-correlation differential times can be measured with ccdt. This is an additional result, not a substitute for absolute locations. Tool resources and documentation are under `TOOLS_BASE_PATH/hypodd/`, `TOOLS_BASE_PATH/growclust/` and `TOOLS_BASE_PATH/cross_correlation/`.
3. Magnitudes are computed from the waveforms and the station metadata (instrument responses in the StationXML); no dedicated magnitude tool is provided.
"""

CHECKER_SECTION = """### Catalog checker

A reference-free catalog checker is provided at `TOOLS_BASE_PATH/checker/`. Read the skill `input/catalog-checker/SKILL.md` before you start: it says what the checker measures, when to run it, and what the output contract requires (the checker report on the submitted products and a disposition for every flag).
"""

KNOWLEDGE_SECTION = """### Catalog checker and knowledge

A reference-free catalog checker is provided at `TOOLS_BASE_PATH/checker/`. Two skills are under `input/agent_resource/skills/`; read each `SKILL.md` before you start and the files it points to when they apply:

- `catalog-checker/SKILL.md`: what the checker measures, when to run it, and what the output contract requires (the checker report on the submitted products and a disposition for every flag);
- `catalog-knowledge/SKILL.md`: how to test on a pilot batch before the full run, how to decide between two candidate products, what each checker symptom can mean and which experiment separates the causes, and which errors no check can see.

`input/agent_resource/magnitude/` holds the local-magnitude formulas with their units, a reference implementation and a library of regional calibrations.
"""

CONTRACT_EXTRA = """
`checker/final/checker_report.json` and `checker/dispositions.json` — as described in the catalog-checker skill.
"""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frontend(case: str) -> Path:
    run = TASKS / case / "runs" / FRONT_END_RUNS[case] / "work"
    out = TASKS / case / "backend/frontend"
    out.mkdir(parents=True, exist_ok=True)
    picks = pd.read_csv(run / "picks.csv", dtype=str, keep_default_na=False)
    picks.to_csv(out / "picks.csv", index=False)
    live = picks[(picks.status.str.lower() != "rejected") & (picks.event_id != "")]
    phase = live.phase.str.upper().str[0]
    ev = pd.DataFrame({"n_picks": live.groupby("event_id").size(),
                       "n_p_picks": live[phase == "P"].groupby("event_id").size(),
                       "n_s_picks": live[phase == "S"].groupby("event_id").size()}).fillna(0).astype(int)
    ev.index.name = "event_id"
    ev.reset_index().to_csv(out / "events.csv", index=False)
    (out / "README.md").write_text(
        "# Front end for the back-end task\n\n"
        "Phase picks and their association to events from an automatic picking and association run on this case's waveforms "
        "(PhaseNet picks; association by an automatic associator). They are fixed for the back-end task.\n\n"
        f"- `picks.csv`: {len(picks):,} picks in the output-contract columns; `event_id` gives the association (empty: unassociated); "
        f"rows with status `rejected` were rejected by that run. SHA-256 {sha256(out / 'picks.csv')}.\n"
        f"- `events.csv`: the {len(ev):,} associated events with their numbers of non-rejected picks. No locations, origin times or magnitudes are given.\n\n"
        f"Built by `workflows/tasks/build_backend_variants.py` from `runs/{FRONT_END_RUNS[case]}/work/picks.csv` (the CSV files are not tracked).\n",
        encoding="utf-8")
    return out


def prompt(case: str, arm: str) -> str:
    tools_prompt = (TASKS / case / "prompt_tools.md").read_text(encoding="utf-8")
    title = re.search(r"^## (.+?) \(minimal instructions, expert tools\)", tools_prompt, re.M).group(1)
    window = re.search(r"Process the half-open window `([^`]+)`", tools_prompt).group(1)
    outputs = tools_prompt[tools_prompt.index("### Required outputs"):tools_prompt.index("### Validity conditions")]
    validity = tools_prompt[tools_prompt.index("### Validity conditions"):]
    label = {"backend": "back end, expert tools", "backend_checker": "back end, expert tools and catalog checker",
             "backend_knowledge": "back end, expert tools, catalog checker and knowledge"}[arm]
    text = [f"## {title} ({label})", "", "### Objective", "",
            f"Phase picks and their association to events are given for the {title.split(' sequence')[0]} sequence. Using them, the supplied "
            "waveform data and station metadata, complete the earthquake catalog: locate every event, add relative relocations where "
            "the data support them, and compute magnitudes.", "",
            "The run-local input is available under `input/`: `input/waveforms/` (`data/` for waveforms, `stations/` for station metadata) "
            "and `input/frontend/` (`picks.csv` with the association in `event_id`, `events.csv` listing the events, `README.md`).", "",
            f"Process the half-open window `{window}`; the catalog reports events with origin time inside it.", "",
            "The picks are fixed: do not add picks or change pick times. You may reject picks (status `rejected`, kept in the file) and "
            "reject events (status `rejected`); every submitted pick keeps its `pick_id`, and every event keeps its `event_id`.", "",
            TOOLS_SECTION.format(tools=TOOLS_WITHOUT_CHECKER if arm == "backend" else TOOLS)]
    if arm == "backend_checker":
        text.append(CHECKER_SECTION)
    if arm == "backend_knowledge":
        text.append(KNOWLEDGE_SECTION)
    out = outputs.rstrip()
    if arm != "backend":
        out = out.replace("Write the following machine-readable files under the output directory.",
                          "Write the following machine-readable files under the output directory (two of them are described in the catalog-checker skill).")
        out += "\n" + CONTRACT_EXTRA
    text += [out, "", validity.rstrip(), ""]
    return "\n".join(text)


def task_json(case: str, arm: str) -> dict:
    base = json.loads((TASKS / case / "task_tools.json").read_text())
    stem = base["task_id"].rsplit("_tools", 1)[0]
    differ = {"backend": "Back-end arm (iteration tier B): the picks and association of a formal tools run are given and fixed; the Agent locates, relocates and computes magnitudes with the location and relocation tools.",
              "backend_checker": "As backend, plus the catalog-checker skill and the checker contract (checker report on the submitted products and a disposition per flag). Isolates the value of the checker on the back end.",
              "backend_knowledge": "As backend_checker, plus the catalog-knowledge skill (pilot protocol, deciding between candidates, symptom playbook, errors no check sees) and the magnitude resource. Isolates the value of procedural knowledge on the back end."}[arm]
    return {**base, "task_id": f"{stem}_{arm}", "title": base["title"].replace("(minimal instructions with expert tools)", f"({arm.replace('_', ' ')})"),
            "summary": differ, "task_prompt_file": f"prompt_{arm}.md",
            "output_contract": "output_contract_min.json" if arm == "backend" else "output_contract_checker.json",
            "software": ["Python", "ObsPy", "NonLinLoc", "HypoInverse", "hypoDD", "GrowClust"],
            "taxonomy": {**base["taxonomy"], "task_type": "catalog_back_end", "scope": "back_end"},
            "input_requirements": base["input_requirements"] + [{"id": "phase_picks", "data_type": "catalog", "format": "CSV", "required": True}]}


def input_json(case: str, arm: str) -> dict:
    base = json.loads((TASKS / case / "input.json").read_text())
    entries = list(base["entries"]) + [{"id": "frontend_picks", "path": str(TASKS / case / "backend/frontend"), "type": "folder",
                                        "notes": "Fixed picks and association (picks.csv, events.csv)."}]
    if arm == "backend_checker":
        entries.append({"id": "checker_skill", "path": str(RESOURCE / "skills/catalog-checker"), "type": "folder",
                        "notes": "The catalog-checker skill."})
    if arm == "backend_knowledge":
        entries.append({"id": "agent_resource", "path": str(RESOURCE), "type": "folder",
                        "notes": "Skills (catalog-checker, catalog-knowledge) and the magnitude resource."})
    return {**base, "description": base["description"] + f" Back-end arm {arm}: adds the fixed front end.", "entries": entries}


def main() -> None:
    for case in FRONT_END_RUNS:
        frontend(case)
        for arm in ARMS:
            (TASKS / case / f"prompt_{arm}.md").write_text(prompt(case, arm), encoding="utf-8")
            (TASKS / case / f"task_{arm}.json").write_text(json.dumps(task_json(case, arm), indent=2, ensure_ascii=False) + "\n")
            (TASKS / case / f"input_{arm}.json").write_text(json.dumps(input_json(case, arm), indent=2, ensure_ascii=False) + "\n")
        print(case, "done")


if __name__ == "__main__":
    main()
