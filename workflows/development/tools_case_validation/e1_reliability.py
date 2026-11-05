#!/usr/bin/env python3
"""E1 of the checker plan (register B5): false alarms and detection of checker 1.3, from validate_checker.py outputs.

Reads ``outputs/checker_v13/<case>/summary.csv`` (the checker as the contract runs it: ``--stage all`` with waveforms
and StationXML, no model ensemble) on the human-in-loop located catalog of each case and on every completed Agent
run, and the runs' trusted-catalog verdicts (``evaluation/agents/<run>/scores.json``, reference-based since
2026-11-05).

- False alarms: flags on the human-in-loop catalogs, which should be clean.
- Detection: for each trusted-catalog criterion, the runs that fail it and, among them, the runs on which at least
  one check that can see that kind of error flags (``SEES`` below; a judgement, recorded in the validation record);
  and flags of those checks on runs that pass the criterion.

Writes ``outputs/checker_v13/e1.json`` and ``docs/research/assets/checker_effect/e1_reliability.png``.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "outputs/checker_v13"
FIG = ROOT / "docs/research/assets/checker_effect/e1_reliability.png"
# criterion -> (checks that can see that kind of error from the catalog's own data, detectability layer)
SEES = {
    "magnitude_offset": ({"magnitude_recompute", "largest_events_magnitude", "magnitude_detection", "magnitude_range"}, "A"),
    "magnitude_spread": ({"magnitude_recompute", "magnitude_range", "largest_events_magnitude"}, "A"),
    "magnitude_scale": ({"magnitude_recompute", "magnitude_range", "largest_events_magnitude"}, "A"),
    "depth_pileup": ({"depth_single_value", "depth_at_edges", "depth_layers"}, "A"),
    "depth_bias": ({"sp_depth_offset", "depth_at_edges", "depth_layers", "depth_single_value"}, "C"),
    "time_bias": ({"wadati_origin_offset", "travel_time_intercept"}, "C"),
    "time_spread": ({"wadati_origin_spread"}, "B"),
    "horizontal_scatter": ({"isolated_events", "events_with_few_picks", "network_geometry"}, "B"),
    "off_structure": ({"isolated_events", "events_with_few_picks", "network_geometry"}, "B"),
    "horizontal_shift": (set(), "C"),
    "large_events_present": ({"largest_events_magnitude"}, "B"),
}
CASE_NAME = {"2011_prague_oklahoma": "Prague", "2020_magna_utah": "Magna", "2017_maple_creek_yellowstone": "Maple Creek",
             "2018_kilauea_hawaii": "Kīlauea", "2019_ridgecrest_california": "Ridgecrest", "2016_kaikoura_new_zealand": "Kaikōura"}


def failed_criteria(case: str, label: str) -> list[str] | None:
    variant, run_id = label.split("@")[0].split("__")
    for f in (ROOT / "workflows/tasks" / case / "evaluation/agents").glob(f"{variant}__*__{run_id}/scores.json"):
        s = json.loads(f.read_text())
        return (s.get("trust") or {}).get("failed")
    return None


def main() -> None:
    t = pd.concat([pd.read_csv(f) for f in sorted(OUT.glob("*/summary.csv"))], ignore_index=True)
    t["flag"] = t.flag.astype(str).str.lower().eq("true")
    flags = t[t.flag].groupby(["case", "catalog"]).check.apply(set).to_dict()
    hil = {CASE_NAME[c]: sorted(flags.get((c, "human_in_loop@all"), set())) for c in CASE_NAME}
    runs = []
    for (case, label), _ in t.groupby(["case", "catalog"]):
        if label.startswith("human_in_loop"):
            continue
        failed = failed_criteria(case, label)
        if failed is None or "completed" in failed:
            continue
        runs.append({"case": CASE_NAME[case], "run": label.split("@")[0], "failed": failed,
                     "flags": sorted(flags.get((case, label), set()))})
    detect = {}
    for crit, (checks, layer) in SEES.items():
        fail = [r for r in runs if crit in r["failed"]]
        ok = [r for r in runs if crit not in r["failed"]]
        detect[crit] = {"layer": layer, "checks": sorted(checks), "runs_failing": len(fail),
                        "detected": sum(bool(checks & set(r["flags"])) for r in fail),
                        "runs_passing": len(ok), "flagged_while_passing": sum(bool(checks & set(r["flags"])) for r in ok)}
    res = {"hil_false_alarms": hil, "hil_flags_per_case": {k: len(v) for k, v in hil.items()},
           "runs": runs, "detection": detect}
    (OUT / "e1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    # figure: left, flags on the human-in-loop catalogs; right, detection per criterion
    fig, (a, b) = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1, 2.2], "wspace": 0.35})
    names = list(hil)
    a.barh(names, [len(hil[n]) for n in names], color="#86b6ef")
    for i, n in enumerate(names):
        a.text(len(hil[n]) + 0.05, i, ", ".join(hil[n]) or "none", va="center", fontsize=6.5, color="#1f1f1e")
    a.set_title("Flags on the human-in-loop catalogs (false alarms)", fontsize=8.5, loc="left")
    a.set_xlim(0, max(4, max(len(v) for v in hil.values()) + 5))
    a.invert_yaxis()
    crits = [c for c in SEES if detect[c]["runs_failing"]]
    y = range(len(crits))
    b.barh(y, [detect[c]["runs_failing"] for c in crits], color="#e4e3de", label="runs failing the criterion")
    b.barh(y, [detect[c]["detected"] for c in crits], color="#2a78d6", label="... with a flag of a check that can see it")
    b.scatter([detect[c]["flagged_while_passing"] for c in crits], list(y), marker="x", color="#b8312f", zorder=3,
              label="runs passing the criterion but flagged")
    b.set_yticks(list(y), [f"{c} ({detect[c]['layer']})" for c in crits], fontsize=7)
    b.invert_yaxis()
    b.set_xlabel("runs", fontsize=7.5)
    b.set_title("Detection of the errors that fail a criterion (layer A visible, B separable, C invisible)", fontsize=8.5, loc="left")
    b.legend(fontsize=6.5, frameon=False, loc="lower right")
    fig.suptitle(f"Checker 1.3 as the contract runs it, on {len(runs)} completed Agent runs and six human-in-loop catalogs",
                 x=0.01, ha="left", fontsize=9)
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG, dpi=170, bbox_inches="tight")
    print(json.dumps({"hil": res["hil_flags_per_case"], "detection": {k: (v["detected"], v["runs_failing"], v["flagged_while_passing"]) for k, v in detect.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
