#!/usr/bin/env python3
"""How well does each judged checker threshold separate catalogs with an error from catalogs without it?

Data: the E1 runs of checker 1.3 (``outputs/checker_v13/<case>/summary.csv``: six human-in-loop location catalogs and
the completed Agent runs, with their reference-based trust verdicts) plus the development-loop runs (their own final
checker reports and scores). For each judged check, the catalogs are split by the trust criterion that the error the
check targets would fail (``TRUTH``): human-in-loop catalogs count as clean, runs as faulty when they fail that
criterion. Per check: the distributions (clean maximum, faulty minimum and median, passing-run maximum), the area under
the ROC curve of |measured| for faulty against the rest, the gap between the faulty minimum and the clean maximum, and
at the current threshold the false alarms on clean catalogs, the detections and the alarms on runs that pass. For the
checks that report a direction (S−P depth offset, Wadati origin offset), whether the sign agrees with the true bias.

Writes ``outputs/threshold_separation/separation.json`` and prints a table.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
E1 = HERE / "outputs/checker_v13"
OUT = HERE / "outputs/threshold_separation"
TASKS = ROOT / "workflows/tasks"

# check -> (criteria whose failure is the error it targets, threshold on |measured| (or the given side), direction truth)
TRUTH = {
    "magnitude_recompute": (["magnitude_offset"], 0.5, None),
    "largest_events_magnitude": (["magnitude_offset", "large_events_present"], 0.5, None),
    "magnitude_detection": (["magnitude_offset"], None, None),  # range [-2.3, 0.5], judged below
    "depth_single_value": (["depth_pileup"], 0.05, None),
    "depth_at_edges": (["depth_pileup"], 0.05, None),
    "depth_layers": (["depth_pileup"], 0.05, None),
    "sp_depth_offset": (["depth_bias"], 1.5, "dz_median_km"),
    "wadati_origin_offset": (["time_bias"], 1.5, "dt_median_s"),
    "wadati_origin_spread": (["time_spread", "time_bias"], 0.5, None),
    "isolated_events": (["off_structure", "horizontal_scatter"], 0.10, None),
    "events_with_few_picks": (["off_structure", "horizontal_scatter"], 0.20, None),
    "silent_stations": ([], 0.10, None),
    "duplicate_picks": ([], 0.02, None),
    "pick_onset_offset": ([], 0.2, None),
}


def trust(path: Path) -> dict | None:
    if not path.is_file():
        return None
    s = json.loads(path.read_text())
    t = s.get("trust") or {}
    if "completed" in (t.get("failed") or []):
        return None
    return {"failed": t.get("failed") or [], "headline": s.get("headline") or {}}


def e1_rows() -> list[dict]:
    t = pd.concat([pd.read_csv(f) for f in sorted(E1.glob("*/summary.csv"))], ignore_index=True)
    rows = []
    for (case, label), g in t.groupby(["case", "catalog"]):
        meas = dict(zip(g.check, pd.to_numeric(g.measured, errors="coerce")))
        if label.startswith("human_in_loop"):
            rows.append({"source": "human_in_loop", "case": case, "run": label, "failed": [], "headline": {}, **{f"m:{k}": v for k, v in meas.items()}})
            continue
        variant, run_id = label.split("@")[0].split("__")
        hits = list((TASKS / case / "evaluation/agents").glob(f"{variant}__*__{run_id}/scores.json"))
        tr = trust(hits[0]) if hits else None
        if tr:
            rows.append({"source": "e1_run", "case": case, "run": label.split("@")[0], **tr, **{f"m:{k}": v for k, v in meas.items()}})
    return rows


def dev_rows() -> list[dict]:
    rows = []
    for d in sorted(TASKS.glob("*/runs/dev_knowledge/claude/*/*")):
        if (d / "EXCLUDED.md").exists():
            continue
        case, rid = d.parts[-6], d.name
        tr = trust(next((TASKS / case / "evaluation/agents").glob(f"dev_knowledge__*__{rid}/scores.json"), Path("-")))
        rep = d / "work/checker/final/checker_report.json"
        if tr is None:  # a rescue score (products one level too deep)
            tr = trust(d / "evaluation/rescue/metrics.json")
            rep = d / "work/work/checker/final/checker_report.json"
        if tr is None or not rep.is_file():
            continue
        checks = json.loads(rep.read_text()).get("checks", [])
        meas = {c["id"]: c.get("measured") for c in checks}
        rows.append({"source": "dev_run", "case": case, "run": f"dev_knowledge {rid}", **tr,
                     **{f"m:{k}": (float(v) if isinstance(v, (int, float)) else np.nan) for k, v in meas.items()}})
    return rows


def auc(score: np.ndarray, pos: np.ndarray) -> float | None:
    if pos.sum() == 0 or (~pos).sum() == 0:
        return None
    r = pd.Series(score).rank().to_numpy()
    return round(float((r[pos].sum() - pos.sum() * (pos.sum() + 1) / 2) / (pos.sum() * (~pos).sum())), 3)


def main() -> None:
    df = pd.DataFrame(e1_rows() + dev_rows())
    res = {"catalogs": {k: int(v) for k, v in df.source.value_counts().items()}, "checks": {}}
    for check, (crit, thr, sign_key) in TRUTH.items():
        col = f"m:{check}"
        if col not in df:
            continue
        d = df[df[col].notna()].copy()
        v = d[col].to_numpy(dtype=float)
        a = np.abs(v) if check != "magnitude_detection" else np.maximum(-2.3 - v, v - 0.5)  # distance outside the range
        clean = (d.source == "human_in_loop").to_numpy()
        faulty = d.failed.apply(lambda f: any(c in f for c in crit)).to_numpy() & ~clean if crit else np.zeros(len(d), bool)
        passing = ~clean & ~faulty
        thr_eff = 0.0 if check == "magnitude_detection" else thr
        alarm = a > thr_eff
        entry = {"criteria": crit, "threshold": thr, "n": {"clean": int(clean.sum()), "faulty": int(faulty.sum()), "passing": int(passing.sum())},
                 "clean_max": round(float(a[clean].max()), 3) if clean.any() else None,
                 "faulty_min": round(float(a[faulty].min()), 3) if faulty.any() else None,
                 "faulty_median": round(float(np.median(a[faulty])), 3) if faulty.any() else None,
                 "passing_max": round(float(a[passing].max()), 3) if passing.any() else None,
                 "auc_faulty_vs_rest": auc(a, faulty) if crit else None,
                 "at_threshold": {"false_alarms_clean": int((alarm & clean).sum()), "detected_faulty": int((alarm & faulty).sum()),
                                  "alarms_on_passing": int((alarm & passing).sum())}}
        if entry["clean_max"] is not None and entry["faulty_min"] is not None:
            entry["gap"] = round(entry["faulty_min"] - entry["clean_max"], 3)
        if sign_key:  # does the flagged direction agree with the true bias? (catalog minus reference)
            truth = d.headline.apply(lambda h: h.get(sign_key)).astype(float).to_numpy()
            ok = np.isfinite(truth) & ~clean
            # sp_depth_offset > 0: S-P depths deeper than the catalog -> catalog too shallow (dz < 0); the Wadati offset
            # (data-implied origin minus catalog origin) > 0 -> catalog origin too early (dt < 0): both opposite in sign
            agree = np.sign(v[ok]) == -np.sign(truth[ok])
            big = np.abs(v[ok]) > thr
            entry["direction"] = {"runs": int(ok.sum()), "agree_all": round(float(agree.mean()), 3) if ok.any() else None,
                                  "above_threshold": int(big.sum()), "agree_above_threshold": round(float(agree[big].mean()), 3) if big.any() else None,
                                  "rank_corr_measured_vs_true_bias": round(float(pd.Series(v[ok]).corr(pd.Series(-truth[ok]), method="spearman")), 3) if ok.sum() > 3 else None}
        res["checks"][check] = entry
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "separation.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps(res["catalogs"]))
    for k, e in res["checks"].items():
        print(f"{k:26s} thr {e['threshold']} n {e['n']} clean_max {e['clean_max']} faulty_min {e['faulty_min']} med {e['faulty_median']} "
              f"passing_max {e['passing_max']} gap {e.get('gap')} AUC {e['auc_faulty_vs_rest']} at_thr {e['at_threshold']}"
              + (f" dir {e['direction']}" if "direction" in e else ""))


if __name__ == "__main__":
    main()
