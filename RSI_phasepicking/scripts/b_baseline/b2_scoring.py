"""b2: score the b1 runs against the analyst's manual picks and the analyst-pick locations.

For each method in --methods, takes its associated picks from
results/b_baseline/b1_pipeline/<method>/4_association/picks_associated.csv,
pairs them with the manual picks (scoring.match), and writes:
scorecard.csv (P and S metrics with 95% event-bootstrap intervals),
strata.csv (by analyst weight code and by channel), matched_<method>.csv,
location_vs_B8.csv, and the figures residuals.png, scorecard.png, strata.png,
location_vs_B8.png under results/b_baseline/b2_scoring/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/, for paths.py; part-b modules sit beside this file
import argparse
import json
import shutil

import pandas as pd

import pipeline as pl
import scoring
import viz
from paths import RES_B

WEIGHT_GROUPS = {0: "0–1", 1: "0–1", 2: "2–3", 3: "2–3"}  # code 3 is rare (3 picks)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--methods", default="B0,B1")
    ap.add_argument("--tol-p", type=float, default=scoring.TOLERANCE_S["P"])
    ap.add_argument("--tol-s", type=float, default=scoring.TOLERANCE_S["S"])
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    out = RES_B / "b2_scoring"
    if out.exists():
        if not args.overwrite:
            sys.exit(f"{out} exists; use --overwrite")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    tol = {"P": args.tol_p, "S": args.tol_s}
    _, _, ref = pl.load_batch()
    ref = ref.copy()
    ref["family"] = ref.channel.str[:2]

    run = RES_B / "b1_pipeline"
    card, strata, scored_all = [], [], {}
    for m in args.methods.split(","):
        picks = pd.read_csv(run / m / "4_association" / "picks_associated.csv")
        picks = picks[picks.assignment_status == "assigned"]
        scored, in_cell = scoring.match(picks, ref, tol)
        scored = scored.merge(ref[["event_id", "station", "phase", "family"]].drop_duplicates(
            ["event_id", "station", "phase"]), on=["event_id", "station", "phase"], how="left")
        scored.to_csv(out / f"matched_{m}.csv", index=False)
        scored_all[m] = scored
        for ph in ("P", "S"):
            s, c = scored[scored.phase == ph], in_cell[in_cell.phase == ph]
            row = dict(method=m, phase=ph, **scoring.summarize(s, c))
            for k, (lo, hi) in scoring.bootstrap(s, c, n=args.bootstrap).items():
                row[f"{k}_lo"], row[f"{k}_hi"] = lo, hi
            card.append(row)
            for kind, col, mapping in (("weight", "weight_code", WEIGHT_GROUPS), ("family", "family", None)):
                key = s[col].map(mapping) if mapping else s[col]
                for val in sorted(key.dropna().unique(), key=str):
                    sub = s[key == val]
                    cells = set(zip(sub.event_id, sub.station))
                    csub = c[[x in cells for x in zip(c.event_id, c.station)]]
                    strata.append(dict(method=m, phase=ph, kind=kind, stratum=str(val),
                                       **scoring.summarize(sub, csub)))
    card, strata = pd.DataFrame(card), pd.DataFrame(strata)
    card.to_csv(out / "scorecard.csv", index=False)
    strata.to_csv(out / "strata.csv", index=False)

    b8 = pd.read_csv(run / "B8" / "5_location" / "locations.csv")
    shifts = {m: scoring.location_shift(pd.read_csv(run / m / "5_location" / "locations.csv"), b8)
              for m in args.methods.split(",")}
    pd.concat([d.assign(method=m) for m, d in shifts.items()]).to_csv(out / "location_vs_B8.csv", index=False)

    viz.fig_residuals(scored_all, tol, out / "residuals.png")
    viz.fig_scorecard(card, out / "scorecard.png")
    viz.fig_strata(strata, out / "strata.png")
    viz.fig_location_shift(shifts, out / "location_vs_B8.png")
    (out / "config.json").write_text(json.dumps(dict(tolerance_s=tol, methods=args.methods,
                                                     bootstrap=args.bootstrap), indent=1))
    cols = ["method", "phase", "n_ref", "recall", "precision", "mae_s", "bias_s", "within_005", "within_01", "within_02"]
    print(card[cols].round(3).to_string(index=False))
    print({m: dict(epi_km_median=round(float(d.epi_km.median()), 3),
                   depth_km_median=round(float(d.depth_km.median()), 3)) for m, d in shifts.items()})


if __name__ == "__main__":
    main()
