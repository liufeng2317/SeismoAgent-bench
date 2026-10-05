#!/usr/bin/env python3
"""
Run the bundled Ridgecrest HypoDD **no-CC** example with function parameters.

This example is catalog-only relocation. It calls the public Python function
API directly and does not load ``hypodd_config.json``.
"""
import sys
from pathlib import Path

from hypodd_runner import (
    EventSelection,
    HypoDDInputs,
    HypoDDParams,
    Ph2dtParams,
    RuntimeOptions,
    run_catalog_only_relocation,
)


def _example_root() -> Path:
    return Path(__file__).resolve().parent


def main() -> None:
    example = _example_root()

    phase_file = example / "input" / "phase_20190705-v1.dat"
    station_file = example / "input" / "station.sta"
    output_folder = example / "output"

    print(
        "Starting catalog-only HypoDD relocation "
        "(cc_engine='none', output_folder='./output')",
        file=sys.stderr,
    )
    # Required files and output naming for this catalog-only example.
    inputs = HypoDDInputs(
        hypo_root="/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/software/hypoDD/HYPODD/src",
        phase_file=str(phase_file),
        station_file=str(station_file),
        output_folder=str(output_folder),
        catalog_code="ridgecrest_nocc",
    )

    # Event subset and phase parser. These bounds are applied before ph2dt.
    selection = EventSelection(
        phase_format="auto",
        dep_corr=2,
        ot_range=("2019-07-04", "2019-07-07"),
        lat_range=(35.45, 36.05),
        lon_range=(-117.8, -117.25),
    )

    # ph2dt controls catalog differential-time pairing.
    ph2dt = Ph2dtParams(
        minwght=0.0,
        maxdist=70.0,
        maxoffset=5.0,
        mnb=10,
        limobs_pair=8,
        minobs_pair=4,
        maxobs_pair=30,
    )

    # HypoDD inversion settings. Iteration rows are scientific parameters.
    hypodd = HypoDDParams(
        iphase=3,
        maxdist=100.0,
        iter_rows=(
            (10, 1.0, 0.5, 0.05, 10.0, 1.0, 0.5, 6.0, 20.0, 120.0),
            (20, 1.0, 0.5, 0.05, 10.0, 0.7, 0.3, 4.0, 15.0, 80.0),
        ),
    )

    # Runtime/grid choices. These are execution controls, not model parameters.
    runtime = RuntimeOptions(
        num_grids=(1, 1),
        xy_pad=(0.06, 0.05),
        num_workers=32,
        keep_grids=False,
    )

    result = run_catalog_only_relocation(
        inputs=inputs,
        selection=selection,
        ph2dt=ph2dt,
        hypodd=hypodd,
        runtime=runtime,
    )
    print(f"Wrote {result.reloc_rows} relocated rows to {result.reloc_path}")


if __name__ == "__main__":
    main()
