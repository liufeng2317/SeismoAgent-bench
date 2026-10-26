#!/usr/bin/env python3
"""Figure for stage 70: epicentral error per association x locator, and locator spread vs error."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

EXPERT = Path(__file__).resolve().parents[1]
OUT = EXPERT / "export/r2/70_method_comparison"
# Okabe-Ito (colour-blind safe), one hue per locator in fixed order
LOCATORS = {"nll_gau": ("NLL GAU_ANALYTIC", "#0072B2"), "nll_edt": ("NLL EDT", "#009E73"),
            "nll_edt_ot_wt": ("NLL EDT_OT_WT", "#56B4E9"), "hypoinverse": ("HypoInverse", "#D55E00")}
ASSOC = {"gamma": "GaMMA", "pyocto": "PyOcto", "real": "REAL"}


def main() -> None:
    s = pd.read_csv(OUT / "scores.csv").set_index("catalog")
    ev = pd.read_csv(OUT / "spread_events.csv").dropna(subset=["epi_error_cochran_km"])
    rep = json.loads((OUT / "report.json").read_text())["spread"]["indicators"]
    plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.1, 3.2), gridspec_kw={"width_ratios": [1.1, 1]})
    y = 0
    ticks, labels = [], []
    for k, name in ASSOC.items():
        for j, (loc, (lab, col)) in enumerate(LOCATORS.items()):
            r = s.loc[f"{k}__{loc}"]
            a.plot([r.epi_median_km, r.epi_p90_km], [y, y], color=col, lw=2, solid_capstyle="round")
            a.plot(r.epi_median_km, y, "o", color=col, ms=5, mec="white", mew=0.8,
                   label=lab if k == "gamma" else None)
            y += 1
        ticks.append(y - 2.5)
        labels.append(f"{name}\n(recall {s.loc[f'{k}__nll_gau'].recall_cochran:.3f})")
        y += 0.8
    a.set_yticks(ticks, labels)
    a.invert_yaxis()
    a.set_xlabel("epicentral offset from Cochran et al. 2020 (km)\ndot: median, bar end: 90th percentile")
    a.legend(frameon=False, loc="lower right", fontsize=7)
    a.set_title("(a) Association x locator, same r2 picks", loc="left", fontsize=8)
    a.grid(axis="x", color="0.9", lw=0.6)
    x, err = ev.spread_h_locators_km.clip(lower=0.01), ev.epi_error_cochran_km.clip(lower=0.01)
    top = x >= x.quantile(0.95)
    b.scatter(x[~top], err[~top], s=4, color="0.6", alpha=0.5, lw=0, label="events")
    b.scatter(x[top], err[top], s=7, color="#D55E00", lw=0, label="top 5 % locator spread")
    b.axhline(2.0, color="0.3", lw=0.6, ls="--")
    b.text(0.012, 2.15, "2 km", fontsize=7, color="0.3")
    b.set_xscale("log")
    b.set_yscale("log")
    b.set_xlabel("locator spread (km): largest epicentre\ndistance from the median of 4 locators")
    b.set_ylabel("NLL-GAU offset from Cochran (km)")
    r = rep["spread_h_locators_km"]
    b.set_title(f"(b) Spread vs error  Spearman ρ {r['spearman_rho']:.2f}, "
                f"lift {r['lift_top']:.1f}×\n(NLL σh ρ {rep['erh_km']['spearman_rho']:.2f}, "
                f"RMS ρ {rep['rms_s']['spearman_rho']:.2f})", loc="left", fontsize=8)
    b.legend(frameon=False, loc="lower right", fontsize=7, markerscale=3)
    fig.tight_layout()
    (OUT / "figures").mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / "figures" / f"method_comparison.{ext}", dpi=200)
    print(OUT / "figures" / "method_comparison.png")


if __name__ == "__main__":
    main()
