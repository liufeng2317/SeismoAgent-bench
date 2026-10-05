#!/usr/bin/env python3
"""Run the Japan Aomori catalog-only HypoDD example as one parameter script.

This script prepares the example inputs, writes quick input figures, and runs
catalog-only HypoDD relocation through ``run_catalog_only_relocation``. It does
not load ``hypodd_config.json`` and does not require a separate prepare step.
"""
from __future__ import annotations

import csv
from pathlib import Path

from obspy import UTCDateTime

from hypodd_runner import (
    EventSelection,
    HypoDDInputs,
    HypoDDParams,
    Ph2dtParams,
    RuntimeOptions,
    build_hypodd_inputs,
    run_catalog_only_relocation,
)


EXAMPLE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_ROOT.parents[6]
REGIONAL_DATA = REPO_ROOT / "examples/japan_aomori/catalog_construction_from_JMA/data/regional"
INPUT_DIR = EXAMPLE_ROOT / "input_20251101_20251201"
FIGURE_DIR = EXAMPLE_ROOT / "figures_20251101_20251201"
OUTPUT_DIR = EXAMPLE_ROOT / "output_20251101_20251201"

HYPODD_ROOT = "/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/software/hypoDD/HYPODD/src"
CATALOG_CODE = "japan_aomori_nocc"

LAT_RANGE = (38.5, 42.5)
LON_RANGE = (141.0, 144.5)
DEP_CORR_KM = 0.0
NUM_GRIDS = (1, 1)
XY_PAD = (0.05, 0.05)
NUM_WORKERS = 16
KEEP_GRIDS = True
OT_RANGE = ("2025-11-01", "2025-12-01")

HYPODD_ITER_ROWS = (
    (8, -9.0, -9.0, -9.0, -9.0, 1.0, 0.7, 0.03, 8.0, 120.0),
    (12, -9.0, -9.0, -9.0, -9.0, 0.7, 0.3, 0.02, 5.0, 80.0),
)
HYPODD_MOD_RATIO = 1.73
HYPODD_MOD_TOP = (0.0, 5.0, 10.0, 20.0, 35.0, 50.0, 90.0)
HYPODD_MOD_VEL = (5.4, 5.8, 6.2, 6.6, 7.2, 7.6, 8.05)


def event_time_range(events_csv: Path) -> tuple[UTCDateTime, UTCDateTime]:
    """Return first/last event origin times from a simple event table."""
    first_time = None
    last_time = None
    with events_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ot = UTCDateTime(row["origin_time"])
            if first_time is None:
                first_time = ot
            last_time = ot
    if first_time is None or last_time is None:
        raise RuntimeError(f"No events found in {events_csv}")
    return first_time, last_time


def load_events(phase_path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with phase_path.open(encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 6:
                continue
            rows.append(
                {
                    "latitude": float(parts[1]),
                    "longitude": float(parts[2]),
                    "depth_km": float(parts[3]),
                    "magnitude": float(parts[4]),
                }
            )
    return rows


def load_stations(station_path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with station_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                    "elevation_m": float(row["elevation_m"]),
                }
            )
    return rows


def write_input_figures(phase_path: Path, station_path: Path) -> None:
    """Write compact input map and depth-section diagnostics if matplotlib exists."""
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"Skip input figures: matplotlib is unavailable ({exc})")
        return

    events = load_events(phase_path)
    stations = load_stations(station_path)
    if not events or not stations:
        print("Skip input figures: no events or stations parsed")
        return

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    ev_lon = [r["longitude"] for r in events]
    ev_lat = [r["latitude"] for r in events]
    ev_dep = [r["depth_km"] for r in events]
    st_lon = [r["longitude"] for r in stations]
    st_lat = [r["latitude"] for r in stations]

    fig, ax = plt.subplots(figsize=(8.5, 8.0), constrained_layout=True)
    sc = ax.scatter(ev_lon, ev_lat, c=ev_dep, s=8, cmap="viridis_r", alpha=0.45, linewidths=0)
    ax.scatter(st_lon, st_lat, marker="^", s=36, c="#d62728", edgecolors="white", linewidths=0.35)
    lon_min, lon_max = LON_RANGE
    lat_min, lat_max = LAT_RANGE
    ax.plot(
        [lon_min, lon_max, lon_max, lon_min, lon_min],
        [lat_min, lat_min, lat_max, lat_max, lat_min],
        color="black",
        linewidth=1.0,
        linestyle="--",
    )
    fig.colorbar(sc, ax=ax, shrink=0.82).set_label("Event depth (km)")
    ax.set_title("Japan Aomori no-CC input: events and stations")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linewidth=0.35, alpha=0.35)
    map_path = FIGURE_DIR / "aomori_nocc_event_station_map.png"
    fig.savefig(map_path, dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), constrained_layout=True)
    for ax, xvals, xlabel in (
        (axes[0], ev_lon, "Longitude"),
        (axes[1], ev_lat, "Latitude"),
    ):
        ax.scatter(xvals, ev_dep, s=7, c="#1f77b4", alpha=0.35, linewidths=0)
        ax.invert_yaxis()
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Depth (km)")
        ax.grid(True, linewidth=0.35, alpha=0.35)
    axes[0].set_title("Longitude-depth")
    axes[1].set_title("Latitude-depth")
    fig.suptitle("Japan Aomori no-CC input event depth distribution")
    depth_path = FIGURE_DIR / "aomori_nocc_event_depth_sections.png"
    fig.savefig(depth_path, dpi=220)
    plt.close(fig)
    print(f"wrote {map_path}")
    print(f"wrote {depth_path}")


