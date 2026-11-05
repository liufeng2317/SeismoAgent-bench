#!/usr/bin/env python3
"""Build the full-pipeline checker arms (S2c, S3) of every case from its tools arm (S1).

The formal comparison runs the whole pipeline (decided 2026-11-05: the detection gap sits in the front end, which
the back-end arms keep fixed). Each arm differs from the one before it by one factor, as in the back-end tier:

- ``tools`` (S1, existing): the seismotools library, ``TOOLS_BASE_PATH``; the checker is not in it;
- ``checker`` (S2c): + the catalog checker (``CHECKER_PATH``), the catalog-checker skill and the checker contract
  (checker report on the submitted products and a disposition per flag); built, run only for an ablation;
- ``knowledge`` (S3): + the catalog-knowledge skill and the magnitude resource (the main experiment).

The prompt is the case's ``prompt_tools.md`` with the checker section of the back-end builder inserted after
``### Tools`` and the two checker files added to the required outputs, so the checker is presented to the Agent in
the same words in both tiers. Writes per case, in ``workflows/tasks/<case>/``: ``prompt_<arm>.md``,
``task_<arm>.json``, ``input_<arm>.json`` and ``output_contract_checker.json`` (a copy of the back-end one).
Usage: ``python workflows/development/full_pipeline_variants/build_full_variants.py``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend_tier_b"))
from build_backend_variants import (CHECKER, CHECKER_SECTION, CONTRACT_EXTRA, FRONT_END_RUNS, KNOWLEDGE_SECTION,  # noqa: E402
                                    RESOURCE, TASKS)

ARMS = ("checker", "knowledge")
LABEL = {"checker": "minimal instructions, expert tools and catalog checker",
         "knowledge": "minimal instructions, expert tools, catalog checker and knowledge"}


def prompt(case: str, arm: str) -> str:
    text = (TASKS / case / "prompt_tools.md").read_text(encoding="utf-8")
    old_label = "(minimal instructions, expert tools)"
    assert old_label in text, case
    text = text.replace(old_label, f"({LABEL[arm]})", 1)
    section = (CHECKER_SECTION if arm == "checker" else KNOWLEDGE_SECTION).format(checker=CHECKER)
    i = text.index("### Required outputs")
    text = text[:i] + section.rstrip() + "\n\n" + text[i:]
    i, j = text.index("### Required outputs"), text.index("### Validity conditions")
    out = text[i:j].rstrip()
    out = out.replace("Write the following machine-readable files under the output directory.",
                      "Write the following machine-readable files under the output directory (two of them are described in the catalog-checker skill).")
    assert "catalog-checker skill" in out, case
    out += "\n" + CONTRACT_EXTRA
    return text[:i] + out + "\n" + text[j:]


def task_json(case: str, arm: str) -> dict:
    base = json.loads((TASKS / case / "task_tools.json").read_text())
    stem = base["task_id"].rsplit("_tools", 1)[0]
    differ = {"checker": "As the tools arm, plus the catalog checker (seismo_checker, CHECKER_PATH), the catalog-checker skill and the checker contract (checker report on the submitted products and a disposition per flag). Isolates the value of the checker over the whole pipeline (S2c).",
              "knowledge": "As the checker arm, plus the catalog-knowledge skill (pilot protocol, deciding between candidates, symptom playbook, errors no check sees) and the magnitude resource. Isolates the value of procedural knowledge over the whole pipeline (S3)."}[arm]
    return {**base, "task_id": f"{stem}_{arm}",
            "title": base["title"].replace("(minimal instructions with expert tools)", f"({LABEL[arm]})"),
            "summary": differ, "task_prompt_file": f"prompt_{arm}.md", "output_contract": "output_contract_checker.json"}


def input_json(case: str, arm: str) -> dict:
    base = json.loads((TASKS / case / "input.json").read_text())
    entries = list(base["entries"])
    if arm == "checker":
        entries.append({"id": "checker_skill", "path": str(RESOURCE / "skills/catalog-checker"), "type": "folder",
                        "notes": "The catalog-checker skill."})
    else:
        entries.append({"id": "agent_resource", "path": str(RESOURCE), "type": "folder",
                        "notes": "Skills (catalog-checker, catalog-knowledge) and the magnitude resource."})
    return {**base, "description": base["description"] + f" Full-pipeline arm {arm}.", "entries": entries}


def main() -> None:
    for case in FRONT_END_RUNS:
        d = TASKS / case
        for arm in ARMS:
            (d / f"prompt_{arm}.md").write_text(prompt(case, arm), encoding="utf-8")
            (d / f"task_{arm}.json").write_text(json.dumps(task_json(case, arm), indent=2, ensure_ascii=False) + "\n")
            (d / f"input_{arm}.json").write_text(json.dumps(input_json(case, arm), indent=2, ensure_ascii=False) + "\n")
        # task specs refer to their contracts by a non-traversing relative path, so the contract sits beside them
        (d / "output_contract_checker.json").write_text((d / "backend/output_contract_checker.json").read_text())
        print(case, "done")


if __name__ == "__main__":
    main()
