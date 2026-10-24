#!/usr/bin/env python3
"""Plot the focused Ridgecrest comparison: reference, expert, and Claude GLM-5.3.

The three displayed populations are:
  reference       Shelly (2020) catalog
  expert          Human-expert reproduction
  claude glm5.3   featured agent run (default: ``tools`` arm; ``--agent`` selects)

The script reuses the data loading, validation, map conventions, and publication
style from ``plot_evaluation_comparison.py``.  It writes one compact six-panel
figure to ``evaluation/figures/05_three_way_comparison.{png,pdf}``.
"""
import argparse
import importlib.util
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np


TASK = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name("plot_evaluation_comparison.py")

spec = importlib.util.spec_from_file_location("evaluation_comparison", SOURCE)
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)

DISPLAY_LABELS = {
    "shelly": "reference",
    "expert": "expert",
}
def load_populations(agent_key):
    """Load and validate only the three populations shown in this figure."""
    cfg, audit, published, inputs = comparison.house.load_data(comparison.CASE)
    shelly = next(record for record in published if record["key"] == "shelly")

    expert_rows = comparison.read_ours(comparison.EXPERT_CATALOG, "origin_time")
    agent_meta = comparison.AGENT_RUNS[agent_key]
    agent_rows = comparison.read_ours(agent_meta["catalog"], "origin_time_utc")
    if not expert_rows:
        raise ValueError(f"No expert rows in evaluation window: {comparison.EXPERT_CATALOG}")
    if not agent_rows:
        raise ValueError(f"No agent rows in evaluation window: {agent_meta['catalog']}")

    agent_label = f"claude glm5.3 ({agent_key.removeprefix('agent_')})"
    populations = [
        shelly,
        comparison.as_record(
            "expert", "expert", comparison.EXPERT_COLOR, expert_rows
        ),
        comparison.as_record(
            agent_key, agent_label, agent_meta["color"], agent_rows
        ),
    ]
    for record in populations:
        record["label"] = DISPLAY_LABELS.get(record["key"], record["label"])

    selected_inputs = {
        "reference": inputs["shelly"],
        "expert": {
            "path": str(comparison.EXPERT_CATALOG.relative_to(TASK)),
            "plotted_records": len(expert_rows),
        },
        agent_label: {
            "path": str(agent_meta["catalog"].relative_to(TASK)),
            "plotted_records": len(agent_rows),
            "run_id": agent_meta["run_id"],
        },
    }
    return cfg, audit, populations, selected_inputs


