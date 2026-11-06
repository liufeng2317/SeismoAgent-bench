#!/usr/bin/env python3
"""Build the development-window arms of every case: ``dev_tools`` (S1) and ``dev_knowledge`` (S3).

The formal full-pipeline runs take 6-17 h each over 3-8 days of data, too slow to iterate on the checker and the
knowledge (decided 2026-11-07). The development loop runs the same arms over one day around the mainshock, from
2 h before to 22 h after it (``development_window`` in ``evaluation/metrics.yaml``, which also says how each anchor
was chosen). Each dev arm is its formal arm with only the processing window changed; the input is the same, and the
prompt already says that the input may contain waveforms beyond the window. The scorer recognises the ``dev_``
prefix and cuts the references and the human-in-loop catalogs to the window (``metrics_baseline_development.json``).

Writes per case, in ``workflows/tasks/<case>/``: ``prompt_dev_<arm>.md``, ``task_dev_<arm>.json`` and
``input_dev_<arm>.json``. Usage: ``python workflows/development/dev_window/build_dev_variants.py``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
TASKS = ROOT / "workflows/tasks"
CASES = ("2011_prague_oklahoma", "2020_magna_utah", "2017_maple_creek_yellowstone", "2018_kilauea_hawaii",
         "2019_ridgecrest_california", "2016_kaikoura_new_zealand")
ARMS = ("tools", "knowledge")
WINDOW = re.compile(r"Process the half-open window `\[[^\]]*\)`")


def build(case: str, arm: str) -> None:
    task = TASKS / case
    w = yaml.safe_load((task / "evaluation/metrics.yaml").read_text(encoding="utf-8"))["development_window"]
    text = (task / f"prompt_{arm}.md").read_text(encoding="utf-8")
    assert len(WINDOW.findall(text)) == 1, (case, arm)
    text = WINDOW.sub(f"Process the half-open window `[{w['start_utc']}, {w['end_utc']})`", text)
    (task / f"prompt_dev_{arm}.md").write_text(text, encoding="utf-8")
    base = json.loads((task / f"task_{arm}.json").read_text(encoding="utf-8"))
    spec = {**base, "task_id": f"{base['task_id']}_dev", "title": f"{base['title']} - development window",
            "summary": f"{base['summary']} Development loop: one day around the mainshock ({w['start_utc']} to {w['end_utc']}).",
            "task_prompt_file": f"prompt_dev_{arm}.md"}
    (task / f"task_dev_{arm}.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    src = task / f"input_{arm}.json"
    inp = json.loads((src if src.is_file() else task / "input.json").read_text(encoding="utf-8"))
    inp["description"] = inp["description"].rstrip(".") + f". Development window {w['start_utc']} to {w['end_utc']}."
    (task / f"input_dev_{arm}.json").write_text(json.dumps(inp, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    for case in CASES:
        for arm in ARMS:
            build(case, arm)
        print(case, "dev_tools, dev_knowledge")


if __name__ == "__main__":
    main()
