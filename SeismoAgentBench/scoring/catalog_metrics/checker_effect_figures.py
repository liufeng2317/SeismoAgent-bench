"""Figures of what the checker and the knowledge changed: the back-end tier (B), six cases (analysis only).

The back-end arms share the picks and association of each case's formal tools run and differ by one factor:
``backend`` (tools only), ``backend_checker`` (+ checker skill and contract), ``backend_knowledge`` (+ knowledge
skill and magnitude resource). Every run is judged with the current scorer against the human-in-loop final, as in
``overview_figures.py``. Kīlauea has a second batch (2026-11-03, checker 1.2).

- ``checker_effect_heatmap.png``: per case, every trusted-catalog criterion (value relative to its threshold) for the
  formal full-pipeline tools run (S1) and the back-end arms;
- ``checker_effect_summary.png``: failed criteria per arm and case, and the size of the two kinds of error the checker
  was expected to treat differently: magnitude offset (implementation errors such as units and responses, which the
  checker can see) and time and depth bias (the velocity model, which no reference-free check sees).

Usage: ``python -m SeismoAgentBench.scoring.catalog_metrics.checker_effect_figures [--out DIR]``
(default ``docs/research/assets/checker_effect/``).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from .overview_figures import CASES, CRITERION_LABEL, INK, MUTED, ORDER, TASKS  # noqa: E402
from .trust import trust_verdict  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
ARMS = [("tools", "S1 tools\n(full pipeline)"), ("backend", "B: tools"), ("backend_checker", "B: + checker"),
        ("backend_knowledge", "B: + checker\n+ knowledge")]
ARM_COLOR = {"tools": "#9a9890", "backend": "#eda100", "backend_checker": "#2a78d6", "backend_knowledge": "#1baf7a"}


def runs(case: str) -> list[tuple[str, str, dict]]:
    """(arm, label, headline) for every scored, not excluded run of the four arms, oldest batch first."""
    out = []
    for arm, label in ARMS:
        found = sorted(p for p in (TASKS / case / "runs" / arm).glob("*/*/2*")
                       if (p / "evaluation/metrics.json").is_file() and not (p / "EXCLUDED.md").exists())
        for p in found:
            m = json.loads((p / "evaluation/metrics.json").read_text())
            if not (m.get("completion") or {}).get("completed"):
                continue
            tag = label if len(found) == 1 or arm == "tools" else f"{label}\n{p.name[4:8]}"
            out.append((arm, tag, m["headline"], p.name))
    return out


def cells(head: dict, final: dict) -> tuple[dict, list]:
    v = trust_verdict(head, final, True)
    row = {}
    for dim in v["dimensions"].values():
        for name, chk in dim["checks"].items():
            val, thr, op = chk.get("value"), chk.get("threshold"), chk.get("op")
            if name == "large_events_present":
                row[name] = (0.5 if chk["verdict"] == "pass" else 2.0, chk["verdict"], None)
            elif val is None or thr in (None, 0):
                row[name] = (None, chk["verdict"], val)
            elif op == ">=":
                row[name] = (thr / val if val else 9.9, chk["verdict"], val)
            else:
                row[name] = (abs(val) / thr, chk["verdict"], val)
    return row, v["failed"]


def collect() -> dict:
    data = {}
    for case in CASES:
        base = json.loads((TASKS / case / "evaluation/human_in_loop/metrics_baseline.json").read_text())
        final = base["rows"]["expert_final"]["headline"]
        data[case] = [(arm, label, *cells(h, final), h, rid) for arm, label, h, rid in runs(case)]
    return data


def heatmap(data: dict, out: Path) -> None:
    cmap = LinearSegmentedColormap.from_list("pass_fail", ["#1c5cab", "#86b6ef", "#f0efec", "#f19b8b", "#b8312f"])
    widths = [max(len(v), 1) for v in data.values()]
    fig = plt.figure(figsize=(16, 10.5))
    rows_fig = fig.subfigures(2, 1, hspace=0.06)
    for sub in rows_fig:
        sub.subplots_adjust(left=0.07, right=0.9)
    axes = []
    for r, sub in enumerate(rows_fig):  # each row sized to its own panels (Kīlauea has two batches)
        axes += list(sub.subplots(1, 3, gridspec_kw={"wspace": 0.05, "width_ratios": widths[3 * r:3 * r + 3]}))
    axes = np.array(axes)
    for k, (ax, (case, rows)) in enumerate(zip(axes.ravel(), data.items())):
        grid = np.full((len(ORDER), len(rows)), np.nan)
        for j, (_, _, row, _, _, _) in enumerate(rows):
            for i, name in enumerate(ORDER):
                c = row.get(name)
                if c and c[0] is not None:
                    grid[i, j] = np.log2(max(min(c[0], 8.0), 1 / 8))
        ax.imshow(np.ma.masked_invalid(grid), cmap=cmap, vmin=-3, vmax=3, aspect="auto")
        for j, (_, _, row, _, _, _) in enumerate(rows):
            for i, name in enumerate(ORDER):
                c = row.get(name)
                if not c or c[1] in (None, "insufficient") or c[0] is None:
                    txt = "–"
                else:
                    mark = "✓" if c[1] == "pass" else "✗" if c[1] == "fail" else "?"
                    txt = mark if c[2] is None else f"{mark} {c[2]:.2g}"
                ax.text(j, i, txt, ha="center", va="center", fontsize=6.2,
                        color="#ffffff" if np.isfinite(grid[i, j]) and abs(grid[i, j]) > 1.6 else INK)
        ax.set_xticks(range(len(rows)), [f"{r[1]}\n{len(r[3])} failed" for r in rows], fontsize=6.5)
        for t, r in zip(ax.get_xticklabels(), rows):
            t.set_color(ARM_COLOR[r[0]])
        ax.set_yticks(range(len(ORDER)), [CRITERION_LABEL[n] for n in ORDER] if k % 3 == 0 else [], fontsize=7)
        ax.set_title(CASES[case][0], loc="left", fontsize=9)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xticks(np.arange(-0.5, len(rows)), minor=True)
        ax.set_yticks(np.arange(-0.5, len(ORDER)), minor=True)
        ax.grid(which="minor", color="#fcfcfb", lw=2)
        ax.tick_params(which="minor", length=0)
        if any(r[0] == "tools" for r in rows):  # the full-pipeline run differs in its front end: set it apart
            ax.axvline(0.5, color=INK, lw=1.2)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(-3, 3))
    cb = fig.colorbar(sm, cax=fig.add_axes([0.915, 0.3, 0.01, 0.4]), ticks=[-3, -2, -1, 0, 1, 2, 3])
    cb.ax.set_yticklabels(["≤ 1/8", "1/4", "1/2", "1 (threshold)", "2", "4", "≥ 8"], fontsize=7)
    cb.set_label("value / threshold (blue passes, red fails)", fontsize=7.5)
    fig.suptitle("Back-end tier: the same picks and association, located by three arms (B: tools only; + checker; + checker and knowledge); "
                 "left of the line the formal full-pipeline tools run. One run per arm (Kīlauea: two batches, 11-01 checker 1.0, 11-03 checker 1.2).",
                 x=0.01, ha="left", fontsize=9, color=INK)
    fig.savefig(out / "checker_effect_heatmap.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def summary(data: dict, out: Path) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(14, 4.2), gridspec_kw={"wspace": 0.38})
    arms = [a for a, _ in ARMS[1:]]
    x = {a: i for i, a in enumerate(arms)}
    panels = [("failed criteria", lambda r: len(r[3]), None),
              ("|magnitude offset| (units / response)", lambda r: abs(r[4].get("dmag_median")) if r[4].get("dmag_median") is not None else None, 0.2),
              ("|origin-time bias| vs final (s)", lambda r: abs(r[4].get("time_bias_final_s")) if r[4].get("time_bias_final_s") is not None else None, 0.3),
              ("|depth bias| vs final (km)", lambda r: abs(r[4].get("dz_final_km")) if r[4].get("dz_final_km") is not None else None, 1.0)]
    markers = ["o", "s", "^", "D", "v", "P"]
    for ax, (title, f, thr) in zip(axes, panels):
        for k, (case, rows) in enumerate(data.items()):
            batches = {}
            for r in rows:
                if r[0] in x:
                    batches.setdefault(r[5][:8], {})[r[0]] = f(r)
            for b, vals in batches.items():
                xs = [x[a] for a in arms if vals.get(a) is not None]
                ys = [vals[a] for a in arms if vals.get(a) is not None]
                if len(xs) < 2:
                    continue
                ax.plot(xs, ys, color=MUTED, lw=0.8, alpha=0.7, zorder=1)
                ax.scatter(xs, ys, c=[ARM_COLOR[a] for a in arms if vals.get(a) is not None], marker=markers[k], s=34,
                           edgecolor="#fcfcfb", linewidth=0.8, zorder=2)
        if thr is not None:
            ax.axhline(thr, color=INK, lw=0.8, ls="--")
            ax.text(2.45, thr, "0.2 + final's own offset" if "magnitude" in title else "threshold", fontsize=6.5, color=INK,
                    va="bottom", ha="right")
        ax.set_xticks(range(len(arms)), ["tools", "+ checker", "+ checker\n+ knowledge"], fontsize=7)
        for t, a in zip(ax.get_xticklabels(), arms):
            t.set_color(ARM_COLOR[a])
        ax.set_xlim(-0.4, len(arms) - 0.6)
        ax.set_title(title, fontsize=8.5, loc="left")
        ax.grid(axis="y", color="#e4e3de", lw=0.6)
    handles = [Line2D([], [], marker=markers[k], ls="", color=MUTED, label=CASES[c][0]) for k, c in enumerate(data)]
    fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=7.5, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Back-end tier, per case (lines join the arms of one batch; Kīlauea has two batches). Magnitude offset: errors the checker sees; "
                 "time and depth bias: the velocity model, which no reference-free check sees.", x=0.01, ha="left", fontsize=9, color=INK)
    fig.savefig(out / "checker_effect_summary.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "docs/research/assets/checker_effect")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    data = collect()
    for case, rows in data.items():
        print(case, [(r[1].replace("\n", " "), len(r[3])) for r in rows])
    heatmap(data, a.out)
    summary(data, a.out)
    print("figures:", a.out)


if __name__ == "__main__":
    main()
