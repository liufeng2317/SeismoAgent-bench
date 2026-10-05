#!/usr/bin/env python3
"""
Run the bundled Ridgecrest HypoDD + **FDTCC** example with function parameters.

FDTCC **REAL station.dat** and **ttdb.txt** are prepared inside ``run_hypoDD`` when
``fdtcc_prepare_inputs`` is true and a velocity model is passed to
``run_fdtcc_relocation``. No separate prepare step or velocity JSON file is
required.

This example passes all run parameters directly to the public Python API and
does not load ``hypodd_config.json``.

Requires FDTCC binary; ObsPy only when ``tt_db/ttdb.txt`` must be built (missing and
``fdtcc_rebuild_ttdb`` false on first run still triggers build if file absent).
"""
from __future__ import annotations

import sys
from pathlib import Path

from hypodd_runner import (
    EventSelection,
    FDTCCParams,
    HypoDDInputs,
    HypoDDParams,
    Ph2dtParams,
    RuntimeOptions,
    run_fdtcc_relocation,
)


def _example_root() -> Path:
    return Path(__file__).resolve().parent


def _count_sac_under(d: Path) -> int:
    if not d.is_dir():
        return 0
    return sum(1 for p in d.rglob("*") if p.is_file() and p.suffix.lower() == ".sac")


def main() -> None:
    example = _example_root()
    fdtcc_wave_dir_mode = "miniseed"
    waveform_dir_raw = example / "input" / "waveform_temp" / "20190705"
    output_folder = example / "output"

    # When fdtcc_wave_dir_mode=miniseed, waveform_dir_raw is converted or copied
    # into a temporary FDTCC SAC tree. No external fdtcc_config.json is needed:
    # station.dat and ttdb are prepared from station/velocity inputs.
    wave_dir = example / "waveforms"
    need_waveforms_check = fdtcc_wave_dir_mode == "fdtcc_sac" and not waveform_dir_raw

    if need_waveforms_check:
        n_sac = _count_sac_under(wave_dir)
        if n_sac == 0:
            raise SystemExit(
                f"No .sac files under {wave_dir}. FDTCC waveform CC will not contribute "
                f"meaningful dt.cc (see waveforms/README.md)."
            )

    print(
        "Starting HypoDD + FDTCC pipeline "
        f"(cc_engine='fdtcc', output_folder={str(output_folder)!r})",
        file=sys.stderr,
    )
    # Required files and output naming. These are the first values to change for
    # a new study region.
    inputs = HypoDDInputs(
        hypo_root="/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/software/hypoDD/HYPODD/src",
        phase_file=str(example / "input" / "phase_20190705-v2.dat"),
        station_file=str(example / "input" / "station.sta"),
        output_folder=str(output_folder),
        catalog_code="ridgecrest_fdtcc",
    )

    # Event subset and phase parser. These bounds are applied before ph2dt.
    selection = EventSelection(
        phase_format="auto",
        dep_corr=2,
        ot_range=("2019-07-04", "2019-07-07"),
        lat_range=(35.45, 36.05),
        lon_range=(-117.8, -117.25),
    )

    # ph2dt controls event-pair selection for catalog differential times.
    ph2dt = Ph2dtParams(
        minwght=0.0,
        maxdist=70.0,
        maxoffset=5.0,
        mnb=10,
        limobs_pair=8,
        minobs_pair=4,
        maxobs_pair=30,
    )

    # HypoDD inversion settings. Iteration rows are scientific parameters:
    # choose them for the target dataset instead of copying blindly.
    hypodd = HypoDDParams(
        idata=2,
        iphase=3,
        maxdist=100.0,
        iter_rows=(
            (10, 1.0, 0.5, 0.05, 10.0, 1.0, 0.5, 6.0, 20.0, 120.0),
            (20, 1.0, 0.5, 0.05, 10.0, 0.7, 0.3, 4.0, 15.0, 80.0),
        ),
    )

    # FDTCC-specific waveform and travel-time settings. The travel-time bounds
    # must cover event depths and event-station distances in the current task.
    fdtcc = FDTCCParams(
        velocity_layer=(0.0, 2.5, 3.0, 24.5, 32.0),
        velocity_vp=(4.34, 4.34, 5.88, 6.30, 7.74),
        velocity_vs=(2.60, 2.60, 3.50, 3.60, 4.50),
        flags={
            "max_distance_deg": 3.0,
            "max_depth_km": 40.0,
            "distance_step_deg": 0.02,
            "depth_step_km": 2.0,
        },
        waveform_dir_raw=str(waveform_dir_raw),
        wave_dir_mode=fdtcc_wave_dir_mode,
        keep_waveform_temp=False,
        prepare_inputs=True,
        rebuild_ttdb=False,
    )

    # Runtime/grid choices. These are execution controls, not scientific model
    # parameters.
    runtime = RuntimeOptions(
        num_grids=(1, 1),
        xy_pad=(0.06, 0.05),
        num_workers=32,
        keep_grids=False,
    )

    cfg = run_fdtcc_relocation(
        inputs=inputs,
        selection=selection,
        ph2dt=ph2dt,
        hypodd=hypodd,
        fdtcc=fdtcc,
        runtime=runtime,
    )
    print(f"Wrote native HypoDD outputs under {cfg.output_folder}")


if __name__ == "__main__":
    main()