def main() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    built = build_hypodd_inputs(
        events_csv=str(REGIONAL_DATA / "events.csv"),
        picks_csv=str(REGIONAL_DATA / "picks.csv"),
        stations_csv=str(REGIONAL_DATA / "station.sta"),
        output_dir=str(INPUT_DIR),
    )
    first_time, last_time = event_time_range(REGIONAL_DATA / "events.csv")

    print(f"prepared station file: {built.station_count} stations -> {built.station_path}")
    print(
        f"prepared phase file: {built.event_count} events, {built.pick_row_count} pick rows, "
        f"filled {built.filled_magnitudes} missing/bad magnitudes -> {built.phase_path}"
    )
    write_input_figures(Path(built.phase_path), Path(built.station_path))

    # Required files and native output naming for this prepared input set.
    inputs = HypoDDInputs(
        hypo_root=HYPODD_ROOT,
        phase_file=built.phase_path,
        station_file=built.station_path,
        output_folder=str(OUTPUT_DIR),
        catalog_code=CATALOG_CODE,
    )

    # Event subset and phase parser. These bounds are applied before ph2dt; for
    # full catalogs, split time windows before exceeding native HypoDD limits.
    selection = EventSelection(
        phase_format="auto",
        dep_corr=DEP_CORR_KM,
        ot_range=OT_RANGE,
        lat_range=LAT_RANGE,
        lon_range=LON_RANGE,
    )

    # ph2dt controls how catalog picks are paired into differential times.
    ph2dt = Ph2dtParams(
        minwght=0.0,
        maxdist=180.0,
        maxoffset=20.0,
        mnb=12,
        limobs_pair=8,
        minobs_pair=6,
        maxobs_pair=40,
    )

    # HypoDD inversion and 1-D velocity-model settings. Iteration rows and
    # velocity model should be reviewed for each study region.
    hypodd = HypoDDParams(
        iphase=3,
        maxdist=180.0,
        minobs_ct=0,
        iter_rows=HYPODD_ITER_ROWS,
        mod_ratio=HYPODD_MOD_RATIO,
        mod_top=HYPODD_MOD_TOP,
        mod_vel=HYPODD_MOD_VEL,
    )

    # Runtime/grid choices. These are execution controls, not inversion weights.
    runtime = RuntimeOptions(
        num_grids=NUM_GRIDS,
        xy_pad=XY_PAD,
        num_workers=NUM_WORKERS,
        keep_grids=KEEP_GRIDS,
    )
    result = run_catalog_only_relocation(
        inputs=inputs,
        selection=selection,
        ph2dt=ph2dt,
        hypodd=hypodd,
        runtime=runtime,
    )
    print(f"relocated rows: {result.reloc_rows}")
    print(f"native reloc output: {result.reloc_path}")
    print(f"native residual output: {result.residual_path}")


if __name__ == "__main__":
    main()
