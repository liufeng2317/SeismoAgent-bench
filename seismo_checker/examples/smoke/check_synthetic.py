#!/usr/bin/env python3
"""Run the checker on the synthetic inputs and require the expected flags.

Each scenario lists the checks that must flag and the checks that may also flag because they see the
same injected error from another stage; every other check must stay quiet. The clean scenarios must
raise no flag at all. Input notes count as flags here. The model ensemble is off (it needs NonLinLoc and minutes).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[2] / "interface/run.py"
SOURCE = Path(__file__).resolve().parents[2] / "source"
MAGNITUDE_SEES_IT = {"magnitude_range", "magnitude_detection", "b_value", "largest_events_magnitude"}


def magnitude_variants(i: Path) -> None:
    """Catalogs whose magnitudes equal the checker's recomputed standard ML, and the same shifted by -2.68
    (an amplitude in mm used with the constant for nm)."""
    sys.path.insert(0, str(SOURCE))
    import pandas as pd
    from catalog_checker.checks import Data
    from catalog_checker.io import read_catalog, read_picks, read_stations, read_waveform_streams
    from catalog_checker.magnitude_recompute import standard_ml, station_amplitudes
    d = Data(read_catalog(i / "catalog.csv"), read_picks(i / "picks.csv"), read_stations(i / "stations.csv"))
    streams, _, _ = read_waveform_streams(i / "waveforms")
    index = streams[["file", "seed_id", "station_id", "location", "channel", "component", "file_start", "file_end"]].drop_duplicates("file")
    amps = station_amplitudes(d, index, i / "stations.xml", list(d.events.event_id))
    ml = amps.assign(ml=standard_ml(amps.amplitude_nm, amps.hypocentral_km)).groupby("event_id").ml.median()
    cat = pd.read_csv(i / "catalog.csv")
    cat["magnitude"] = cat.event_id.map(ml).round(3)
    cat.to_csv(i / "variants/catalog_ml_consistent.csv", index=False)
    cat.assign(magnitude=cat.magnitude - 2.68).to_csv(i / "variants/catalog_ml_unit_error.csv", index=False)


LOCATION_SEES_IT = {"depth_at_edges", "depth_single_value", "depth_layers", "sp_depth_offset", "travel_time_intercept",
                    "station_residual_azimuth", "station_residual_outliers", "wadati_origin_offset"}


def scenarios(i: Path) -> list[tuple]:
    v = i / "variants"
    base = ["--stations", str(i / "stations.csv")]
    cat, picks = ["--catalog", str(i / "catalog.csv")], ["--picks", str(i / "picks.csv")]
    return [
        ("data_clean", ["--stage", "data", "--waveforms", str(i / "waveforms")] + base, set()),
        ("data_mixed_rates", ["--stage", "data", "--waveforms", str(i / "waveforms_mixed_rates")] + base, {"channel_sample_rates"}),
        ("data_processed_shift", ["--stage", "data", "--waveforms", str(i / "waveforms"),
                                  "--processed-waveforms", str(i / "processed_shifted")] + base, {"processing_time_shift"}),
        ("picks_clean", ["--stage", "picks", "--waveforms", str(i / "waveforms")] + picks + base, set()),
        ("picks_early", ["--stage", "picks", "--waveforms", str(i / "waveforms"), "--picks", str(v / "picks_early_2p5s.csv")] + base,
         {"pick_onset_offset"}),
        ("picks_duplicated", ["--stage", "picks", "--picks", str(v / "picks_duplicated.csv")] + base, {"duplicate_picks"}),
        ("magnitude_clean", ["--stage", "magnitude"] + cat + picks + base, set()),
        ("depth_layer", ["--stage", "location", "--catalog", str(v / "catalog_depth_layer.csv")] + picks + base,
         {"depth_layers", "depth_single_value"}),
        ("magnitude_offset", ["--stage", "magnitude", "--catalog", str(v / "catalog_magnitude_offset.csv")] + picks + base,
         {"magnitude_detection", "magnitude_range"}),
        ("relocation_clean", ["--stage", "relocation", "--catalog", str(v / "relocated_clean.csv"), "--catalog-before", str(i / "catalog.csv")]
         + picks + base, set()),
        ("relocation_shifted", ["--stage", "relocation", "--catalog", str(v / "relocated_shifted.csv"), "--catalog-before", str(i / "catalog.csv")]
         + picks + base, {"relocation_shift"}, LOCATION_SEES_IT),
        ("relocation_collapsed", ["--stage", "relocation", "--catalog", str(v / "relocated_collapsed.csv"), "--catalog-before", str(i / "catalog.csv")]
         + picks + base, {"relocation_thinning"}, LOCATION_SEES_IT | {"relocation_large_moves"}),
        ("magnitude_recompute_consistent", ["--stage", "magnitude", "--catalog", str(v / "catalog_ml_consistent.csv"),
                                            "--waveforms", str(i / "waveforms"), "--stations", str(i / "stations.xml")] + picks,
         set(), MAGNITUDE_SEES_IT),
        ("magnitude_recompute_unit_error", ["--stage", "magnitude", "--catalog", str(v / "catalog_ml_unit_error.csv"),
                                            "--waveforms", str(i / "waveforms"), "--stations", str(i / "stations.xml")] + picks,
         {"magnitude_recompute", "largest_events_magnitude"}, MAGNITUDE_SEES_IT),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    ok = True
    magnitude_variants(args.inputs_dir)
    for name, cli, expected, *allowed in scenarios(args.inputs_dir):
        allowed = allowed[0] if allowed else set()
        out = args.output_dir / name
        proc = subprocess.run([args.python, "-W", "ignore", str(RUN), *cli, "--output-dir", str(out)],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"FAIL {name}: exit {proc.returncode}\n{proc.stderr[-2000:]}")
            ok = False
            continue
        report = json.loads((out / "checker_report.json").read_text())
        flagged = {c["id"] for c in report["checks"] if c["flag"] or (c["kind"] == "input" and c["out_of_range"])}
        good = expected <= flagged and not (flagged - expected - allowed)
        ok &= good
        print(f"{'ok  ' if good else 'FAIL'} {name}: flagged {sorted(flagged) or '-'}" + ("" if good else f", expected {sorted(expected) or '-'}"))
    print("PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