def plot_three_way(out, cfg, audit, populations, agent_key,
                   stem="05_three_way_comparison"):
    """Create spatial, magnitude, depth, and temporal three-way comparisons."""
    bounds = cfg["scientific_design"]["candidate_window"]["native_comparison_bounds"]
    fig = plt.figure(figsize=(comparison.house.WIDTH_INCHES, 6.25))
    grid = fig.add_gridspec(
        2,
        3,
        left=0.085,
        right=0.975,
        bottom=0.145,
        top=0.955,
        wspace=0.34,
        hspace=0.48,
    )

    # Top row: identical map encoding, display names, and the fixed
    # reference-box extent for all three panels, so the maps compare
    # directly. Agent events outside the box are clipped and only counted in
    # the red annotation — mostly distant detections that would shrink the
    # main sequence (the task-level atlas shows where they land instead).
    for index, record in enumerate(populations):
        ax = fig.add_subplot(grid[0, index])
        comparison.map_panel(
            ax,
            record,
            bounds,
            audit,
            chr(ord("a") + index),
            record["label"],
        )
        if record["key"] == agent_key:
            # Keep the overflow note clear of the bottom-right event count.
            for text in ax.texts:
                if "outside reference box" in text.get_text():
                    text.set_position((0.04, 0.96))
                    text.set_verticalalignment("top")
        if index:
            ax.set_ylabel("")

    # Bottom-left: magnitude complementary cumulative distribution.
    amag = fig.add_subplot(grid[1, 0])
    for record in populations:
        magnitude = np.sort(record["magnitude"][np.isfinite(record["magnitude"])])
        values, first = np.unique(magnitude, return_index=True)
        amag.step(
            values,
            (len(magnitude) - first) / len(magnitude),
            where="pre",
            color=record["color"],
            lw=1.35,
            label=record["label"],
        )
    amag.set_yscale("log")
    amag.set_xlim(-2, 7.4)
    amag.set_ylim(1e-4, 1.6)
    amag.set_xlabel("Native magnitude")
    amag.set_ylabel("Fraction with magnitude ≥ M")
    amag.legend(frameon=False, loc="lower left", fontsize=6.2)
    comparison.house.panel_label(amag, "d", "Magnitude distribution")

    # Bottom-middle: depth cumulative distribution.
    adepth = fig.add_subplot(grid[1, 1])
    for record in populations:
        depth = np.sort(record["depth_km"][np.isfinite(record["depth_km"])])
        adepth.step(
            depth,
            np.arange(1, len(depth) + 1) / len(depth),
            where="post",
            color=record["color"],
            lw=1.35,
            label=record["label"],
        )
    adepth.set_xlim(0, 20)
    adepth.set_ylim(0, 1)
    adepth.set_xlabel("Native depth (km)")
    adepth.set_ylabel("Cumulative fraction")
    adepth.legend(frameon=False, loc="lower right", fontsize=6.2)
    comparison.house.panel_label(adepth, "e", "Depth distribution")

    # Bottom-right: hourly rate through the fixed 72-hour evaluation window.
    arate = fig.add_subplot(grid[1, 2])
    for record in populations:
        counts, edges = np.histogram(record["hour"], bins=np.arange(73))
        arate.stairs(
            counts,
            edges,
            color=record["color"],
            lw=1.25,
            label=record["label"],
        )
    for key in ("mw6_4", "mw7_1"):
        hour = (
            comparison.parse_time(audit["anchors"][key]["time"]) - comparison.W0
        ).total_seconds() / 3600
        arate.axvline(hour, color="#999999", lw=0.7, ls="--", zorder=0)
        arate.text(
            hour + 0.7,
            0.97,
            f"Mw {audit['anchors'][key]['magnitude']:.1f}",
            transform=arate.get_xaxis_transform(),
            fontsize=6,
            va="top",
        )
    arate.set_xlim(0, 72)
    arate.set_yscale("symlog", linthresh=1)
    arate.set_ylim(0, 2500)
    arate.set_yticks([0, 10, 100, 1000], labels=["0", "10", "100", "1,000"])
    arate.set_xticks([0, 24, 48, 72], labels=["4 Jul", "5 Jul", "6 Jul", "7 Jul"])
    arate.set_xlabel("2019 (UTC)")
    arate.set_ylabel("Events per hour")
    arate.legend(frameon=False, loc="lower right", fontsize=6.2)
    comparison.house.panel_label(arate, "f", "Hourly event rate")

    # A single shared depth scale applies to all three map panels.
    cax = fig.add_axes([0.26, 0.055, 0.48, 0.014])
    colorbar = fig.colorbar(
        plt.cm.ScalarMappable(norm=Normalize(0, 20), cmap="viridis_r"),
        cax=cax,
        orientation="horizontal",
        ticks=[0, 5, 10, 15, 20],
    )
    colorbar.set_label("Native depth (km)", labelpad=3)

    comparison.house.save_figure(fig, out / stem)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, default=TASK)
    parser.add_argument("--agent", default=comparison.FOCUS_AGENT,
                        choices=sorted(comparison.AGENT_RUNS),
                        help="featured agent arm")
    args = parser.parse_args()
    out = args.task_dir / "evaluation" / "figures"
    out.mkdir(parents=True, exist_ok=True)

    cfg, audit, populations, _ = load_populations(args.agent)
    with comparison.house.publication_style():
        plot_three_way(out, cfg, audit, populations, args.agent)

    print({record["label"]: len(record["rows"]) for record in populations})
    print(f"Figure: {out / '05_three_way_comparison.png'}")


if __name__ == "__main__":
    main()
