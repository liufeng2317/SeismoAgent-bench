"""Complete score table across cases (docs/research/progress/SCORE_TABLE.md).

Built only from tracked outputs, so it can be regenerated after every run:
each case's ``evaluation/human_in_loop/metrics_baseline.json`` (references,
ceilings, the human-in-loop final) and ``evaluation/agents/<run>/scores.json``
(headline, trust verdict, swap, audit, process), plus ``metrics_summary.json``
for excluded runs. One table per dimension, rows = runs grouped by case with
the case's human-in-loop final first; a value that fails a trust criterion is
marked ✗ (docs/framework/02_Catalog_Metrics.md §7a).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import METRICS_VERSION
import yaml

from .case import AGENTS_DIR, BASELINE_FILE, CONFIG_FILE, EXPERT_DIR
from .matching import PRIMARY_GATES
from .summary import SUMMARY_FILE
from .trust import CRITERION_METRIC

# Case order follows the difficulty tiers (docs/research/00_Research_Plan.md §2.2).
CASES = [
    ("2011_prague_oklahoma", "Prague 2011", "basic"),
    ("2020_magna_utah", "Magna 2020", "basic"),
    ("2017_maple_creek_yellowstone", "Maple Creek 2017", "intermediate"),
    ("2018_kilauea_hawaii", "Kīlauea 2018", "intermediate"),
    ("2019_ridgecrest_california", "Ridgecrest 2019", "hard"),
    ("2016_kaikoura_new_zealand", "Kaikōura 2016", "hard"),
]
MARK = {"pass": "✓", "fail": "✗", "pending": "…"}
PICK_KEYS = ("pick_recall_P", "pick_recall_S", "pick_residual_mad_P_s", "pick_residual_mad_S_s")


def _load(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _fmt(value: Any, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        if isinstance(value, int) and not isinstance(value, bool):
            return f"{value:,}"
        if abs(value) >= 100:
            return f"{value:,.0f}"
        return f"{value:.{digits}f}"
    return str(value)


def _pct(value: Any) -> str:
    return "—" if value is None else f"{100 * value:.1f} %"


def _after_large(h: dict) -> float | None:
    after, other = h.get("recall_after_large"), h.get("recall_other")
    return after / other if after is not None and other else None


class Row:
    """One table row: the human-in-loop final or an Agent run (or its reference-only rescue)."""

    def __init__(self, label: str, headline: dict, trust: dict | None = None, extra: dict | None = None):
        self.label = label
        self.h = headline or {}
        self.trust = trust
        self.extra = extra or {}
        self.failed_metrics = set()
        for dim in ((trust or {}).get("dimensions") or {}).values():
            for name, check in dim["checks"].items():
                if check["verdict"] == "fail":
                    self.failed_metrics.add(CRITERION_METRIC.get(name, name))

    def cell(self, key: str, fmt: Callable = _fmt) -> str:
        value = _after_large(self.h) if key == "after_large" else self.h.get(key)
        text = fmt(value)
        return f"{text} ✗" if key in self.failed_metrics and value is not None else text


def _case_rows(task: Path) -> tuple[list[Row], dict | None, list]:
    baseline = _load(task / EXPERT_DIR / BASELINE_FILE)
    rows = []
    if baseline:
        rows.append(Row("human-in-loop final", baseline["rows"]["expert_final"]["headline"]))
    for scores in sorted((task / AGENTS_DIR).glob("*__*__*__*/scores.json")):
        s = _load(scores)
        run = s["run"]
        label = f"{run['variant']} ({run['harness']} × {run['model']}, {run['run_id']})"
        rows.append(Row(label, s.get("headline") or {}, s.get("trust"),
                        {"state": s.get("formal_state") or s.get("run_state"), "swap": s.get("swap"),
                         "audit": s.get("audit"), "process": s.get("process"),
                         "leakage": s.get("leakage_flag"), "completed": (s.get("completion") or {}).get("completed")}))
        rescue = s.get("rescue_reference_only")
        if rescue:
            rows.append(Row(f"{run['variant']} — rescue, reference only", rescue.get("headline") or {},
                            rescue.get("trust"), {"state": "not a formal result", "swap": rescue.get("swap")}))
    summary = _load(task / AGENTS_DIR / SUMMARY_FILE) or {}
    return rows, baseline, summary.get("excluded_runs", [])


def _table(header: list[str], body: list[list[str]]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + ["| " + " | ".join(r) + " |" for r in body]


def _dimension(cases: list, title: str, intro: str, columns: list[tuple[str, str, Callable]]) -> list[str]:
    body = []
    for name, rows in cases:
        for r in rows:
            body.append([name, r.label] + [r.cell(key, fmt) for _, key, fmt in columns])
    return [f"## {title}", "", intro, ""] + _table(["Case", "Catalog"] + [c[0] for c in columns], body) + [""]


def build(tasks_root: Path) -> str:
    cases, refs_body, verdict_body, picks_body, swap_body, process_body, excluded = [], [], [], [], [], [], []
    for case_id, name, tier in CASES:
        task = tasks_root / case_id
        rows, baseline, excl = _case_rows(task)
        cases.append((name, rows))
        excluded += [(name, e) for e in excl]
        if baseline:
            config = yaml.safe_load((task / "evaluation" / CONFIG_FILE).read_text(encoding="utf-8"))
            primary = tuple(config.get("primary_gates") or PRIMARY_GATES)
            for key, ref in baseline["references"].items():
                ceil = (baseline["ceilings"].get(key) or {})
                gates = ("|Δt| ≤ 1 s, time only" if ref["time_only"] else
                         f"{ref['gates'][0]:g} s / {ref['gates'][1]:g} km (own)" if ref["gates"] else
                         f"{primary[0]:g} s / {primary[1]:g} km")
                refs_body.append([name, tier, key, ref["roles"], _fmt(ref["events"]), gates,
                                  _fmt(ceil.get("value")), ceil.get("by") or "—"])
        agent_rows = [r for r in rows if r.label != "human-in-loop final"]
        for r in rows:  # the final first, then the runs
            if r.h.get("pick_recall_P") is not None:
                picks_body.append([name, r.label] + [_fmt(r.h.get(k)) for k in PICK_KEYS])
        if not agent_rows:
            verdict_body.append([name, "no scored formal run yet", "—", "—", "—", "—", "—", "—", "—"])
        for r in agent_rows:
            t = r.trust or {}
            dims = t.get("dimensions") or {}
            verdict_body.append([name, r.label, r.extra.get("state") or "—",
                                 {True: "**trusted**", False: "not trusted", None: "pending"}[t.get("trusted")]
                                 if t else "—"]
                                + [MARK.get((dims.get(d) or {}).get("verdict"), "—") for d in ("reality", "time", "space", "strength")]
                                + [", ".join(t.get("failed") or []) or "—"])
            swap = (r.extra.get("swap") or {}).get("rows") or {}
            for side, label in (("agent_locations", "Agent's own locations"), ("expert_locator", "Agent's picks, expert locator")):
                if side in swap:
                    v = swap[side]
                    swap_body.append([name, r.label, label] + [_fmt(v.get(k)) for k in
                                     ("recall_norm", "shift_final_km", "dz_final_km", "dt_final_s", "dt_median_s",
                                      "off_structure_fraction", "depth_mode_share")])
            p = r.extra.get("process")
            if p:
                a = r.extra.get("audit") or {}
                labels = a.get("labels") or {}
                process_body.append([name, r.label, _fmt((p.get("elapsed_s") or 0) / 3600, 1) if p.get("elapsed_s") else "—",
                                     _fmt(p.get("cost_usd")), _fmt(p.get("turns")),
                                     "yes" if r.extra.get("leakage") else "no",
                                     (f"{a['sampled']} of {a['unsupported']:,} unsupported events; "
                                      + ("labelled" if labels else "not labelled")) if a else "—"])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out = [
        "# Score table",
        "",
        f"Generated {now} by `python -m SeismoAgentBench.scoring.catalog_metrics table` from the tracked score files (catalog metrics v{METRICS_VERSION}); do not edit by hand. How each number is computed: [`../03_Scoring_Method.md`](../03_Scoring_Method.md); definitions: [`docs/framework/02_Catalog_Metrics.md`](../../framework/02_Catalog_Metrics.md).",
        "",
        "Rows are grouped by case in tier order; the first row of each case is the human-in-loop final, the upper bound every run is compared with (it has no values *against the final*). ✗ marks a value that fails a trusted-catalog criterion (§7a); ✓ / ✗ / … in the verdict table are pass / fail / pending (blind audit not labelled). Each configuration has one run so far.",
        "",
        "## 1. Trusted-catalog verdict",
        "",
        "The verdict judges whether the events are real and whether their time, space and strength are accurate and stable against the final; completeness is reported in §3 and not judged.",
        "",
    ]
    out += _table(["Case", "Run", "State", "Verdict", "Reality", "Time", "Space", "Strength", "Failed criteria"], verdict_body) + [""]
    out += ["## 2. References and ceilings", "",
            "Roles: D detection, L absolute location, S structure, M magnitude. Matching gates: the case's primary gates (2 s / 5 km; Kaikōura 4 s / 15 km), a reference's own gates where its origin times are coarse, or time only. The ceiling is the best chance-corrected recall another reference reaches; `recall_norm` divides by the primary detection reference's ceiling.", ""]
    out += _table(["Case", "Tier", "Reference", "Roles", "Events in mask", "Matching gates", "Ceiling", "Ceiling by"], refs_body) + [""]
    out += _dimension(cases, "3. Completeness (reported, not judged)",
                      "`recall_norm` against the primary detection reference (normalised by its ceiling); `recall_tight` the same at 1 s / 3 km; `recall_final` the share of the final's events recovered; `event_ratio_final` events relative to the final; F1 by magnitude class against the magnitude authority.",
                      [("recall_norm", "recall_norm", _fmt), ("recall (net)", "recall", _fmt), ("recall_tight", "recall_tight", _fmt),
                       ("recall_final", "recall_final", _fmt), ("event_ratio_final", "event_ratio_final", _fmt),
                       ("F1 M2+", "f1_M2", _fmt), ("F1 M3+", "f1_M3", _fmt), ("F1 M4+", "f1_M4", _fmt)])
    out += _dimension(cases, "4. Event reality",
                      "Share of rows outside the evaluation region, chance-corrected support by any reference or the final, the final's share of the run's events, and the audited false-event rate (blank until the blind review is labelled).",
                      [("outside region", "out_of_mask_fraction", _pct), ("union_support", "union_support", _fmt),
                       ("precision_final", "precision_final", _fmt), ("audited false rate", "audited_false_rate", _pct)])
    out += _dimension(cases, "5. Time",
                      "Against the final: median signed origin-time difference and its MAD (seconds). Against the primary location reference: median |Δt|. Detection after large events: recall within 1 h after M ≥ 4 relative to all other times.",
                      [("bias vs final (s)", "time_bias_final_s", _fmt), ("MAD vs final (s)", "time_mad_final_s", _fmt),
                       ("\\|Δt\\| vs ref (s)", "dt_median_s", _fmt), ("after large / other", "after_large", _fmt)])
    out += _dimension(cases, "6. Space",
                      "Against the final: common horizontal shift, scatter about it, median depth difference (km, positive = deeper). Against the primary location reference: shift, scatter and depth difference. Structure: share of epicentres > r_off from every structure reference. Depth pile-up: largest share at one depth value.",
                      [("shift vs final", "shift_final_km", _fmt), ("scatter vs final", "scatter_final_km", _fmt),
                       ("dz vs final", "dz_final_km", _fmt), ("shift vs ref", "shift_km", _fmt),
                       ("scatter vs ref", "scatter_median_km", _fmt), ("dz vs ref", "dz_median_km", _fmt),
                       ("off structure", "off_structure_fraction", _pct), ("depth pile-up", "depth_mode_share", _pct)])
    out += _dimension(cases, "7. Strength",
                      "Against the magnitude authority (the operational catalog; Cochran for Prague): median and spread of the magnitude difference, its slope against magnitude (negative = compressed scale), b-value difference, recall of M ≥ 4 events.",
                      [("dmag median", "dmag_median", _fmt), ("dmag std", "dmag_std", _fmt),
                       ("dmag slope", "dmag_slope_per_unit", _fmt), ("b difference", "b_difference", _fmt),
                       ("recall M4+", "recall_M4", _fmt)])
    out += ["## 8. Phase picks", "", "Against manual or correlation picks (Magna: Baker; Maple Creek: Shelly): share recovered within 0.5 s and residual MAD (s).", ""]
    out += _table(["Case", "Catalog", "recall P", "recall S", "MAD P (s)", "MAD S (s)"], picks_body) + [""]
    out += ["## 9. Component swap", "", "The run's own picks and associations relocated with the expert's velocity model and locator (no station delays): what remains is the front end (picks, association); what disappears was the back end (model, locator).", ""]
    out += _table(["Case", "Run", "Locations", "recall_norm", "shift vs final", "dz vs final", "\\|Δt\\| vs final", "\\|Δt\\| vs ref", "off structure", "depth pile-up"], swap_body) + [""]
    out += ["## 10. Process and audit", ""]
    out += _table(["Case", "Run", "Wall time (h)", "Cost (USD)", "Turns", "Leakage", "Blind audit"], process_body) + [""]
    if excluded:
        out += ["## 11. Excluded runs", "", "Runs stopped by a harness defect, not by the Agent; repeated after the fix (metrics §11).", ""]
        out += _table(["Case", "Run", "Reason"], [[n, e["run"], e["reason"]] for n, e in excluded]) + [""]
    return "\n".join(out)


def write_table(tasks_root: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build(tasks_root) + "\n", encoding="utf-8")
    return output
