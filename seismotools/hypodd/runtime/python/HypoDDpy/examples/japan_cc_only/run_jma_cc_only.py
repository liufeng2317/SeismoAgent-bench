#!/usr/bin/env python3
"""Auto-windowed CC-only HypoDD-FDTCC example for the Japan JMA catalog.

This is the single recommended entry point for this example. Edit paths and
function parameters in this script, then run it. The selected catalog is split
into event-count windows before CC-only relocation; if the selection is small,
the planner may produce a single window.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypodd_runner import (  # noqa: E402
    CCOnlyWindowParams,
    EventSelection,
    FDTCCParams,
    HypoDDInputs,
    HypoDDParams,
    Ph2dtParams,
    RuntimeOptions,
    default_fdtcc_flags,
    plan_cc_only_time_windows,
    run_cc_only_auto_time_windows,
    scaled_layered_velocity_model,
)
from prepare_jma_cc_only_inputs import prepare_jma_cc_only_inputs  # noqa: E402


# Edit paths here, then set task-specific values directly in the calls below.
HERE = Path(__file__).resolve().parent
REPO_ROOT = Path("/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/TRACE-1.1")
CATALOG = REPO_ROOT / "examples/japan_aomori/catalog_analysis_JMA/data/catalog/Snet_catalog_full.csv"
MAIN_EARTHQUAKE_CSV = REPO_ROOT / "examples/japan_aomori/catalog_analysis_JMA/data/catalog/main_earthquake.csv"
STATIONS = REPO_ROOT / "examples/japan_aomori/catalog_analysis_JMA/data/stations/japan_stations.txt"
WAVEFORM_ROOT = Path(
    "/ai4earthafs/liufeng/ScienceDiscovery/Japan_Aomori_Mw7.5/continus_wave_sac/miniseed_daily/1_45hz_rotated"
)
SAC_CACHE_DIR = Path(
    "/ai4earthafs/liufeng/ScienceDiscovery/Japan_Aomori_Mw7.5/continus_wave_sac/miniseed_daily/1_45hz_sac"
)
HYPO_ROOT = "/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/software/hypoDD/HYPODD/src"


def main() -> None:
    prepared = prepare_jma_cc_only_inputs(
        catalog=str(CATALOG),
        stations=str(STATIONS),
        waveform_root=str(WAVEFORM_ROOT),
        run_dir=str((HERE / "runs_windows").resolve()),
        start="2025-11-01T00:00:00",
        end="2025-11-12T00:00:00",
        lon_range=(141.0, 144.5),
        lat_range=(38.5, 42.5),
        selection_mode="box",
        center_lon=None,
        center_lat=None,
        radius_km=300.0,
        main_earthquake_csv=str(MAIN_EARTHQUAKE_CSV),
        main_index="",
        max_depth_km=90.0,
        min_mag=None,
        max_events=0,
        max_stations=0,
        station_pad_deg=None,
        vp_km_s=6.2,
        vs_km_s=3.55,
        waveform_station_inventory=str(HERE / "input" / "waveform_station_inventory.csv"),
        rebuild_waveform_station_inventory=False,
    )
    velocity_layer, velocity_vp, velocity_vs = scaled_layered_velocity_model(
        vp_km_s=6.2,
        vp_vs_ratio=6.2 / 3.55,
    )
    inputs = HypoDDInputs(
        hypo_root=HYPO_ROOT,
        phase_file=str(prepared.phase_file),
        station_file=str(prepared.station_file),
        output_folder=str(prepared.output_dir),
        catalog_code="jma_cc_only",
    )
    selection = EventSelection(
        ot_range=("2025-11-01T00:00:00", "2025-11-12T00:00:00"),
        lat_range=prepared.lat_range,
        lon_range=prepared.lon_range,
        phase_format="auto",
    )
    ph2dt = Ph2dtParams(
        maxdist=180.0,
        maxoffset=20.0,
        mnb=12,
        limobs_pair=8,
        minobs_pair=6,
        maxobs_pair=40,
    )
    hypodd = HypoDDParams(
        idata=1,
        iphase=3,
        maxdist=180.0,
        minobs_cc=4,
        minobs_ct=0,
        mod_ratio=6.2 / 3.55,
        mod_top=velocity_layer,
        mod_vel=velocity_vp,
    )
    fdtcc = FDTCCParams(
        flags=default_fdtcc_flags(max_depth_km=90.0),
        waveform_dir_raw=str(WAVEFORM_ROOT.resolve()),
        waveform_temp_basename=str(SAC_CACHE_DIR.resolve()),
        velocity_layer=velocity_layer,
        velocity_vp=velocity_vp,
        velocity_vs=velocity_vs,
        wave_dir_mode="miniseed",
        keep_waveform_temp=True,
        prepare_inputs=True,
        rebuild_ttdb=False,
    )
    runtime = RuntimeOptions(
        num_grids=(1, 1),
        xy_pad=(0.05, 0.05),
        num_workers=64,
        keep_grids=False,
    )
    windows = CCOnlyWindowParams(
        base="day",
        min_events_per_window=300,
        max_events_per_window=1000,
        window_prefix="jma_cc",
        continue_on_error=False,
        skip_existing=False,
    )
    if False:  # Set to True to inspect planned windows without running relocation.
        plans = plan_cc_only_time_windows(
            phase_file=inputs.phase_file,
            ot_range=selection.ot_range,
            lat_range=selection.lat_range,
            lon_range=selection.lon_range,
            phase_format=selection.phase_format,
            base=windows.base,
            min_events_per_window=windows.min_events_per_window,
            max_events_per_window=windows.max_events_per_window,
            window_prefix=windows.window_prefix,
        )
        for plan in plans:
            print(plan.as_dict())
        return

    result = run_cc_only_auto_time_windows(
        inputs=inputs,
        selection=selection,
        ph2dt=ph2dt,
        hypodd=hypodd,
        fdtcc=fdtcc,
        runtime=runtime,
        windows=windows,
    )
    print(
        "CC-only result: "
        f"success={result.success_windows}, failed={result.failed_windows}, "
        f"skipped={result.skipped_windows}"
    )
    print(f"status_csv={result.status_csv}")
    print(f"manifest_json={result.manifest_json}")


if __name__ == "__main__":
    main()
